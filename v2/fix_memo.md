# Fix Memo — Stage 5

## Failure targeted
**Q8:** "If you push a heavy box and a light box with the same force, which one moves faster?"
- v1 result: REFUSED ("I don't have that in my study materials.")
- Failure category: **Synonym/vocabulary mismatch**
- Root cause: BM25 relies on exact term overlap. The query contains "heavy box",
  "light box", "same force" — none of these phrases appear verbatim in the F=ma
  chunk. BM25 retrieved an unrelated chunk, the strict prompt correctly refused
  because the context didn't contain the answer. The failure was in retrieval,
  not in the prompt.

## Fix implemented
**Switched retriever from BM25 → Hybrid RRF (BM25 + Dense).**

Reciprocal Rank Fusion (RRF) combines BM25 and dense rankings using rank
positions only (score = 1/(60 + rank)), avoiding the scale mismatch between
BM25 scores (0–30+) and cosine similarity (0–1).

Dense retrieval finds the F=ma/inertia chunk semantically even when exact
words don't match. RRF promotes it when BM25 ranks it low.

Single variable changed: retriever only. Prompt, LLM, chunking, eval set —
all identical between v1 and v2.

## Score delta

| Metric | v1 BM25 | v2 Hybrid RRF | Delta |
|---|---|---|---|
| Correctness (9 non-OOS) | 83% (7.5/9) | 83% (7.5/9) | 0 |
| Grounded (9 non-OOS) | 89% (8/9) | 89% (8/9) | 0 |
| Refusal appropriate (4 OOS) | 75% (3/4) | 75% (3/4) | 0 |

## Honest assessment
Q8 was fixed: hybrid retrieved the correct inertia/F=ma chunk and the model
answered correctly with a citation.

However, Q4 ("What is atomic mass and what is 1 amu?") regressed — it answered
partially in v1 but refused in v2. RRF fusion promoted a mole/molecular-mass
chunk (strong in dense) over the atomic mass definition chunk (strong in BM25).
The net score delta is zero.

**What this means:** Hybrid RRF is a better retriever overall for paraphrased
queries, but the fixed k=5 context window means promoting one chunk sometimes
demotes another. The real fix for Q4 is better chunking — the atomic mass
definition and 1 amu definition are likely split across two chunks and neither
alone contains both answers.

## What I would fix in Wk11
For Q4: implement a **chunk stitching** strategy — when a query asks for a
multi-part definition, retrieve the top-2 adjacent chunks from the same section
and merge them into one context block before prompting. This targets the
example-solution split failure mode identified in Wk9 analysis.

For Q7 (still partial): add a metadata filter at retrieval time to prefer
`content_type=concept` chunks over `content_type=example` for definition-style
queries. The ball-stopping question retrieves an example chunk that correctly
mentions opposing force but doesn't explain friction by name.