DocMind
an AI-Powered PDF Q&A app built with RAG(retrieval-Augmented Generation)
* LIVE DEMO : https://docmind-ragmind.streamlit.app/

what id DocMind?
DocMind lets you upload any PDF and have a conversation with it. ask questions, get accurate answers with page citations, and summarize entire documents in sseconds-all powered by a full RAG pipeline built from scratch.

features:
*pdf upload 
*semantic search-finds relevent passsages using meaning , not just keywords
*Ai answers - poweres by Groq's llama-3.1-8b
*source citations-eevry answer includes page numbers and source chuncks
*document summarization by one click.
*handles spelling mistakes -pular/singular.
*chat interface

HOW IT WORKS:

PDF Upload
    ↓
Text Extraction (PyMuPDF)
    ↓
Sentence-Aware Chunking (500 chars, overlap)
    ↓
Embeddings (all-MiniLM-L6-v2, 384 dimensions)
    ↓
Vector Store (cosine similarity search)
    ↓
Query → Embed → Search → Top Chunks
    ↓
Groq llama-3.1-8b → Answer with citations


Tech Stack
Component     Technology
Frontend      Streamlit 
PDF Parsing   PyMuPDF (fitz)
Embeddings    sentence-transformers (all-MiniLM-L6-v2)
Vector Store  Custom cosine similarity (numpy)
LLM           Groq API — llama-3.1-8b-instant
Deployment    Streamlit Cloud



Project Structure:

rag-doc-qa/
├── app.py              # Streamlit UI
├── pdf_parser.py       # PDF text extraction + cleaning
├── chunker.py          # Sentence-aware chunking with overlap
├── embedder.py         # SentenceTransformer embeddings
├── vector_store.py     # Custom vector store with cosine search
├── llm.py              # Groq LLM integration + prompt engineering
├── requirements.txt    # Dependencies
└── README.md


# Clone the repo
git clone https://github.com/ankitha-km/rag-doc-qa.git
cd rag-doc-qa

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
# Create a .env file with:
# GROQ_API_KEY=your_groq_api_key_here

# Run the app
streamlit run app.py

Get a free Groq API key at console.groq.com


Key Learnings
Building this project covered the full RAG pipeline from scratch:

Why RAG? LLMs have context limits and no access to private documents. RAG solves both.
Embeddings convert text meaning into vectors — similar meaning = similar vectors
Chunking tradeoff — too small loses context, too large loses precision
Cosine similarity measures angle between vectors to find semantically similar chunks
Prompt engineering — strict vs flexible prompts dramatically affect answer quality
LLM choice matters — 0.5B models hallucinate, 8B models reason properly


Future Improvements

 Multi-PDF support
 Chat memory (conversation context)
 Persistent vector store across sessions
 Streaming responses
 Support for DOCX, TXT files


Author
Built by Ankitha as a learning project to understand RAG systems from the ground up.