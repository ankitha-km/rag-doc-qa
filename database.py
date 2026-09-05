"""
DocMind database layer — SQLite via SQLAlchemy.

Two tables:
  - documents: one row per uploaded PDF (so you can see what's been indexed over time)
  - queries:   one row per question asked, linked to the document it was asked against

This gives you real "history scoped to a document" instead of one global chat log —
upload a new PDF and you get a fresh history, but old sessions are still stored and
queryable later (e.g. for an analytics dashboard, or just to show in an interview
that you understand relational modeling).
"""

from datetime import datetime, timezone

from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session

DATABASE_URL = "sqlite:///./docmind.db"

# check_same_thread=False is needed because FastAPI can use SQLite from
# multiple threads within one process — safe for our single-writer use case
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    documents = relationship("Document", back_populates="owner", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    pages = Column(Integer, nullable=False)
    chunks = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    owner = relationship("User", back_populates="documents")
    queries = relationship("Query", back_populates="document", cascade="all, delete-orphan")


class Query(Base):
    __tablename__ = "queries"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    top_k = Column(Integer)
    similarity_threshold = Column(Float)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    document = relationship("Document", back_populates="queries")


def init_db():
    """Create tables if they don't exist yet. Safe to call every startup."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency — yields a session, always closes it after the request."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()