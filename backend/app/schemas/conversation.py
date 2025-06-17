from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class MessageCreate(BaseModel):
    content: str
    role: Optional[str] = "user"

class MessageResponse(BaseModel):
    role: str
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

class ConversationCreate(BaseModel):
    neighborhood_id: str
    newsletter_id: Optional[str] = None

class ConversationResponse(BaseModel):
    id: str = Field(..., alias="_id")
    neighborhood_id: str
    newsletter_id: Optional[str] = None
    messages: Optional[List[MessageResponse]] = []
    status: str
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
