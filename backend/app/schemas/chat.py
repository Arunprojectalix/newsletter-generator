from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class ChatMessage(BaseModel):
    message: str
    conversation_history: Optional[List[Dict[str, str]]] = None

class ChatRequest(BaseModel):
    """Basic chat request schema"""
    message: str
    newsletter_id: Optional[str] = None

class ChatAction(BaseModel):
    type: str
    label: str
    action: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    message: str
    actions: List[ChatAction] = []
    data: Optional[Dict[str, Any]] = None
    newsletter_id: Optional[str] = None

class EventSearchRequest(BaseModel):
    postcode: str
    radius: float = 10.0
    frequency: str = "weekly"

class EventManagementRequest(BaseModel):
    action: str  # add, refresh, organize, remove
    data: Optional[Dict[str, Any]] = None

class ToolExecutionRequest(BaseModel):
    tool_id: str
    parameters: Dict[str, Any]

class ToolInfo(BaseModel):
    tool_id: str
    name: str
    description: str
    parameters: Dict[str, Any]

class ToolListResponse(BaseModel):
    tools: List[ToolInfo]

class WebSearchRequest(BaseModel):
    query: str
    location: Optional[Dict[str, str]] = None
    max_results: int = 5

class WebSearchResult(BaseModel):
    url: str
    title: str
    description: str
    source: str

class WebSearchResponse(BaseModel):
    query: str
    results: List[WebSearchResult]
    results_count: int

class ContentGenerationRequest(BaseModel):
    content_type: str
    topic: str
    style: str = "professional"
    length: str = "medium"

class ContentGenerationResponse(BaseModel):
    content_type: str
    topic: str
    style: str
    length: str
    generated_content: str

class ImageSearchRequest(BaseModel):
    query: str
    style: str = "professional"
    size: str = "large"

class ImageResult(BaseModel):
    url: str
    title: str
    description: str
    size: str
    style: str

class ImageSearchResponse(BaseModel):
    query: str
    images: List[ImageResult]
    images_count: int

class NewsletterCustomizationRequest(BaseModel):
    newsletter_id: str
    customization_type: str  # layout, styling, content, schedule
    parameters: Dict[str, Any]

class ScheduleManagementRequest(BaseModel):
    newsletter_id: str
    action: str  # schedule, reschedule, cancel
    schedule_data: Optional[Dict[str, Any]] = None

class LocalBusinessSearchRequest(BaseModel):
    query: str
    location: str
    business_type: str = "any"

class RealTimeInfoRequest(BaseModel):
    query: str
    info_type: str = "general"  # weather, traffic, transport, general

class ToolExecutionResult(BaseModel):
    success: bool
    tool_id: str
    tool_name: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str

class AIReasoningChatRequest(BaseModel):
    """Request for AI chat with reasoning and function calling"""
    message: str
    newsletter_id: str
    conversation_history: Optional[List[Dict[str, Any]]] = []

class AIReasoningChatResponse(BaseModel):
    """Response from AI chat with reasoning and function calling"""
    message: str
    function_calls: List[Dict[str, Any]]
    reasoning: str
    conversation_history: List[Dict[str, Any]]
    newsletter_id: str 