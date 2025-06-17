import asyncio
from typing import List, Dict, Any, Optional, Union
import logging
from datetime import datetime, timedelta
import json

from .web_search_service import WebSearchService
from .enhanced_event_scraper import EnhancedEventScraper
from .ai_service import AIService

logger = logging.getLogger(__name__)

class ToolsService:
    def __init__(self):
        self.web_search = WebSearchService()
        self.event_scraper = EnhancedEventScraper()
        self.ai_service = AIService()
        
        # Define available tools
        self.available_tools = {
            "web_search": {
                "name": "Web Search",
                "description": "Search the web for current information, news, and real-time data",
                "parameters": {
                    "query": {"type": "string", "required": True, "description": "Search query"},
                    "location": {"type": "object", "required": False, "description": "Location context"},
                    "max_results": {"type": "integer", "required": False, "default": 5}
                },
                "function": self.tool_web_search
            },
            "event_search": {
                "name": "Event Search",
                "description": "Find local events, meetups, and activities",
                "parameters": {
                    "postcode": {"type": "string", "required": True, "description": "UK postcode"},
                    "radius": {"type": "number", "required": False, "default": 10, "description": "Search radius in miles"},
                    "frequency": {"type": "string", "required": False, "default": "weekly", "description": "weekly or monthly"},
                    "event_type": {"type": "string", "required": False, "description": "Type of events to search for"}
                },
                "function": self.tool_event_search
            },
            "local_business_search": {
                "name": "Local Business Search",
                "description": "Find local businesses, restaurants, and services",
                "parameters": {
                    "query": {"type": "string", "required": True, "description": "Business search query"},
                    "location": {"type": "string", "required": True, "description": "Location to search in"},
                    "business_type": {"type": "string", "required": False, "default": "any", "description": "Type of business"}
                },
                "function": self.tool_local_business_search
            },
            "real_time_info": {
                "name": "Real-time Information",
                "description": "Get current weather, traffic, transport, and other real-time data",
                "parameters": {
                    "query": {"type": "string", "required": True, "description": "Information query"},
                    "info_type": {"type": "string", "required": False, "default": "general", "description": "weather, traffic, transport, or general"}
                },
                "function": self.tool_real_time_info
            },
            "newsletter_customization": {
                "name": "Newsletter Customization",
                "description": "Customize newsletter content, layout, and styling",
                "parameters": {
                    "newsletter_id": {"type": "string", "required": True, "description": "Newsletter ID"},
                    "customization_type": {"type": "string", "required": True, "description": "Type of customization"},
                    "parameters": {"type": "object", "required": True, "description": "Customization parameters"}
                },
                "function": self.tool_newsletter_customization
            },
            "content_generation": {
                "name": "Content Generation",
                "description": "Generate custom content for newsletters using AI",
                "parameters": {
                    "content_type": {"type": "string", "required": True, "description": "Type of content to generate"},
                    "topic": {"type": "string", "required": True, "description": "Content topic"},
                    "style": {"type": "string", "required": False, "default": "professional", "description": "Writing style"},
                    "length": {"type": "string", "required": False, "default": "medium", "description": "Content length"}
                },
                "function": self.tool_content_generation
            },
            "image_search": {
                "name": "Image Search",
                "description": "Find relevant images for newsletter content",
                "parameters": {
                    "query": {"type": "string", "required": True, "description": "Image search query"},
                    "style": {"type": "string", "required": False, "default": "professional", "description": "Image style"},
                    "size": {"type": "string", "required": False, "default": "large", "description": "Image size"}
                },
                "function": self.tool_image_search
            },
            "schedule_management": {
                "name": "Schedule Management",
                "description": "Manage newsletter scheduling and automation",
                "parameters": {
                    "newsletter_id": {"type": "string", "required": True, "description": "Newsletter ID"},
                    "action": {"type": "string", "required": True, "description": "schedule, reschedule, or cancel"},
                    "schedule_data": {"type": "object", "required": False, "description": "Schedule parameters"}
                },
                "function": self.tool_schedule_management
            }
        }
    
    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of all available tools."""
        return [
            {
                "tool_id": tool_id,
                "name": tool_data["name"],
                "description": tool_data["description"],
                "parameters": tool_data["parameters"]
            }
            for tool_id, tool_data in self.available_tools.items()
        ]
    
    async def execute_tool(self, tool_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific tool with given parameters."""
        try:
            if tool_id not in self.available_tools:
                return {
                    "success": False,
                    "error": f"Tool '{tool_id}' not found",
                    "available_tools": list(self.available_tools.keys())
                }
            
            tool = self.available_tools[tool_id]
            result = await tool["function"](**parameters)
            
            return {
                "success": True,
                "tool_id": tool_id,
                "tool_name": tool["name"],
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error executing tool {tool_id}: {e}")
            return {
                "success": False,
                "tool_id": tool_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def tool_web_search(self, query: str, location: Optional[Dict[str, str]] = None, max_results: int = 5) -> Dict[str, Any]:
        """Web search tool implementation."""
        try:
            results = await self.web_search.search_web(query, location, max_results)
            return {
                "query": query,
                "location": location,
                "results_count": len(results),
                "results": results
            }
        except Exception as e:
            logger.error(f"Web search tool error: {e}")
            return {"error": str(e), "results": []}
    
    async def tool_event_search(self, postcode: str, radius: float = 10, frequency: str = "weekly", event_type: Optional[str] = None) -> Dict[str, Any]:
        """Event search tool implementation."""
        try:
            events = await self.event_scraper.search_events(postcode, radius, frequency)
            
            # Filter by event type if specified
            if event_type:
                filtered_events = []
                for event in events:
                    if event_type.lower() in event.get('event_title', '').lower() or \
                       event_type.lower() in event.get('description', '').lower():
                        filtered_events.append(event)
                events = filtered_events
            
            return {
                "postcode": postcode,
                "radius": radius,
                "frequency": frequency,
                "event_type": event_type,
                "events_count": len(events),
                "events": events
            }
        except Exception as e:
            logger.error(f"Event search tool error: {e}")
            return {"error": str(e), "events": []}
    
    async def tool_local_business_search(self, query: str, location: str, business_type: str = "any") -> Dict[str, Any]:
        """Local business search tool implementation."""
        try:
            results = await self.web_search.search_local_businesses(query, location, business_type)
            return {
                "query": query,
                "location": location,
                "business_type": business_type,
                "results_count": len(results),
                "results": results
            }
        except Exception as e:
            logger.error(f"Local business search tool error: {e}")
            return {"error": str(e), "results": []}
    
    async def tool_real_time_info(self, query: str, info_type: str = "general") -> Dict[str, Any]:
        """Real-time information tool implementation."""
        try:
            results = await self.web_search.search_real_time_info(query, info_type)
            return {
                "query": query,
                "info_type": info_type,
                "results_count": len(results),
                "results": results
            }
        except Exception as e:
            logger.error(f"Real-time info tool error: {e}")
            return {"error": str(e), "results": []}
    
    async def tool_newsletter_customization(self, newsletter_id: str, customization_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Newsletter customization tool implementation."""
        try:
            # This would integrate with your newsletter service
            customizations = {
                "layout": self._customize_layout,
                "styling": self._customize_styling,
                "content": self._customize_content,
                "schedule": self._customize_schedule
            }
            
            if customization_type not in customizations:
                return {
                    "error": f"Customization type '{customization_type}' not supported",
                    "supported_types": list(customizations.keys())
                }
            
            result = await customizations[customization_type](newsletter_id, parameters)
            
            return {
                "newsletter_id": newsletter_id,
                "customization_type": customization_type,
                "parameters": parameters,
                "result": result
            }
        except Exception as e:
            logger.error(f"Newsletter customization tool error: {e}")
            return {"error": str(e)}
    
    async def tool_content_generation(self, content_type: str, topic: str, style: str = "professional", length: str = "medium") -> Dict[str, Any]:
        """Content generation tool implementation."""
        try:
            # Generate content using AI service
            prompt = f"Generate {length} {style} content about {topic} for a newsletter. Content type: {content_type}"
            
            content = await self.ai_service.generate_content(prompt)
            
            return {
                "content_type": content_type,
                "topic": topic,
                "style": style,
                "length": length,
                "generated_content": content
            }
        except Exception as e:
            logger.error(f"Content generation tool error: {e}")
            return {"error": str(e)}
    
    async def tool_image_search(self, query: str, style: str = "professional", size: str = "large") -> Dict[str, Any]:
        """Image search tool implementation."""
        try:
            # Use Unsplash API or similar for high-quality images
            images = []
            
            # Generate Unsplash URLs based on query
            base_url = "https://images.unsplash.com/photo"
            
            # Sample image IDs for different queries
            image_mappings = {
                "community": "1511632765486-a01980e01a18",
                "event": "1513475382585-d06e58bcb0e0",
                "meetup": "1551698618-1dfe5d97d256",
                "business": "1507003211169-0a1dd7228f2d",
                "food": "1495474472287-4d71bcdd2085",
                "technology": "1518709268805-4e9042af9f23"
            }
            
            # Find best matching image
            image_id = None
            for keyword, img_id in image_mappings.items():
                if keyword in query.lower():
                    image_id = img_id
                    break
            
            if not image_id:
                image_id = "1511632765486-a01980e01a18"  # Default
            
            size_params = {
                "small": "w=400&h=300",
                "medium": "w=800&h=600", 
                "large": "w=1200&h=900"
            }
            
            size_param = size_params.get(size, size_params["large"])
            
            images.append({
                "url": f"{base_url}-{image_id}?{size_param}&fit=crop&auto=format&q=90",
                "title": f"Image for {query}",
                "description": f"{style.title()} style image related to {query}",
                "size": size,
                "style": style
            })
            
            return {
                "query": query,
                "style": style,
                "size": size,
                "images_count": len(images),
                "images": images
            }
        except Exception as e:
            logger.error(f"Image search tool error: {e}")
            return {"error": str(e), "images": []}
    
    async def tool_schedule_management(self, newsletter_id: str, action: str, schedule_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Schedule management tool implementation."""
        try:
            # This would integrate with your scheduling service
            actions = {
                "schedule": self._schedule_newsletter,
                "reschedule": self._reschedule_newsletter,
                "cancel": self._cancel_newsletter_schedule
            }
            
            if action not in actions:
                return {
                    "error": f"Action '{action}' not supported",
                    "supported_actions": list(actions.keys())
                }
            
            result = await actions[action](newsletter_id, schedule_data)
            
            return {
                "newsletter_id": newsletter_id,
                "action": action,
                "schedule_data": schedule_data,
                "result": result
            }
        except Exception as e:
            logger.error(f"Schedule management tool error: {e}")
            return {"error": str(e)}
    
    # Helper methods for newsletter customization
    async def _customize_layout(self, newsletter_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Customize newsletter layout."""
        return {
            "message": f"Layout customization applied to newsletter {newsletter_id}",
            "changes": parameters
        }
    
    async def _customize_styling(self, newsletter_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Customize newsletter styling."""
        return {
            "message": f"Styling customization applied to newsletter {newsletter_id}",
            "changes": parameters
        }
    
    async def _customize_content(self, newsletter_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Customize newsletter content."""
        return {
            "message": f"Content customization applied to newsletter {newsletter_id}",
            "changes": parameters
        }
    
    async def _customize_schedule(self, newsletter_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Customize newsletter schedule."""
        return {
            "message": f"Schedule customization applied to newsletter {newsletter_id}",
            "changes": parameters
        }
    
    # Helper methods for schedule management
    async def _schedule_newsletter(self, newsletter_id: str, schedule_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Schedule a newsletter."""
        return {
            "message": f"Newsletter {newsletter_id} scheduled successfully",
            "schedule": schedule_data
        }
    
    async def _reschedule_newsletter(self, newsletter_id: str, schedule_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Reschedule a newsletter."""
        return {
            "message": f"Newsletter {newsletter_id} rescheduled successfully",
            "new_schedule": schedule_data
        }
    
    async def _cancel_newsletter_schedule(self, newsletter_id: str, schedule_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Cancel newsletter schedule."""
        return {
            "message": f"Newsletter {newsletter_id} schedule cancelled successfully"
        } 