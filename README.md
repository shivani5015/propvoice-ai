# 🏠 Real Estate - Voice Assistant

A voice assistant for a property dealer. You speak a question, it answers in a human voice —
and it answers **only** from the dealer's own documents, never from the model's own knowledge.

Built around the one question a property buyer actually asks: **"total kitna lagega?"**
That number is not the price — it is the price plus down payment, stamp duty, registration
and brokerage. This bot answers it.

---

## What it answers

| Tool | Handles | Source |
|---|---|---|
| `search_properties` | price, BHK, area, floor, parking, possession | `properties.csv` |
| `search_loan` | salary needed, CIBIL, down payment, EMI, interest, subsidy | `home_loan.md` |
| `search_legal` | stamp duty, registration, GST, patta, RERA, **total buying cost** | `legal_charges.pdf` |
| `search_knowledge` | anything across all documents | all |
| `search_web_tool` | live things documents cannot hold — today's repo rate, circle rate | Serper |

Ask something outside real estate and it refuses instead of guessing:

> **"Who is the Prime Minister of India?"** → *"I can only answer questions about
> properties, home loans and registration."* — in 0.66s, with zero LLM tokens spent.

---

## How it works

**Index** (once, whenever `data/` changes)

```
data/ (csv · md · pdf) → load_documents() → chunk_text() → embed() → FAISS → vector_db/
```

21 documents → 28 chunks. Each CSV row, each PDF page and each markdown section
becomes its own chunk.

**Per question**

```
mic → Sarvam STT → pick_tool() → MCP tool → FAISS → Groq LLM → Sarvam TTS → speaker
```

If nothing in the documents clears the similarity threshold, the tool returns `NOT_FOUND`
and the question goes to web search instead. The LLM is never asked to answer from an
empty context, which keeps both the tokens and the mistakes down.

---

## Tech

| Part | Used |
|---|---|
| Speech to text | Sarvam `saaras:v3` |
| LLM | Groq `qwen/qwen3.8-27b` |
| Text to speech | Sarvam `bulbul:v4-flash` |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector DB | FAISS `IndexFlatIP` (cosine) |
| Tools | MCP over `streamable-http` (FastMCP) |
| Web fallback | Serper |
| Server | FastAPI + Uvicorn |

---

## Measured latency

| Question type | End to end |
|---|---|
| Answered from documents | **2.0 – 3.1s** |
| Refused as off topic | **0.5 – 0.9s** |
| Answered from web search | 4.5 – 6s |

Retrieval itself takes 0.14 – 0.92s. Most of the remaining time is the speech API.

---

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` in the project root:

```
GROQ_API_KEY=your_key
SARVAM_API_KEY=your_key
SERPER_API_KEY=your_key
```

## Run

```bash
python build_vector_store.py     # 1. build the index (once)
python -m mcp_server.server      # 2. MCP server — keep this terminal open
uvicorn main:app --reload        # 3. web app — new terminal
```

Open **http://127.0.0.1:8000**

`check_scores.py` prints the top similarity score for questions that are in the data and
questions that are not, and suggests the `min_similarity` that separates them.

---

## Logs

Every turn writes three lines to `logs/voice_agent.log`:

```
STT=0.25s | SEARCH=0.14s | LLM=1.29s | TTS=1.44s | TOTAL=3.12s | tool=search_legal
TOKENS: in=239 out=24 total=263
USER: Is stamp duty less for a woman? | AI: Yes, stamp duty is 5 percent for a female buyer, compared to 6 percent for a male buyer.
```

The full chat history with per-stage timings and token counts is appended to
`logs/history.json`.

---

## Design note

Only the data and the config are domain specific. `loader.py`, `chunker.py`,
`embeddings.py`, `vector_store.py`, `retriever.py` and `main.py` contain nothing about real
estate at all — the pipeline is the product, the domain is just data.

## Known limitation

Numeric range filtering — *"3 BHK under 50 lakh"* — is not reliable through vector search
alone, because embeddings compare meaning, not magnitude. Doing it properly needs a
metadata filter on top of the vector search, which is the next step for this project.

---

*Demo project. The property, loan and legal figures in `data/` are sample values —
check official sources before any real decision.*