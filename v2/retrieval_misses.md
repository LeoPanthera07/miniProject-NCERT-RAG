# Retrieval Misses Analysis — Wk10 Stage 2

## BM25 Misses

**Q4: "What is momentum? Write its formula."**
- BM25 top-1: chunk about "carbon tetrachloride" (chapter: Science)
- BM25 score: 10.182 (low — signal of weak match)
- Diagnosis: **Vocabulary mismatch**. The word "formula" appears heavily in
  chemistry chapters (molecular formulas), so BM25 retrieves a chemistry chunk
  instead of the physics momentum definition. BM25 cannot distinguish
  "formula" in a physics vs chemistry context.

**Q9: "What is the universal law of gravitation?"**
- BM25 top-1: retrieved a question/exercise chunk ("What happens to the force
  between two objects...") rather than the definition chunk.
- Diagnosis: **Exercise chunk ranked above concept chunk**. BM25 found high
  term overlap with the exercise chunk because it contains the words
  "universal", "law", "gravitation" — but it's a question, not the answer.
  Content-type filtering at retrieval time would fix this.

**Q10: "Define work in science and write its SI unit."**
- BM25 chapter detected as "Ork And" — chapter name extraction mangled
  "Work And Energy".
- Diagnosis: **Chapter detection bug** (all-caps line regex truncated the
  heading). Cosmetic issue — the chunk text is still from the right chapter.

## Dense Misses

**Q1: "State Newton's second law of motion."**
- Dense top-1: chunk about "Two objects of masses 100g and 200g moving along
  the same line" (a worked example, not the law definition).
- Dense score: 0.759 (moderate — not confident)
- Diagnosis: **Semantic proximity to application, not definition**. The
  embedding model finds the numerical example semantically close to "second
  law" because it's in the same conceptual neighbourhood. A reranker would
  demote this in favour of the definitional chunk.

**Q8: "State the law of conservation of mass."**
- Dense top-1: chunk about "SI unit of force is kg m s⁻²... newton"
- Dense score: 0.744 (low)
- Diagnosis: **Cross-chapter semantic bleed**. "Conservation", "mass", and
  "law" appear in physics chapters too (conservation of momentum, mass of
  newton). Dense embeddings conflate these related but distinct concepts.
  BM25 handles this better because "conservation of mass" as an exact phrase
  is rare outside the chemistry chapter.

## Summary

| Query | BM25 | Dense | Winner |
|---|---|---|---|
| Newton's second law | ✓ correct | ✗ wrong (example chunk) | BM25 |
| Newton's first law | ✓ correct | ✓ correct | Tie |
| Inertia + example | ✓ correct | ✓ correct | Tie |
| Momentum formula | ✗ wrong (chemistry) | ✓ correct | Dense |
| Conservation of momentum | ✓ correct | ✓ correct | Tie |
| Dalton's atomic theory | ✓ correct | ✓ correct | Tie |
| Atomic mass / amu | ✓ correct | ✓ correct | Tie |
| Conservation of mass | ✓ correct | ✗ wrong (force chunk) | BM25 |
| Universal law of gravitation | ✗ wrong (exercise chunk) | ✓ correct | Dense |
| Work and SI unit | ✓ correct | ✓ correct | Tie |

**BM25 wins: 5 | Dense wins: 3 | Ties: 5 | Neither correct: 0**

Key insight: BM25 is stronger on exact scientific phrases and law names.
Dense is stronger on paraphrased/semantic queries and cross-chapter concepts.
Hybrid retrieval (RRF fusion) should eliminate most of these individual misses.