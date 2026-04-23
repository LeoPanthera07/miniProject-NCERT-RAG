# High Level Design (HLD)

## 1. Overview
The system transforms NCERT textbook chapters into a retrieval-ready knowledge base and uses that knowledge to answer student questions with grounded LLM responses.

---

## 2. Architecture

```text
PDF Chapters
    |
    v
Text Extraction Layer
    |
    v
Content Structuring Layer
    |
    v
Chunking + Metadata Layer
    |
    v
Lexical Retrieval Layer
    |
    v
Grounded LLM Answer Generation
    |
    v
Evaluation Layer
```

---

## 3. Components

### 3.1 Text Extraction Layer
Extracts text from PDF chapters using PyMuPDF or pdfplumber.

**Input:** NCERT PDF  
**Output:** raw extracted text

---

### 3.2 Content Structuring Layer
Separates extracted content into:
- concept sections
- examples
- questions

**Output:** labeled sections

---

### 3.3 Chunking Layer
Splits sections into overlapping chunks.

Each chunk contains:
- text
- chapter
- section
- content type

---

### 3.4 Retrieval Layer
Uses BM25/TF-IDF to retrieve top-k relevant chunks for a query.

**Input:** student query  
**Output:** ranked chunks

---

### 3.5 Grounded Generation Layer
Builds prompt using:
- user question
- retrieved chunks

LLM is instructed to:
- answer only from context
- refuse unsupported questions

**Output:** grounded answer

---

### 3.6 Evaluation Layer
Evaluates responses for:
- correctness
- grounding
- refusal

Outputs logs and metrics.

---

## 4. Data Flow

1. PDF chapters ingested
2. Text extracted
3. Sections identified
4. Chunks indexed
5. Query retrieved
6. LLM generates answer
7. Results evaluated

---

## 5. Design Decisions

### Why lexical retrieval first?
Lexical retrieval is interpretable, lightweight, and sufficient for building a retrieval-ready base system.

### Why chunk metadata?
Metadata improves traceability and evaluation.

### Why strict refusal logic?
To minimize hallucinations and preserve trust.

---

## 6. Future Enhancements
- Dense retrieval embeddings
- Hybrid retrieval
- Reranking
- Guardrails
- Multilingual support
- Teacher citations

---

## 7. Deployment Considerations
The current design is prototype-ready and suitable for:
- notebook validation
- low-volume testing

Production deployment would require:
- API orchestration
- logging
- monitoring
- caching
- scalability improvements
