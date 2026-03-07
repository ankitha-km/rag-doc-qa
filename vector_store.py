import json
import os
import numpy as np

STORE_PATH = "/tmp/docmind_store.json"

_store = []


def _cosine_similarity(a, b):
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def store_chunks(chunks):
    global _store
    _store = []
    for chunk in chunks:
        _store.append({
            "text":        chunk["text"],
            "page_number": chunk["page_number"],
            "embedding":   chunk["embedding"]
        })
    # persist to disk
    with open(STORE_PATH, "w") as f:
        json.dump(_store, f)


def search(query_embedding, top_k=5):
    global _store

    # load from disk if memory is empty
    if not _store and os.path.exists(STORE_PATH):
        with open(STORE_PATH) as f:
            _store = json.load(f)

    if not _store:
        return []

    scored = []
    for chunk in _store:
        sim = _cosine_similarity(query_embedding, chunk["embedding"])
        scored.append({
            "text":        chunk["text"],
            "page_number": chunk["page_number"],
            "similarity":  round(sim, 3),
            "distance":    round(1 - sim, 3)
        })

    scored.sort(key=lambda x: x["similarity"], reverse=True)
    return scored[:top_k]


def get_count():
    global _store
    if not _store and os.path.exists(STORE_PATH):
        with open(STORE_PATH) as f:
            _store = json.load(f)
    return len(_store)  