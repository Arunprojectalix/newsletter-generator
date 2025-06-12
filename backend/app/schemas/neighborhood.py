from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class ManagerInfoCreate(BaseModel):
    email: EmailStr
    whatsapp: Optional[str] = None

class BrandingInfoCreate(BaseModel):
    company_name: str
    footer_description: str
    primary_color: Optional[str] = "#1E40AF"
    logo_url: Optional[str] = None

class NeighborhoodCreate(BaseModel):
    title: str
    postcode: str
    frequency: str = Field(..., pattern="^(Weekly|Monthly)$")
    info: Optional[str] = None
    manager: ManagerInfoCreate
    radius: float = Field(..., gt=0, le=50)
    branding: BrandingInfoCreate

class NeighborhoodResponse(NeighborhoodCreate):
    id: str = Field(..., alias="_id")
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        populate_by_name = True
