from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
import httpx
import os
import logging
from datetime import datetime

from app.core.database import get_db
from app.core.models import User
from app.core.auth import create_access_token
from datetime import timedelta

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/kratos", tags=["kratos-authentication"])

# Kratos configuration
KRATOS_PUBLIC_URL = os.getenv("KRATOS_PUBLIC_URL", "http://localhost:4433")
KRATOS_ADMIN_URL = os.getenv("KRATOS_ADMIN_URL", "http://kratos:4434")
WEBHOOK_SECRET = os.getenv("KRATOS_WEBHOOK_SECRET", "your-webhook-secret")

class KratosWebhookRequest(BaseModel):
    identity_id: str
    email: EmailStr
    first_name: str
    last_name: str
    mobile: Optional[str] = None
    role: Optional[str] = "inspector"

class SessionResponse(BaseModel):
    session_token: Optional[str] = None
    session: Optional[Dict[str, Any]] = None
    access_token: Optional[str] = None
    user: Optional[Dict[str, Any]] = None

@router.post("/webhook")
async def kratos_webhook(
    request: Request,
    webhook_data: KratosWebhookRequest,
    db: Session = Depends(get_db)
):
    """Handle webhook from Kratos after registration."""
    
    # Verify webhook token
    webhook_token = request.headers.get("X-Kratos-Webhook-Token")
    if webhook_token != WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook token"
        )
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == webhook_data.email).first()
        
        if existing_user:
            # Update existing user with Kratos identity ID
            existing_user.kratos_identity_id = webhook_data.identity_id
            existing_user.updated_at = datetime.utcnow()
        else:
            # Create new user
            user = User(
                email=webhook_data.email,
                first_name=webhook_data.first_name,
                last_name=webhook_data.last_name,
                mobile=webhook_data.mobile,
                kratos_identity_id=webhook_data.identity_id,
                role=webhook_data.role,
                is_active=True
            )
            db.add(user)
        
        db.commit()
        
        logger.info(f"User {webhook_data.email} synced with Kratos identity {webhook_data.identity_id}")
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process webhook"
        )

@router.get("/session")
async def get_session(request: Request, db: Session = Depends(get_db)):
    """Check Kratos session and return user info with JWT token."""
    
    # Get session token from cookie or header
    session_token = request.cookies.get("annie_kratos_session")
    if not session_token:
        # Check Authorization header as fallback
        auth_header = request.headers.get("X-Session-Token")
        if auth_header:
            session_token = auth_header
    
    logger.info(f"Session check - token present: {bool(session_token)}")
    logger.info(f"Request cookies: {request.cookies}")
    logger.info(f"Request headers: {dict(request.headers)}")
    
    if not session_token:
        return SessionResponse()
    
    try:
        # Validate session with Kratos
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{KRATOS_PUBLIC_URL}/sessions/whoami",
                cookies={"annie_kratos_session": session_token},
                headers={"X-Session-Token": session_token},
                follow_redirects=False
            )
            
            logger.info(f"Kratos whoami response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.warning(f"Kratos session invalid: {response.status_code}")
                return SessionResponse()
            
            session_data = response.json()
            logger.info(f"Kratos session data: {session_data}")
            
        # Get user from database
        kratos_id = session_data["identity"]["id"]
        user = db.query(User).filter(User.kratos_identity_id == kratos_id).first()
        
        if not user:
            # User not synced yet, try to find by email
            email = session_data["identity"]["traits"]["email"]
            user = db.query(User).filter(User.email == email).first()
            
            if user:
                # Update with Kratos ID
                user.kratos_identity_id = kratos_id
                db.commit()
            else:
                # Create user from Kratos data
                traits = session_data["identity"]["traits"]
                user = User(
                    email=traits["email"],
                    first_name=traits.get("first_name", ""),
                    last_name=traits.get("last_name", ""),
                    mobile=traits.get("mobile"),
                    kratos_identity_id=kratos_id,
                    role=traits.get("role", "inspector"),
                    is_active=True
                )
                db.add(user)
                db.commit()
                db.refresh(user)
        
        # Create JWT token for API access
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "kratos_identity_id": user.kratos_identity_id
            },
            expires_delta=timedelta(hours=24)
        )
        
        return SessionResponse(
            session_token=session_token,
            session=session_data,
            access_token=access_token,
            user={
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "mobile": user.mobile,
                "role": user.role
            }
        )
        
    except Exception as e:
        logger.error(f"Session check error: {str(e)}")
        return SessionResponse()

@router.post("/logout")
async def logout(request: Request, response: Response):
    """Logout from Kratos session."""
    
    # Get session token
    session_token = request.cookies.get("annie_kratos_session")
    if not session_token:
        session_token = request.headers.get("X-Session-Token")
    
    if session_token:
        try:
            # Revoke session in Kratos
            async with httpx.AsyncClient() as client:
                kratos_response = await client.delete(
                    f"{KRATOS_ADMIN_URL}/sessions",
                    headers={"X-Session-Token": session_token}
                )
                
                if kratos_response.status_code == 204:
                    # Clear session cookie
                    response.delete_cookie("annie_kratos_session", path="/", domain="localhost")
                    return {"message": "Logged out successfully"}
                    
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
    
    return {"message": "Logout completed"}

@router.get("/flows/{flow_type}")
async def get_flow_status(flow_type: str, flow: str):
    """Get the status of a Kratos flow (login, registration, etc)."""
    
    if flow_type not in ["login", "registration", "recovery", "verification", "settings"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid flow type"
        )
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{KRATOS_PUBLIC_URL}/self-service/{flow_type}/flows",
                params={"id": flow}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Flow not found"
                )
                
    except httpx.RequestError as e:
        logger.error(f"Error fetching flow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch flow"
        )

@router.get("/flows/{flow_type}/browser")
async def init_flow(flow_type: str, request: Request, response: Response):
    """Initialize a Kratos flow (proxy endpoint)."""
    
    if flow_type not in ["login", "registration", "recovery", "verification", "settings"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid flow type"
        )
    
    try:
        # Forward all cookies from request to Kratos
        cookies = {}
        for key, value in request.cookies.items():
            cookies[key] = value
        
        # Include any CSRF tokens
        headers = {}
        if "x-csrf-token" in request.headers:
            headers["x-csrf-token"] = request.headers["x-csrf-token"]
        
        logger.info(f"Initializing {flow_type} flow")
        logger.info(f"Forwarding cookies: {cookies}")
        
        async with httpx.AsyncClient() as client:
            kratos_response = await client.get(
                f"{KRATOS_PUBLIC_URL}/self-service/{flow_type}/browser",
                cookies=cookies,
                headers=headers,
                follow_redirects=False
            )
            
            logger.info(f"Kratos response status: {kratos_response.status_code}")
            logger.info(f"Kratos response headers: {dict(kratos_response.headers)}")
            
            # Forward cookies from Kratos response, especially the session cookie
            for cookie_name, cookie_value in kratos_response.cookies.items():
                # Set cookie on the backend's domain (port 8006)
                response.set_cookie(
                    key=cookie_name,
                    value=cookie_value,
                    path="/",
                    httponly=True,
                    samesite="lax",
                    secure=False,  # Set to True in production with HTTPS
                    max_age=86400  # 24 hours
                )
            
            if kratos_response.status_code == 200:
                return kratos_response.json()
            elif kratos_response.status_code in [302, 303]:
                # Handle redirects
                location = kratos_response.headers.get("Location")
                if location:
                    # Check if redirected to frontend URL without flow param (already logged in)
                    if location.startswith("http://localhost:5179/") and "flow=" not in location:
                        # User is already logged in
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail={"error": {"id": "session_already_available", "message": "Already logged in"}}
                        )
                    
                    # Extract flow ID from redirect URL
                    import re
                    flow_match = re.search(r'flow=([a-f0-9-]+)', location)
                    if flow_match:
                        flow_id = flow_match.group(1)
                        # Fetch the flow
                        flow_response = await client.get(
                            f"{KRATOS_PUBLIC_URL}/self-service/{flow_type}/flows",
                            params={"id": flow_id},
                            cookies=cookies
                        )
                        if flow_response.status_code == 200:
                            return flow_response.json()
                
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to initialize flow"
                )
            elif kratos_response.status_code == 400:
                # Pass through the error response from Kratos
                error_data = kratos_response.json()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_data
                )
            else:
                raise HTTPException(
                    status_code=kratos_response.status_code,
                    detail=kratos_response.text
                )
                
    except httpx.RequestError as e:
        logger.error(f"Error initializing flow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize flow"
        )

@router.post("/flows/{flow_type}")
async def submit_flow(flow_type: str, request: Request, response: Response, db: Session = Depends(get_db)):
    """Submit a Kratos flow (proxy endpoint)."""
    
    if flow_type not in ["login", "registration", "recovery", "verification", "settings"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid flow type"
        )
    
    try:
        # Get flow_id from query params
        flow_id = request.query_params.get("flow_id")
        if not flow_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="flow_id parameter is required"
            )
        
        # Get request body
        body = await request.json()
        
        # Forward all cookies from request to Kratos
        cookies = {}
        for key, value in request.cookies.items():
            cookies[key] = value
        
        # Include any CSRF tokens in headers
        headers = {"Content-Type": "application/json"}
        if "x-csrf-token" in request.headers:
            headers["x-csrf-token"] = request.headers["x-csrf-token"]
        
        # Log for debugging
        print(f"Submitting {flow_type} flow {flow_id}")
        print(f"Cookies: {cookies}")
        print(f"Body: {body}")
        print(f"Headers: {dict(request.headers)}")
        
        async with httpx.AsyncClient() as client:
            kratos_response = await client.post(
                f"{KRATOS_PUBLIC_URL}/self-service/{flow_type}",
                params={"flow": flow_id},
                json=body,
                cookies=cookies,
                headers=headers,
                follow_redirects=False
            )
            
            # Forward cookies from Kratos response, especially the session cookie
            for cookie_name, cookie_value in kratos_response.cookies.items():
                # Set cookie on the backend's domain (port 8006)
                response.set_cookie(
                    key=cookie_name,
                    value=cookie_value,
                    path="/",
                    httponly=True,
                    samesite="lax",
                    secure=False,  # Set to True in production with HTTPS
                    max_age=86400  # 24 hours
                )
            
            if kratos_response.status_code == 200:
                result = kratos_response.json()
                
                # If login/registration successful and session created, also create JWT
                if flow_type in ["login", "registration"] and result.get("session"):
                    session = result["session"]
                    # Get user from database
                    kratos_id = session["identity"]["id"]
                    user = db.query(User).filter(User.kratos_identity_id == kratos_id).first()
                    
                    if user:
                        # Create JWT token
                        access_token = create_access_token(
                            data={
                                "sub": str(user.id),
                                "email": user.email,
                                "kratos_identity_id": user.kratos_identity_id
                            },
                            expires_delta=timedelta(hours=24)
                        )
                        result["access_token"] = access_token
                
                return result
            elif kratos_response.status_code in [400, 403]:
                # Flow has validation errors or CSRF error
                error_data = kratos_response.json()
                logger.error(f"Kratos flow submission error: {error_data}")
                return JSONResponse(
                    status_code=kratos_response.status_code,
                    content=error_data
                )
            else:
                logger.error(f"Kratos error {kratos_response.status_code}: {kratos_response.text}")
                raise HTTPException(
                    status_code=kratos_response.status_code,
                    detail=kratos_response.text
                )
                
    except httpx.RequestError as e:
        logger.error(f"Error submitting flow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit flow"
        )