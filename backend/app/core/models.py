from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    
    # User profile information
    email = Column(String(255), unique=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    mobile = Column(String(20))  # Mobile/phone number
    
    # Authentication - password for simple auth, Kratos ID for production
    password_hash = Column(String(255))  # For simple auth in development
    kratos_identity_id = Column(String(255), unique=True)  # Kratos identity ID for production
    
    # Authorization
    role = Column(String(50), default="inspector")  # inspector, admin, viewer
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# Create indexes for User
Index('idx_user_email', User.email)
Index('idx_user_kratos_identity', User.kratos_identity_id)
Index('idx_user_active', User.is_active)