from logger import log
from knowledge.embeddings import embed
from knowledge.vector_store import VectorStore


class Retriever:
    def __init__(self, config: dict):
        self.top_k = config["retrieval"]["top_k"]
        self.min_similarity = config["retrieval"]["min_similarity"]
        self.index, self.chunks = VectorStore(config).load()

        log.info(f"Retriever ready with {len(self.chunks)} indexed chunks")

    def retrieve(self, query: str):
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

        
        if query != "warm up":      

            names = []
            for r in results:
                names.append(f"{r['source']} #{r['chunk_id']} ({r['score']})")

            log.info(f"Retrieved {len(results)} chunks from {', '.join(names)} "
                     f"| top score={round(float(scores[0][0]), 4)} "
                     f"| chahiye {self.min_similarity} | query: '{query}'")

        return results