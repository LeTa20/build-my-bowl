from fastapi import HTTPException, status, Depends, Request
from sqlmodel import Session, select
from typing import Optional
import hashlib

from app.db import get_session
from app.models import User


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash


def get_current_user(
    request: Request, session: Session = Depends(get_session)
) -> User:
    username = request.cookies.get("username")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    user = session.exec(select(User).where(User.username == username)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    return user


def get_optional_user(
    request: Request, session: Session = Depends(get_session)
) -> Optional[User]:
    username = request.cookies.get("username")
    if not username:
        return None
    
    user = session.exec(select(User).where(User.username == username)).first()
    return user

