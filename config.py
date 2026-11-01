import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name(".env"))

# ---------- API keys ----------
GROQ_KEY = os.getenv("GROQ_API_KEY")
SARVAM_KEY = os.getenv("SARVAM_API_KEY")
HEADERS = {"api-subscription-key": SARVAM_KEY}

# ---------- audio file paths ----------
os.makedirs("temp_audio", exist_ok=True)
IN_FILE = "temp_audio/in.webm"
OUT_FILE = "temp_audio/out.mp3"

# ---------- models ----------
STT_MODEL = "saaras:v3"
LLM_MODEL = "qwen/qwen3.8-27b"      # non-reasoning -> tez aur kam tokens
TTS_MODEL = "bulbul:v4-flash"
SPEAKER = "simran_en_conversation"

LANG = "en-IN"       # Hindi ke liye "hi-IN" + Hindi speaker (jaise ritu_hi_conversation)

# ---------- RAG settings (ek hi jagah) ----------
RAG = {
    "knowledge_base": {"chunk_size": 500, "chunk_overlap": 80},
    "vector_store":   {"dir": "vector_db"},
    "retrieval":      {"top_k": 2, "min_similarity": 0.32},
}

MAX_TOKENS = 150     # qwen sochta nahi, to itna kaafi hai
