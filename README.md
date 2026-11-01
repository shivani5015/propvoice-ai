# 🏠 PropVoice AI — Real Estate Voice Assistant

Speak a question about a property, get a spoken answer in about two seconds — answered
**only** from the dealer's own documents, never from the model's own knowledge.

Built around the one question a buyer actually asks: **"total kitna lagega?"** That number
is not the price — it is the price plus down payment, stamp duty, registration and brokerage.

---

## What it answers

| Tool | Handles | Source |
|---|---|---|
| `search_properties` | price, BHK, area, floor, parking, possession | `properties.csv` |
| `search_loan` | salary needed, CIBIL, down payment, EMI, interest | `home_loan.md` |
| `search_legal` | stamp duty, registration, GST, patta, RERA, **total cost** | `legal_charges.pdf` |
| `search_knowledge` | anything across all documents | all |
| `search_web_tool` | live things documents can't hold — today's repo rate | Serper |

Ask something outside real estate and it refuses in 1.5s with **zero LLM tokens spent**:

> *"Who is the Prime Minister of India?"* → *"I can only answer questions about properties,
> home loans and registration."*

---

## How it works

```
Index (once)      data/ (csv · md · pdf) → chunk → embed → FAISS      21 docs → 28 chunks
Per question      mic → Sarvam STT → pick_tool() → MCP tool → FAISS → Groq → Sarvam TTS
```

If no chunk clears the similarity threshold, the tool returns `NOT_FOUND` and the question
goes to web search instead — so the LLM is never asked to answer from an empty context.

| Part | Used |
|---|---|
| STT / TTS | Sarvam `saaras:v3` / `bulbul:v4-flash` |
| LLM | Groq `qwen/qwen3.8-27b` |
| Embeddings | `all-MiniLM-L6-v2` |
| Vector DB | FAISS `IndexFlatIP` (cosine) |
| Tools | MCP over `streamable-http` (FastMCP) |
| Server | FastAPI + Uvicorn |

---

## Measured, not estimated

Every stage is timed and priced in the logs.

| | Latency | Cost |
|---|---|---|
| Answered from documents | **1.5 – 2.1s** | ₹0.07 – 0.15 |
| Refused as off topic | **0.6 – 1.5s** | **₹0.01** |
| Answered from web search | 3.0 – 5.0s | ₹0.16 |

**Average ₹0.10 per query — about ₹104 per 1,000.** Retrieval itself takes 0.07 – 0.3s;
text-to-speech is both the slowest and the most expensive stage, more than the LLM. All
rates sit in `config.py`, taken from each provider's pricing page.

---

## Run

```bash
pip install -r requirements.txt     # keys go in .env (see .env.example)

python build_vector_store.py        # 1. build the index (once)
python -m mcp_server.server         # 2. MCP server — keep this terminal open
uvicorn main:app --reload           # 3. web app — new terminal
```

Open **http://127.0.0.1:8000**. `check_scores.py` suggests the `min_similarity` that
separates questions the data can answer from ones it cannot.

---

## Logs

```
retriever.py:38 | Retrieved 2 chunks from properties.csv #0 (0.6259) | top score=0.6259 | query: '...'
pipeline.py:227 | STT=0.24s | SEARCH=0.08s | LLM=0.36s | TTS=1.37s | TOTAL=2.05s | tool=search_properties
pipeline.py:229 | TOKENS: in=410 out=19 total=429
pipeline.py:236 | COST (Rs): stt=0.0271 tts=0.048 llm=0.0356 web=0 TOTAL=0.1106
```

The first line is the grounding proof — the exact file and chunk the answer came from.
Full history with timings, tokens and cost goes to `logs/history.json`.

Only the data and config are domain specific; `loader.py`, `chunker.py`, `embeddings.py`,
`vector_store.py`, `retriever.py` and `main.py` contain nothing about real estate at all.

---

*Demo project. Figures in `data/` are sample values — check official sources before any
real decision.*
