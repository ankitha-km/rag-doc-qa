# Persistent client — data survives across restarts, stored on disk.
# Created lazily on first use (not at import time) so importing this module
# is instant — chromadb client setup does real disk I/O, which is too slow
# to happen during app startup on constrained hosting.
CHROMA_PATH = "/tmp/docmind_chroma"
_client = None
_collection = None


def _get_collection():
    global _client, _collection
    if _collection is None:
        import chromadb  # deferred: chromadb itself is a heavier import
        _client = chromadb.PersistentClient(path=CHROMA_PATH)
        _collection = _client.get_or_create_collection(
            name="docmind_chunks",
            metadata={"hnsw:space": "cosine"}  # match your old cosine-similarity behavior
        )
    return _collection


def store_chunks(chunks):
    """Replaces all existing chunks with the new set (matches old overwrite behavior)."""
    global _collection
    collection = _get_collection()
    _client.delete_collection("docmind_chunks")
    _collection = _client.get_or_create_collection(
        name="docmind_chunks",
        metadata={"hnsw:space": "cosine"}
    )

    ids = [str(i) for i in range(len(chunks))]
    documents = [chunk["text"] for chunk in chunks]
    embeddings = [chunk["embedding"] for chunk in chunks]
    metadatas = [{"page_number": chunk["page_number"]} for chunk in chunks]

    _collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )


def search(query_embedding, top_k=5):
    collection = _get_collection()
    count = collection.count()
    if count == 0:
        return []

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, count)
    )

    scored = []
    # results is a dict of lists-of-lists (one inner list per query — we only have 1 query)
    for text, meta, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        similarity = 1 - distance  # cosine space: distance = 1 - similarity
        scored.append({
            "text":        text,
            "page_number": meta["page_number"],
            "similarity":  round(similarity, 3),
            "distance":    round(distance, 3)
        })

    return scored


def get_count():
    return _get_collection().count()