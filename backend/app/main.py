# backend/app/main.py

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db, engine
from app.core.models import Base, User
import logging
import os
import psycopg2
import time
import uuid
from typing import Dict, Any, Optional

# Configure logging so all app.* loggers output to stdout
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

# Import routers
from app.api import auth_simplified, auth_kratos, auth_simple, products, system, orders, settings, analytics
from app.api import stock, stock_verification, raw_materials, stocktake, reports
# from app.api import upload  # Temporarily disabled

# Import authentication
from app.core.auth import get_current_user, get_current_user_optional, require_role

# Import Gmail poller singleton
from app.services.gmail_service import gmail_poller

# Initialize FastAPI application
app = FastAPI(
    title="Ramjet API",
    description="Ramjet API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5280", "http://localhost:3000", "http://localhost:5173"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
# app.include_router(upload.router)  # Temporarily disabled
app.include_router(auth_simplified.router)
app.include_router(auth_kratos.router)
app.include_router(auth_simple.router)
app.include_router(products.router)
app.include_router(system.router)
app.include_router(orders.router)
app.include_router(settings.router)
app.include_router(analytics.router)
app.include_router(stock.router)
app.include_router(stock_verification.router)
app.include_router(raw_materials.router)
app.include_router(stocktake.router)
app.include_router(reports.router)

# Database connection details are pulled from environment variables.
DB_HOST = os.environ.get('DB_HOST')
DB_NAME = os.environ.get('POSTGRES_DB') 
DB_USER = os.environ.get('POSTGRES_USER')
DB_PASSWORD = os.environ.get('POSTGRES_PASSWORD')

# Pydantic model for defining the structure of response messages.
class Message(BaseModel):
    message: str

# This event runs when the FastAPI application starts up.
# It attempts to connect to the database to ensure it's available.
@app.on_event("startup")
async def startup_event():
    print("Attempting to connect to the database...")
    # Implement a retry mechanism for database connection.
    # This helps if the DB container isn't fully ready when the backend starts.
    for i in range(10): # Try up to 10 times
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            conn.close() # Close the connection immediately after successful test
            print("Successfully connected to the database!")

            # Conditionally start Gmail poller if credentials are configured
            if os.environ.get("GMAIL_REFRESH_TOKEN"):
                print("Gmail credentials found — starting email poller...")
                await gmail_poller.start()
            else:
                print("Gmail credentials not configured — email poller disabled")

            return # Exit the loop and continue startup
        except psycopg2.OperationalError as e:
            # Catch specific operational errors related to connection issues
            print(f"Database connection failed on attempt {i+1}: {e}")
            time.sleep(3) # Wait for 3 seconds before the next retry

    # If all retries fail, raise an exception to prevent the application from starting
    print("Could not connect to the database after multiple attempts. Application will not start.")
    raise HTTPException(status_code=500, detail="Database startup failed: Could not connect to PostgreSQL.")

@app.on_event("shutdown")
async def shutdown_event():
    if gmail_poller.is_running:
        print("Shutting down Gmail poller...")
        await gmail_poller.stop()


# Define a root endpoint (GET /)
@app.get("/", response_model=Message)
async def read_root():
    """
    Returns a simple welcome message from the FastAPI backend.
    """
    return {"message": "Hello from the Annie Defect Tracking API!"}

# Define a database test endpoint (GET /db_test)
@app.get("/db_test", response_model=Message)
async def db_test():
    """
    Tests the connection to the PostgreSQL database and returns its version.
    """
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cur = conn.cursor() # Create a cursor object
        cur.execute("SELECT version();") # Execute a SQL query to get DB version
        db_version = cur.fetchone()[0] # Fetch the first column of the first row
        cur.close() # Close the cursor
        conn.close() # Close the connection
        return {"message": f"Successfully connected to PostgreSQL! Version: {db_version}"}
    except Exception as e:
        # If any error occurs during DB interaction, raise an HTTP exception
        raise HTTPException(status_code=500, detail=f"Database connection error: {e}")

# Test SQLAlchemy ORM connection
@app.get("/orm_test", response_model=Message)
async def orm_test(db: Session = Depends(get_db)):
    """
    Tests the SQLAlchemy ORM connection by counting users.
    """
    try:
        user_count = db.query(User).count()
        return {"message": f"SQLAlchemy ORM connected! Found {user_count} users in database."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ORM connection error: {e}")

# Protected endpoint example
@app.get("/api/protected", response_model=Message)
async def protected_route(current_user: User = Depends(get_current_user)):
    """
    Example of a protected endpoint that requires authentication.
    """
    return {"message": f"Hello {current_user.email}! This is a protected route."}

# Admin-only endpoint example
@app.get("/api/admin", response_model=Message, dependencies=[Depends(require_role("admin"))])
async def admin_route():
    """
    Example of an admin-only endpoint.
    Requires the user to have the 'admin' role.
    """
    return {"message": "This is an admin-only route."}

# User management endpoint
@app.get("/api/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get information about the currently authenticated user.
    """
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "mobile": current_user.mobile,
        "role": current_user.role,
        "is_active": current_user.is_active
    }

# List all users endpoint (admin only)
@app.get("/api/admin/users", dependencies=[Depends(require_role("admin"))])
async def list_users(db: Session = Depends(get_db)):
    """
    List all users (admin only).
    """
    users = db.query(User).all()
    return [
        {
            "id": str(u.id),
            "email": u.email,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "mobile": u.mobile,
            "role": u.role,
            "is_active": u.is_active
        } for u in users
    ]

# This block is for running the app directly (e.g., for local testing without Docker)
# In a Docker setup, uvicorn is typically run via the CMD in the Dockerfile.
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)