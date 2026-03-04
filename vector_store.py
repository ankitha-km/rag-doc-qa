import chromadb

# create a persistent ChromaDB client
# persistent = saves to disk, survives between runs
client = chromadb.PersistentClient(path="./chroma_db")

# a collection = like a table in SQL, stores our chunks
collection = client.get_or_create_collection(
    name="documents",
    metadata={"hnsw:space": "cosine"}  # use cosine similarity
)


def store_chunks(chunks):
    """
    Stores embedded chunks into ChromaDB.
    Each chunk needs 3 things:
    - id         → unique identifier
    - embedding  → the 384 numbers
    - document   → original text (so we can return it later)
    - metadata   → page number etc.
    """
    
    print(f"💾 Storing {len(chunks)} chunks in ChromaDB...")
    
    # ChromaDB wants these as separate lists
    ids         = []
    embeddings  = []
    documents   = []
    metadatas   = []
    
    for chunk in chunks:
        ids.append(str(chunk["chunk_id"]))
        embeddings.append(chunk["embedding"])
        documents.append(chunk["text"])
        metadatas.append({
            "page_number": chunk["page_number"],
            "char_count":  chunk["char_count"]
        })
    
    # clear old data first (fresh start each time)
    existing = collection.get()
    if existing["ids"]:
        collection.delete(ids=existing["ids"])
        print(f"🗑️  Cleared old data")
    
    # store everything in one go
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas
    )
    
    print(f"✅ Stored! Collection now has {collection.count()} chunks")


def search(query_embedding, top_k=3):
    """
    Finds top_k most similar chunks to the query.
    Returns the actual text + metadata + similarity scores.
    """
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )
    
    # reformat results into clean list
    hits = []
    for i in range(len(results["ids"][0])):
        hits.append({
            "text":        results["documents"][0][i],
            "page_number": results["metadatas"][0][i]["page_number"],
            "distance":    results["distances"][0][i],
            # distance 0 = identical, 2 = completely opposite
            # convert to similarity score (1 = perfect match)
            "similarity":  round(1 - results["distances"][0][i], 3)
        })
    
    return hits


if __name__ == "__main__":
    from pdf_parser import extract_text_from_pdf
    from chunker    import chunk_text
    from embedder   import embed_chunks, embed_query
    
    # full pipeline
    pages  = extract_text_from_pdf("sample.pdf")
    chunks = chunk_text(pages)
    chunks = embed_chunks(chunks)
    
    # store in ChromaDB
    store_chunks(chunks)
    
    # now search!
    print("\n🔍 SEARCH TEST 1:")
    print("-" * 40)
    query1 = "What is the attention mechanism?"
    hits   = search(embed_query(query1), top_k=3)
    
    print(f"Query: '{query1}'\n")
    for i, hit in enumerate(hits):
        print(f"Result {i+1} — Page {hit['page_number']} | Similarity: {hit['similarity']}")
        print(f"{hit['text'][:150]}...")
        print()
    
    print("\n🔍 SEARCH TEST 2:")
    print("-" * 40)
    query2 = "How many parameters does the model have?"
    hits   = search(embed_query(query2), top_k=3)
    
    print(f"Query: '{query2}'\n")
    for i, hit in enumerate(hits):
        print(f"Result {i+1} — Page {hit['page_number']} | Similarity: {hit['similarity']}")
        print(f"{hit['text'][:150]}...")
        print()