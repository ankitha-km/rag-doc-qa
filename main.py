"""
DocMind API — FastAPI wrapper around the existing RAG pipeline.

This does NOT change any of your core logic in pdf_parser.py, chunker.py,
embedder.py, vector_store.py, or llm.py. It just exposes them as routes
instead of gluing them together inline inside a Streamlit script.

Run locally:
    uvicorn main:app --reload
Then open http://127.0.0.1:8000/docs for the interactive Swagger UI —
that free auto-generated docs page is itself a nice thing to show off
in an interview.
"""

import os
import tempfile

from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel, Field

from pdf_parser import extract_text_from_pdf
from chunker import chunk_text
from embedder import embed_chunks, embed_query
from vector_store import store_chunks, search, get_count
from llm import ask_llm, summarize_document

app = FastAPI(
    title="DocMind API",
    description="Upload a PDF, then ask questions about it — RAG over your own documents.",
    version="0.1.0",
)

# ── In-memory doc stats (fine for v1 — becomes a DB table in the next step) ──
_doc_stats = {"pages": 0, "chunks": 0, "filename": None}


# ── Request/response schemas ─────────────────────────────────────────────
class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Question about the uploaded document")
    top_k: int = Field(3, ge=1, le=8)
    similarity_threshold: float = Field(0.2, ge=0.0, le=1.0)


class QueryResponse(BaseModel):
    answer: str
    sources: list[dict]


class UploadResponse(BaseModel):
    filename: str
    pages: int
    chunks: int


class SummaryResponse(BaseModel):
    summary: str


class StatsResponse(BaseModel):
    indexed: bool
    pages: int
    chunks: int
    filename: str | None


# ── Routes ────────────────────────────────────────────────────────────────
@app.post("/documents/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload a PDF, extract + chunk + embed + store it. Replaces any previously indexed doc (v1 = single-document)."""
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        pages = extract_text_from_pdf(tmp_path)
        if not pages:
            raise HTTPException(status_code=422, detail="Couldn't extract any text from this PDF")

        chunks = chunk_text(pages)
        chunks = embed_chunks(chunks)
        store_chunks(chunks)
    finally:
        os.unlink(tmp_path)

    _doc_stats.update(pages=len(pages), chunks=len(chunks), filename=file.filename)
    return UploadResponse(filename=file.filename, pages=len(pages), chunks=len(chunks))


@app.post("/query", response_model=QueryResponse)
async def query_document(req: QueryRequest):
    """Ask a question about the currently indexed document."""
    if get_count() == 0:
        raise HTTPException(status_code=400, detail="No document indexed yet — upload one first")

    q_embedding = embed_query(req.question)
    hits = search(q_embedding, top_k=req.top_k)
    answer = ask_llm(req.question, hits, req.similarity_threshold)

    good_hits = [h for h in hits if h["similarity"] >= req.similarity_threshold]
    return QueryResponse(answer=answer, sources=good_hits)


@app.post("/summarize", response_model=SummaryResponse)
async def summarize():
    """Summarize the currently indexed document."""
    if get_count() == 0:
        raise HTTPException(status_code=400, detail="No document indexed yet — upload one first")

    q_embedding = embed_query("introduction background methodology results conclusion")
    all_chunks = search(q_embedding, top_k=8)
    summary = summarize_document(all_chunks)
    return SummaryResponse(summary=summary)


@app.get("/documents/stats", response_model=StatsResponse)
async def document_stats():
    """Quick check: is a document indexed, and what's in it."""
    count = get_count()
    return StatsResponse(
        indexed=count > 0,
        pages=_doc_stats["pages"],
        chunks=count,
        filename=_doc_stats["filename"],
    )


@app.get("/health")
async def health():
    return {"status": "ok"}