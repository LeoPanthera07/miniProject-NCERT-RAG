# Low Level Design (LLD)

## 1. Module Breakdown

### 1.1 pdf_ingestion.py
Responsible for extracting raw text from NCERT PDF chapters.

**Functions**
- `load_pdf(path)` → loads PDF
- `extract_text(pdf)` → extracts page-wise text

---

### 1.2 content_parser.py
Classifies raw extracted text into semantic sections.

**Functions**
- `identify_sections(text)` → labels:
  - concept
  - example
  - question

---

### 1.3 tokenizer_analysis.py
Compares tokenization behavior.

**Functions**
- `compare_tokenizers(text_samples)` → compares:
  - BERT tokenizer
  - GPT tokenizer

Outputs token counts and boundaries.

---

### 1.4 chunker.py
Creates overlapping chunks with metadata.

**Functions**
- `create_chunks(sections, chunk_size, overlap)`

**Chunk Schema**
```json
{
  "chunk_id": "",
  "chapter": "",
  "section": "",
  "content_type": "",
  "text": ""
}
```

---

### 1.5 retriever.py
Indexes chunks and retrieves top-k relevant chunks.

**Functions**
- `build_index(chunks)`
- `retrieve(query, k=3)`

Uses BM25 / TF-IDF.

---

### 1.6 prompt_builder.py
Creates grounding prompt.

**Functions**
- `build_prompt(question, context_chunks)`

---

### 1.7 generator.py
Calls LLM API.

**Functions**
- `generate_answer(prompt)`

Returns:
```json
{
  "answer": "",
  "confidence": 0.0
}
```

---

### 1.8 evaluator.py
Evaluates system outputs.

**Functions**
- `evaluate_answer(predicted, expected)`
- `log_results()`

---

## 2. Sequence Flow

1. PDF extracted
2. Sections identified
3. Chunks created
4. Chunks indexed
5. Query received
6. Top-k retrieved
7. Prompt built
8. LLM generates answer
9. Evaluator scores output

---

## 3. Error Handling

### PDF extraction failure
Return extraction error log.

### Retrieval miss
Return "insufficient context"

### API timeout
Retry 2 times before failure response

---

## 4. Configurations

```yaml
chunk_size: 500
overlap: 100
top_k: 3
temperature: 0
```
