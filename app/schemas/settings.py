from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PrivacyPolicyUpdate(BaseModel):
    content: str
    version: Optional[str] = None


class PrivacyPolicyResponse(BaseModel):
    id: int
    content: str
    version: str
    updated_at: Optional[datetime]
    updated_by: Optional[int]

    class Config:
        from_attributes = True


class TermsOfServiceUpdate(BaseModel):
    content: str
    version: Optional[str] = None


class TermsOfServiceResponse(BaseModel):
    id: int
    content: str
    version: str
    updated_at: Optional[datetime]
    updated_by: Optional[int]

    class Config:
        from_attributes = True
