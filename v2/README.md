# Study Assistant v2.0 — PariShiksha NCERT RAG
**Week 10 Mini-Project · PG Diploma in AI-ML & Agentic AI Engineering · IIT Gandhinagar**

> v1.0 (Wk9) built the retrieval-ready foundation — BM25, chunking, grounded generation.
> v2.0 (Wk10) adds dense embeddings, hybrid RRF retrieval, strict citation-level grounding,
> and honest diagnostic evaluation. Same repo, same corpus, production-shaped upgrade.

---

## The scenario

PariShiksha is an edtech startup serving Class 9 students across Tier-2/3 cities.
The senior science teacher reviewed 30 questions on the v1 prototype and flagged 8 as
"almost right — not wrong enough to escalate, not right enough to ship."

Her three asks for v2.0:
1. **Diagnose the almost-right problem** — retrieval rank? prompt? chunk boundary?
2. **Fix tables and worked examples** — the Wk9 chunker split worked examples mid-row
3. **Source highlighting** — every answer must cite the specific chunk it came from

---

## What's new in v2.0 (Wk10)

| Capability | v1.0 (Wk9) | v2.0 (Wk10) |
|---|---|---|
| PDF loading | PyMuPDF, flat text | PyMuPDF + improved block splitter |
| Chunking | Character-based, 400 chars | Token-aware (tiktoken), 200 tokens max |
| Chunking strategy | Content-type aware | Content-type + sentence-boundary fallback; example blocks kept whole |
| Retrieval | BM25 only | BM25 + Dense (bge-small-en) + Hybrid RRF |
| Vector store | None | Chroma (local persistent, cosine similarity) |
| Embeddings | None | `BAAI/bge-small-en-v1.5` via sentence-transformers (local, free) |
| Generation | Groq LLaMA, basic grounding | Groq LLaMA, strict constraint prompt + `[chunk_id]` inline citations |
| Evaluation | 18 Q, manual | 12 Q across 3 categories, 3-axis scoring, v1 vs v2 delta |
| LLM backend | Groq LLaMA-3.3-70b | Groq LLaMA-3.3-70b (free-tier API) |
| Cost | $0 (Groq free) | $0 (Groq free + local embeddings) |

---

## Tech stack

| Component | Library / Tool |
|---|---|
| LLM | [Groq API](https://console.groq.com) — `llama-3.3-70b-versatile` (free tier) |
| Embeddings | `BAAI/bge-small-en-v1.5` via `sentence-transformers` (local, no API cost) |
| Vector store | `chromadb==0.5.*` — local persistent, cosine similarity |
| Lexical retrieval | `rank-bm25` — BM25Okapi |
| Hybrid fusion | Reciprocal Rank Fusion (RRF, k=60) — custom implementation |
| PDF extraction | `PyMuPDF` (fitz) |
| Token counting | `tiktoken` (cl100k_base encoding) |
| LangChain | `langchain==0.3.*`, `langchain-community`, `langchain-groq` |
| Python | 3.10+ |

---

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/<your-username>/miniProject-NCERT-RAG.git
cd miniProject-NCERT-RAG
```

### 2. Create and activate virtual environment
```bash
python -m venv venv
# Windows CMD:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 3. Install Wk10 dependencies
```bash
cd v2
pip install -r requirements.txt
```

> If `torch` times out, install it first:
> `pip install torch --index-url https://download.pytorch.org/whl/cpu`

### 4. Set up environment variables
```bash
# Windows CMD:
copy .env.example .env
# macOS/Linux:
cp .env.example .env
```
Open `.env` and add your Groq API key. Get a free key at https://console.groq.com/keys

### 5. Download NCERT corpus
Download the full Class 9 Science textbook from the official source and place it in `Book/`:
Book/
└── class 9 science.pdf

**Primary source:** https://ncert.nic.in/textbook.php?iesc1=0-11
> PDFs are NOT committed to this repo per NCERT terms of use.

---

## Running the pipeline (end-to-end)

All commands run from inside `v2/`.

### Step 1 — Build chunks
```bash
python -m src.chunking "../Book/class 9 science.pdf"
# Output: wk10_chunks.json (659 chunks, avg 167 tokens)
```

### Step 2 — Build dense index (embed once, persists to disk)
```bash
python -m src.retrieval
# First run: ~90 seconds to embed 659 chunks locally
# Subsequent runs: instant (loads from .chroma_wk10/)
# Output: retrieval_log.json, BM25 vs Dense comparison printed
```

### Step 3 — Test ask() with strict grounding
```bash
python -m src.ask
# Output: prompt_diff.md (permissive vs strict on 3 queries)
```

### Step 4 — Run evaluation v1 (BM25 baseline)
```bash
python -m src.eval
# Output: eval_raw.csv, eval_scored.csv (fill in 3 score columns manually)
```

### Step 5 — Run evaluation v2 (Hybrid RRF fix)
```bash
python -m src.eval_v2
# Output: eval_v2_scored.csv
```

---

## Evaluation results

### 12-question eval set composition
- 6 direct textbook questions
- 3 paraphrased questions (tests semantic retrieval)
- 2 out-of-scope questions (should refuse)
- 1 out-of-scope-tricky (plausibly answerable — Moon gravity value not in corpus)

### Scores

| Metric | v1 BM25 | v2 Hybrid RRF | Target |
|---|---|---|---|
| Correctness (9 non-OOS) | 83% (7.5/9) | 83% (7.5/9) | ≥ 70% ✅ |
| Grounded (9 non-OOS) | 89% (8/9) | 89% (8/9) | ≥ 80% ✅ |
| Refusal appropriate (4 OOS) | 75% (3/4) | 75% (3/4) | ≥ 75% ✅ |

### Key finding
Q8 ("push a heavy vs light box with same force") was a **wrong refusal in v1** — BM25 failed to
match the paraphrased phrasing to the F=ma chunk. Switching to Hybrid RRF (Stage 5 fix) resolved
this. However, Q4 (atomic mass + 1 amu) regressed — RRF promoted a mole-definition chunk over the
atomic mass chunk. Net delta is zero, demonstrating that single-variable iteration surfaces
trade-offs that multi-change iterations hide.

---

## Key design decisions

| Decision | Choice | Rationale |
|---|---|---|
| Chunk size | 200 tokens (tiktoken) | Aligns index-time and query-time tokenisation; avoids character vs token mismatch |
| Example block handling | Keep whole, never split | Fixes Wk9 Failure Mode 3: example-solution splits |
| Sentence-boundary fallback | Split on `.?!` + capital | Handles PyMuPDF single-`\n` PDFs without double-newline paragraph breaks |
| Embedding model | `BAAI/bge-small-en-v1.5` | Free, local, OSS — no API cost; competitive recall for NCERT English text |
| Vector store | Chroma local persistent | Sufficient for student-scale; no external service needed |
| Hybrid fusion | Reciprocal Rank Fusion (RRF, k=60) | Scale-invariant — BM25 (0–30) and cosine (0–1) scores can't be directly compared |
| Prompt style | Strict constraint | "Refuse if not in context" outperforms "prefer context" on out-of-scope queries |
| Temperature | 0.0 | Deterministic evaluation — reproducible score comparison across prompt versions |
| LLM | Groq LLaMA-3.3-70b | Free-tier API; fast inference; sufficient for NCERT QA |

---

## Failure modes (v2.0 remaining)

See [`fix_memo.md`](fix_memo.md) for the full Stage 5 analysis. Summary:

1. **Multi-part definition splits (Q4)** — atomic mass + 1 amu definition split across two chunks;
   neither alone answers both parts of the question. Fix: chunk stitching for adjacent same-section chunks.
2. **Thin paraphrase answers (Q7)** — retrieves the right chunk but the chunk contains a one-sentence
   mention, not a full explanation. Fix: metadata filter to prefer `content_type=concept` over
   `content_type=example` for definition queries.
3. **Chapter detection over-firing** — 32 chapter labels detected vs 15 actual; all-caps section
   headings misidentified as chapter titles. Fix: TOC-based or page-range detection.

---

## Corpus
- **Source:** https://ncert.nic.in/textbook.php?iesc1=0-11
- **Used:** Full NCERT Class 9 Science textbook (all 15 chapters, 225 pages)
- **PDF not committed** — download from the link above and place in `Book/`

---

## Wk9 → Wk10 progression
| | Wk9 v1 | Wk10 v2 |
|---|---|---|
| Chunks | 439 (character-based) | 659 (token-aware, sentence-boundary) |
| Retrieval | BM25 only | BM25 + Dense + Hybrid RRF |
| Vector store | None | Chroma (local persistent) |
| Citations | Chapter name only | `[chunk_id]` inline per factual claim |
| Eval questions | 18 | 12 (3 categories, harder OOS design) |
| Cost | $0 | $0 |
