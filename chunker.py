import re


def split_into_sentences(text):
    """
    Splits text into sentences using punctuation as boundaries.
    Much smarter than cutting every 500 characters.
    """
    # split after . ! ? followed by space or newline
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    # remove empty strings
    sentences = [s.strip() for s in sentences if s.strip()]
    
    return sentences


def chunk_text(pages, chunk_size=500, overlap=50):
    """
    Splits pages into chunks by sentences, not raw characters.
    This way we never cut mid-sentence.
    """
    
    all_chunks = []
    chunk_id = 0
    
    for page in pages:
        sentences = split_into_sentences(page["text"])
        page_number = page["page_number"]
        
        current_chunk = []   # sentences in current chunk
        current_size  = 0    # character count so far
        
        for sentence in sentences:
            sentence_size = len(sentence)
            
            # if adding this sentence exceeds chunk_size
            # AND we already have something — save current chunk
            if current_size + sentence_size > chunk_size and current_chunk:
                
                chunk_text = " ".join(current_chunk)
                all_chunks.append({
                    "chunk_id":    chunk_id,
                    "page_number": page_number,
                    "text":        chunk_text,
                    "char_count":  len(chunk_text)
                })
                chunk_id += 1
                
                # overlap — keep last sentence in next chunk
                current_chunk = current_chunk[-1:]
                current_size  = len(current_chunk[0]) if current_chunk else 0
            
            current_chunk.append(sentence)
            current_size += sentence_size
        
        # don't forget the last chunk on this page
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            all_chunks.append({
                "chunk_id":    chunk_id,
                "page_number": page_number,
                "text":        chunk_text,
                "char_count":  len(chunk_text)
            })
            chunk_id += 1
    
    return all_chunks


if __name__ == "__main__":
    from pdf_parser import extract_text_from_pdf
    
    pages  = extract_text_from_pdf("sample.pdf")
    chunks = chunk_text(pages, chunk_size=500, overlap=50)
    
    print(f"\n✅ Total chunks: {len(chunks)}")
    
    print("\n📦 CHUNK 1:")
    print("-" * 40)
    print(chunks[0]["text"])
    
    print("\n📦 CHUNK 2:")
    print("-" * 40)
    print(chunks[1]["text"])
    
    print("\n📦 CHUNK 3:")
    print("-" * 40)
    print(chunks[2]["text"])
    
    # show chunk from page 2 — actual paper content
    page2_chunks = [c for c in chunks if c["page_number"] == 2]
    print(f"\n📄 Page 2 produced {len(page2_chunks)} chunks")
    print("\n📦 FIRST CHUNK FROM PAGE 2:")
    print("-" * 40)
    print(page2_chunks[0]["text"])