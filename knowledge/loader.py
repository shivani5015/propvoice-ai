from pathlib import Path
import csv
import pdfplumber

DATA = Path(__file__).resolve().parent.parent / "data"

def load_documents():
    docs = []

    for file in DATA.iterdir():
        if file.suffix.lower() == ".md":
            text = file.read_text(encoding="utf-8")
            docs.append({"text": text, "source": file.name})

        elif file.suffix.lower() == ".csv":
            with file.open(encoding="utf-8-sig", newline="") as f:
                for row in csv.DictReader(f):
                    docs.append({
                        "text": " | ".join(f"{k}: {v}" for k, v in row.items()),
                        "source": file.name,
                    })

        elif file.suffix.lower() == ".pdf":
            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    if text.strip():
                        docs.append({"text": text, "source": file.name})

    if not docs:
        raise ValueError("No readable documents found in data/")

    return docs
