from config import RAG
from knowledge.chunker import build_chunks
from knowledge.vector_store import VectorStore

kb = RAG["knowledge_base"]
chunks = build_chunks(kb["chunk_size"], kb["chunk_overlap"])
VectorStore(RAG).build(chunks)
