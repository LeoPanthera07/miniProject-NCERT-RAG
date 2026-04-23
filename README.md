# Retrieval-Ready Study Assistant for NCERT Science

## Project Overview
This project implements a **retrieval-ready grounded question-answering assistant** for **NCERT Class 9 Science**, designed to support students when tutors are unavailable.  
The assistant extracts content from NCERT Science chapters, structures it into semantically meaningful chunks, retrieves relevant content for a student query, and uses an LLM to generate **grounded answers only from textbook context**.

This is the foundational stage of a future **RAG (Retrieval-Augmented Generation)** system.  
The focus of this phase is:
- corpus extraction,
- tokenizer comparison,
- chunking strategy,
- lexical retrieval,
- grounded answer generation,
- evaluation and failure analysis.

---

## Business Context
The project is inspired by an edtech use case where tutoring support is limited, and the study assistant must remain **strictly aligned to NCERT textbook content**.  
The goal is to provide students with reliable answers while minimizing hallucinations and ensuring the system refuses unsupported questions.

---

## Features
- Extracts NCERT Science chapter text from PDF
- Separates content into:
  - concept paragraphs
  - worked examples
  - end-of-chapter questions
- Compares multiple tokenizers for chunking decisions
- Builds a BM25/TF-IDF lexical retrieval system
- Uses an LLM API for grounded answer generation
- Refuses out-of-scope queries
- Evaluates correctness, grounding, and refusal behavior

---

## Project Structure
```bash
.
├── README.md
├── docs
│   ├── SRS.md
│   └── HLD.md
├── notebook.ipynb
├── evaluation_results.csv
└── reflection.md
```

---

## Tech Stack
- Python 3.10+
- PyMuPDF / pdfplumber
- transformers
- tokenizers
- rank_bm25 / scikit-learn
- torch
- Gemini / OpenAI API

---

## Workflow
1. **Extract PDF Text**
2. **Classify Content Sections**
3. **Compare Tokenizers**
4. **Chunk Content with Metadata**
5. **Retrieve Relevant Chunks**
6. **Generate Grounded Answer**
7. **Evaluate Response Quality**

---

## Evaluation Metrics
The system is evaluated on:
- **Correctness**
- **Grounding**
- **Refusal Appropriateness**

---

## Future Enhancements
- Dense retrieval with embeddings
- Cross-encoder reranking
- Guardrails for prompt injection
- Teacher mode with citations
- Multilingual English/Hindi support

---

## Outcome
This project demonstrates:
- practical RAG foundations,
- retrieval design,
- LLM grounding strategies,
- evaluation discipline,
- system design for AI applications.

It is intended as a **portfolio-ready AI engineering project**.
