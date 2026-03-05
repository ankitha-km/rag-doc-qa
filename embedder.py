from sentence_transformers import SentenceTransformer

# ── module-level cache ────────────────────────────────
# This loads ONCE when the module is first imported
# and never again for the entire session
_model = None

def get_model():
    global _model
    if _model is None:
        print("⏳ Loading embedding model for the first time...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        print("✅ Model cached in memory!")
    return _model


def embed_chunks(chunks):
    model = get_model()  # instant after first call

    texts = [chunk["text"] for chunk in chunks]
    embeddings = model.encode(texts, batch_size=32, show_progress_bar=False)

    for i, chunk in enumerate(chunks):
        chunk["embedding"] = embeddings[i].tolist()

    return chunks


def embed_query(query_text):
    model = get_model()  # instant, already loaded
    return model.encode([query_text])[0].tolist()