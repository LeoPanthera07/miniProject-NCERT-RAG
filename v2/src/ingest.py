import os
import fitz  # PyMuPDF
from typing import List, Dict

def load_pdf_pages(pdf_path: str) -> List[Dict]:
    """
    Load a PDF and return a list of page dicts with raw text + page number.
    We use PyMuPDF (fitz) directly — it's already installed and your Wk9
    corpus works fine with it. We'll add structure on top in chunking.py.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    doc = fitz.open(pdf_path)
    pages = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")  # plain text extraction
        text = text.strip()
        if text:  # skip blank pages
            pages.append({
                "page": page_num + 1,   # 1-indexed to match PDF viewer
                "text": text,
                "source": os.path.basename(pdf_path),
            })

    doc.close()
    print(f"[ingest] Loaded {len(pages)} pages from '{os.path.basename(pdf_path)}'")
    return pages


def load_multiple_pdfs(pdf_paths: List[str]) -> List[Dict]:
    """Load and combine pages from multiple PDFs."""
    all_pages = []
    for path in pdf_paths:
        all_pages.extend(load_pdf_pages(path))
    print(f"[ingest] Total pages loaded: {len(all_pages)}")
    return all_pages


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m src.ingest <path_to_pdf>")
        sys.exit(1)

    pages = load_pdf_pages(sys.argv[1])
    print(f"\nSample page 1 text (first 300 chars):\n{pages[0]['text'][:300]}")
    print(f"\nSample page 2 text (first 300 chars):\n{pages[1]['text'][:300]}")