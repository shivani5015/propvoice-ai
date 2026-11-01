"""Har sawal ka top score dikhata hai -> min_similarity kitna rakhna hai, ye tay karne ke liye."""

from config import RAG
from knowledge.retriever import Retriever

# HAI  = data me hai, score UPAR hona chahiye
# NAHI = data me nahi, score NEECHE hona chahiye (tabhi Serper chalegi)
TESTS = [
    # --- properties ---
    ("HAI ", "What is the price of the 3 BHK flat in Mansarovar?"),
    ("HAI ", "Do you have any plot on Ajmer Road?"),
    ("HAI ", "When will I get possession of the Sanganer flat?"),
    ("HAI ", "Which is the cheapest flat you have?"),
    # --- home loan ---
    ("HAI ", "How much salary do I need for a home loan?"),
    ("HAI ", "What will be the EMI on a 50 lakh loan?"),
    ("HAI ", "How much down payment do I have to pay?"),
    ("HAI ", "What is the CIBIL score required?"),
    # --- legal and charges ---
    ("HAI ", "How much stamp duty do I have to pay?"),
    ("HAI ", "What documents are needed for registry?"),
    ("HAI ", "Is GST applicable on a ready to move flat?"),
    ("HAI ", "What is the total cost of buying the 62 lakh flat?"),
    ("HAI ", "What is a patta?"),
    # --- bolne wala andaz (natural speech) ---
    ("HAI ", "How much money do I need upfront?"),
    ("HAI ", "What papers should I bring?"),
    # --- data me nahi hai -> web pe jana chahiye ---
    ("NAHI", "What is the price of a flat in Mumbai?"),
    ("NAHI", "What is the current repo rate?"),
    ("NAHI", "Which is the best builder in Delhi?"),
    ("NAHI", "What is the circle rate in Gurgaon?"),
]

retriever = Retriever({**RAG, "retrieval": {"top_k": 1, "min_similarity": 0}})
rows = [(tag, q, retriever.retrieve(q)[0]["score"]) for tag, q in TESTS]

print("\n" + "-" * 78)
for tag, q, score in sorted(rows, key=lambda r: -r[2]):
    print(f"  {score:.3f}  [{tag}] {q}")

lo = min(s for t, _, s in rows if t == "HAI ")
hi = max(s for t, _, s in rows if t == "NAHI")
print("-" * 78)
print(f"  HAI min = {lo:.3f}   NAHI max = {hi:.3f}   GAP = {lo - hi:+.3f}")

if lo > hi:
    print(f"  -> min_similarity = {round((lo + hi) / 2, 2)}  (beech me, dono taraf saaf)\n")
else:
    print(f"  -> min_similarity = {round(lo - 0.01, 2)}  (HAI min se thoda neeche)")
    print("     GAP negative hai. Neeche rakhna surakshit hai - jo NAHI upar nikal")
    print("     aayenge unhe LLM fallback pakad lega aur web pe bhej dega.\n")
