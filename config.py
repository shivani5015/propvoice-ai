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

# ---------- cost (rates provider ke pricing page se - Nov 2026) ----------
USD_TO_INR = 88      # badal jaye to bas yahan update karo

COST = {
    # Sarvam STT -> Rs 0.49 per minute. Frontend 16 kbps pe record karta hai,
    # to 1 sec = ~1.95 KB -> 1 min = ~117 KB -> 0.49 / 117 = 0.00418
    "stt_per_kb": 0.00418,

    # Sarvam TTS bulbul:v4-flash -> Rs 1.00 per 1000 characters
    "tts_per_1k_chars": 1.00,

    # Groq qwen/qwen3.8-27b -> $0.80 input / $4.00 output per 10 lakh tokens
    "llm_in_per_1m": 0.80 * USD_TO_INR,
    "llm_out_per_1m": 4.00 * USD_TO_INR,

    # Serper -> $0.001 per search (free tier me 2500 search free hain)
    "web_per_search": 0.001 * USD_TO_INR,
}
# FAISS aur embeddings local chalte hain -> inka koi API charge nahi (cost = 0)
