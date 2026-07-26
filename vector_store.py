import chromadb

# Persistent client — data survives across restarts, stored on disk
CHROMA_PATH = "/tmp/docmind_chroma"
_client = chromadb.PersistentClient(path=CHROMA_PATH)

# get_or_create so re-imports don't blow up if the collection already exists
_collection = _client.get_or_create_collection(
    name="docmind_chunks",
    metadata={"hnsw:space": "cosine"}  # match your old cosine-similarity behavior
)


def store_chunks(chunks):
    """Replaces all existing chunks with the new set (matches old overwrite behavior)."""
    # Clear existing data — Chroma has no "truncate", so delete + recreate
    global _collection
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
    count = _collection.count()
    if count == 0:
        return []

    results = _collection.query(
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
    return _collection.count()