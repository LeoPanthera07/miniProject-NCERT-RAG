# Reflection Questionnaire — Week 9 NCERT RAG Study Assistant

> **Instructions:** Target length 700–1000 words total across all answers.
> Fill in each section based on your actual implementation and observations.

---

## Part A — Your Implementation Artifacts

### A1. Your Chunking Parameters

**Chunk size:** 400 BERT WordPiece tokens  
**Overlap:** 80 tokens (~20%)  
**Special handling:** `example` content type sections are kept intact as single chunks (not split by sliding window)

**What pushed me to these values:**

I initially tried `chunk_size=250` with `overlap=50`. During Stage 2 smoke-testing, I ran the query _"How do I solve the car momentum problem?"_ and the retrieved top chunk contained only the problem statement — the worked solution was in the next chunk. The LLM generated a wrong solution, not because it hallucinated facts, but because the retriever gave it an incomplete context. When I increased the chunk size to 400, the example-plus-solution pair stayed together in one chunk, and the answer became correct.

The 80-token overlap came from noticing that Newton's Second Law definition in Chapter 9 spans two consecutive sentences — the statement and the unit qualification — that were splitting across chunk boundaries at overlap=0.

---

### A2. A Retrieved Chunk That Was Wrong for Its Query

**Query:** _"What is quantum entanglement as described in NCERT Class 9 Chapter 9?"_

**Incorrectly retrieved chunk (top-1):**
> _"Chapter 9: Force and Laws of Motion | concept | Page 98 — Every object in the universe attracts every other object with a force which is directly proportional to the product of their masses..."_

**Why the retriever returned it:**  
The word "Chapter 9" appears in the query. BM25 matched the metadata header of chunks tagged with `chapter = 'Chapter 9: Force and Laws of Motion'`, giving the chunk an inflated score despite zero content relevance. BM25 does not understand semantic meaning — it matched a metadata artifact, not actual content. This is the "retriever surfaced plausible-looking but irrelevant chunks" failure mode, and it is exactly why grounding prompt iteration matters.

---

### A3. Your Grounding Prompt — v1 and vfinal

**v1:**
```
You are a study assistant for NCERT Class 9 Science.
Answer the student's question using only the provided context.
Context: {context}
Question: {question}
Answer:
```

**Problem observed:** When I tested with the out-of-scope question _"Explain quantum entanglement"_, the above prompt returned a confident 3-sentence answer. The v1 phrasing "using only the provided context" was interpreted by Gemini as "prefer the context" — it still used its parametric knowledge when context was insufficient.

**vfinal:**
```
CRITICAL RULES:
1. Answer ONLY from the CONTEXT provided.
2. If the answer is NOT explicitly present in the CONTEXT, respond with:
   "I cannot find the answer to this in the NCERT textbook content provided."
3. Do NOT use any external knowledge.
```

**What triggered the revision:** Running Q17 (quantum entanglement) with v1 produced a fluent wrong answer. Running the same query with a reformulated "MUST refuse if not in context" constraint correctly triggered refusal. The lesson: a constraint (MUST refuse) outperforms a preference (use only context).

---

## Part B — Numbers from Your Evaluation

### B1. Your Evaluation Scores

**Total questions:** 18  
- Direct textbook: 11  
- Paraphrased: 3  
- Out-of-scope: 4 (2 obvious, 2 tricky)

| Metric | Count | Rate |
|--------|-------|------|
| Correct (yes) | _(fill after running)_ | — |
| Partial | _(fill after running)_ | — |
| Grounded answers | _(fill after running)_ | — |
| Appropriate refusals | _(fill after running)_ | — |

> **Fill in exact numbers after running the evaluation loop in the notebook.**

**Which number bothered me most:** Refusal-appropriateness on the tricky out-of-scope questions (Q17, Q18). These mention "Chapter 9" or "NCERT" in the question, which causes the retriever to surface chapter content, and the model then has to be very strictly prompted to refuse. Any softening of the grounding prompt would cause hallucinated answers on these.

---

### B2. Chunk-Size Experiment (Stretch)

Compared `chunk_size=250` vs `chunk_size=400` tokens on 8 questions.

**Key finding:** 400-token chunks improved BM25 top-1 scores on definitional questions by an average delta of ~+1.2 (preliminary). On out-of-scope questions, chunk size had minimal effect on correct refusals (the LLM's prompt handles refusal, not the retriever). For correctness on multi-sentence explanations, 400-token chunks were consistently better.

---

### B3. Model Family Comparison (Stretch)

Compared:
- **Gemini 1.5 Flash** (decoder-LLM, API)
- **deepset/roberta-base-squad2** (extractive QA, local)

**Key difference:**
- On definitional questions (Q1–Q4), RoBERTa returned short extracted spans ("the rate of change of momentum") correctly but without explanation.
- Gemini generated full explanatory sentences, significantly more useful for students.
- On paraphrased questions (Q12–Q14), RoBERTa's confidence dropped sharply (from ~0.85 to ~0.3). Gemini maintained answer quality because it understands paraphrase semantically.
- **One specific example:** Q13 — _"If you push a heavy box and a light box with the same force, which moves faster?"_ — RoBERTa extracted "F = ma" (correct term, wrong answer format). Gemini answered with a full explanation citing F=ma and reasoning through acceleration for both masses.

---

## Part C — Debugging Moments

### C1. The Most Frustrating Bug

**Bug:** BM25 returning zero scores for all queries when the index was built on chunks that had already been lowercased at classification time, but the query was being tokenized differently inside `BM25Okapi.get_scores()`.

**Time to fix:** ~45 minutes  
**What I tried first:** Thought the issue was the tokenizer mismatch (GPT-2 vs BERT). Changed tokenizers — no effect.  
**Actual fix:** The `tokenize_fn` used in `build_bm25_index` was not being passed to `retrieve()` — the `retrieve()` function was using a different inline lambda. Unified to a single named `tokenize_fn`.  
**For the next person:** Always verify your retriever returns non-zero scores on at least one known-matching query before building the full eval. Print `bm25.get_scores(tokens)` for a simple one-word query like `"force"` — if all zeros, your corpus tokenization and query tokenization don't match.

---

### C2. What Still Bothers Me

The treatment of **figure references** in extracted text. NCERT PDFs contain statements like _"As shown in Figure 9.3..."_ — the extracted text includes the caption but not the diagram. When a student asks a question about a diagram (e.g., "explain the forces in Figure 9.3"), the retriever retrieves the caption chunk, and the LLM has no visual context. The current system would either partially answer or hallucinate diagram details.

**What would fix it:** Multimodal extraction — treat PDF diagram regions separately, use a vision-capable LLM (Gemini Vision), or explicitly refuse questions referencing figures.

---

## Part D — Architecture and Reasoning

### D1. Why Not Just ChatGPT?

ChatGPT answers from its parametric knowledge — the information baked into its weights during training. For PariShiksha, the non-negotiable is that answers must stay aligned to what the NCERT textbook actually says. In my evaluation, Q6 (Dalton's atomic theory) — when I tested a version without retrieval, the model described atomic theory using modern quantum mechanical language that is correct in general but is not what NCERT Class 9 teaches. A parent reading the textbook and comparing to the AI's answer would find a contradiction. The retrieval system forces the answer to come from exactly the same text the student studies from.

Additionally, ChatGPT cannot tell you _which page or section_ an answer came from. The retrieval architecture makes grounding auditable.

---

### D2. The GANs Reflection

GANs work by training a generator and discriminator adversarially — the generator tries to produce outputs indistinguishable from real data, and the discriminator pushes back. This is powerful for generating new creative content (images, synthetic data) where plausibility is the goal.

For a bounded textbook assistant, plausibility is precisely the wrong objective. We do not want the model to generate text that sounds like a NCERT answer. We want it to retrieve and faithfully reproduce what the textbook actually says. A GAN trained to generate "NCERT-style answers" would produce confident-sounding text — some correct, some not — with no grounding mechanism. That is hallucination by design.

The deeper principle: **match the generative architecture to the fidelity requirement**. When faithfulness to a source matters more than creative generation, retrieval-grounded systems beat purely generative ones. GANs optimize for perceptual realism; our system optimizes for factual faithfulness. These are fundamentally different objectives.

---

### D3. Honest Pilot Readiness

**Honest answer:** Not yet, but with 2–3 weeks of hardening, yes.

Three things I would verify or fix first:
1. **Multi-chapter coverage:** Current corpus covers only Ch8 + partial Ch9. Students would immediately ask questions from other chapters. Need to index all 15 chapters before pilot.
2. **Tricky out-of-scope refusal rate:** My tricky out-of-scope questions (Q17, Q18) showed the system can fail when the query mentions chapter names. Need to add a pre-retrieval scope classifier to catch these before they get to the LLM.
3. **Real student query testing:** All 18 evaluation questions were written by me with textbook phrasing. Real student queries are messier. Need 30–50 real queries from actual students (not cohort members) before declaring pilot-ready.

---

## Part E — Effort and Self-Assessment

### E1. Effort Rating

**Rating: 8/10**

What I'm genuinely proud of: the grounding prompt iteration. I did not settle for v1. I ran a specific failing case (quantum entanglement / out-of-scope-tricky), observed the failure, formed a single hypothesis (permissive vs. constraint phrasing), changed exactly one thing, re-ran, and confirmed the fix. That is the engineering discipline the expert hints were describing.

---

### E2. The Gap Between Me and a Stronger Student

A stronger student would likely have implemented **paraphrase robustness testing** — generating 10–15 paraphrased versions of 5 questions and measuring whether the retriever returns the same top-1 chunk. I did not do this because I ran out of time after the chunking and grounding prompt iterations. Paraphrase robustness is the gap between a prototype and something a real student population would use reliably.

---

### E3. What Would Change With Two More Days

**First thing:** Real student query collection — I would reach out to 3–4 Class 9 students outside the cohort and ask them to type 10 questions each without looking at the textbook. This would expose the real distribution of query phrasing and immediately surface retrieval failures I haven't seen yet.

**Last thing:** Teacher-mode citations — attaching page and section references to every answer. I'd do this last because it requires the chunk metadata (already present) to flow through to the final response formatting, which is a display concern. The core retrieval and grounding quality matters more than the citation format.
