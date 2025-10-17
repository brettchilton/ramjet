# backend/app/core/auth.py

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from typing import Optional, Dict, Any
import httpx
import os
from functools import lru_cache
from passlib.context import CryptContext
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.models import User
from app.core.database import get_db

# Security scheme for JWT bearer tokens
security = HTTPBearer(auto_error=True)

# Ory Hydra configuration
HYDRA_ADMIN_URL = os.environ.get("HYDRA_ADMIN_URL", "http://hydra:4445")
HYDRA_PUBLIC_URL = os.environ.get("HYDRA_PUBLIC_URL", "http://hydra:4444")
HYDRA_CLIENT_ID = os.environ.get("HYDRA_CLIENT_ID", "annie-defect-frontend")
HYDRA_CLIENT_SECRET = os.environ.get("HYDRA_CLIENT_SECRET", "")

# JWT configuration for local token generation (for simple auth)
SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token for simple authentication."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def introspect_token(token: str) -> Dict[str, Any]:
    """
    Introspect an OAuth2 token using Ory Hydra's introspection endpoint.
    Returns token metadata if valid, raises exception if invalid.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{HYDRA_ADMIN_URL}/oauth2/introspect",
                data={
                    "token": token,
                    "token_type_hint": "access_token"
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            )
            response.raise_for_status()
            
            introspection_result = response.json()
            
            if not introspection_result.get("active", False):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token is not active"
                )
            
            return introspection_result
    except httpx.HTTPError as e:
        print(f"Error introspecting token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate token"
        )

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Verify the JWT token from the Authorization header.
    First tries Hydra introspection, then falls back to local JWT verification.
    """
    token = credentials.credentials
    
    print(f"AUTH: Verifying token (first 50 chars): {token[:50]}...")
    
    # First, try to introspect as an OAuth2 token
    try:
        introspection_result = await introspect_token(token)
        print(f"AUTH: OAuth2 token verified via introspection")
        return {
            "sub": introspection_result.get("sub"),
            "email": introspection_result.get("ext", {}).get("email"),
            "username": introspection_result.get("username"),
            "scope": introspection_result.get("scope", "").split(" "),
            "token_type": "oauth2"
        }
    except:
        # If introspection fails, try to decode as a local JWT
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            print(f"AUTH: Local JWT token verified")
            return {
                "sub": payload.get("sub"),
                "email": payload.get("email"),
                "username": payload.get("username"),
                "token_type": "jwt"
            }
        except JWTError as e:
            print(f"AUTH: JWT verification error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

async def get_current_user(
    token_payload: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
) -> User:
    """
    Extract user information from the verified token and fetch from database.
    """
    email = token_payload.get("email")
    username = token_payload.get("username")
    
    if not email and not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user information"
        )
    
    # Try to find user by email first, then username
    user = None
    if email:
        user = db.query(User).filter(User.email == email).first()
    elif username:
        user = db.query(User).filter(User.email == username).first()
    
    if not user:
        # Create a new user if they don't exist
        user = User(
            email=email or username,
            first_name=token_payload.get("given_name", ""),
            last_name=token_payload.get("family_name", ""),
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"AUTH: Created new user: {user.email}")
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    return user

def require_role(required_role: str):
    """
    Dependency to require a specific role for endpoint access.
    """
    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role != required_role and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have required role: {required_role}"
            )
        return current_user
    return role_checker

# Optional: Create a dependency for optional authentication
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Optional authentication - returns user info if authenticated, None otherwise.
    """
    if not credentials:
        return None
    
    try:
        token_payload = await verify_token(credentials)
        return await get_current_user(token_payload, db)
    except:
        return None

# Simple username/password authentication for initial setup
async def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Authenticate a user with email and password.
    For use with simple login before OAuth2 is fully configured.
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    # For now, we'll need to add a password field to User model
    # This is temporary until OAuth2 is fully set up
    return user