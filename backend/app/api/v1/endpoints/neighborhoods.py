from fastapi import APIRouter, HTTPException, Depends
from typing import List
from bson import ObjectId

from app.database.mongodb import get_database
from app.schemas.neighborhood import NeighborhoodCreate, NeighborhoodResponse
from app.models.neighborhood import NeighborhoodModel

router = APIRouter()

@router.post("/", response_model=NeighborhoodResponse)
@router.post("", response_model=NeighborhoodResponse)
async def create_neighborhood(neighborhood: NeighborhoodCreate):
    """Create a new neighborhood."""
    db = get_database()
    
    # Convert to model
    neighborhood_model = NeighborhoodModel(**neighborhood.dict())
    
    # Insert into database
    result = await db.neighborhoods.insert_one(
        neighborhood_model.dict(by_alias=True, exclude={"id"})
    )
    
    # Retrieve created neighborhood
    created = await db.neighborhoods.find_one({"_id": result.inserted_id})
    created["_id"] = str(created["_id"])  # Convert ObjectId to string
    return NeighborhoodResponse(**created)

@router.get("/", response_model=List[NeighborhoodResponse])
@router.get("", response_model=List[NeighborhoodResponse])
async def get_neighborhoods(skip: int = 0, limit: int = 10):
    """Get all neighborhoods."""
    db = get_database()
    
    neighborhoods = []
    cursor = db.neighborhoods.find({"is_active": True}).skip(skip).limit(limit)
    
    async for neighborhood in cursor:
        neighborhood["_id"] = str(neighborhood["_id"])  # Convert ObjectId to string
        neighborhoods.append(NeighborhoodResponse(**neighborhood))
    
    return neighborhoods

@router.get("/{neighborhood_id}", response_model=NeighborhoodResponse)
@router.get("/{neighborhood_id}/", response_model=NeighborhoodResponse)
async def get_neighborhood(neighborhood_id: str):
    """Get a specific neighborhood."""
    db = get_database()
    
    if not ObjectId.is_valid(neighborhood_id):
        raise HTTPException(status_code=400, detail="Invalid neighborhood ID")
    
    neighborhood = await db.neighborhoods.find_one({"_id": ObjectId(neighborhood_id)})
    
    if not neighborhood:
        raise HTTPException(status_code=404, detail="Neighborhood not found")
    
    neighborhood["_id"] = str(neighborhood["_id"])  # Convert ObjectId to string
    return NeighborhoodResponse(**neighborhood)

@router.delete("/{neighborhood_id}")
@router.delete("/{neighborhood_id}/")
async def delete_neighborhood(neighborhood_id: str):
    """Soft delete a neighborhood."""
    db = get_database()
    
    if not ObjectId.is_valid(neighborhood_id):
        raise HTTPException(status_code=400, detail="Invalid neighborhood ID")
    
    result = await db.neighborhoods.update_one(
        {"_id": ObjectId(neighborhood_id)},
        {"$set": {"is_active": False}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Neighborhood not found")
    
    return {"message": "Neighborhood deleted successfully"}
