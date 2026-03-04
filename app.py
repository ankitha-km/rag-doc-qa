import streamlit as st
import tempfile
import os
from pdf_parser   import extract_text_from_pdf
from chunker      import chunk_text
from embedder     import embed_chunks, embed_query
from vector_store import store_chunks, search
from llm          import ask_llm

# ── Page config ──────────────────────────────────────
st.set_page_config(
    page_title="RAG Document Q&A",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 RAG Document Q&A")
st.caption("Upload a PDF → Ask questions → Get answers with page citations")

# ── Session state ─────────────────────────────────────
if "indexed" not in st.session_state:
    st.session_state.indexed = False

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ── Sidebar ───────────────────────────────────────────
with st.sidebar:
    st.header("📄 Upload Document")
    uploaded_file = st.file_uploader("Choose a PDF", type="pdf")

    st.divider()
    st.header("⚙️ Settings")

    top_k = st.slider(
        "Chunks to retrieve",
        min_value=1, max_value=8, value=3,
        help="How many chunks to send to the LLM"
    )

    similarity_threshold = st.slider(
        "Similarity threshold",
        min_value=0.0, max_value=1.0, value=0.4, step=0.05,
        help="Minimum similarity score to include a chunk"
    )

    st.divider()
    if st.button("🗑️ Clear chat"):
        st.session_state.chat_history = []
        st.rerun()

# ── Index PDF when uploaded ───────────────────────────
if uploaded_file:
    if st.session_state.get("last_file") != uploaded_file.name:

        # save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        st.write(f"DEBUG — saved to: {tmp_path}")

        with st.spinner("📖 Reading PDF..."):
            pages = extract_text_from_pdf(tmp_path)

        with st.spinner("✂️ Chunking text..."):
            chunks = chunk_text(pages)

        with st.spinner("🔢 Generating embeddings..."):
            chunks = embed_chunks(chunks)

        with st.spinner("💾 Storing in ChromaDB..."):
            store_chunks(chunks)

        # clean up temp file
        os.unlink(tmp_path)

        st.session_state.indexed   = True
        st.session_state.last_file = uploaded_file.name
        st.session_state.doc_stats = {
            "pages":  len(pages),
            "chunks": len(chunks),
            "file":   uploaded_file.name
        }
        st.session_state.chat_history = []
        st.success(f"✅ Indexed {len(pages)} pages → {len(chunks)} chunks")

# ── Doc stats ─────────────────────────────────────────
if st.session_state.indexed:
    stats = st.session_state.doc_stats
    col1, col2, col3 = st.columns(3)
    col1.metric("📄 Pages",  stats["pages"])
    col2.metric("📦 Chunks", stats["chunks"])
    col3.metric("🔍 Top-K",  top_k)
    st.divider()

# ── Chat interface ────────────────────────────────────
if st.session_state.indexed:

    # render chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg["role"] == "assistant" and "sources" in msg:
                with st.expander("📚 View sources"):
                    for i, src in enumerate(msg["sources"]):
                        st.markdown(f"**Source {i+1} — Page {src['page_number']} | Similarity: {src['similarity']}**")
                        st.caption(src["text"][:300] + "...")
                        st.divider()

    # question input
    question = st.chat_input("Ask anything about your document...")

    if question:
        with st.chat_message("user"):
            st.write(question)

        st.session_state.chat_history.append({
            "role": "user", "content": question
        })

        with st.chat_message("assistant"):
            with st.spinner("🔍 Searching document..."):
                hits = search(embed_query(question), top_k=top_k)

            with st.spinner("🤖 Generating answer..."):
                answer = ask_llm(question, hits, similarity_threshold)

            st.write(answer)

            good_hits = [h for h in hits if h["similarity"] >= similarity_threshold]
            with st.expander("📚 View sources"):
                for i, src in enumerate(good_hits):
                    st.markdown(f"**Source {i+1} — Page {src['page_number']} | Similarity: {src['similarity']}**")
                    st.caption(src["text"][:300] + "...")
                    st.divider()

        st.session_state.chat_history.append({
            "role":    "assistant",
            "content": answer,
            "sources": good_hits
        })

else:
    st.info("👈 Upload a PDF from the sidebar to get started!")
    st.markdown("""
    ### How this works:
    1. **Upload** any PDF document
    2. App **chunks** it into pieces
    3. Each chunk gets **embedded** into vectors
    4. Vectors are **stored** in ChromaDB
    5. Your question is **matched** to relevant chunks
    6. LLM **reads** those chunks and answers
    """)