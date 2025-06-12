from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl, validator
from bson import ObjectId
from app.models.neighborhood import PyObjectId

class EventDetails(BaseModel):
    event_title: str
    description: str
    location: str
    cost: str
    date: str
    booking_details: Optional[str] = None
    images: List[str] = []  # Changed from HttpUrl to str to allow empty list or placeholder strings
    additional_info: Optional[str] = None
    is_recurring: bool = False
    tags: List[str] = []
    source_url: Optional[HttpUrl] = None
    verified: bool = False
    
    @validator('images', pre=True)
    def validate_images(cls, v):
        """Validate images - filter out invalid URLs and placeholder filenames."""
        if not v:
            return []
        
        valid_images = []
        for img in v:
            if isinstance(img, str):
                # Skip placeholder filenames that aren't real URLs
                if img.startswith('http://') or img.startswith('https://'):
                    valid_images.append(img)
                elif img.endswith('.jpg') or img.endswith('.png') or img.endswith('.jpeg'):
                    # Skip placeholder filenames like 'family_fun_day.jpg'
                    continue
                else:
                    # Allow other string formats that might be valid
                    valid_images.append(img)
        
        return valid_images

class NewsletterContent(BaseModel):
    header: Dict[str, Any]
    main_channel: Dict[str, Any]
    weekly_schedule: Optional[Dict[str, Any]] = None
    monthly_schedule: Optional[Dict[str, Any]] = None
    featured_venue: Optional[Dict[str, Any]] = None
    partner_spotlight: Optional[Dict[str, Any]] = None
    newsletter_highlights: List[Dict[str, Any]] = []
    events: List[EventDetails] = []

class NewsletterMetadata(BaseModel):
    location: str
    postcode: str
    radius: float
    generation_date: datetime
    template_version: str = "v1"
    source_count: int = 0
    verification_status: str = "pending"

class NewsletterModel(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    neighborhood_id: PyObjectId
    conversation_id: Optional[PyObjectId] = None
    newsletter_metadata: NewsletterMetadata
    content: NewsletterContent
    status: str = Field(default="generating", pattern="^(generating|generated|accepted|rejected|error)$")
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = 1

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
