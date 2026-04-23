# Resume Project Summary

## Retrieval-Ready Study Assistant for NCERT Science

Built a **grounded AI study assistant** for **NCERT Class 9 Science** that retrieves textbook context and generates reliable answers using **BM25 retrieval + LLM prompting**, designed as the foundational stage of a Retrieval-Augmented Generation (RAG) pipeline.

### Key Contributions:
- Developed an **end-to-end retrieval-ready QA system** using **PyMuPDF**, **BM25**, and **LLM APIs**
- Designed **semantic chunking + metadata tagging** for textbook concepts, examples, and exercises
- Implemented **grounded prompting logic** to reduce hallucinations and enforce refusal on unsupported questions
- Built an **evaluation framework** measuring correctness, grounding, and refusal appropriateness
- Created **modular AI system architecture docs** including **SRS, HLD, LLD, API Spec, Deployment Architecture**

### Tech Stack:
Python, BM25, FastAPI, Transformers, PyMuPDF, Gemini/OpenAI API, Docker

### Outcome:
Achieved a **retrieval-grounded educational QA prototype** suitable for scaling into a production-grade RAG assistant with dense retrieval and vector search.
