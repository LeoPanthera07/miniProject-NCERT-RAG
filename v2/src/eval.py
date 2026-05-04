import os
import csv
import json
from typing import List, Dict
from src.retrieval import BM25Retriever, DenseRetriever, load_chunks
from src.ask import ask

# ── 12-Question eval set ───────────────────────────────────────────────────────
# 6 direct, 3 paraphrased, 3 out-of-scope (1 plausibly answerable OOS)
EVAL_QUESTIONS = [
    # --- Direct (6) ---
    {
        "id": 1,
        "category": "direct",
        "question": "State Newton's second law of motion.",
    },
    {
        "id": 2,
        "category": "direct",
        "question": "What is the law of conservation of momentum?",
    },
    {
        "id": 3,
        "category": "direct",
        "question": "Define inertia and give an example.",
    },
    {
        "id": 4,
        "category": "direct",
        "question": "What is atomic mass and what is 1 amu?",
    },
    {
        "id": 5,
        "category": "direct",
        "question": "What is the universal law of gravitation?",
    },
    {
        "id": 6,
        "category": "direct",
        "question": "Define work in science and write its SI unit.",
    },
    # --- Paraphrased (3) ---
    {
        "id": 7,
        "category": "paraphrased",
        "question": "Why does a rolling ball slow down and stop even on a flat surface?",
    },
    {
        "id": 8,
        "category": "paraphrased",
        "question": "If you push a heavy box and a light box with the same force, which one moves faster?",
    },
    {
        "id": 9,
        "category": "paraphrased",
        "question": "What is the smallest particle of an element that keeps its chemical identity?",
    },
    # --- Out-of-scope (3) ---
    {
        "id": 10,
        "category": "out-of-scope",
        "question": "Who is the current Prime Minister of India?",
    },
    {
        "id": 11,
        "category": "out-of-scope",
        "question": "Explain Einstein's theory of special relativity and time dilation.",
    },
    {
        "id": 12,
        "category": "out-of-scope-tricky",
        # Plausibly answerable — formula is in corpus but Moon-specific values aren't
        "question": "What is the value of gravitational acceleration on the surface of the Moon?",
    },
]

# ── Run evaluation ─────────────────────────────────────────────────────────────
def run_eval(retriever, label: str = "bm25") -> List[Dict]:
    """Run all 12 questions through ask() and return raw results."""
    results = []
    print(f"\n[eval] Running 12-Q eval with retriever={label}")
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
            "top_chunk_text": res["chunks"][0]["text"][:150] if res["chunks"] else "",
            "top_chunk_chapter": res["chunks"][0]["chapter"] if res["chunks"] else "",
        }
        results.append(row)
        status = "REFUSED" if res["is_refusal"] else "ANSWERED"
        print(f"  Q{item['id']:02d} [{item['category']:20s}] → {status}")
        print(f"       {res['answer'][:120]}...")

    return results


def save_raw_csv(results: List[Dict], path: str) -> None:
    if not results:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    print(f"\n[eval] Raw results saved → {path}")


def save_scored_template(results: List[Dict], path: str) -> None:
    """
    Save a CSV pre-filled with answer and refusal columns.
    You fill in: correctness, grounded, refusal_appropriate manually.
    """
    with open(path, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "id", "category", "question",
            "correctness",          # fill in: yes / partial / no
            "grounded",             # fill in: true / false
            "refusal_appropriate",  # fill in: yes / no / N/A
            "is_refusal",
            "answer",
            "top_chunk_chapter",
            "chunk_ids",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow({
                "id": r["id"],
                "category": r["category"],
                "question": r["question"],
                "correctness": "",          # YOU fill this in
                "grounded": "",             # YOU fill this in
                "refusal_appropriate": "",  # YOU fill this in
                "is_refusal": r["is_refusal"],
                "answer": r["answer"],
                "top_chunk_chapter": r["top_chunk_chapter"],
                "chunk_ids": r["chunk_ids"],
            })
    print(f"[eval] Scoring template saved → {path}")
    print("       Open it, read each answer, fill in the 3 blank columns.")


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))

    chunks = load_chunks()
    bm25 = BM25Retriever(chunks)
    dense = DenseRetriever(chunks)  # loads from Chroma cache instantly

    # Run with BM25 (Stage 4 baseline — we diagnosed BM25 weaknesses in Stage 2)
    results = run_eval(bm25, label="bm25")

    raw_path = os.path.join(BASE_DIR, "eval_raw.csv")
    scored_path = os.path.join(BASE_DIR, "eval_scored.csv")

    save_raw_csv(results, raw_path)
    save_scored_template(results, scored_path)

    print("\n[eval] NEXT STEP:")
    print("  1. Open eval_scored.csv")
    print("  2. Read each answer carefully")
    print("  3. Fill in 'correctness', 'grounded', 'refusal_appropriate'")
    print("  4. Save and tell me the scores — we'll do Stage 5 next.")