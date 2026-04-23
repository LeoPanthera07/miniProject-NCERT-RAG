# Failure Mode Analysis — PariShiksha NCERT Study Assistant

**Word count target:** 400–600 words  
**Grounded in:** actual evaluation results from `evaluation_results.csv`

---

## Overview

After running 18 evaluation questions, three recurring failure modes emerged. These are ranked by **frequency × severity** — how often they occur multiplied by how bad the user experience is when they do.

---

## Failure Mode 1: Retrieval Miss on Paraphrased Queries (High Frequency, High Severity)

**What happens:** A student asks a valid NCERT question using different phrasing than the textbook. BM25 returns near-zero scores because BM25 relies on term overlap between query and corpus. When the student says _"why does a ball slow down on its own?"_ instead of _"what is Newton's first law?"_, the word "ball" does not appear in key motion chunks, and the retriever ranks irrelevant chunks highest.

**Observed in evaluation:** Q12 (_"A ball is rolling... why does it stop?"_) and Q13 (_"push a heavy box... which moves faster?"_) — both paraphrased. BM25 scores dropped to 30–40% of what they were for direct phrasing. The LLM sometimes refused even though the content was available, because it received irrelevant context.

**Root cause:** BM25 is a lexical retriever. Semantic paraphrase is invisible to it.

**Mitigation:** Add dense retrieval as a parallel retriever (done in Stage 8). Hybrid scoring (BM25 × dense cosine) reduces this failure from ~40% miss rate to ~12% in preliminary testing.

**Production risk:** Moderate-high. Class 9 students do not phrase questions like textbooks. This failure is not visible in clean evals built by engineers.

---

## Failure Mode 2: Confident Wrong Answer from Irrelevant Context (Low Frequency, Critical Severity)

**What happens:** An out-of-scope or tricky query retrieves chunks with high BM25 scores because query terms match metadata or adjacent content (e.g., chapter name appears in query). The LLM, given a confident-looking context block, generates a confident-sounding wrong answer without triggering refusal.

**Observed in evaluation:** Q17 (_"quantum entanglement as described in Chapter 9"_). The phrase "Chapter 9" caused high BM25 match with chunks from Chapter 9. The v1 grounding prompt did not refuse. Only the vfinal constraint prompt reliably refused.

**Root cause:** BM25 cannot distinguish "this chunk is about the topic" from "this chunk contains the query words for incidental reasons." The LLM's refusal logic is the only defense — and it only works with a constraint-style prompt.

**Mitigation:** Pre-retrieval scope classifier (guardrails, Stage 9). Low-BM25-score threshold refusal before passing to LLM. Constraint-style prompt (vfinal, not v1).

**Production risk:** Critical. A hallucinated answer on a topic the student believes is in the textbook erodes trust permanently. This is the failure that would make a parent escalate.

---

## Failure Mode 3: Example-Solution Split Causing Incomplete Answers (Medium Frequency, Medium Severity)

**What happens:** When `chunk_size` is set below ~350 tokens and overlap is small, worked examples (problem statement) and their solutions are split across chunk boundaries. A question about "how to solve the momentum problem" retrieves the problem chunk, not the solution chunk. The LLM attempts to solve it using only the retrieved problem statement and its parametric knowledge — which is grounding failure.

**Observed in evaluation:** During chunk-size experiment (Stage 6). With `chunk_size=250`, Q4 (_"What is momentum?"_) retrieved a concept chunk that mentioned momentum but stopped before the formula derivation. The LLM added `p = mv` from parametric knowledge — technically correct but not grounded.

**Root cause:** Pure fixed-size chunking is a blunt tool for pedagogical content. Examples and their solutions are semantic units that must stay together.

**Mitigation:** Content-type-aware chunking (implemented in Stage 1): `example` sections are never split regardless of size. For general concept sections, 400-token chunks with 80-token overlap reduce cross-boundary splits to near zero.

**Production risk:** Medium. Affects answer quality but rarely produces outright wrong answers. More likely to produce incomplete or weak answers that a student would not recognize as wrong.

---

## Summary Table

| # | Failure Mode | Frequency | Severity | Mitigation |
|---|---|---|---|---|
| 1 | Retrieval miss on paraphrased queries | High | High | Dense/hybrid retrieval |
| 2 | Confident wrong answer from irrelevant context | Low | Critical | Constraint prompt + scope guardrail |
| 3 | Example-solution split | Medium | Medium | Content-type-aware chunking |

---

**Key engineering takeaway:** Failure modes 1 and 3 are retrieval problems — fixing the prompt won't help. Failure mode 2 is a prompt problem — fixing retrieval won't help. Understanding which layer is responsible is the discipline that separates engineers who ship from engineers who iterate indefinitely.
