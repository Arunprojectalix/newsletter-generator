from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta
import json
import re

from app.database.mongodb import get_database
from app.models.newsletter import NewsletterModel, NewsletterContent
from app.services.ai_service import AIService
from app.services.enhanced_event_scraper import EnhancedEventScraper
from app.schemas.newsletter import NewsletterGenerateRequest, NewsletterResponse
from app.schemas.chat import (
    ChatMessage, 
    ChatResponse, 
    EventSearchRequest, 
    EventManagementRequest,
    ToolExecutionRequest,
    ToolListResponse,
    ChatRequest,
    AIReasoningChatRequest,
    AIReasoningChatResponse
)
from app.services.tools_service import ToolsService
from app.services.ai_chat_service import AIChatService

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
tools_service = ToolsService()
event_scraper = EnhancedEventScraper()

# Initialize AI Chat Service only when needed
ai_chat_service = None

def get_ai_chat_service():
    """Get AI chat service, initializing only when needed"""
    global ai_chat_service
    if ai_chat_service is None:
        try:
            ai_chat_service = AIChatService()
        except ValueError as e:
            logger.error(f"Failed to initialize AI Chat Service: {e}")
            raise e  # Re-raise to be handled by the endpoint
    return ai_chat_service

class ChatService:
    def __init__(self):
        self.ai_service = AIService()
        self.tools_service = tools_service
        self.event_scraper = event_scraper
    
    async def process_message(self, newsletter_id: str, message: str) -> ChatResponse:
        """Process a chat message and determine the appropriate response."""
        try:
            logger.info(f"Processing chat message for newsletter {newsletter_id}: {message}")
            
            # Analyze the message intent
            intent = self._analyze_intent(message)
            
            # Route to appropriate handler
            if intent["type"] == "web_search":
                return await self._handle_web_search(newsletter_id, message, intent)
            elif intent["type"] == "event_search":
                return await self._handle_event_search(newsletter_id, message, intent)
            elif intent["type"] == "event_management":
                return await self._handle_event_management(newsletter_id, message, intent)
            elif intent["type"] == "newsletter_customization":
                return await self._handle_newsletter_customization(newsletter_id, message, intent)
            elif intent["type"] == "content_generation":
                return await self._handle_content_generation(newsletter_id, message, intent)
            elif intent["type"] == "tool_execution":
                return await self._handle_tool_execution(newsletter_id, message, intent)
            elif intent["type"] == "help":
                return await self._handle_help_request(newsletter_id, message)
            else:
                return await self._handle_general_query(newsletter_id, message)
                
        except Exception as e:
            logger.error(f"Error processing chat message: {e}")
            return ChatResponse(
                message="I encountered an error processing your request. Please try again.",
                actions=[],
                data={"error": str(e)}
            )
    
    def _analyze_intent(self, message: str) -> Dict[str, Any]:
        """Analyze the user's message to determine intent."""
        message_lower = message.lower()
        
        # Web search patterns
        web_search_patterns = [
            r"search (?:for |the web for )?(.+)",
            r"find (?:information about |me )?(.+)",
            r"look up (.+)",
            r"what (?:is|are) (.+)",
            r"tell me about (.+)"
        ]
        
        # Event search patterns
        event_patterns = [
            r"find (?:me )?(?:some )?events? (?:in |near |around )?(.+)",
            r"search (?:for )?events? (?:in |near |around )?(.+)",
            r"what events? (?:are )?(?:happening |on )?(?:in |near |around )?(.+)",
            r"(?:any )?events? (?:in |near |around )?(.+)",
            r"show me events? (?:in |near |around )?(.+)"
        ]
        
        # Event management patterns
        event_management_patterns = [
            r"add (?:these |the )?events? to (?:the )?newsletter",
            r"refresh (?:the )?events?",
            r"update (?:the )?events?",
            r"organize (?:the )?events? by (.+)",
            r"remove (?:this |that )?event"
        ]
        
        # Newsletter customization patterns
        customization_patterns = [
            r"customize (?:the )?newsletter",
            r"change (?:the )?(?:layout|style|design)",
            r"modify (?:the )?newsletter",
            r"update (?:the )?(?:template|format)"
        ]
        
        # Content generation patterns
        content_patterns = [
            r"generate (?:some )?(?:content|text|article) (?:about |for )?(.+)",
            r"write (?:me )?(?:an? )?(?:article|content|text) (?:about |for )?(.+)",
            r"create (?:some )?content (?:about |for )?(.+)"
        ]
        
        # Tool execution patterns
        tool_patterns = [
            r"use (?:the )?(.+) tool",
            r"execute (?:the )?(.+) tool",
            r"run (?:the )?(.+) tool"
        ]
        
        # Help patterns
        help_patterns = [
            r"help",
            r"what can you do",
            r"available (?:tools|commands|options)",
            r"how (?:do i|can i|to)"
        ]
        
        # Check patterns in order of specificity
        for pattern in web_search_patterns:
            match = re.search(pattern, message_lower)
            if match:
                return {
                    "type": "web_search",
                    "query": match.group(1).strip(),
                    "confidence": 0.9
                }
        
        for pattern in event_patterns:
            match = re.search(pattern, message_lower)
            if match:
                return {
                    "type": "event_search",
                    "location": match.group(1).strip(),
                    "confidence": 0.9
                }
        
        for pattern in event_management_patterns:
            match = re.search(pattern, message_lower)
            if match:
                return {
                    "type": "event_management",
                    "action": match.group(0).strip(),
                    "confidence": 0.8
                }
        
        for pattern in customization_patterns:
            match = re.search(pattern, message_lower)
            if match:
                return {
                    "type": "newsletter_customization",
                    "action": match.group(0).strip(),
                    "confidence": 0.8
                }
        
        for pattern in content_patterns:
            match = re.search(pattern, message_lower)
            if match:
                return {
                    "type": "content_generation",
                    "topic": match.group(1).strip(),
                    "confidence": 0.8
                }
        
        for pattern in tool_patterns:
            match = re.search(pattern, message_lower)
            if match:
                return {
                    "type": "tool_execution",
                    "tool": match.group(1).strip(),
                    "confidence": 0.7
                }
        
        for pattern in help_patterns:
            if re.search(pattern, message_lower):
                return {
                    "type": "help",
                    "confidence": 0.9
                }
        
        return {
            "type": "general",
            "confidence": 0.5
        }
    
    async def _handle_web_search(self, newsletter_id: str, message: str, intent: Dict[str, Any]) -> ChatResponse:
        """Handle web search requests."""
        try:
            query = intent.get("query", message)
            
            # Execute web search tool
            result = await self.tools_service.execute_tool("web_search", {
                "query": query,
                "max_results": 5
            })
            
            if result["success"]:
                search_results = result["result"]["results"]
                
                response_message = f"I found {len(search_results)} results for '{query}':"
                
                actions = []
                for i, result_item in enumerate(search_results[:3]):
                    actions.append({
                        "type": "link",
                        "label": result_item["title"],
                        "url": result_item["url"],
                        "description": result_item["description"]
                    })
                
                return ChatResponse(
                    message=response_message,
                    actions=actions,
                    data={"search_results": search_results, "query": query}
                )
            else:
                return ChatResponse(
                    message=f"I couldn't search for '{query}' right now. Please try again later.",
                    actions=[],
                    data={"error": result.get("error")}
                )
                
        except Exception as e:
            logger.error(f"Error handling web search: {e}")
            return ChatResponse(
                message="I encountered an error while searching. Please try again.",
                actions=[],
                data={"error": str(e)}
            )
    
    async def _handle_event_search(self, newsletter_id: str, message: str, intent: Dict[str, Any]) -> ChatResponse:
        """Handle event search requests."""
        try:
            location = intent.get("location", "")
            
            # Try to extract postcode from location
            postcode_match = re.search(r'([A-Z]{1,2}[0-9][A-Z0-9]?\s?[0-9][A-Z]{2})', location.upper())
            if postcode_match:
                postcode = postcode_match.group(1)
            else:
                # Default postcode for demo
                postcode = "TS13NE"
            
            # Execute event search tool
            result = await self.tools_service.execute_tool("event_search", {
                "postcode": postcode,
                "radius": 10,
                "frequency": "weekly"
            })
            
            if result["success"]:
                events = result["result"]["events"]
                
                response_message = f"I found {len(events)} upcoming events near {postcode}:"
                
                actions = []
                for event in events[:3]:
                    actions.append({
                        "type": "event",
                        "label": f"View {event['event_title']}",
                        "url": event["source_url"],
                        "description": f"{event['location']} - {event['cost']}"
                    })
                
                actions.append({
                    "type": "action",
                    "label": "Add Events to Newsletter",
                    "action": "add_events",
                    "data": {"events": events}
                })
                
                return ChatResponse(
                    message=response_message,
                    actions=actions,
                    data={"events": events, "postcode": postcode}
                )
            else:
                return ChatResponse(
                    message=f"I couldn't find events near {location}. Please try a different location or postcode.",
                    actions=[],
                    data={"error": result.get("error")}
                )
                
        except Exception as e:
            logger.error(f"Error handling event search: {e}")
            return ChatResponse(
                message="I encountered an error while searching for events. Please try again.",
                actions=[],
                data={"error": str(e)}
            )
    
    async def _handle_event_management(self, newsletter_id: str, message: str, intent: Dict[str, Any]) -> ChatResponse:
        """Handle event management requests."""
        try:
            action = intent.get("action", "")
            
            if "add" in action:
                return ChatResponse(
                    message="I can help you add events to your newsletter. Please search for events first, then I'll show you options to add them.",
                    actions=[
                        {
                            "type": "action",
                            "label": "Search for Events",
                            "action": "search_events",
                            "description": "Find local events to add"
                        }
                    ],
                    data={"action": "add_events"}
                )
            elif "refresh" in action:
                return ChatResponse(
                    message="I'll refresh the events in your newsletter with the latest information.",
                    actions=[
                        {
                            "type": "action",
                            "label": "Refresh Events",
                            "action": "refresh_events",
                            "description": "Update with latest event information"
                        }
                    ],
                    data={"action": "refresh_events"}
                )
            elif "organize" in action:
                return ChatResponse(
                    message="I can organize your events by different criteria.",
                    actions=[
                        {
                            "type": "action",
                            "label": "Organize by Date",
                            "action": "organize_by_date",
                            "description": "Sort events chronologically"
                        },
                        {
                            "type": "action",
                            "label": "Organize by Type",
                            "action": "organize_by_type",
                            "description": "Group events by category"
                        }
                    ],
                    data={"action": "organize_events"}
                )
            else:
                return ChatResponse(
                    message="I can help you manage events in your newsletter. What would you like to do?",
                    actions=[
                        {
                            "type": "action",
                            "label": "Add Events",
                            "action": "add_events",
                            "description": "Add new events to newsletter"
                        },
                        {
                            "type": "action",
                            "label": "Refresh Events",
                            "action": "refresh_events",
                            "description": "Update existing events"
                        },
                        {
                            "type": "action",
                            "label": "Organize Events",
                            "action": "organize_events",
                            "description": "Reorganize event layout"
                        }
                    ],
                    data={"action": "event_management"}
                )
                
        except Exception as e:
            logger.error(f"Error handling event management: {e}")
            return ChatResponse(
                message="I encountered an error while managing events. Please try again.",
                actions=[],
                data={"error": str(e)}
            )
    
    async def _handle_newsletter_customization(self, newsletter_id: str, message: str, intent: Dict[str, Any]) -> ChatResponse:
        """Handle newsletter customization requests."""
        try:
            return ChatResponse(
                message="I can help you customize your newsletter in several ways:",
                actions=[
                    {
                        "type": "action",
                        "label": "Change Layout",
                        "action": "customize_layout",
                        "description": "Modify newsletter structure and organization"
                    },
                    {
                        "type": "action",
                        "label": "Update Styling",
                        "action": "customize_styling",
                        "description": "Change colors, fonts, and visual design"
                    },
                    {
                        "type": "action",
                        "label": "Modify Content",
                        "action": "customize_content",
                        "description": "Edit sections and content areas"
                    },
                    {
                        "type": "action",
                        "label": "Schedule Settings",
                        "action": "customize_schedule",
                        "description": "Change delivery timing and frequency"
                    }
                ],
                data={"newsletter_id": newsletter_id, "action": "customization"}
            )
            
        except Exception as e:
            logger.error(f"Error handling newsletter customization: {e}")
            return ChatResponse(
                message="I encountered an error while accessing customization options. Please try again.",
                actions=[],
                data={"error": str(e)}
            )
    
    async def _handle_content_generation(self, newsletter_id: str, message: str, intent: Dict[str, Any]) -> ChatResponse:
        """Handle content generation requests."""
        try:
            topic = intent.get("topic", "general newsletter content")
            
            # Execute content generation tool
            result = await self.tools_service.execute_tool("content_generation", {
                "content_type": "article",
                "topic": topic,
                "style": "professional",
                "length": "medium"
            })
            
            if result["success"]:
                generated_content = result["result"]["generated_content"]
                
                return ChatResponse(
                    message=f"I've generated content about '{topic}' for your newsletter:",
                    actions=[
                        {
                            "type": "action",
                            "label": "Add to Newsletter",
                            "action": "add_content",
                            "data": {"content": generated_content}
                        },
                        {
                            "type": "action",
                            "label": "Generate Different Style",
                            "action": "regenerate_content",
                            "data": {"topic": topic}
                        }
                    ],
                    data={"generated_content": generated_content, "topic": topic}
                )
            else:
                return ChatResponse(
                    message=f"I couldn't generate content about '{topic}' right now. Please try again later.",
                    actions=[],
                    data={"error": result.get("error")}
                )
                
        except Exception as e:
            logger.error(f"Error handling content generation: {e}")
            return ChatResponse(
                message="I encountered an error while generating content. Please try again.",
                actions=[],
                data={"error": str(e)}
            )
    
    async def _handle_tool_execution(self, newsletter_id: str, message: str, intent: Dict[str, Any]) -> ChatResponse:
        """Handle direct tool execution requests."""
        try:
            tool_name = intent.get("tool", "")
            
            # Get available tools
            available_tools = await self.tools_service.get_available_tools()
            
            # Find matching tool
            matching_tool = None
            for tool in available_tools:
                if tool_name in tool["name"].lower() or tool_name in tool["tool_id"]:
                    matching_tool = tool
                    break
            
            if matching_tool:
                return ChatResponse(
                    message=f"I found the {matching_tool['name']} tool. Here's what it can do:",
                    actions=[
                        {
                            "type": "action",
                            "label": f"Use {matching_tool['name']}",
                            "action": "execute_tool",
                            "data": {"tool_id": matching_tool["tool_id"]}
                        }
                    ],
                    data={"tool": matching_tool}
                )
            else:
                return ChatResponse(
                    message=f"I couldn't find a tool called '{tool_name}'. Here are the available tools:",
                    actions=[
                        {
                            "type": "action",
                            "label": tool["name"],
                            "action": "execute_tool",
                            "data": {"tool_id": tool["tool_id"]},
                            "description": tool["description"]
                        }
                        for tool in available_tools[:5]
                    ],
                    data={"available_tools": available_tools}
                )
                
        except Exception as e:
            logger.error(f"Error handling tool execution: {e}")
            return ChatResponse(
                message="I encountered an error while accessing tools. Please try again.",
                actions=[],
                data={"error": str(e)}
            )
    
    async def _handle_help_request(self, newsletter_id: str, message: str) -> ChatResponse:
        """Handle help and capability requests."""
        try:
            available_tools = await self.tools_service.get_available_tools()
            
            return ChatResponse(
                message="I'm your newsletter assistant! Here's what I can help you with:",
                actions=[
                    {
                        "type": "info",
                        "label": "🔍 Web Search",
                        "description": "Search the web for current information and news"
                    },
                    {
                        "type": "info",
                        "label": "📅 Event Search",
                        "description": "Find local events, meetups, and activities"
                    },
                    {
                        "type": "info",
                        "label": "🏢 Local Business Search",
                        "description": "Find restaurants, services, and businesses"
                    },
                    {
                        "type": "info",
                        "label": "⚡ Real-time Information",
                        "description": "Get weather, traffic, and transport updates"
                    },
                    {
                        "type": "info",
                        "label": "🎨 Newsletter Customization",
                        "description": "Customize layout, styling, and content"
                    },
                    {
                        "type": "info",
                        "label": "✍️ Content Generation",
                        "description": "Generate articles and content using AI"
                    },
                    {
                        "type": "info",
                        "label": "🖼️ Image Search",
                        "description": "Find relevant images for your newsletter"
                    },
                    {
                        "type": "info",
                        "label": "📋 Schedule Management",
                        "description": "Manage newsletter scheduling and automation"
                    }
                ],
                data={"available_tools": available_tools}
            )
            
        except Exception as e:
            logger.error(f"Error handling help request: {e}")
            return ChatResponse(
                message="I'm here to help with your newsletter! Try asking me to search for events, customize your newsletter, or generate content.",
                actions=[],
                data={"error": str(e)}
            )
    
    async def _handle_general_query(self, newsletter_id: str, message: str) -> ChatResponse:
        """Handle general queries that don't match specific patterns."""
        try:
            return ChatResponse(
                message="I'm not sure exactly what you're looking for, but I can help you with several things:",
                actions=[
                    {
                        "type": "action",
                        "label": "Search the Web",
                        "action": "web_search",
                        "description": "Find current information online"
                    },
                    {
                        "type": "action",
                        "label": "Find Events",
                        "action": "event_search",
                        "description": "Search for local events and activities"
                    },
                    {
                        "type": "action",
                        "label": "Customize Newsletter",
                        "action": "newsletter_customization",
                        "description": "Modify your newsletter design and content"
                    },
                    {
                        "type": "action",
                        "label": "Generate Content",
                        "action": "content_generation",
                        "description": "Create articles and content with AI"
                    },
                    {
                        "type": "action",
                        "label": "Show All Tools",
                        "action": "show_tools",
                        "description": "See all available tools and capabilities"
                    }
                ],
                data={"message": message, "intent": "general"}
            )
            
        except Exception as e:
            logger.error(f"Error handling general query: {e}")
            return ChatResponse(
                message="I'm here to help! Try asking me to search for something, find events, or customize your newsletter.",
                actions=[],
                data={"error": str(e)}
            )

# Initialize chat service
chat_service = ChatService()

# IMPORTANT: Specific routes must come BEFORE parameterized routes
# Otherwise /{newsletter_id} will catch everything

@router.post("/ai-chat", response_model=AIReasoningChatResponse)
async def ai_chat_with_reasoning(request: AIReasoningChatRequest):
    """
    AI Chat with GPT Function Calling and Reasoning
    This is exactly what you requested - AI that can reason and use tools.
    """
    try:
        logger.info(f"AI Chat request received: {request.message}")
        
        # Use the AI chat service with reasoning
        ai_service = get_ai_chat_service()
        logger.info("AI Chat service initialized successfully")
        
        result = await ai_service.chat_with_reasoning(
            user_message=request.message,
            newsletter_id=request.newsletter_id,
            conversation_history=request.conversation_history
        )
        
        logger.info(f"AI Chat result: {result}")
        
        return AIReasoningChatResponse(
            message=result["message"],
            function_calls=result["function_calls"],
            reasoning=result["reasoning"],
            conversation_history=result["conversation_history"],
            newsletter_id=request.newsletter_id
        )
        
    except ValueError as e:
        # Handle missing OpenAI API key
        logger.error(f"Configuration error in AI chat: {e}")
        return AIReasoningChatResponse(
            message=f"AI Chat requires OpenAI API key. Error: {str(e)}",
            function_calls=[],
            reasoning="Configuration error",
            conversation_history=[],
            newsletter_id=request.newsletter_id
        )
    except Exception as e:
        logger.error(f"Error in AI chat: {e}")
        return AIReasoningChatResponse(
            message=f"AI chat error: {str(e)}",
            function_calls=[],
            reasoning="Error occurred",
            conversation_history=[],
            newsletter_id=request.newsletter_id
        )

@router.post("/chat", response_model=ChatResponse)
async def basic_chat(request: ChatRequest):
    """
    Basic chat endpoint (legacy support)
    For full AI capabilities, use /ai-chat endpoint
    """
    try:
        logger.info(f"Basic chat request: {request.message}")
        
        # Convert to AI chat request
        ai_request = AIReasoningChatRequest(
            message=request.message,
            newsletter_id=request.newsletter_id or "default",
            conversation_history=[]
        )
        
        # Use AI chat service
        result = await get_ai_chat_service().chat_with_reasoning(
            user_message=ai_request.message,
            newsletter_id=ai_request.newsletter_id,
            conversation_history=ai_request.conversation_history
        )
        
        # Convert back to basic response format
        return ChatResponse(
            message=result["message"],
            actions=[],
            data={"function_calls": result["function_calls"]},
            newsletter_id=request.newsletter_id
        )
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise HTTPException(
            status_code=400, 
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in basic chat: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Chat error: {str(e)}"
        )

@router.get("/tools/available", response_model=ToolListResponse)
async def get_available_tools():
    """Get list of all available tools for the chat interface."""
    try:
        tools = await tools_service.get_available_tools()
        return ToolListResponse(tools=tools)
    except Exception as e:
        logger.error(f"Error getting available tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tools/execute", response_model=Dict[str, Any])
async def execute_tool(request: ToolExecutionRequest):
    """Execute a specific tool with given parameters."""
    try:
        result = await tools_service.execute_tool(request.tool_id, request.parameters)
        return result
    except Exception as e:
        logger.error(f"Error executing tool: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/events/search")
async def search_events(request: EventSearchRequest):
    """Search for events using the enhanced event scraper."""
    try:
        events = await event_scraper.search_events(
            request.postcode, 
            request.radius, 
            request.frequency
        )
        return {
            "success": True,
            "events": events,
            "count": len(events)
        }
    except Exception as e:
        logger.error(f"Error searching events: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/events/manage/{newsletter_id}")
async def manage_events(newsletter_id: str, request: EventManagementRequest):
    """Manage events for a newsletter (add, refresh, organize)."""
    try:
        # This would integrate with your newsletter service
        # For now, return a success response
        return {
            "success": True,
            "message": f"Events {request.action} for newsletter {newsletter_id}",
            "newsletter_id": newsletter_id,
            "action": request.action,
            "data": request.data
        }
    except Exception as e:
        logger.error(f"Error managing events: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Parameterized routes MUST come last
@router.post("/{newsletter_id}", response_model=ChatResponse)
async def chat_with_assistant(
    newsletter_id: str,
    message: ChatMessage
):
    """
    Chat with the newsletter assistant.
    Supports various commands for customization and content management.
    """
    try:
        response = await chat_service.process_message(newsletter_id, message.message)
        return response
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 