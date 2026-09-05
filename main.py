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

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from pdf_parser import extract_text_from_pdf
from chunker import chunk_text
from embedder import embed_chunks, embed_query
from vector_store import store_chunks, search, get_count
from llm import ask_llm, summarize_document
from database import init_db, get_db, Document, Query as QueryModel

app = FastAPI(
    title="DocMind API",
    description="Upload a PDF, then ask questions about it — RAG over your own documents.",
    version="0.2.0",
)


@app.on_event("startup")
def on_startup():
    init_db()


# ── Tracks which document is "active" for the /query and /summarize routes.
#    Still single-document-at-a-time for v1 — the DB stores full history
#    regardless, this just points at the most recently uploaded one. ──
_active_document_id: int | None = None


# ── Request/response schemas ─────────────────────────────────────────────
class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Question about the uploaded document")
    top_k: int = Field(3, ge=1, le=8)
    similarity_threshold: float = Field(0.2, ge=0.0, le=1.0)


class QueryResponse(BaseModel):
    answer: str
    sources: list[dict]


class UploadResponse(BaseModel):
    document_id: int
    filename: str
    pages: int
    chunks: int


class HistoryEntry(BaseModel):
    id: int
    question: str
    answer: str
    created_at: str


class DocumentSummary(BaseModel):
    id: int
    filename: str
    pages: int
    chunks: int
    created_at: str


class SummaryResponse(BaseModel):
    summary: str


class StatsResponse(BaseModel):
    indexed: bool
    pages: int
    chunks: int
    filename: str | None


# ── Routes ────────────────────────────────────────────────────────────────
@app.post("/documents/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload a PDF, extract + chunk + embed + store it, and make it the active document for queries."""
    global _active_document_id

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

    doc = Document(filename=file.filename, pages=len(pages), chunks=len(chunks))
    db.add(doc)
    db.commit()
    db.refresh(doc)

    _active_document_id = doc.id
    return UploadResponse(document_id=doc.id, filename=doc.filename, pages=doc.pages, chunks=doc.chunks)


@app.post("/query", response_model=QueryResponse)
async def query_document(req: QueryRequest, db: Session = Depends(get_db)):
    """Ask a question about the currently active document. Saves the Q&A to that document's history."""
    if get_count() == 0 or _active_document_id is None:
        raise HTTPException(status_code=400, detail="No document indexed yet — upload one first")

    q_embedding = embed_query(req.question)
    hits = search(q_embedding, top_k=req.top_k)
    answer = ask_llm(req.question, hits, req.similarity_threshold)

    db.add(QueryModel(
        document_id=_active_document_id,
        question=req.question,
        answer=answer,
        top_k=req.top_k,
        similarity_threshold=req.similarity_threshold,
    ))
    db.commit()

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
async def document_stats(db: Session = Depends(get_db)):
    """Quick check: is a document indexed, and what's the active one."""
    count = get_count()
    active = db.query(Document).filter(Document.id == _active_document_id).first() if _active_document_id else None
    return StatsResponse(
        indexed=count > 0,
        pages=active.pages if active else 0,
        chunks=count,
        filename=active.filename if active else None,
    )


@app.get("/documents", response_model=list[DocumentSummary])
async def list_documents(db: Session = Depends(get_db)):
    """All documents ever uploaded, most recent first."""
    docs = db.query(Document).order_by(Document.created_at.desc()).all()
    return [
        DocumentSummary(
            id=d.id, filename=d.filename, pages=d.pages, chunks=d.chunks,
            created_at=d.created_at.isoformat(),
        )
        for d in docs
    ]


@app.get("/documents/{document_id}/history", response_model=list[HistoryEntry])
async def document_history(document_id: int, db: Session = Depends(get_db)):
    """Every question asked against a specific document, oldest first."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return [
        HistoryEntry(id=q.id, question=q.question, answer=q.answer, created_at=q.created_at.isoformat())
        for q in sorted(doc.queries, key=lambda q: q.created_at)
    ]


@app.get("/health")
async def health():
    return {"status": "ok"}