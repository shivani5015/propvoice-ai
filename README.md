# 🏠 PropVoice AI — Real Estate Voice Assistant

Speak a question about a property, get a spoken answer in about two seconds — answered
**only** from the dealer's own documents, never from the model's own knowledge.

Built around the one question a buyer actually asks: **"total kitna lagega?"** That number
is not the price — it is the price plus down payment, stamp duty, registration and
brokerage, and no listing site tells you the sum. This bot does, out loud.

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

There are two separate jobs, and they run at different times.

**Building the index** — runs once, and again only when `data/` changes:

```
data/ (csv · md · pdf) → load_documents() → chunk_text() → embed() → FAISS → vector_db/
```

Each file type is split the way that suits it, which is what keeps retrieval sharp:

| File | How it is split | Documents | Chunks |
|---|---|---|---|
| `properties.csv` | one row per property | 12 | 12 |
| `home_loan.md` | by section | 1 | 8 |
| `legal_charges.pdf` | one topic per page | 8 | 8 |

Each property row also carries a `summary` column written as a full sentence, because the
embedding model compares meaning — a readable sentence matches a spoken question far
better than a row of `key: value` pairs.

**Answering a question** — runs on every request:

```
mic → Sarvam STT → pick_tool() → MCP tool → FAISS → Groq LLM → Sarvam TTS → speaker
```

### Picking the tool

`pick_tool()` reads the question and matches keywords — no LLM call, so it costs nothing
and takes no time. The order of the checks matters: `search_legal` is checked before
`search_properties`, so *"what is the **total cost** of buying the flat?"* lands on the
charges page rather than on the flat's own row.

### Two filters, not one

A single similarity threshold cannot tell *"a flat in Mansarovar"* (in the data) from
*"a flat in Mumbai"* (not in the data) — the two sentences mean nearly the same thing. So
there are two gates:

1. **The threshold** drops chunks that score below `min_similarity`.
2. **The LLM** is told to answer only from the context, and to say so when it can't. If it
   says it can't, the same question goes to web search instead.

Because of the second gate, the LLM is never asked to answer from an empty context — which
keeps the token count down and stops it from guessing.

---

## Tech

| Part | Used |
|---|---|
| STT / TTS | Sarvam `saaras:v3` / `bulbul:v4-flash` |
| LLM | Groq `qwen/qwen3.8-27b` (non-reasoning, for speed) |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector DB | FAISS `IndexFlatIP` (cosine, exact — no approximation) |
| Tools | MCP over `streamable-http` (FastMCP) |
| Web fallback | Serper |
| Server | FastAPI + Uvicorn |

---

## Measured, not estimated

Every stage is timed and priced in the logs, so these are readings rather than guesses.

| | Latency | Cost |
|---|---|---|
| Answered from documents | **1.5 – 2.1s** | ₹0.07 – 0.15 |
| Refused as off topic | **0.6 – 1.5s** | **₹0.01** |
| Answered from web search | 3.0 – 5.0s | ₹0.16 |

**Average ₹0.10 per query — about ₹104 per 1,000.**

Three things the numbers show. Retrieval is not the bottleneck: it takes 0.07 – 0.3s.
Text-to-speech is both the slowest and the most expensive stage — more than the LLM. And a
single web fallback costs more than all three local stages put together, which is why the
documents are searched first.

What keeps it quick: the MCP connection is opened once and reused, a background task keeps
the model and index warm, the LLM is a non-reasoning model, and the three fixed replies
have their audio cached after first use. All cost rates sit in `config.py`, taken from each
provider's pricing page rather than hardcoded in the logic.

---

## Project structure

```
propvoice-ai/
├── main.py                  # FastAPI app: routes, warm-up task
├── pipeline.py              # STT → tool → LLM → TTS, timings, tokens, cost
├── config.py                # models, RAG settings, cost rates
├── logger.py                # logging setup
├── build_vector_store.py    # builds the index from data/
├── check_scores.py          # tunes min_similarity
├── knowledge/
│   ├── loader.py            # reads csv / md / pdf
│   ├── chunker.py           # splits documents into chunks
│   ├── embeddings.py        # text → 384 numbers
│   ├── vector_store.py      # builds and loads the FAISS index
│   └── retriever.py         # embeds the question, searches, filters by score
├── mcp_server/
│   ├── server.py            # runs the MCP server on port 8001
│   └── tools.py             # the five tools
├── templates/index.html     # mic UI, transcript, per-answer metrics
├── data/                    # the knowledge base
└── logs/                    # voice_agent.log, history.json
```

---

## Run

```bash
pip install -r requirements.txt     # keys go in .env (see .env.example)

python build_vector_store.py        # 1. build the index (once)
python -m mcp_server.server         # 2. MCP server — keep this terminal open
uvicorn main:app --reload           # 3. web app — new terminal
```

Open **http://127.0.0.1:8000**.

`check_scores.py` prints the top similarity score for questions the data *can* answer and
for questions it *cannot*, then suggests the `min_similarity` that separates the two —
so the threshold is measured rather than picked by feel.

---

## Logs

Four lines per question:

```
retriever.py:38 | Retrieved 2 chunks from properties.csv #0 (0.6259) | top score=0.6259 | query: '...'
pipeline.py:227 | STT=0.24s | SEARCH=0.08s | LLM=0.36s | TTS=1.37s | TOTAL=2.05s | tool=search_properties
pipeline.py:229 | TOKENS: in=410 out=19 total=429
pipeline.py:236 | COST (Rs): stt=0.0271 tts=0.048 llm=0.0356 web=0 TOTAL=0.1106
```

The first line is the grounding proof — the exact file and chunk the answer came from,
with its score. The full history, with timings, tokens and cost per turn, is appended to
`logs/history.json`.

---

## Design note

Only the data and the config are domain specific. `loader.py`, `chunker.py`,
`embeddings.py`, `vector_store.py`, `retriever.py` and `main.py` contain nothing about real
estate at all — swapping the documents and a handful of keywords points the same pipeline
at a different domain.

---

*Demo project. Figures in `data/` are sample values — check official sources before any
real decision.*

---

