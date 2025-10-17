from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.core.database import get_db
from app.core.models import User
from app.core.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user information."""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "mobile": current_user.mobile,
        "role": current_user.role
    }

@router.get("/status")
async def auth_status(request: Request):
    """Check if user is authenticated."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return {"authenticated": False}
    
    try:
        # In production, validate the token properly
        return {"authenticated": True}
    except:
        return {"authenticated": False}