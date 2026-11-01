from logger import log
from knowledge.loader import load_documents


def chunk_text(text: str, chunk_size: int, chunk_overlap: int):
    chunks = []
    current = ""

    for para in text.split("\n\n"):
        para = para.strip()
        if not para:
            continue

        if len(current) + len(para) <= chunk_size:
            current = current + "\n\n" + para if current else para
        else:
            if current:
                chunks.append(current)

            last = current[-chunk_overlap:]              
            overlap = " ".join(last.split(" ")[1:])     
            current = (overlap + "\n\n" + para).strip()

    if current:
        chunks.append(current)

    return chunks


def build_chunks(chunk_size: int, chunk_overlap: int):
    docs = load_documents()
    chunks = []

    for doc in docs:
        for i, part in enumerate(chunk_text(doc["text"], chunk_size, chunk_overlap)):
            chunks.append({"source": doc["source"], "chunk_id": i, "text": part})

    log.info(f"Built {len(chunks)} chunks from {len(docs)} documents")
    return chunks
