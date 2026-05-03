import re
import json
import uuid
import tiktoken
from typing import List, Dict
from src.config import (
    CHUNK_SIZE_TOKENS,
    CHUNK_OVERLAP_TOKENS,
    TIKTOKEN_ENCODING,
    CHUNKS_FILE,
)

# ── Tokenizer (for sizing chunks in tokens, not characters) ───────────────────
_enc = tiktoken.get_encoding(TIKTOKEN_ENCODING)

def count_tokens(text: str) -> int:
    return len(_enc.encode(text))


# ── Content-type detection (same logic you used in Wk9, slightly tightened) ──
_EXAMPLE_PATTERNS = [
    r"^example\s*\d*[\.\:]",
    r"^worked\s+example",
    r"^sample\s+problem",
    r"^solved\s+example",
    r"^activity\s*\d*[\.\:]",
]
_QUESTION_PATTERNS = [
    r"^(exercise|exercises)[\s\d\.\:]",
    r"^(question|questions)[\s\d\.\:]",
    r"^(in\s+text\s+question)",
    r"^\d+\.\s+[A-Z]",   # numbered questions like "1. What is..."
]

def detect_content_type(text: str) -> str:
    first_line = text.strip().split("\n")[0].lower().strip()
    for pat in _EXAMPLE_PATTERNS:
        if re.match(pat, first_line, re.IGNORECASE):
            return "example"
    for pat in _QUESTION_PATTERNS:
        if re.match(pat, first_line, re.IGNORECASE):
            return "question"
    return "concept"


# ── Section / chapter detection from raw page text ───────────────────────────
_CHAPTER_PATTERN = re.compile(
    r"^chapter\s+\d+|^unit\s+\d+", re.IGNORECASE | re.MULTILINE
)

def extract_chapter_name(text: str, fallback: str = "Unknown") -> str:
    """Best-effort chapter name from the first matching heading line."""
    for line in text.split("\n"):
        line = line.strip()
        if _CHAPTER_PATTERN.match(line) and len(line) < 80:
            return line.title()
    return fallback


# ── Core chunker ──────────────────────────────────────────────────────────────
def chunk_pages(pages: List[Dict]) -> List[Dict]:
    """
    Split pages into token-aware, content-type-aware chunks.

    Rules:
    - Chunks are sized in tokens (CHUNK_SIZE_TOKENS), not characters.
    - 'example' blocks are NEVER split mid-block — they're kept whole
      even if they exceed CHUNK_SIZE_TOKENS (up to 2× limit).
    - Overlap of CHUNK_OVERLAP_TOKENS ensures context isn't lost at boundaries.
    - Each chunk gets a unique chunk_id + metadata.
    """
    chunks = []
    current_chapter = "Unknown"

    for page in pages:
        text = page["text"]
        page_num = page["page"]
        source = page["source"]

        # Update chapter tracker if this page has a chapter heading
        detected = extract_chapter_name(text, fallback=current_chapter)
        if detected != "Unknown":
            current_chapter = detected

        # Split page into logical blocks (paragraphs / double-newline breaks)
        blocks = _split_into_blocks(text)

        # Accumulate blocks into token-sized chunks with overlap
        buffer = []
        buffer_tokens = 0

        for block in blocks:
            block_tokens = count_tokens(block)
            content_type = detect_content_type(block)

            # Example blocks: flush buffer first, then keep the whole block intact
            if content_type == "example":
                if buffer:
                    chunks.append(_make_chunk(
                        " ".join(buffer), current_chapter,
                        content_type="concept", page=page_num, source=source
                    ))
                    buffer, buffer_tokens = _apply_overlap(buffer)

                # Keep example whole (allow up to 2× limit)
                chunks.append(_make_chunk(
                    block, current_chapter,
                    content_type="example", page=page_num, source=source
                ))
                continue

            # Normal blocks: accumulate until token limit
            if buffer_tokens + block_tokens > CHUNK_SIZE_TOKENS and buffer:
                chunks.append(_make_chunk(
                    " ".join(buffer), current_chapter,
                    content_type=detect_content_type(" ".join(buffer)),
                    page=page_num, source=source
                ))
                buffer, buffer_tokens = _apply_overlap(buffer)

            buffer.append(block)
            buffer_tokens += block_tokens

        # Flush remaining buffer at end of page
        if buffer:
            chunks.append(_make_chunk(
                " ".join(buffer), current_chapter,
                content_type=detect_content_type(" ".join(buffer)),
                page=page_num, source=source
            ))

    print(f"[chunking] Created {len(chunks)} chunks")
    return chunks


def _split_into_blocks(text: str) -> List[str]:
    """Split text on double newlines (paragraph breaks), clean each block."""
    raw_blocks = re.split(r"\n{2,}", text)
    blocks = []
    for b in raw_blocks:
        b = b.strip().replace("\n", " ")
        # Skip very short blocks (page numbers, headers, footers)
        if len(b) > 30:
            blocks.append(b)
    return blocks


def _apply_overlap(buffer: List[str]) -> tuple:
    """
    Keep the last N tokens worth of blocks as overlap for the next chunk.
    Returns (new_buffer, new_token_count).
    """
    overlap_tokens = 0
    overlap_buffer = []
    for block in reversed(buffer):
        t = count_tokens(block)
        if overlap_tokens + t <= CHUNK_OVERLAP_TOKENS:
            overlap_buffer.insert(0, block)
            overlap_tokens += t
        else:
            break
    return overlap_buffer, overlap_tokens


def _make_chunk(text: str, chapter: str, content_type: str,
                page: int, source: str) -> Dict:
    """Create a chunk dict with all required metadata."""
    return {
        "chunk_id": str(uuid.uuid4())[:12],   # short unique ID
        "text": text.strip(),
        "chapter": chapter,
        "content_type": content_type,         # concept | example | question
        "page": page,
        "source": source,
        "token_count": count_tokens(text),
    }


# ── Persist + load ────────────────────────────────────────────────────────────
def save_chunks(chunks: List[Dict], path: str = CHUNKS_FILE) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)
    print(f"[chunking] Saved {len(chunks)} chunks → {path}")


def load_chunks(path: str = CHUNKS_FILE) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    print(f"[chunking] Loaded {len(chunks)} chunks from {path}")
    return chunks


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    from src.ingest import load_pdf_pages

    if len(sys.argv) < 2:
        print("Usage: python -m src.chunking <path_to_pdf>")
        sys.exit(1)

    pages = load_pdf_pages(sys.argv[1])
    chunks = chunk_pages(pages)
    save_chunks(chunks)

    # Print a quick summary
    from collections import Counter
    types = Counter(c["content_type"] for c in chunks)
    chapters = Counter(c["chapter"] for c in chunks)
    token_counts = [c["token_count"] for c in chunks]

    print(f"\n── Chunk Summary ──────────────────────────")
    print(f"Total chunks : {len(chunks)}")
    print(f"Content types: {dict(types)}")
    print(f"Avg tokens   : {sum(token_counts)/len(token_counts):.1f}")
    print(f"Max tokens   : {max(token_counts)}")
    print(f"Chapters     : {len(chapters)}")

    print(f"\n── Sample chunk (first 'example' type) ───")
    for c in chunks:
        if c["content_type"] == "example":
            print(f"ID      : {c['chunk_id']}")
            print(f"Chapter : {c['chapter']}")
            print(f"Page    : {c['page']}")
            print(f"Tokens  : {c['token_count']}")
            print(f"Text    :\n{c['text'][:400]}")
            break