import os
import csv
from typing import List, Dict
from src.retrieval import BM25Retriever, DenseRetriever, HybridRetriever, load_chunks
from src.ask import ask
from src.eval import EVAL_QUESTIONS   # reuse same 12 questions

def run_eval_v2(retriever, label: str = "hybrid") -> List[Dict]:
    """Re-run full 12-Q eval with the new retriever."""
    results = []
    print(f"\n[eval_v2] Running 12-Q eval with retriever={label}")
    print("="*60)

    for item in EVAL_QUESTIONS:
        res = ask(item["question"], retriever, strict=True)
        row = {
            "id": item["id"],
            "category": item["category"],
            "question": item["question"],
            "answer": res["answer"],
            "is_refusal": res["is_refusal"],
            "chunk_ids": "|".join(res["chunk_ids"]),
            "top_chunk_chapter": res["chunks"][0]["chapter"] if res["chunks"] else "",
        }
        results.append(row)
        status = "REFUSED" if res["is_refusal"] else "ANSWERED"
        print(f"  Q{item['id']:02d} [{item['category']:20s}] → {status}")
        print(f"       {res['answer'][:120]}...")

    return results


def save_scored_template_v2(results: List[Dict], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "id", "category", "question",
            "correctness", "grounded", "refusal_appropriate",
            "is_refusal", "answer", "top_chunk_chapter", "chunk_ids",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow({
                "id": r["id"],
                "category": r["category"],
                "question": r["question"],
                "correctness": "",
                "grounded": "",
                "refusal_appropriate": "",
                "is_refusal": r["is_refusal"],
                "answer": r["answer"],
                "top_chunk_chapter": r["top_chunk_chapter"],
                "chunk_ids": r["chunk_ids"],
            })
    print(f"[eval_v2] Template saved → {path}")


if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))

    chunks = load_chunks()
    bm25 = BM25Retriever(chunks)
    dense = DenseRetriever(chunks)      # loads from Chroma cache
    hybrid = HybridRetriever(bm25, dense)

    results = run_eval_v2(hybrid, label="hybrid_rrf")

    path = os.path.join(BASE_DIR, "eval_v2_scored.csv")
    save_scored_template_v2(results, path)

    print("\n[eval_v2] NEXT STEP:")
    print("  Open eval_v2_scored.csv and fill in the 3 score columns.")
    print("  Then compare Q8 result with eval_scored.csv — did hybrid fix it?")