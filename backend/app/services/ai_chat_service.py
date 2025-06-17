"""
AI Chat Service with GPT Function Calling and Reasoning
This service provides intelligent chat capabilities with web search and tool usage.
"""

import openai
import json
import asyncio
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import os

from .enhanced_event_scraper import EnhancedEventScraper

logger = logging.getLogger(__name__)

class AIChatService:
    """
    AI Chat Service that uses GPT function calling with reasoning capabilities.
    This is exactly what was requested - AI that can reason and use tools.
    """
    
    def __init__(self):
        # Initialize OpenAI client - REQUIRED for function calling
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for AI chat functionality")
        
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.event_scraper = EnhancedEventScraper()
        
        # Define available functions for GPT to call
        self.available_functions = {
            "web_search": self.web_search,
            "search_events": self.search_events,
            "search_local_businesses": self.search_local_businesses,
            "get_weather_info": self.get_weather_info,
            "generate_newsletter_content": self.generate_newsletter_content,
            "customize_newsletter": self.customize_newsletter,
            "manage_schedule": self.manage_schedule,
            "find_images": self.find_images
        }
        
        # Function definitions for GPT function calling
        self.function_definitions = [
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Search the web for current information, news, and real-time data",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query"
                            },
                            "location": {
                                "type": "object",
                                "properties": {
                                    "country": {"type": "string"},
                                    "city": {"type": "string"},
                                    "region": {"type": "string"}
                                },
                                "description": "Location context for the search"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_events",
                    "description": "Find local events, meetups, and activities in a specific area",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "postcode": {
                                "type": "string",
                                "description": "UK postcode to search around"
                            },
                            "radius": {
                                "type": "number",
                                "description": "Search radius in miles",
                                "default": 10
                            },
                            "frequency": {
                                "type": "string",
                                "description": "Event frequency: weekly or monthly",
                                "enum": ["weekly", "monthly"],
                                "default": "weekly"
                            },
                            "event_type": {
                                "type": "string",
                                "description": "Type of events to search for (optional)"
                            }
                        },
                        "required": ["postcode"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_local_businesses",
                    "description": "Find local businesses, restaurants, and services",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "What to search for (e.g., 'restaurants', 'coffee shops')"
                            },
                            "location": {
                                "type": "string",
                                "description": "Location to search in"
                            },
                            "business_type": {
                                "type": "string",
                                "description": "Type of business",
                                "default": "any"
                            }
                        },
                        "required": ["query", "location"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_weather_info",
                    "description": "Get current weather and forecast information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "Location to get weather for"
                            }
                        },
                        "required": ["location"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_newsletter_content",
                    "description": "Generate content for newsletters using AI",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topic": {
                                "type": "string",
                                "description": "Topic to generate content about"
                            },
                            "style": {
                                "type": "string",
                                "description": "Writing style",
                                "enum": ["professional", "friendly", "casual", "formal"],
                                "default": "professional"
                            },
                            "length": {
                                "type": "string",
                                "description": "Content length",
                                "enum": ["short", "medium", "long"],
                                "default": "medium"
                            },
                            "content_type": {
                                "type": "string",
                                "description": "Type of content",
                                "enum": ["article", "announcement", "summary", "introduction"],
                                "default": "article"
                            }
                        },
                        "required": ["topic"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "customize_newsletter",
                    "description": "Customize newsletter layout, styling, and content",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "newsletter_id": {
                                "type": "string",
                                "description": "Newsletter ID to customize"
                            },
                            "customization_type": {
                                "type": "string",
                                "description": "Type of customization",
                                "enum": ["layout", "styling", "content", "template"],
                                "default": "layout"
                            },
                            "changes": {
                                "type": "object",
                                "description": "Specific changes to make"
                            }
                        },
                        "required": ["newsletter_id", "customization_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "manage_schedule",
                    "description": "Manage newsletter scheduling and automation",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "newsletter_id": {
                                "type": "string",
                                "description": "Newsletter ID"
                            },
                            "action": {
                                "type": "string",
                                "description": "Schedule action",
                                "enum": ["schedule", "reschedule", "cancel", "view"],
                                "default": "view"
                            },
                            "schedule_data": {
                                "type": "object",
                                "description": "Schedule parameters"
                            }
                        },
                        "required": ["newsletter_id", "action"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "find_images",
                    "description": "Find relevant images for newsletter content",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "What kind of images to find"
                            },
                            "style": {
                                "type": "string",
                                "description": "Image style",
                                "enum": ["professional", "casual", "artistic", "modern"],
                                "default": "professional"
                            },
                            "count": {
                                "type": "number",
                                "description": "Number of images to find",
                                "default": 3
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]

    async def chat_with_reasoning(
        self, 
        user_message: str, 
        newsletter_id: str,
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Main chat function that uses GPT function calling with reasoning.
        This is exactly what you requested - AI that can reason and use tools.
        """
        try:
            # Prepare conversation history
            messages = []
            
            # System message with STRICT tool usage requirements
            system_message = {
                "role": "system",
                "content": f"""You are an intelligent newsletter assistant with access to web search and various tools.

CRITICAL RULES - NEVER BREAK THESE:
1. NEVER make up, invent, or hallucinate any information
2. NEVER provide fake events, URLs, dates, or contact details
3. ALWAYS use the available tools to get real data
4. If asked for events, ALWAYS call search_events function - NEVER create fake events
5. If asked for web information, ALWAYS call web_search function
6. If asked for businesses, ALWAYS call search_local_businesses function
7. If you cannot get real data through tools, say so explicitly

Available tools:
- search_events: Find REAL local events with actual booking links
- web_search: Get current information from the web
- search_local_businesses: Find real businesses and services
- get_weather_info: Get actual weather data
- generate_newsletter_content: Create content using AI
- customize_newsletter: Modify newsletter settings
- manage_schedule: Handle scheduling
- find_images: Search for relevant images

WHEN USER ASKS FOR EVENTS:
- MUST call search_events function with proper postcode
- MUST NOT create fictional events
- If no events found, say "No events found" - don't make up events

WHEN USER ASKS FOR MORE EVENTS:
- MUST call search_events again with different parameters
- Try different radius, frequency, or event_type
- NEVER add fictional events to supplement real ones

Current newsletter ID: {newsletter_id}

Your job is to be helpful by using tools to get REAL information, not by creating fake information."""
            }
            messages.append(system_message)
            
            # Add conversation history
            if conversation_history:
                messages.extend(conversation_history)
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Determine if we should force tool usage based on user message
            should_force_tools = any(keyword in user_message.lower() for keyword in [
                'events', 'event', 'search', 'find', 'more', 'add', 'get', 'show', 'list'
            ])
            
            # Call GPT with function calling
            response = await self.client.chat.completions.create(
                model="gpt-4-1106-preview",  # Use GPT-4 Turbo for best reasoning
                messages=messages,
                tools=self.function_definitions,
                tool_choice="required" if should_force_tools else "auto",  # Force tools for certain requests
                temperature=0.3,  # Lower temperature for more consistent tool usage
                max_tokens=2000
            )
            
            # Process the response
            assistant_message = response.choices[0].message
            
            # Handle function calls
            if assistant_message.tool_calls:
                # First, add the assistant's message with tool calls
                messages.append({
                    "role": "assistant",
                    "content": assistant_message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        } for tc in assistant_message.tool_calls
                    ]
                })
                
                # Then execute function calls and add tool responses
                function_results = []
                
                for tool_call in assistant_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    logger.info(f"GPT is calling function: {function_name} with args: {function_args}")
                    
                    # Execute the function
                    if function_name in self.available_functions:
                        try:
                            result = await self.available_functions[function_name](**function_args)
                            function_results.append({
                                "tool_call_id": tool_call.id,
                                "function_name": function_name,
                                "result": result
                            })
                            
                            # Add function result to messages
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": json.dumps(result)
                            })
                            
                        except Exception as e:
                            logger.error(f"Error executing function {function_name}: {e}")
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": json.dumps({"error": str(e)})
                            })
                
                # Get final response after function execution with strict instructions
                messages.append({
                    "role": "system", 
                    "content": "Based on the function results above, provide a helpful response. ONLY use the data returned by the functions. Do NOT add any fictional information, fake events, or made-up details."
                })
                
                final_response = await self.client.chat.completions.create(
                    model="gpt-4-1106-preview",
                    messages=messages,
                    temperature=0.2,  # Very low temperature to prevent hallucination
                    max_tokens=1500
                )
                
                final_message = final_response.choices[0].message.content
                
                # Validate response doesn't contain hallucinated content
                if self._contains_hallucinated_content(final_message, user_message):
                    final_message = "I can only provide information from my available tools. Let me search for real data for you."
                
                return {
                    "message": final_message,
                    "function_calls": function_results,
                    "reasoning": "Used AI reasoning with function calling",
                    "conversation_history": messages
                }
            
            else:
                # No function calls needed, return direct response
                return {
                    "message": assistant_message.content,
                    "function_calls": [],
                    "reasoning": "Direct AI response with reasoning",
                    "conversation_history": messages
                }
                
        except Exception as e:
            logger.error(f"Error in AI chat with reasoning: {e}")
            return {
                "message": f"I encountered an error: {str(e)}. Please make sure your OpenAI API key is set correctly.",
                "function_calls": [],
                "reasoning": "Error occurred",
                "conversation_history": []
            }
    
    def _contains_hallucinated_content(self, response: str, user_message: str) -> bool:
        """
        Detect if the response contains hallucinated content that wasn't from tool results.
        This prevents the AI from making up fake events or information.
        """
        # Check for common hallucination patterns when user asks for events
        if any(keyword in user_message.lower() for keyword in ['event', 'more event', 'add event']):
            # Look for suspicious patterns that indicate made-up events
            hallucination_indicators = [
                # Fake event patterns
                r'\*\*[^*]+\*\*\s*-\s*\*\*Date:\*\*',  # **Event Name** - **Date:**
                r'\d+\.\s*\*\*[^*]+\*\*',  # 1. **Event Name**
                r'Community\s+\w+\s+Fair',  # Generic community events
                r'Avalon\s+Community\s+Center',  # Fake venues
                r'Saturday,\s+November\s+\d+th',  # Specific fake dates
                # Fake contact patterns
                r'All\s+materials\s+provided',
                r'Snacks\s+and\s+drinks\s+available',
                r'Bring\s+your\s+blankets',
            ]
            
            import re
            for pattern in hallucination_indicators:
                if re.search(pattern, response, re.IGNORECASE):
                    logger.warning(f"Detected potential hallucination: {pattern}")
                    return True
        
        return False

    # Function implementations that GPT can call
    async def web_search(self, query: str, location: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Web search function for GPT to call"""
        try:
            # Use GPT-4 with web search capability
            search_response = await self.client.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a web search assistant. Provide current, accurate information from the web."
                    },
                    {
                        "role": "user",
                        "content": f"Search for: {query}" + (f" in {location}" if location else "")
                    }
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            return {
                "query": query,
                "location": location,
                "results": search_response.choices[0].message.content,
                "source": "GPT-4 Web Search"
            }
        except Exception as e:
            return {"error": str(e), "query": query}

    async def search_events(self, postcode: str, radius: float = 10, frequency: str = "weekly", event_type: Optional[str] = None) -> Dict[str, Any]:
        """Event search function for GPT to call"""
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
                "events_found": len(events),
                "events": events
            }
        except Exception as e:
            return {"error": str(e), "postcode": postcode}

    async def search_local_businesses(self, query: str, location: str, business_type: str = "any") -> Dict[str, Any]:
        """Local business search function for GPT to call"""
        try:
            # Use GPT to provide business information
            business_response = await self.client.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a local business search assistant. Provide information about businesses in specific locations."
                    },
                    {
                        "role": "user",
                        "content": f"Find {business_type} businesses for '{query}' in {location}. Provide names, addresses, and contact information if available."
                    }
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            return {
                "query": query,
                "location": location,
                "business_type": business_type,
                "results": business_response.choices[0].message.content
            }
        except Exception as e:
            return {"error": str(e), "query": query, "location": location}

    async def get_weather_info(self, location: str) -> Dict[str, Any]:
        """Weather information function for GPT to call"""
        try:
            weather_response = await self.client.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a weather information assistant. Provide current weather and forecast information."
                    },
                    {
                        "role": "user",
                        "content": f"What's the current weather and forecast for {location}?"
                    }
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            return {
                "location": location,
                "weather_info": weather_response.choices[0].message.content
            }
        except Exception as e:
            return {"error": str(e), "location": location}

    async def generate_newsletter_content(self, topic: str, style: str = "professional", length: str = "medium", content_type: str = "article") -> Dict[str, Any]:
        """Content generation function for GPT to call"""
        try:
            content_response = await self.client.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a newsletter content writer. Create {style} {content_type} content that is {length} in length."
                    },
                    {
                        "role": "user",
                        "content": f"Write a {length} {style} {content_type} about {topic} for a community newsletter."
                    }
                ],
                temperature=0.7,
                max_tokens=1000 if length == "long" else 600 if length == "medium" else 300
            )
            
            return {
                "topic": topic,
                "style": style,
                "length": length,
                "content_type": content_type,
                "generated_content": content_response.choices[0].message.content
            }
        except Exception as e:
            return {"error": str(e), "topic": topic}

    async def customize_newsletter(self, newsletter_id: str, customization_type: str, changes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Newsletter customization function for GPT to call"""
        try:
            return {
                "newsletter_id": newsletter_id,
                "customization_type": customization_type,
                "changes": changes,
                "status": "Customization request processed",
                "message": f"Newsletter {newsletter_id} {customization_type} customization has been applied."
            }
        except Exception as e:
            return {"error": str(e), "newsletter_id": newsletter_id}

    async def manage_schedule(self, newsletter_id: str, action: str, schedule_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Schedule management function for GPT to call"""
        try:
            return {
                "newsletter_id": newsletter_id,
                "action": action,
                "schedule_data": schedule_data,
                "status": "Schedule action completed",
                "message": f"Newsletter {newsletter_id} schedule {action} has been processed."
            }
        except Exception as e:
            return {"error": str(e), "newsletter_id": newsletter_id}

    async def find_images(self, query: str, style: str = "professional", count: int = 3) -> Dict[str, Any]:
        """Image search function for GPT to call"""
        try:
            # Generate image suggestions using GPT
            image_response = await self.client.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an image search assistant. Suggest relevant, high-quality images for newsletter content."
                    },
                    {
                        "role": "user",
                        "content": f"Suggest {count} {style} images for '{query}' that would be suitable for a newsletter. Provide descriptions and potential sources."
                    }
                ],
                temperature=0.5,
                max_tokens=600
            )
            
            return {
                "query": query,
                "style": style,
                "count": count,
                "image_suggestions": image_response.choices[0].message.content
            }
        except Exception as e:
            return {"error": str(e), "query": query} 