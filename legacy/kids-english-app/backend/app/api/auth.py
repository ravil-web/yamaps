"""
Authentication API Routes
"""
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import User, ParentChildRelation, ParentSettings
from app.schemas import (
    ChildCreate, ParentCreate, UserLogin, UserResponse, Token
)
from app.auth import (
    hash_password, verify_password, create_access_token, create_refresh_token,
    get_current_active_user, rate_limiter
)
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register/parent", response_model=Token)
async def register_parent(
    user_data: ParentCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new parent account"""
    # Check if username exists
    result = await db.execute(
        select(User).where(User.username == user_data.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email exists
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create parent user
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        role="parent",
        language_preference="ru"
    )
    db.add(user)
    await db.flush()
    
    # Create parent settings
    parent_settings = ParentSettings(parent_id=user.id)
    db.add(parent_settings)
    
    await db.commit()
    await db.refresh(user)
    
    # Create tokens
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role}
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "role": user.role}
    )
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user)
    )


@router.post("/register/child", response_model=Token)
async def register_child(
    user_data: ChildCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new child account (requires parent email)"""
    # Check if username exists
    result = await db.execute(
        select(User).where(User.username == user_data.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Find parent by email
    result = await db.execute(
        select(User).where(
            User.email == user_data.parent_email,
            User.role == "parent"
        )
    )
    parent = result.scalar_one_or_none()
    
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Parent account not found. Please ask your parent to register first."
        )
    
    # Create child user
    user = User(
        username=user_data.username,
        password_hash=hash_password(user_data.password),
        role="child",
        date_of_birth=user_data.date_of_birth,
        language_preference=user_data.language_preference
    )
    db.add(user)
    await db.flush()
    
    # Create parent-child relation
    relation = ParentChildRelation(
        parent_id=parent.id,
        child_id=user.id
    )
    db.add(relation)
    
    await db.commit()
    await db.refresh(user)
    
    # Create tokens
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role}
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "role": user.role}
    )
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user)
    )


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """Login with username and password"""
    # Check rate limiting
    if rate_limiter.is_blocked(credentials.username):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed attempts. Please try again later."
        )
    
    # Find user
    result = await db.execute(
        select(User).where(User.username == credentials.username)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        rate_limiter.record_attempt(credentials.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    # Clear failed attempts
    rate_limiter.clear_attempts(credentials.username)
    
    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()
    
    # Create tokens
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role}
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "role": user.role}
    )
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user)
    )


@router.post("/refresh")
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token"""
    from app.auth import decode_token
    
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    result = await db.execute(
        select(User).where(User.id == uuid.UUID(user_id))
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new tokens
    new_access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role}
    )
    new_refresh_token = create_refresh_token(
        data={"sub": str(user.id), "role": user.role}
    )
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_active_user)
):
    """Logout current user"""
    # In a production system, you would invalidate the token
    # by adding it to a blacklist in Redis
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information"""
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    avatar_url: str = None,
    language_preference: str = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user profile"""
    if avatar_url:
        current_user.avatar_url = avatar_url
    if language_preference:
        current_user.language_preference = language_preference
    
    await db.commit()
    await db.refresh(current_user)
    
    return UserResponse.model_validate(current_user)
