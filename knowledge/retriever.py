from logger import log
from knowledge.embeddings import embed
from knowledge.vector_store import VectorStore


class Retriever:
    """Sawal ka vector banata hai aur index se sabse milte-julte chunks laata hai."""

    def __init__(self, config: dict):
        self.top_k = config["retrieval"]["top_k"]
        self.min_similarity = config["retrieval"]["min_similarity"]
        self.index, self.chunks = VectorStore(config).load()

        log.info(f"Retriever ready with {len(self.chunks)} indexed chunks")

    def retrieve(self, query: str):
        """[{source, chunk_id, text, score}] lauta do. Kam score wale chhod do."""
        query_vec = embed([query])
        scores, indices = self.index.search(query_vec, self.top_k)
        results = []

        for score, idx in zip(scores[0], indices[0]):
            if idx == -1 or score < self.min_similarity:
                continue

            chunk = self.chunks[idx]
            results.append({
                "source": chunk["source"],
                "chunk_id": chunk["chunk_id"],
                "text": chunk["text"],
                "score": round(float(score), 4),
            })

        if query != "warm up":      # keep_warm ka apna sawal - iska log nahi chahiye
            log.info(f"Retrieved {len(results)} chunks | top score={round(float(scores[0][0]), 4)} "
                     f"| chahiye {self.min_similarity} | query: '{query}'")

        return results
