import json
from pathlib import Path

import faiss

from logger import log
from knowledge.embeddings import embed


class VectorStore:

    def __init__(self, config: dict):
        self.dir = Path(config["vector_store"]["dir"])
        self.index_file = self.dir / "index.faiss"
        self.chunks_file = self.dir / "chunks.json"

    def build(self, chunks: list):

        vectors = embed([c["text"] for c in chunks])

        index = faiss.IndexFlatIP(vectors.shape[1])      # IP = cosine similarity
        index.add(vectors)

        self.dir.mkdir(exist_ok=True)
        faiss.write_index(index, str(self.index_file))
        self.chunks_file.write_text(json.dumps(chunks), encoding="utf-8")

        log.info(f"Vector store built with {len(chunks)} chunks -> {self.dir}")

    def load(self):
        """Disk se index aur chunks wapas lao."""
        index = faiss.read_index(str(self.index_file))
        chunks = json.loads(self.chunks_file.read_text(encoding="utf-8"))

        return index, chunks
