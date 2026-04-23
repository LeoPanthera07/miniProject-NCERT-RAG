# Deployment Architecture

## 1. Deployment Goal
Deploy the study assistant as a lightweight API service for low-latency grounded Q&A.

---

## 2. Architecture Diagram

```text
Client App / Web UI
        |
        v
     FastAPI
        |
        +----------------------+
        |                      |
        v                      v
 Retrieval Service        LLM Service
 (BM25/TF-IDF)           (Gemini/OpenAI)
        |
        v
 Chunk Store
 (JSON / SQLite)
```

---

## 3. Components

### 3.1 FastAPI Backend
Handles:
- `/ask`
- `/health`
- `/evaluate`

### 3.2 Retrieval Service
Loads indexed chunks and returns top-k results.

### 3.3 LLM Service
Generates grounded answers using retrieved chunks.

### 3.4 Chunk Store
Stores structured chunks:
- JSON for prototype
- SQLite for scale

---

## 4. Deployment Stack
- FastAPI
- Uvicorn
- Docker
- SQLite
- Gemini/OpenAI API

---

## 5. Containerization

```dockerfile
FROM python:3.10
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 6. Production Improvements
- Redis cache
- PostgreSQL
- Vector DB
- Monitoring
- CI/CD pipeline
