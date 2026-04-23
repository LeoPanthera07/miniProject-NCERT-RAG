# Software Requirements Specification (SRS)

## 1. Introduction

### 1.1 Purpose
This system provides a **retrieval-ready question-answering assistant** for NCERT Class 9 Science, ensuring answers are generated only from textbook context.

### 1.2 Scope
The system:
- extracts NCERT textbook chapters,
- structures them into chunks,
- retrieves relevant chunks,
- generates grounded answers,
- evaluates performance.

This is not a full production RAG pipeline; it is the retrieval-ready foundation.

---

## 2. Stakeholders
- Students
- Tutors
- Parents
- Backend Engineer
- ML Engineer

---

## 3. Functional Requirements

### FR1: PDF Text Extraction
The system shall extract text from NCERT PDF chapters.

### FR2: Content Structuring
The system shall classify extracted text into:
- concepts
- examples
- questions

### FR3: Tokenizer Comparison
The system shall compare at least two tokenizers to inform chunk size decisions.

### FR4: Chunking
The system shall split content into overlapping chunks while preserving semantic boundaries.

### FR5: Retrieval
The system shall retrieve top-k relevant chunks using BM25 or TF-IDF.

### FR6: Grounded Answer Generation
The system shall generate answers only from retrieved chunks.

### FR7: Refusal Logic
The system shall refuse to answer when context is insufficient.

### FR8: Evaluation
The system shall score:
- correctness
- grounding
- refusal behavior

---

## 4. Non-Functional Requirements

### NFR1: Reproducibility
Notebook must run end-to-end on a fresh clone.

### NFR2: Performance
The system shall run on CPU with 8GB RAM minimum.

### NFR3: Reliability
The system must prioritize grounded refusal over hallucinated responses.

### NFR4: Determinism
Evaluation shall use deterministic generation settings.

---

## 5. Data Requirements
Input data:
- NCERT Class 9 Science PDF chapters

Output data:
- chunk store
- retrieved chunks
- generated answers
- evaluation logs

---

## 6. External Interfaces
- LLM API (Gemini / OpenAI)
- PDF extraction libraries
- retrieval libraries

---

## 7. Acceptance Criteria
The project is accepted when:
- extraction works,
- retrieval is relevant,
- answers are grounded,
- evaluation metrics are recorded,
- failures are analyzed.
