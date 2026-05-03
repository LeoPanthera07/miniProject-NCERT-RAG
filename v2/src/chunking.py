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
    """
    Detect content type from the first 2 lines.
    NCERT uses 'Example X.Y', 'Activity X.Y', 'EXERCISES', 'QUESTIONS' etc.
    """
    first_two = " ".join(text.strip().split("\n")[:2]).lower().strip()

    example_patterns = [
        r"example\s*\d",
        r"activity\s*\d",
        r"worked\s+example",
        r"sample\s+problem",
        r"solved\s+example",
        r"illustration\s*\d",
        r"let\s+us\s+take\s+an\s+example",
    ]
    question_patterns = [
        r"^exercises?[\s\d\.\:]",
        r"^questions?[\s\d\.\:]",
        r"^in\s+text\s+question",
        r"^additional\s+exercise",
        r"^think\s+and\s+discuss",
        r"^\d+\.\s+[a-z].*\?",     # numbered questions ending with ?
    ]

    for pat in example_patterns:
        if re.search(pat, first_two, re.IGNORECASE):
            return "example"
    for pat in question_patterns:
        if re.search(pat, first_two, re.IGNORECASE):
            return "question"
    return "concept"


# ── Section / chapter detection from raw page text ───────────────────────────
_CHAPTER_PATTERN = re.compile(
    r"^chapter\s+\d+|^unit\s+\d+", re.IGNORECASE | re.MULTILINE
)

def extract_chapter_name(text: str, fallback: str = "Unknown") -> str:
    """
    Best-effort chapter name from page text.
    NCERT uses patterns like:
      'CHAPTER 3', 'Chapter 3', '3. ATOMS AND MOLECULES'
    """
    lines = text.split("\n")
    for line in lines:
        line = line.strip()
        # Match "CHAPTER 3" or "Chapter 3" style
        if re.match(r"^chapter\s+\d+", line, re.IGNORECASE) and len(line) < 80:
            return line.title()
        # Match "3. ATOMS AND MOLECULES" style (chapter title as numbered heading)
        if re.match(r"^\d+\.\s+[A-Z][A-Z\s]{5,}", line) and len(line) < 80:
            return line.title()
        # Match all-caps short lines that are likely chapter titles
        if re.match(r"^[A-Z][A-Z\s\-]{4,40}$", line) and len(line) < 60:
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
            # Example/activity blocks: only keep whole if they're substantial
            if content_type == "example" and block_tokens > 20:
                if buffer:
                    chunks.append(_make_chunk(
                        " ".join(buffer), current_chapter,
                        content_type="concept", page=page_num, source=source
                    ))
                    buffer, buffer_tokens = _apply_overlap(buffer)
                chunks.append(_make_chunk(
                    block, current_chapter,
                    content_type="example", page=page_num, source=source
                ))
                continue

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
    """
    Split text into logical blocks.
    Handles both double-newline (paragraph) and single-newline PDFs.
    Also splits on sentence boundaries when blocks are still too large.
    """
    # First try double-newline paragraph splits
    raw_blocks = re.split(r"\n{2,}", text)

    # If that gave us only 1-2 large blocks, fall back to single-newline splits
    if len(raw_blocks) <= 2:
        raw_blocks = re.split(r"\n", text)

    blocks = []
    for b in raw_blocks:
        b = b.strip()
        if len(b) < 30:          # skip page numbers, headers, footers
            continue

        # If a block is still too large (> 1.5× CHUNK_SIZE_TOKENS),
        # split further on sentence boundaries (. ? !)
        if count_tokens(b) > CHUNK_SIZE_TOKENS * 1.5:
            sentence_chunks = _split_on_sentences(b)
            blocks.extend(sentence_chunks)
        else:
            blocks.append(b)

    return blocks


def _split_on_sentences(text: str) -> List[str]:
    """
    Split a large block into sentence groups, each under CHUNK_SIZE_TOKENS.
    Groups sentences greedily until the token limit is reached.
    """
    # Split on sentence-ending punctuation followed by space + capital letter
    sentences = re.split(r'(?<=[.?!])\s+(?=[A-Z])', text)

    groups = []
    current = []
    current_tokens = 0

    for sent in sentences:
        t = count_tokens(sent)
        if current_tokens + t > CHUNK_SIZE_TOKENS and current:
            groups.append(" ".join(current))
            current = []
            current_tokens = 0
        current.append(sent)
        current_tokens += t

    if current:
        groups.append(" ".join(current))

    return groups


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