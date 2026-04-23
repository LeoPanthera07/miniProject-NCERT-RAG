# API Specification

## Base URL
`/api/v1`

---

## 1. Ask Question

### Endpoint
`POST /ask`

### Request
```json
{
  "question": "What is Newton's second law?"
}
```

### Response
```json
{
  "answer": "Newton's second law states...",
  "chunks": [],
  "status": "success"
}
```

---

## 2. Health Check

### Endpoint
`GET /health`

### Response
```json
{
  "status": "ok"
}
```

---

## 3. Evaluate

### Endpoint
`POST /evaluate`

### Request
```json
{
  "question": "",
  "expected_answer": ""
}
```

### Response
```json
{
  "correctness": "yes",
  "grounded": true,
  "status": "evaluated"
}
```

---

## Error Codes
- 400 Invalid request
- 500 Internal server error
