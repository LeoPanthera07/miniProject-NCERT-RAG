import os
from typing import List, Dict
from groq import Groq
from src.config import GROQ_API_KEY, GROQ_MODEL, TOP_K
from src.retrieval import BM25Retriever, DenseRetriever, load_chunks

# ── Groq client ───────────────────────────────────────────────────────────────
_client = Groq(api_key=GROQ_API_KEY)

# ── Prompt templates ──────────────────────────────────────────────────────────

PERMISSIVE_PROMPT = """\
You are a study assistant for NCERT Class 9 Science.
Use the context below to answer the student's question.

Context:
{context}

Question: {question}
Answer:"""

STRICT_PROMPT = """\
You are a study assistant for NCERT Class 9 Science.
Your only knowledge source is the context provided below.

Rules you must follow without exception:
1. If the answer is not present in the context, reply with exactly:
   "I don't have that in my study materials."
   Do not add anything else.
2. After every factual claim, cite the chunk it came from using square
   brackets, e.g. [chunk_a1b2c3].
3. Never use outside knowledge. Never guess. Never infer beyond what the
   context explicitly states.

Context:
{context}

Question: {question}
Answer:"""

# ── Context builder ───────────────────────────────────────────────────────────

def build_context(chunks: List[Dict]) -> str:
    """Format retrieved chunks into a numbered context block with chunk_ids."""
    parts = []
    for i, c in enumerate(chunks, 1):
        parts.append(
            f"[{c['chunk_id']}] (Chapter: {c['chapter']}, Page: {c['page']})\n"
            f"{c['text']}"
        )
    return "\n\n---\n\n".join(parts)


# ── Core ask() function ───────────────────────────────────────────────────────

def ask(
    question: str,
    retriever,                  # BM25Retriever or DenseRetriever instance
    k: int = TOP_K,
    strict: bool = True,        # False = permissive prompt, True = strict prompt
    temperature: float = 0.0,   # always 0 for evaluation
) -> Dict:
    """
    Retrieve top-k chunks and generate a grounded answer.

    Returns:
        {
            "question": str,
            "answer": str,
            "chunks": List[Dict],       # full chunk dicts
            "chunk_ids": List[str],     # just the IDs for easy logging
            "prompt_type": str,         # "strict" or "permissive"
            "is_refusal": bool,         # True if model said it doesn't know
        }
    """
    chunks = retriever.retrieve(question, k=k)
    context = build_context(chunks)
    prompt_template = STRICT_PROMPT if strict else PERMISSIVE_PROMPT
    prompt = prompt_template.format(context=context, question=question)

    response = _client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=512,
    )

    answer = response.choices[0].message.content.strip()
    is_refusal = answer.strip().startswith("I don't have that in my study materials")

    return {
        "question": question,
        "answer": answer,
        "chunks": chunks,
        "chunk_ids": [c["chunk_id"] for c in chunks],
        "prompt_type": "strict" if strict else "permissive",
        "is_refusal": is_refusal,
    }


# ── Quick test + prompt_diff.md generator ────────────────────────────────────

if __name__ == "__main__":
    import json

    chunks = load_chunks()
    bm25 = BM25Retriever(chunks)
    dense = DenseRetriever(chunks)   # loads from Chroma cache instantly

    # 3 test queries: 1 in-scope direct, 1 paraphrased, 1 out-of-scope
    test_cases = [
        {
            "label": "in-scope direct",
            "question": "State the law of conservation of momentum.",
        },
        {
            "label": "paraphrased",
            "question": "Why does a moving ball eventually stop on its own?",
        },
        {
            "label": "out-of-scope",
            "question": "Explain Einstein's theory of special relativity.",
        },
    ]

    prompt_diff_lines = [
        "# Prompt Diff — Permissive vs Strict\n",
        "Testing 3 queries: in-scope direct, paraphrased, out-of-scope.\n",
        "Retriever used: BM25\n",
        "="*60 + "\n",
    ]

    for case in test_cases:
        q = case["question"]
        label = case["label"]
        print(f"\n{'='*60}")
        print(f"[{label.upper()}] {q}")

        # Permissive
        res_p = ask(q, bm25, strict=False)
        print(f"\n  PERMISSIVE:\n  {res_p['answer'][:300]}")

        # Strict
        res_s = ask(q, bm25, strict=True)
        print(f"\n  STRICT:\n  {res_s['answer'][:300]}")
        print(f"  Refusal triggered: {res_s['is_refusal']}")
        print(f"  Cited chunks: {res_s['chunk_ids']}")

        # Write to diff doc
        prompt_diff_lines += [
            f"\n## [{label.upper()}]\n",
            f"**Question:** {q}\n\n",
            f"### Permissive prompt response\n",
            f"{res_p['answer']}\n\n",
            f"### Strict prompt response\n",
            f"{res_s['answer']}\n\n",
            f"**Refusal triggered:** {res_s['is_refusal']}  \n",
            f"**Cited chunk_ids:** {res_s['chunk_ids']}\n\n",
            "-"*60 + "\n",
        ]

    # Save prompt_diff.md
    diff_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "prompt_diff.md"
    )
    with open(diff_path, "w", encoding="utf-8") as f:
        f.writelines(prompt_diff_lines)
    print(f"\n[ask] prompt_diff.md saved → {diff_path}")