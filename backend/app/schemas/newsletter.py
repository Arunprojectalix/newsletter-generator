from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class NewsletterGenerateRequest(BaseModel):
    neighborhood_id: str
    conversation_id: Optional[str] = None

class NewsletterUpdateRequest(BaseModel):
    user_message: str
    
class NewsletterResponse(BaseModel):
    id: str = Field(..., alias="_id")
    neighborhood_id: str
    conversation_id: Optional[str] = None
    newsletter_metadata: Dict[str, Any]
    content: Dict[str, Any]
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    version: int

    class Config:
        populate_by_name = True

class NewsletterActionRequest(BaseModel):
    action: str = Field(..., pattern="^(accept|reject)$")
    feedback: Optional[str] = None
