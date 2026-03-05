import requests
import json


def fix_query(question):
    """
    Fixes spelling mistakes in the query before embedding.
    'waht are tranformers' → 'what are transformers'
    """
    try:
        from spellchecker import SpellChecker
        spell = SpellChecker()
        
        words = question.split()
        corrected = []
        
        for word in words:
            # get best correction
            correction = spell.correction(word)
            corrected.append(correction if correction else word)
        
        fixed = " ".join(corrected)
        
        # only use correction if something actually changed
        if fixed != question:
            print(f"  Query corrected: '{question}' → '{fixed}'")
        
        return fixed
    except Exception:
        return question  # fallback to original if anything fails

def ask_llm(question, chunks, similarity_threshold=0.4):
    """
    Takes a question and retrieved chunks.
    Builds a prompt and sends to Ollama.
    Returns the answer as a string.
    """
    question = fix_query(question)
    # filter out low quality chunks
    good_chunks = [c for c in chunks if c["similarity"] >= similarity_threshold]
    
    if not good_chunks:
        return "I couldn't find relevant information in the document to answer that question."
    
    # build context from chunks
    context = ""
    for i, chunk in enumerate(good_chunks):
        context += f"[Page {chunk['page_number']}]: {chunk['text']}\n\n"
    
    # build the prompt
    prompt = f"""You are a document assistant. Your ONLY job is to answer based on the context below.

STRICT RULES:
- ONLY use information from the CONTEXT below
- If the answer is not in the context, say "I don't find that in the document"
- Do NOT use your own knowledge
- Do NOT make up names, dates, or facts
- Keep answer under 3 sentences
- Mention the page number


CONTEXT FROM DOCUMENT:
{context}

QUESTION: {question}

ANSWER:"""
    
    print(f"📤 Sending to Ollama...")
    print(f"   Using {len(good_chunks)} chunks as context")
    
    # call Ollama API
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model":  "qwen2:0.5b",
            "prompt": prompt,
            "stream": False      # wait for full response
        },
        timeout=60
    )
    
    if response.status_code == 200:
        answer = response.json()["response"]
        return answer.strip()
    else:
        return f"Ollama error: {response.status_code}"


if __name__ == "__main__":
    from pdf_parser   import extract_text_from_pdf
    from chunker      import chunk_text
    from embedder     import embed_chunks, embed_query
    from vector_store import store_chunks, search
    
    # full pipeline
    print("🔄 Building index...")
    pages  = extract_text_from_pdf("sample.pdf")
    chunks = chunk_text(pages)
    chunks = embed_chunks(chunks)
    store_chunks(chunks)
    
    print("\n✅ Index ready! Testing questions...\n")
    
    # test question 1
    q1   = "What is the attention mechanism?"
    hits = search(embed_query(q1), top_k=3)
    ans  = ask_llm(q1, hits)
    
    print("="*50)
    print(f"Q: {q1}")
    print(f"A: {ans}")
    
    # test question 2
    q2   = "What are the main contributions of this paper?"
    hits = search(embed_query(q2), top_k=3)
    ans  = ask_llm(q2, hits)
    
    print("="*50)
    print(f"Q: {q2}")
    print(f"A: {ans}")