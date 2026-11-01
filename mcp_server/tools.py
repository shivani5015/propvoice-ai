import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from fastmcp import FastMCP

from config import RAG
from knowledge.retriever import Retriever

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

NOT_FOUND = "NOT_FOUND"
serper = requests.Session()     
retriever = Retriever(RAG)   
mcp = FastMCP("property")


def local_search(query):
    results = retriever.retrieve(query)

    if not results:
        return NOT_FOUND

    return "\n\n".join(f"Source: {r['source']}\n{r['text']}" for r in results)


# ---------- 4 custom tools ----------

@mcp.tool
def search_properties(query: str) -> str:
    return local_search(query)


@mcp.tool
def search_loan(query: str) -> str:
    return local_search(query)


@mcp.tool
def search_legal(query: str) -> str:
    """Search stamp duty, registration charges, GST, patta, RERA, brokerage and total buying cost."""
    return local_search(query)


@mcp.tool
def search_knowledge(query: str) -> str:
    """Search all property documents."""
    return local_search(query)


# ---------- 5th tool: web search ----------

@mcp.tool
def search_web_tool(query: str) -> str:
    """Search the web using Serper."""
    key = os.getenv("SERPER_API_KEY")

    if not key:
        return "SERPER_API_KEY .env me nahi hai."

    try:
        res = serper.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": key},
            json={"q": query, "gl": "in", "hl": "en", "num": 5},      # gl=in -> India ke result
            timeout=(3, 5),     # 3 sec judne ka, 5 sec jawab ka
        )
        res.raise_for_status()
        data = res.json()
        parts = []

        # answerBox = Google ka seedha jawab (rate, tareekh wagairah). Isme sabse saaf hota hai
        box = data.get("answerBox") or {}
        parts.append(box.get("answer") or box.get("snippet") or "")

        # link nahi bhej rahe -> TTS URL nahi bolega, tokens bhi bachte hain
        for x in data.get("organic", [])[:3]:
            parts.append(f"{x.get('title')}\n{x.get('snippet')}")

        return "\n\n".join(p for p in parts if p) or NOT_FOUND

    except requests.RequestException as e:
        return f"Web search failed: {e}"
