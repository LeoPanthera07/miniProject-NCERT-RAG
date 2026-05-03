import os
from dotenv import load_dotenv

# Resolve path to v2/.env regardless of where the script is run from
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# ── API Keys ──────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY not set. Add it to v2/.env")

# ── LLM (Groq, free-tier) ─────────────────────────────────────────────────────
GROQ_MODEL = "llama-3.3-70b-versatile"   # swap to llama-3.3-70b-versatile if available on your key

# ── Embeddings (local OSS, no API cost) ───────────────────────────────────────
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"  # ~33MB, runs fine on CPU

# ── Chroma ────────────────────────────────────────────────────────────────────
CHROMA_PATH = os.path.join(BASE_DIR, ".chroma_wk10")   # persisted on disk

# ── Chunking ──────────────────────────────────────────────────────────────────
CHUNK_SIZE_TOKENS = 200        # max tokens per chunk
CHUNK_OVERLAP_TOKENS = 40      # overlap between adjacent chunks
TIKTOKEN_ENCODING = "cl100k_base"   # used by both tiktoken and bge-small for rough sizing

# ── Retrieval ─────────────────────────────────────────────────────────────────
TOP_K = 5                      # how many chunks to retrieve

# ── Output files (relative to v2/) ────────────────────────────────────────────
CHUNKS_FILE = os.path.join(BASE_DIR, "wk10_chunks.json")
EVAL_RAW_FILE = os.path.join(BASE_DIR, "eval_raw.csv")
EVAL_SCORED_FILE = os.path.join(BASE_DIR, "eval_scored.csv")