from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class PrivacyPolicy(Base):
    __tablename__ = "privacy_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    version = Column(String, default="1.0")
    updated_by = Column(Integer, ForeignKey("admins.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class TermsOfService(Base):
    __tablename__ = "terms_of_service"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    version = Column(String, default="1.0")
    updated_by = Column(Integer, ForeignKey("admins.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
