from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlmodel import Session, select
from pydantic import BaseModel, Field

from app.db import get_session
from app.models import User
from app.auth import hash_password

router = APIRouter()

# Validate username and password 
class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=30, pattern=r"^[a-zA-Z0-9_]+$", description="Username, 3-30 characters, alphanumeric and underscore only")
    password: str = Field(min_length=6, description="Password, must be at least 6 characters")

# Define the response when a user is registered 
class RegisterResponse(BaseModel):
    user_id: int
    username: str
    name: str
    
# Register new user account and return user information 
@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(
    request: RegisterRequest,
    response: Response,
    session: Session = Depends(get_session),  # Get database session
) -> RegisterResponse:
    existing = session.exec(  # Check if there is an existing user with the same username
        select(User).where(User.username == request.username)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,  # Bad request if username exists 
            detail="Username already exists",
        )
    
    user = User(
        username=request.username,
        password_hash=hash_password(request.password),
        name=request.username,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    response.set_cookie(key="username", value=user.username)
    
    return RegisterResponse(
        user_id=user.id,
        username=user.username,
        name=user.name,
    )

