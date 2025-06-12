from typing import Optional, Dict
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        from pydantic_core import core_schema
        
        def validate_object_id(value):
            if isinstance(value, ObjectId):
                return str(value)
            if isinstance(value, str):
                if ObjectId.is_valid(value):
                    return value
                raise ValueError("Invalid ObjectId")
            raise ValueError("Invalid ObjectId type")
        
        return core_schema.no_info_plain_validator_function(
            validate_object_id,
            serialization=core_schema.to_string_ser_schema()
        )

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        return {'type': 'string'}

class ManagerInfo(BaseModel):
    email: EmailStr
    whatsapp: Optional[str] = None

class BrandingInfo(BaseModel):
    company_name: str
    footer_description: str
    primary_color: Optional[str] = "#1E40AF"
    logo_url: Optional[str] = None

class NeighborhoodModel(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    title: str
    postcode: str
    frequency: str = Field(..., pattern="^(Weekly|Monthly)$")
    info: Optional[str] = None
    manager: ManagerInfo
    radius: float = Field(..., gt=0, le=50)
    branding: BrandingInfo
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "title": "Tower Hamlets Community",
                "postcode": "E1 6LF",
                "frequency": "Weekly",
                "info": "Family-friendly community newsletter",
                "manager": {
                    "email": "manager@example.com",
                    "whatsapp": "+447123456789"
                },
                "radius": 2.0,
                "branding": {
                    "company_name": "Community Housing",
                    "footer_description": "Building stronger communities together"
                }
            }
        }
