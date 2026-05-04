import json
import time
from typing import List, Dict, Tuple
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

from src.config import (
    EMBEDDING_MODEL,
    CHROMA_PATH,
    CHUNKS_FILE,
    TOP_K,
)

# ── Load chunks from disk ─────────────────────────────────────────────────────
def load_chunks(path: str = CHUNKS_FILE) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    print(f"[retrieval] Loaded {len(chunks)} chunks")
    return chunks


# ── BM25 Retriever ─────────────────────────────────────────────────────────────
class BM25Retriever:
    def __init__(self, chunks: List[Dict]):
        self.chunks = chunks
        tokenized = [c["text"].lower().split() for c in chunks]
        self.bm25 = BM25Okapi(tokenized)
        print(f"[BM25] Index built over {len(chunks)} chunks")

    def retrieve(self, query: str, k: int = TOP_K) -> List[Dict]:
        scores = self.bm25.get_scores(query.lower().split())
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        results = []
        for idx in top_indices:
            chunk = self.chunks[idx].copy()
            chunk["score"] = round(float(scores[idx]), 4)
            chunk["retriever"] = "bm25"
            results.append(chunk)
        return results


# ── Dense Retriever (Chroma + sentence-transformers) ─────────────────────────
class DenseRetriever:
    COLLECTION_NAME = "ncert_wk10"

    def __init__(self, chunks: List[Dict]):
        self.chunks = chunks
        self.model = SentenceTransformer(EMBEDDING_MODEL)
        self.client = chromadb.PersistentClient(path=CHROMA_PATH)
        self.collection = self._get_or_create_collection(chunks)

    def _get_or_create_collection(self, chunks: List[Dict]):
        collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

        # Only embed if collection is empty — never re-embed on restart
        if collection.count() == 0:
            print(f"[Dense] Embedding {len(chunks)} chunks with '{EMBEDDING_MODEL}'...")
            print("[Dense] This takes ~60-90 seconds on CPU. Only runs once.")
            t0 = time.time()

            texts = [c["text"] for c in chunks]
            ids = [c["chunk_id"] for c in chunks]
            metadatas = [
                {
                    "chapter": c["chapter"],
                    "content_type": c["content_type"],
                    "page": c["page"],
                    "source": c["source"],
                    "token_count": c["token_count"],
                }
                for c in chunks
            ]

            # Embed in batches of 64 to avoid OOM on CPU
            batch_size = 64
            all_embeddings = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                embs = self.model.encode(batch, show_progress_bar=False).tolist()
                all_embeddings.extend(embs)
                print(f"  Embedded {min(i + batch_size, len(texts))}/{len(texts)}...", end="\r")

            collection.add(
                ids=ids,
                documents=texts,
                embeddings=all_embeddings,
                metadatas=metadatas,
            )
            elapsed = time.time() - t0
            print(f"\n[Dense] Embedded and persisted in {elapsed:.1f}s")
        else:
            print(f"[Dense] Collection already has {collection.count()} embeddings — skipping re-embed ✓")

        return collection

    def retrieve(self, query: str, k: int = TOP_K) -> List[Dict]:
        query_embedding = self.model.encode([query])[0].tolist()
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )

        chunks_out = []
        for i in range(len(results["ids"][0])):
            # Chroma cosine distance → similarity: score = 1 - distance
            similarity = round(1 - results["distances"][0][i], 4)
            chunks_out.append({
                "chunk_id": results["ids"][0][i],
                "text": results["documents"][0][i],
                **results["metadatas"][0][i],
                "score": similarity,
                "retriever": "dense",
            })
        return chunks_out

# ── Hybrid Retriever (BM25 + Dense via RRF fusion) ────────────────────────────
class HybridRetriever:
    """
    Reciprocal Rank Fusion (RRF) over BM25 + Dense results.
    RRF score = 1/(k + rank_bm25) + 1/(k + rank_dense)
    k=60 is standard; higher k smooths rank differences.

    Why RRF and not weighted scores?
    BM25 scores (0-30+) and cosine similarity (0-1) are on different scales.
    RRF uses only rank positions, so no normalisation needed.
    """
    RRF_K = 60

    def __init__(self, bm25: BM25Retriever, dense: DenseRetriever):
        self.bm25 = bm25
        self.dense = dense
        print("[Hybrid] RRF retriever ready (BM25 + Dense)")

    def retrieve(self, query: str, k: int = TOP_K) -> List[Dict]:
        # Get top 2k from each retriever to ensure enough candidates for fusion
        fetch_k = min(k * 2, 20)
        bm25_results = self.bm25.retrieve(query, k=fetch_k)
        dense_results = self.dense.retrieve(query, k=fetch_k)

        # Build RRF score map keyed on chunk_id
        rrf_scores = {}
        chunk_map = {}   # chunk_id → chunk dict

        for rank, chunk in enumerate(bm25_results):
            cid = chunk["chunk_id"]
            rrf_scores[cid] = rrf_scores.get(cid, 0) + 1 / (self.RRF_K + rank + 1)
            chunk_map[cid] = chunk

        for rank, chunk in enumerate(dense_results):
            cid = chunk["chunk_id"]
            rrf_scores[cid] = rrf_scores.get(cid, 0) + 1 / (self.RRF_K + rank + 1)
            chunk_map[cid] = chunk

        # Sort by RRF score descending
        ranked = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:k]

        results = []
        for cid, rrf_score in ranked:
            chunk = chunk_map[cid].copy()
            chunk["score"] = round(rrf_score, 6)
            chunk["retriever"] = "hybrid_rrf"
            results.append(chunk)

        return results

# ── Quick comparison test ─────────────────────────────────────────────────────
if __name__ == "__main__":
    chunks = load_chunks()
    bm25 = BM25Retriever(chunks)
    dense = DenseRetriever(chunks)   # embeds once, then persists

    # 10 test queries (your Wk9 eval questions)
    test_queries = [
        "State Newton's second law of motion.",
        "What is Newton's first law of motion?",
        "Define inertia and give an example.",
        "What is momentum? Write its formula.",
        "State the law of conservation of momentum.",
        "What is an atom according to Dalton's atomic theory?",
        "What is atomic mass and what is 1 amu?",
        "State the law of conservation of mass.",
        "What is the universal law of gravitation?",
        "Define work in science and write its SI unit.",
    ]

    print("\n" + "="*70)
    print("BM25 vs Dense Retrieval — Top-1 Comparison")
    print("="*70)

    log = []
    for q in test_queries:
        bm25_top = bm25.retrieve(q, k=1)[0]
        dense_top = dense.retrieve(q, k=1)[0]

        print(f"\nQ: {q}")
        print(f"  BM25  | score={bm25_top['score']:.3f} | ch={bm25_top['chapter'][:25]} | {bm25_top['text'][:80]}...")
        print(f"  Dense | score={dense_top['score']:.3f} | ch={dense_top['chapter'][:25]} | {dense_top['text'][:80]}...")

        log.append({
            "query": q,
            "bm25_chunk_id": bm25_top["chunk_id"],
            "bm25_score": bm25_top["score"],
            "bm25_chapter": bm25_top["chapter"],
            "bm25_top1_text_snippet": bm25_top["text"][:120],
            "dense_chunk_id": dense_top["chunk_id"],
            "dense_score": dense_top["score"],
            "dense_chapter": dense_top["chapter"],
            "dense_top1_text_snippet": dense_top["text"][:120],
        })

    # Save retrieval log
    import json, os
    log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "retrieval_log.json")
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)
    print(f"\n[retrieval] Log saved → {log_path}")