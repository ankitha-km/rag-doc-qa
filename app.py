import streamlit as st
import tempfile
import os

st.set_page_config(
    page_title="DocMind",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Söhne:wght@300;400;500&family=Inter:wght@300;400;500;600&display=swap');

* { box-sizing: border-box; }

html, body, [data-testid="stApp"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: #1a1a1a;
    color: #ececec;
    font-size: 15px;
}

#MainMenu, footer, header { visibility: hidden; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #171717 !important;
    border-right: 1px solid #2a2a2a !important;
    padding-top: 0 !important;
}
[data-testid="stSidebar"] > div {
    padding: 1.25rem 1rem !important;
}
[data-testid="stSidebar"] * {
    color: #ececec !important;
}
[data-testid="collapsedControl"] {
    color: #ececec !important;
    background: #2a2a2a !important;
}

/* Sidebar logo */
.sidebar-brand {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0 1.25rem 0;
    border-bottom: 1px solid #2a2a2a;
    margin-bottom: 1.25rem;
}
.sidebar-brand-name {
    font-size: 1rem;
    font-weight: 600;
    color: #ececec;
    letter-spacing: -0.2px;
}
.sidebar-brand-dot {
    width: 8px;
    height: 8px;
    background: #c084fc;
    border-radius: 50%;
    flex-shrink: 0;
}

/* Sidebar labels */
.sidebar-section {
    font-size: 0.7rem;
    font-weight: 500;
    color: #666 !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.75rem;
    margin-top: 1.25rem;
}

/* Sliders */
.stSlider label p {
    font-size: 0.82rem !important;
    color: #aaa !important;
}
[data-baseweb="slider"] [role="slider"] {
    background: #c084fc !important;
    border-color: #c084fc !important;
}
[data-baseweb="slider"] [data-testid="stSliderTrackFill"] {
    background: #c084fc !important;
}

/* Sidebar buttons */
.stButton > button {
    width: 100%;
    background: transparent !important;
    border: 1px solid #2a2a2a !important;
    color: #aaa !important;
    border-radius: 6px !important;
    font-size: 0.82rem !important;
    font-weight: 400 !important;
    padding: 0.45rem 0.75rem !important;
    text-align: left !important;
    transition: all 0.15s !important;
}
.stButton > button:hover {
    background: #2a2a2a !important;
    border-color: #3a3a3a !important;
    color: #ececec !important;
}

/* Metric */
[data-testid="stMetric"] {
    background: #222 !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 8px !important;
    padding: 0.6rem 0.75rem !important;
}
[data-testid="stMetricValue"] {
    font-size: 1.2rem !important;
    font-weight: 600 !important;
    color: #c084fc !important;
}
[data-testid="stMetricLabel"] p {
    font-size: 0.7rem !important;
    color: #666 !important;
}

/* ── Main area ── */
.main-wrap {
    max-width: 720px;
    margin: 0 auto;
    padding: 2rem 1rem;
}

/* Header */
.app-header {
    text-align: center;
    padding: 3rem 0 2rem 0;
    max-width: 720px;
    margin: 0 auto;
}
.app-title {
    font-size: 1.75rem;
    font-weight: 600;
    color: #ececec;
    letter-spacing: -0.5px;
    margin-bottom: 0.4rem;
}
.app-title span { color: #c084fc; }
.app-subtitle {
    font-size: 0.88rem;
    color: #666;
    font-weight: 400;
}

/* Upload zone */
[data-testid="stFileUploader"] {
    background: #222 !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 12px !important;
    max-width: 720px !important;
    margin: 0 auto !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: #c084fc !important;
}
[data-testid="stFileUploader"] label {
    color: #888 !important;
    font-size: 0.82rem !important;
}

/* Success */
[data-testid="stAlert"] {
    background: #1e2a1e !important;
    border: 1px solid #2d4a2d !important;
    border-radius: 8px !important;
    max-width: 720px !important;
    margin: 0.75rem auto !important;
    font-size: 0.85rem !important;
}

/* Progress */
.stProgress {
    max-width: 720px !important;
    margin: 0 auto !important;
}
.stProgress > div > div {
    background: #c084fc !important;
    border-radius: 4px !important;
}

/* ── Chat ── */
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    border-radius: 0 !important;
    max-width: 720px !important;
    margin: 0 auto 0.25rem auto !important;
    padding: 0.75rem 0 !important;
    border-bottom: 1px solid #222 !important;
}

/* User message bubble */
[data-testid="stChatMessage"][data-testid*="user"],
[aria-label="user message"] {
    background: #222 !important;
    border-radius: 12px !important;
    border: 1px solid #2a2a2a !important;
    padding: 0.75rem 1rem !important;
}

/* Chat text */
[data-testid="stChatMessage"] p {
    font-size: 0.92rem !important;
    line-height: 1.7 !important;
    color: #ddd !important;
}

/* Chat input */
[data-testid="stChatInput"] {
    max-width: 720px !important;
    margin: 0 auto !important;
    border: 1px solid #333 !important;
    border-radius: 12px !important;
}
[data-testid="stChatInput"] textarea {
    background: #222 !important;
    border: 1px solid #333 !important;
    border-radius: 12px !important;
    color: #ececec !important;
    font-size: 0.92rem !important;
    padding: 0.85rem 1rem !important;
    resize: none !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: #444 !important;
    box-shadow: none !important;
    outline: none !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: #555 !important;
}

/* Expander */
[data-testid="stExpander"] {
    background: #1e1e1e !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 8px !important;
    margin-top: 0.5rem !important;
}
[data-testid="stExpander"] summary {
    font-size: 0.75rem !important;
    color: #666 !important;
    padding: 0.5rem 0.75rem !important;
}

/* Source chips */
.src-chip {
    display: inline-block;
    background: #252525;
    border: 1px solid #333;
    color: #888;
    border-radius: 20px;
    padding: 0.1rem 0.6rem;
    font-size: 0.72rem;
    margin: 0.1rem;
}
.src-chip-purple {
    border-color: #c084fc50;
    color: #c084fc;
}

/* Welcome */
.welcome-wrap {
    max-width: 480px;
    margin: 3rem auto;
    text-align: center;
}
.welcome-icon {
    font-size: 2.5rem;
    margin-bottom: 1rem;
    opacity: 0.9;
}
.welcome-title {
    font-size: 1.1rem;
    font-weight: 500;
    color: #ccc;
    margin-bottom: 0.5rem;
}
.welcome-sub {
    font-size: 0.85rem;
    color: #555;
    line-height: 1.7;
    margin-bottom: 2rem;
}
.step-row {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    text-align: left;
    padding: 0.4rem 0;
    color: #666;
    font-size: 0.82rem;
}
.step-dot {
    width: 6px;
    height: 6px;
    background: #c084fc;
    border-radius: 50%;
    margin-top: 0.45rem;
    flex-shrink: 0;
}

/* Divider */
hr { border-color: #2a2a2a !important; }

/* Caption */
.stCaption { color: #555 !important; font-size: 0.75rem !important; }
</style>
""", unsafe_allow_html=True)


# ── Cache ─────────────────────────────────────────────
@st.cache_resource
def load_all_modules():
    from pdf_parser   import extract_text_from_pdf
    from chunker      import chunk_text
    from embedder     import embed_chunks, embed_query
    from vector_store import store_chunks, search
    from llm          import ask_llm
    return {
        "extract": extract_text_from_pdf,
        "chunk":   chunk_text,
        "embed":   embed_chunks,
        "query":   embed_query,
        "store":   store_chunks,
        "search":  search,
        "ask":     ask_llm
    }


# ── Session state ─────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "indexed" not in st.session_state:
    # check if ChromaDB already has data from before refresh
    try:
        import chromadb
        client = chromadb.PersistentClient(path="./chroma_db")
        col = client.get_or_create_collection("documents")
        count = col.count()
        if count > 0:
            st.session_state.indexed = True
            st.session_state.doc_stats = {
                "pages":  "?",
                "chunks": count,
                "file":   "Previous session"
            }
        else:
            st.session_state.indexed = False
    except Exception:
        st.session_state.indexed = False


# ── Sidebar ───────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <div class="sidebar-brand-dot"></div>
        <div class="sidebar-brand-name">DocMind</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">Settings</div>', unsafe_allow_html=True)

    top_k = st.slider(
        "Chunks to retrieve", min_value=1, max_value=8, value=3,
        key="top_k_slider"
    )
    similarity_threshold = st.slider(
        "Min similarity", min_value=0.0, max_value=1.0,
        value=0.4, step=0.05, key="sim_slider"
    )

    if st.session_state.indexed:
        st.markdown('<div class="sidebar-section">Document</div>', unsafe_allow_html=True)
        stats = st.session_state.doc_stats
        c1, c2 = st.columns(2)
        c1.metric("Pages",  stats["pages"])
        c2.metric("Chunks", stats["chunks"])
        st.caption(f"📄 {stats['file']}")

    st.markdown('<div class="sidebar-section">Actions</div>', unsafe_allow_html=True)

    if st.button("🗑  Clear chat"):
        st.session_state.chat_history = []
        st.rerun()

    if st.button("↩  New document"):
        st.session_state.indexed      = False
        st.session_state.chat_history = []
        st.session_state.last_file    = None
        st.rerun()


# ── Header ────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <div class="app-title">Doc<span>Mind</span></div>
    <div class="app-subtitle">Upload a PDF and ask questions about it</div>
</div>
""", unsafe_allow_html=True)


# ── Upload ────────────────────────────────────────────
uploaded_file = st.file_uploader(
    "Drop your PDF here",
    type="pdf",
    label_visibility="collapsed"
)


# ── Index ─────────────────────────────────────────────
if uploaded_file:
    if st.session_state.get("last_file") != uploaded_file.name:

        m = load_all_modules()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        bar = st.progress(0, text="Reading PDF...")
        pages = m["extract"](tmp_path)

        bar.progress(30, text="Chunking text...")
        chunks = m["chunk"](pages)

        bar.progress(55, text="Generating embeddings...")
        chunks = m["embed"](chunks)

        bar.progress(85, text="Storing in ChromaDB...")
        m["store"](chunks)

        bar.progress(100, text="Done!")
        os.unlink(tmp_path)
        bar.empty()

        st.session_state.indexed   = True
        st.session_state.last_file = uploaded_file.name
        st.session_state.doc_stats = {
            "pages":  len(pages),
            "chunks": len(chunks),
            "file":   uploaded_file.name
        }
        st.session_state.chat_history = []
        st.success(f"Ready — {len(pages)} pages · {len(chunks)} chunks")


# ── Chat ──────────────────────────────────────────────
if st.session_state.indexed:

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg["role"] == "assistant" and msg.get("sources") and "couldn't find" not in msg["content"]:
                with st.expander("Sources"):
                    for src in msg["sources"]:
                        st.markdown(
                            f'<span class="src-chip src-chip-purple">p.{src["page_number"]}</span>'
                            f'<span class="src-chip">{src["similarity"]}</span>',
                            unsafe_allow_html=True
                        )
                        st.caption(src["text"][:250] + "...")
                        st.divider()

    question = st.chat_input("Ask anything about your document...")

    if question:
        with st.chat_message("user"):
            st.write(question)

        st.session_state.chat_history.append({
            "role": "user", "content": question
        })

        with st.chat_message("assistant"):
            with st.spinner("Searching..."):
                m    = load_all_modules()
                hits = m["search"](m["query"](question), top_k=top_k)
            with st.spinner("Thinking..."):
                answer = m["ask"](question, hits, similarity_threshold)

            st.write(answer)

            good_hits = [h for h in hits if h["similarity"] >= similarity_threshold]
            if good_hits and "couldn't find" not in answer:
                with st.expander("Sources"):
                    for src in good_hits:
                        st.markdown(
                            f'<span class="src-chip src-chip-purple">p.{src["page_number"]}</span>'
                            f'<span class="src-chip">{src["similarity"]}</span>',
                            unsafe_allow_html=True
                        )
                        st.caption(src["text"][:250] + "...")
                        st.divider()

        st.session_state.chat_history.append({
            "role":    "assistant",
            "content": answer,
            "sources": good_hits
        })


# ── Welcome ───────────────────────────────────────────
else:
    st.markdown("""
    <div class="welcome-wrap">
        <div class="welcome-icon">🧠</div>
        <div class="welcome-title">Chat with any document</div>
        <div class="welcome-sub">
            Upload a PDF above and ask questions in plain English.
            DocMind retrieves the most relevant sections and answers accurately.
        </div>
        <div class="step-row"><div class="step-dot"></div>Upload a PDF using the file picker above</div>
        <div class="step-row"><div class="step-dot"></div>Wait a moment while it gets indexed</div>
        <div class="step-row"><div class="step-dot"></div>Ask any question about the content</div>
        <div class="step-row"><div class="step-dot"></div>Get cited answers with source pages</div>
    </div>
    """, unsafe_allow_html=True)