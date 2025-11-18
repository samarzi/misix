from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional
import logging
from datetime import datetime, timedelta
import jwt
import bcrypt
from passlib.context import CryptContext

from app.shared.config import settings
from app.shared.supabase import get_supabase_client

router = APIRouter()
logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Pydantic models
class UserBase(BaseModel):
    email: EmailStr
    full_name: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: str
    created_at: str
    updated_at: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class TokenData(BaseModel):
    email: Optional[str] = None

# Helper functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except jwt.PyJWTError:
        raise credentials_exception

    # Get user from database
    supabase = get_supabase_client()
    response = supabase.table("users").select("*").eq("email", token_data.email).execute()

    if not response.data:
        raise credentials_exception

    user_data = response.data[0]
    return User(**user_data)

@router.post("/register", response_model=User)
async def register_user(user: UserCreate):
    """Register a new user."""
    try:
        supabase = get_supabase_client()

        # Check if user already exists
        existing = supabase.table("users").select("email").eq("email", user.email).execute()
        if existing.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Hash password
        hashed_password = get_password_hash(user.password)

        # Create user
        user_data = {
            "email": user.email,
            "full_name": user.full_name,
            "password_hash": hashed_password
        }

        response = supabase.table("users").insert(user_data).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )

        return User(**response.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/login", response_model=Token)
async def login_user(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login user and return access token."""
    try:
        supabase = get_supabase_client()

        # Get user by email
        response = supabase.table("users").select("*").eq("email", form_data.username).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_data = response.data[0]

        # Verify password
        if not verify_password(form_data.password, user_data["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Create access token
        access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": user_data["email"]}, expires_delta=access_token_expires
        )

        user = User(**user_data)

        return Token(
            access_token=access_token,
            token_type="bearer",
            user=user
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error logging in user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return current_user

@router.put("/me", response_model=User)
async def update_user(
    full_name: Optional[str] = None,
    bio: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Update current user profile."""
    try:
        supabase = get_supabase_client()

        update_data = {}
        if full_name is not None:
            update_data["full_name"] = full_name
        if bio is not None:
            update_data["bio"] = bio

        if not update_data:
            return current_user

        update_data["updated_at"] = "now()"

        response = supabase.table("users").update(update_data).eq("id", current_user.id).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user"
            )

        return User(**response.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Update failed"
        )

@router.get("/telegram/{telegram_id}")
async def get_user_by_telegram_id(telegram_id: int):
    """Get user by Telegram ID for Telegram WebApp authentication."""
    try:
        supabase = get_supabase_client()

        # Get user by telegram_id
        response = supabase.table("users").select("*").eq("telegram_id", telegram_id).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        user_data = response.data[0]
        
        return {
            "id": user_data["id"],
            "telegram_id": user_data["telegram_id"],
            "full_name": user_data.get("full_name"),
            "username": user_data.get("username"),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user by telegram_id: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user"
        )
