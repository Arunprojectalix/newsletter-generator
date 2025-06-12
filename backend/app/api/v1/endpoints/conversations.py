from fastapi import APIRouter, HTTPException
from typing import List
from bson import ObjectId
from datetime import datetime

from app.database.mongodb import get_database
from app.schemas.conversation import (
    ConversationCreate, 
    ConversationResponse, 
    MessageCreate,
    MessageResponse
)
from app.models.conversation import ConversationModel, Message

router = APIRouter()

@router.post("/", response_model=ConversationResponse)
@router.post("", response_model=ConversationResponse)
async def create_conversation(conversation: ConversationCreate):
    """Create a new conversation."""
    db = await get_database()
    
    # Validate neighborhood exists
    if not ObjectId.is_valid(conversation.neighborhood_id):
        raise HTTPException(status_code=400, detail="Invalid neighborhood ID")
    
    neighborhood = await db.neighborhoods.find_one({"_id": ObjectId(conversation.neighborhood_id)})
    if not neighborhood:
        raise HTTPException(status_code=404, detail="Neighborhood not found")
    
    # Create conversation model
    conversation_model = ConversationModel(
        neighborhood_id=ObjectId(conversation.neighborhood_id),
        newsletter_id=ObjectId(conversation.newsletter_id) if conversation.newsletter_id else None,
        messages=[
            Message(
                role="system",
                content=f"You are helping to create a newsletter for {neighborhood['title']} community."
            )
        ]
    )
    
    # Insert conversation
    result = await db.conversations.insert_one(
        conversation_model.dict(by_alias=True, exclude={"id"})
    )
    
    # Retrieve created conversation
    created = await db.conversations.find_one({"_id": result.inserted_id})
    created["_id"] = str(created["_id"])  # Convert ObjectId to string
    created["neighborhood_id"] = str(created["neighborhood_id"])  # Convert ObjectId to string
    if created.get("newsletter_id"):
        created["newsletter_id"] = str(created["newsletter_id"])  # Convert ObjectId to string
    return ConversationResponse(**created)

@router.get("/{conversation_id}", response_model=ConversationResponse)
@router.get("/{conversation_id}/", response_model=ConversationResponse)
async def get_conversation(conversation_id: str):
    """Get a specific conversation."""
    db = await get_database()
    
    if not ObjectId.is_valid(conversation_id):
        raise HTTPException(status_code=400, detail="Invalid conversation ID")
    
    conversation = await db.conversations.find_one({"_id": ObjectId(conversation_id)})
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conversation["_id"] = str(conversation["_id"])  # Convert ObjectId to string
    conversation["neighborhood_id"] = str(conversation["neighborhood_id"])  # Convert ObjectId to string
    if conversation.get("newsletter_id"):
        conversation["newsletter_id"] = str(conversation["newsletter_id"])  # Convert ObjectId to string
    return ConversationResponse(**conversation)

@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def add_message(conversation_id: str, message: MessageCreate):
    """Add a message to conversation."""
    db = await get_database()
    
    if not ObjectId.is_valid(conversation_id):
        raise HTTPException(status_code=400, detail="Invalid conversation ID")
    
    # Check if conversation exists and is active
    conversation = await db.conversations.find_one({"_id": ObjectId(conversation_id)})
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if conversation.get("status") == "closed":
        raise HTTPException(status_code=400, detail="Conversation is closed")
    
    # Create message
    new_message = Message(
        role=message.role,
        content=message.content
    )
    
    # Add message to conversation
    await db.conversations.update_one(
        {"_id": ObjectId(conversation_id)},
        {
            "$push": {"messages": new_message.dict()},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    return MessageResponse(**new_message.dict())

@router.get("/neighborhood/{neighborhood_id}", response_model=List[ConversationResponse])
@router.get("/neighborhood/{neighborhood_id}/", response_model=List[ConversationResponse])
async def get_neighborhood_conversations(neighborhood_id: str):
    """Get all conversations for a neighborhood."""
    db = await get_database()
    
    if not ObjectId.is_valid(neighborhood_id):
        raise HTTPException(status_code=400, detail="Invalid neighborhood ID")
    
    conversations = []
    # Query for both string and ObjectId formats to handle legacy data
    cursor = db.conversations.find(
        {"$or": [
            {"neighborhood_id": ObjectId(neighborhood_id)},
            {"neighborhood_id": neighborhood_id}
        ]}
    ).sort("created_at", -1)
    
    async for conversation in cursor:
        conversation["_id"] = str(conversation["_id"])  # Convert ObjectId to string
        conversation["neighborhood_id"] = str(conversation["neighborhood_id"])  # Convert ObjectId to string
        if conversation.get("newsletter_id"):
            conversation["newsletter_id"] = str(conversation["newsletter_id"])  # Convert ObjectId to string
        conversations.append(ConversationResponse(**conversation))
    
    return conversations
