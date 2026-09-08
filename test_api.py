"""
DocMind API tests.

The RAG pipeline itself (pdf_parser/chunker/embedder/vector_store/llm) is
mocked out here on purpose:
  - it's slow (model downloads, real API calls to Groq)
  - vector_store.py replaces ALL indexed data on every upload, so running it
    for real in a test would destroy whatever document you actually have
    indexed on your machine

These tests check the API layer — auth, routing, request validation, and
per-user data isolation — which is the part that's actually at risk of
regressing as you keep building. The pipeline itself you've already verified
works, manually, end to end.
"""

import pytest


@pytest.fixture(autouse=True)
def mock_pipeline(monkeypatch):
    """Replaces the heavy RAG pipeline functions with fast, predictable fakes."""
    import main

    monkeypatch.setattr(main, "extract_text_from_pdf", lambda path: ["page one text"])
    monkeypatch.setattr(main, "chunk_text", lambda pages: [{"text": "a chunk", "page_number": 1}])
    monkeypatch.setattr(main, "embed_chunks", lambda chunks: chunks)
    monkeypatch.setattr(main, "embed_query", lambda q: [0.1, 0.2, 0.3])
    monkeypatch.setattr(main, "store_chunks", lambda chunks: None)
    monkeypatch.setattr(main, "get_count", lambda: 1)
    monkeypatch.setattr(
        main, "search",
        lambda embedding, top_k: [{"text": "a chunk", "page_number": 1, "similarity": 0.9, "distance": 0.1}],
    )
    monkeypatch.setattr(main, "ask_llm", lambda question, hits, threshold: f"Mock answer to: {question}")
    monkeypatch.setattr(main, "summarize_document", lambda hits: "Mock summary")


def upload_sample(client, headers):
    return client.post(
        "/documents/upload",
        files={"file": ("sample.pdf", b"%PDF-1.4 fake content", "application/pdf")},
        headers=headers,
    )


# ── Health ──
def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


# ── Auth ──
def test_register_returns_token(client):
    res = client.post("/auth/register", json={"username": "alice", "password": "hunter22"})
    assert res.status_code == 200
    assert "access_token" in res.json()


def test_register_duplicate_username_rejected(client):
    client.post("/auth/register", json={"username": "alice", "password": "hunter22"})
    res = client.post("/auth/register", json={"username": "alice", "password": "different1"})
    assert res.status_code == 400


def test_login_wrong_password_rejected(client):
    client.post("/auth/register", json={"username": "alice", "password": "hunter22"})
    res = client.post("/auth/login", data={"username": "alice", "password": "wrongpass"})
    assert res.status_code == 401


def test_login_correct_password_succeeds(client):
    client.post("/auth/register", json={"username": "alice", "password": "hunter22"})
    res = client.post("/auth/login", data={"username": "alice", "password": "hunter22"})
    assert res.status_code == 200
    assert "access_token" in res.json()


# ── Auth is required on protected routes ──
def test_upload_without_token_rejected(client):
    res = upload_sample(client, headers={})
    assert res.status_code == 401


def test_query_without_token_rejected(client):
    res = client.post("/query", json={"question": "hi", "top_k": 3, "similarity_threshold": 0.2})
    assert res.status_code == 401


# ── Upload validation ──
def test_upload_rejects_non_pdf(client, auth_headers):
    res = client.post(
        "/documents/upload",
        files={"file": ("notes.txt", b"just text", "text/plain")},
        headers=auth_headers,
    )
    assert res.status_code == 400


# ── Core flow ──
def test_query_before_any_upload_fails(client, auth_headers):
    res = client.post(
        "/query", json={"question": "hi", "top_k": 3, "similarity_threshold": 0.2}, headers=auth_headers
    )
    assert res.status_code == 400


def test_upload_then_query_succeeds(client, auth_headers):
    upload_res = upload_sample(client, auth_headers)
    assert upload_res.status_code == 200
    body = upload_res.json()
    assert body["filename"] == "sample.pdf"
    assert "document_id" in body

    query_res = client.post(
        "/query",
        json={"question": "what is this about?", "top_k": 3, "similarity_threshold": 0.2},
        headers=auth_headers,
    )
    assert query_res.status_code == 200
    assert "what is this about?" in query_res.json()["answer"]
    assert len(query_res.json()["sources"]) > 0


def test_summarize_after_upload_succeeds(client, auth_headers):
    upload_sample(client, auth_headers)
    res = client.post("/summarize", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["summary"] == "Mock summary"


def test_history_records_the_question_asked(client, auth_headers):
    upload_res = upload_sample(client, auth_headers)
    doc_id = upload_res.json()["document_id"]

    client.post(
        "/query",
        json={"question": "what is this about?", "top_k": 3, "similarity_threshold": 0.2},
        headers=auth_headers,
    )

    history_res = client.get(f"/documents/{doc_id}/history", headers=auth_headers)
    assert history_res.status_code == 200
    entries = history_res.json()
    assert len(entries) == 1
    assert entries[0]["question"] == "what is this about?"


# ── Per-user isolation — the whole point of adding auth ──
def test_users_cannot_see_each_others_documents(client):
    alice_token = client.post("/auth/register", json={"username": "alice", "password": "hunter22"}).json()["access_token"]
    bob_token = client.post("/auth/register", json={"username": "bob", "password": "hunter22"}).json()["access_token"]

    alice_headers = {"Authorization": f"Bearer {alice_token}"}
    bob_headers = {"Authorization": f"Bearer {bob_token}"}

    upload_res = upload_sample(client, alice_headers)
    doc_id = upload_res.json()["document_id"]

    # Bob can't see Alice's document in his list
    bob_docs = client.get("/documents", headers=bob_headers).json()
    assert bob_docs == []

    # Bob can't read Alice's document history
    forbidden_res = client.get(f"/documents/{doc_id}/history", headers=bob_headers)
    assert forbidden_res.status_code == 403

    # Alice can see her own
    alice_docs = client.get("/documents", headers=alice_headers).json()
    assert len(alice_docs) == 1


def test_history_for_nonexistent_document_returns_404(client, auth_headers):
    res = client.get("/documents/99999/history", headers=auth_headers)
    assert res.status_code == 404