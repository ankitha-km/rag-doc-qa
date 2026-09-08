"""
Shared pytest fixtures.

Runs the whole test suite against a throwaway SQLite file (test_docmind.db)
instead of your real docmind.db, so running tests never touches your actual
data. Deleted automatically after each test.
"""

import os

# Must be set BEFORE main.py (and therefore database.py/auth.py) is imported,
# since they read these at module load time.
os.environ["DATABASE_URL"] = "sqlite:///./test_docmind.db"
os.environ.setdefault("JWT_SECRET_KEY", "test-only-secret-not-for-production")

import pytest
from fastapi.testclient import TestClient

from main import app
from database import engine


@pytest.fixture()
def client():
    """A fresh TestClient per test, with a clean database each time."""
    engine.dispose()  # drop any pooled connections to the previous test's db file
    if os.path.exists("test_docmind.db"):
        os.remove("test_docmind.db")

    with TestClient(app) as c:
        yield c

    engine.dispose()
    if os.path.exists("test_docmind.db"):
        os.remove("test_docmind.db")


@pytest.fixture()
def auth_headers(client):
    """Registers a throwaway user and returns ready-to-use auth headers."""
    res = client.post("/auth/register", json={"username": "testuser", "password": "testpass123"})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}