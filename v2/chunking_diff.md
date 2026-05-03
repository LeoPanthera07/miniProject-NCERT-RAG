# Chunking Diff — Wk9 v1 vs Wk10 v2

## Wk9 Baseline
- **Loader:** PyMuPDF full-text extraction
- **Chunk strategy:** Fixed character-based splits with 80-token overlap
- **Total chunks:** 439
- **Sizing unit:** Characters (not tokens)
- **Content-type awareness:** Concept / example / question via regex on first line
- **Known failure:** Example-solution splits when chunk_size < 350 chars;
  tables flattened into wall of text; chapter detection not reliable

## Wk10 v2 (this run)
- **Loader:** PyMuPDF (same), improved block splitter
- **Chunk strategy:** Token-aware (tiktoken cl100k_base), sentence-boundary fallback
- **Total chunks:** 659
- **Avg tokens:** 167.3 | **Max tokens:** 202
- **Content types:** concept: 603, example: 55, question: 1
- **Sizing unit:** Tokens — index-time and query-time tokenization now match
- **Example handling:** Example/activity blocks kept whole (never split mid-block)
- **Overlap:** 40 tokens (carried forward as context between adjacent chunks)

## Key improvements
1. **Token-aware sizing** — chunk boundaries now align with how the embedding
   model sees text; no more character vs token mismatch
2. **Example blocks preserved** — activity/example sections are flushed as
   atomic units, fixing Failure Mode 3 from Wk9 analysis
3. **Sentence-boundary fallback** — large single-line blocks split on `.?!`
   instead of arbitrary character positions

## Known remaining gaps (for Stage 5 / Wk11)
- Chapter detection over-fires (32 detected vs 15 actual) — all-caps section
  headings like "MOTION", "SCIENCE" are being treated as chapter names.
  Fix: use page number ranges or TOC-based detection.
- Question chunks severely under-detected (1 vs expected ~100+) — NCERT
  exercise sections don't match current regex patterns.
  Fix: detect "EXERCISES" as a section marker and tag all following numbered
  items as questions.