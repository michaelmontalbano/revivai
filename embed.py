from sentence_transformers import SentenceTransformer
import json

model = SentenceTransformer("all-MiniLM-L6-v2")

documents = []
embeddings = []

with open("rag_docs/chunks.jsonl", "r") as f:
    for line in f:
        entry = json.loads(line)
        documents.append(entry)
        embeddings.append(model.encode(entry["text"], normalize_embeddings=True))
