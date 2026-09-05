"""
DocMind auth — password hashing + JWT issuing/verification.

Flow:
  1. POST /auth/register  -> creates a user, password stored as a bcrypt hash (never plaintext)
  2. POST /auth/login     -> verifies password, returns a signed JWT access token
  3. Every protected route takes that token in the Authorization header
     (Authorization: Bearer <token>) and get_current_user() decodes it to
     figure out who's calling.

JWT_SECRET_KEY must be set in your .env file — never hardcode it, and never
commit it. If it's missing, this raises immediately at import time so you
catch the mistake before it becomes a real bug.
"""

import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database import get_db, User

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY is not set — add it to your .env file")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours — fine for a learning project

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def hash_password(plain_password: str) -> str:
    # bcrypt caps input at 72 bytes — fine for any real password, but encode explicitly
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_error
    except jwt.PyJWTError:
        raise credentials_error

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_error
    return user