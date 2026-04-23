# Evaluation Plan

## 1. Objective
Measure how reliably the system answers textbook questions while remaining grounded in retrieved context.

---

## 2. Evaluation Dataset
Use:
- 10 direct textbook questions
- 3 paraphrased questions
- 3 out-of-scope questions

Total: **16 questions**

---

## 3. Metrics

### 3.1 Correctness
Scored as:
- Yes
- Partial
- No

### 3.2 Grounding
Checks whether answer is supported by retrieved chunks.

### 3.3 Refusal Appropriateness
Checks whether unsupported questions are refused.

---

## 4. Success Threshold
- Correctness ≥ 70%
- Grounding ≥ 80%
- Refusal ≥ 75%

---

## 5. Error Taxonomy
Track failures by:
- retrieval miss
- partial grounding
- hallucination
- incorrect refusal

---

## 6. Reporting Format

```csv
question,correctness,grounded,refusal,notes
```

---

## 7. Improvement Loop
1. Identify failures
2. Inspect retrieved chunks
3. Improve chunking / prompt
4. Re-run evaluation
