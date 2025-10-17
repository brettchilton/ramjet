"""
Script to create test tenant and user for development
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, engine
from models import Tenant, User
from sqlalchemy.orm import Session
import uuid

# Test IDs from upload.py
TEST_TENANT_ID = "550e8400-e29b-41d4-a716-446655440000"
TEST_USER_ID = "550e8400-e29b-41d4-a716-446655440001"

def create_test_data():
    db = SessionLocal()
    
    try:
        # Check if test tenant exists
        existing_tenant = db.query(Tenant).filter(Tenant.id == TEST_TENANT_ID).first()
        if not existing_tenant:
            # Create test tenant
            test_tenant = Tenant(
                id=TEST_TENANT_ID,
                name="Test Tenant",
                slug="test-tenant",
                contact_email="test@example.com",
                is_active=True
            )
            db.add(test_tenant)
            db.commit()
            print(f"Created test tenant: {TEST_TENANT_ID}")
        else:
            print("Test tenant already exists")
        
        # Check if test user exists
        existing_user = db.query(User).filter(User.id == TEST_USER_ID).first()
        if not existing_user:
            # Create test user
            test_user = User(
                id=TEST_USER_ID,
                tenant_id=TEST_TENANT_ID,
                email="test@example.com",
                first_name="Test",
                last_name="User",
                is_active=True
            )
            db.add(test_user)
            db.commit()
            print(f"Created test user: {TEST_USER_ID}")
        else:
            print("Test user already exists")
            
    except Exception as e:
        print(f"Error creating test data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_data()