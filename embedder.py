from sentence_transformers import SentenceTransformer

# load the model (downloads ~80MB on first run)
model = SentenceTransformer("all-MiniLM-L6-v2")


def embed_chunks(chunks):
    """
    Takes list of chunk dicts from chunker.py
    Adds an 'embedding' key to each chunk — a list of 384 numbers
    """
    
    print(f"🔢 Embedding {len(chunks)} chunks...")
    
    # extract just the text from each chunk
    texts = [chunk["text"] for chunk in chunks]
    
    # embed all texts at once (faster than one by one)
    embeddings = model.encode(texts, show_progress_bar=True)
    
    # add embedding back into each chunk dict
    for i, chunk in enumerate(chunks):
        chunk["embedding"] = embeddings[i].tolist()
    
    print(f"✅ Done! Each chunk now has a vector of {len(chunks[0]['embedding'])} numbers")
    
    return chunks


def embed_query(query_text):
    """
    Embeds a single search query.
    Must use the SAME model as embed_chunks!
    """
    embedding = model.encode([query_text])[0]
    return embedding.tolist()


if __name__ == "__main__":
    from pdf_parser import extract_text_from_pdf
    from chunker import chunk_text
    
    # full pipeline so far
    pages  = extract_text_from_pdf("sample.pdf")
    chunks = chunk_text(pages)
    chunks = embed_chunks(chunks)
    
    print("\n📊 INSPECT ONE CHUNK:")
    print("-" * 40)
    print(f"Page:       {chunks[5]['page_number']}")
    print(f"Text:       {chunks[5]['text'][:100]}...")
    print(f"Vector dim: {len(chunks[5]['embedding'])}")
    print(f"First 5 numbers: {chunks[5]['embedding'][:5]}")
    
    # now test semantic similarity
    print("\n🧪 SIMILARITY TEST:")
    print("-" * 40)
    
    q1 = embed_query("What is the attention mechanism?")
    q2 = embed_query("How does a cat chase a mouse?")
    
    # get embedding of chunk 5
    chunk_vec = chunks[5]["embedding"]
    
    # simple dot product similarity (higher = more similar)
    import numpy as np
    
    sim1 = np.dot(q1, chunk_vec)
    sim2 = np.dot(q2, chunk_vec)
    
    print(f"Query: 'What is the attention mechanism?'")
    print(f"Similarity to chunk 5: {sim1:.4f}")
    print()
    print(f"Query: 'How does a cat chase a mouse?'")
    print(f"Similarity to chunk 5: {sim2:.4f}")
    print()
    print("Higher number = more relevant to that chunk")