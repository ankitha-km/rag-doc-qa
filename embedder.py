from fastembed import TextEmbedding

# ── module-level cache ────────────────────────────────
# This loads ONCE, on the first real request that needs it — not at
# import time. Keeps app startup fast (important on constrained hosting
# where startup has a much shorter timeout than a request does).
#
# Uses fastembed (ONNX runtime, quantized model, no torch) instead of
# sentence-transformers — torch alone is 550MB+ and pulls in GPU/CUDA
# libraries that are dead weight on CPU-only free-tier hosting. This
# model produces 384-dim embeddings, same as the old all-MiniLM-L6-v2,
# so retrieval quality should be comparable.
_model = None

def get_model():
    global _model
    if _model is None:
        print("⏳ Loading embedding model for the first time...")
        _model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        print("✅ Model cached in memory!")
    return _model


def embed_chunks(chunks):
    model = get_model()  # instant after first call

    texts = [chunk["text"] for chunk in chunks]
    embeddings = list(model.embed(texts))  # fastembed returns a generator of numpy arrays

    for i, chunk in enumerate(chunks):
        chunk["embedding"] = embeddings[i].tolist()

    return chunks


def embed_query(query_text):
    model = get_model()  # instant, already loaded
    return list(model.embed([query_text]))[0].tolist()