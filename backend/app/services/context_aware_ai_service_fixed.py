import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import openai
from openai import OpenAI
import httpx
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)

class ActionType(Enum):
    GENERATE_NEWSLETTER = "generate_newsletter"
    ADD_EVENTS = "add_events"
    CHANGE_EVENTS = "change_events"
    CHANGE_TONE = "change_tone"
    DELETE_EVENTS = "delete_events"
    SEARCH_WEB = "search_web"
    SEARCH_EVENTS = "search_events"
    CUSTOMIZE_CONTENT = "customize_content"
    RESPOND_IN_CHAT = "respond_in_chat"
    UPDATE_NEWSLETTER = "update_newsletter"

class ContextType(Enum):
    USER_INTENT = "user_intent"
    CONVERSATION_HISTORY = "conversation_history"
    NEWSLETTER_STATE = "newsletter_state"
    USER_PREFERENCES = "user_preferences"
    TEMPORAL = "temporal"
    SPATIAL = "spatial"

@dataclass
class ContextItem:
    type: ContextType
    content: Any
    timestamp: datetime
    relevance_score: float = 0.0
    importance: float = 0.5

@dataclass
class ActionDecision:
    action_type: ActionType
    target: str  # "chat", "newsletter", "system"
    parameters: Dict[str, Any]
    reasoning: str
    confidence: float

class ContextAwareAIService:
    def __init__(self):
        self._client = None
        self.context_memory: List[ContextItem] = []
        self.conversation_history: List[Dict[str, Any]] = []
        self.current_newsletter_state: Optional[Dict[str, Any]] = None
        self.user_preferences: Dict[str, Any] = {}
    
    @property
    def client(self):
        """Lazy-load OpenAI client to avoid requiring API key at startup"""
        if self._client is None:
            try:
                self._client = OpenAI()
            except Exception as e:
                logger.warning(f"OpenAI client not available: {e}")
                raise e
        return self._client
        
    async def process_user_request(self, user_message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Main entry point for processing user requests with full context awareness
        """
        try:
            # Step 1: Extract and enrich context
            enriched_context = await self._extract_context(user_message, context or {})
            
            # Step 2: Analyze user intent and determine action
            action_decision = await self._analyze_intent_and_decide_action(user_message, enriched_context)
            
            # Step 3: Execute the determined action
            result = await self._execute_action(action_decision, enriched_context)
            
            # Step 4: Update context memory
            await self._update_context_memory(user_message, action_decision, result)
            
            return {
                "success": True,
                "action_taken": action_decision.action_type.value,
                "target": action_decision.target,
                "reasoning": action_decision.reasoning,
                "result": result,
                "confidence": action_decision.confidence
            }
            
        except Exception as e:
            logger.error(f"Error processing user request: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "fallback_response": "I encountered an error processing your request. Could you please rephrase or provide more details?"
            }

    async def _extract_context(self, user_message: str, provided_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract multi-dimensional context from user message and environment
        """
        context = {
            "user_message": user_message,
            "timestamp": datetime.now(),
            "conversation_history": self.conversation_history[-10:],  # Last 10 messages
            "current_newsletter": self.current_newsletter_state,
            "user_preferences": self.user_preferences,
            **provided_context
        }
        
        # Add temporal context
        context["temporal"] = {
            "current_time": datetime.now().isoformat(),
            "day_of_week": datetime.now().strftime("%A"),
            "is_weekend": datetime.now().weekday() >= 5
        }
        
        # Add spatial context if available
        if "postcode" in provided_context:
            context["spatial"] = {
                "postcode": provided_context["postcode"],
                "region": provided_context.get("region", "UK")
            }
        
        return context

    async def _analyze_intent_and_decide_action(self, user_message: str, context: Dict[str, Any]) -> ActionDecision:
        """
        Analyze user intent and decide on appropriate action using rule-based approach with GPT-4 fallback
        """
        # First try rule-based analysis for common patterns
        rule_based_decision = self._rule_based_intent_analysis(user_message, context)
        if rule_based_decision.confidence > 0.7:
            return rule_based_decision
        
        # Fallback to GPT-4 for complex cases
        try:
            system_prompt = """You are a context-aware AI assistant that helps users with newsletter generation and customization. 

Your job is to:
1. Analyze the user's request in context
2. Determine the most appropriate action
3. Decide WHERE to apply changes (chat response, newsletter update, or system action)
4. Provide clear reasoning for your decision

Available actions:
- GENERATE_NEWSLETTER: Create a new newsletter
- ADD_EVENTS: Add more events to existing newsletter  
- CHANGE_EVENTS: Modify existing events in newsletter
- CHANGE_TONE: Change the tone/style of newsletter content
- DELETE_EVENTS: Remove specific events from newsletter
- SEARCH_WEB: Search for current information
- SEARCH_EVENTS: Find specific events
- CUSTOMIZE_CONTENT: Modify newsletter content/structure
- RESPOND_IN_CHAT: Provide information/answer in chat only
- UPDATE_NEWSLETTER: Apply changes directly to newsletter

Target options:
- "chat": Respond in chat conversation
- "newsletter": Apply changes to newsletter content
- "system": Perform system-level actions

Consider:
- Does the user want information (chat response) or changes (newsletter update)?
- Is there an existing newsletter to modify?
- What's the user's intent based on conversation history?
- Should changes be applied immediately or discussed first?

Respond with a JSON object containing:
{
    "action_type": "ACTION_NAME",
    "target": "chat|newsletter|system", 
    "parameters": {...},
    "reasoning": "Clear explanation of why this action and target",
    "confidence": 0.0-1.0
}"""

            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"""
User message: "{user_message}"

Context:
- Conversation history: {json.dumps(context.get('conversation_history', [])[-3:], default=str)}
- Current newsletter exists: {context.get('current_newsletter') is not None}
- User preferences: {json.dumps(context.get('user_preferences', {}), default=str)}
- Temporal context: {json.dumps(context.get('temporal', {}), default=str)}

Analyze this request and determine the appropriate action and target.
"""}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            decision_json = json.loads(response.choices[0].message.content)
            
            return ActionDecision(
                action_type=ActionType(decision_json["action_type"]),
                target=decision_json["target"],
                parameters=decision_json.get("parameters", {}),
                reasoning=decision_json["reasoning"],
                confidence=decision_json.get("confidence", 0.8)
            )
            
        except Exception as e:
            logger.error(f"Error in GPT-4 intent analysis: {str(e)}")
            # Return rule-based decision even if confidence is lower
            return rule_based_decision

    def _rule_based_intent_analysis(self, user_message: str, context: Dict[str, Any]) -> ActionDecision:
        """
        Rule-based intent analysis for common patterns
        """
        message_lower = user_message.lower()
        
        # Newsletter generation patterns
        if any(phrase in message_lower for phrase in [
            "generate newsletter", "create newsletter", "make newsletter", 
            "new newsletter", "generate a newsletter", "create a newsletter"
        ]):
            # Extract parameters from context and message
            postcode = context.get("postcode", "TS1 3BA")
            radius = 5.0
            frequency = "weekly" if "weekly" in message_lower else "monthly" if "monthly" in message_lower else "weekly"
            
            # Extract target audience
            target_audience = "families with children in social housing"
            if "families" in message_lower:
                target_audience = "families with children in social housing"
            elif "children" in message_lower:
                target_audience = "families with children in social housing"
            
            return ActionDecision(
                action_type=ActionType.GENERATE_NEWSLETTER,
                target="newsletter",
                parameters={
                    "postcode": postcode,
                    "radius": radius,
                    "frequency": frequency,
                    "target_audience": target_audience
                },
                reasoning=f"User explicitly requested newsletter generation with {frequency} frequency for {target_audience}",
                confidence=0.9
            )
        
        # Add events patterns
        if any(phrase in message_lower for phrase in [
            "add more events", "add events", "more events", "find more events",
            "add additional events", "include more events"
        ]):
            return ActionDecision(
                action_type=ActionType.ADD_EVENTS,
                target="newsletter",
                parameters={
                    "postcode": context.get("postcode", "TS1 3BA"),
                    "radius": 10.0,  # Expand radius for more events
                    "frequency": "weekly"
                },
                reasoning="User wants to add more events to existing newsletter",
                confidence=0.85
            )
        
        # Change tone patterns
        if any(phrase in message_lower for phrase in [
            "change tone", "change the tone", "make it more", "tone to",
            "more casual", "more professional", "more friendly", "more formal"
        ]):
            # Extract tone
            tone = "friendly and informative"
            if "casual" in message_lower or "friendly" in message_lower:
                tone = "casual and friendly"
            elif "professional" in message_lower or "formal" in message_lower:
                tone = "professional and informative"
            elif "enthusiastic" in message_lower:
                tone = "enthusiastic and engaging"
            
            return ActionDecision(
                action_type=ActionType.CHANGE_TONE,
                target="newsletter",
                parameters={"tone": tone},
                reasoning=f"User wants to change newsletter tone to {tone}",
                confidence=0.8
            )
        
        # Delete events patterns
        if any(phrase in message_lower for phrase in [
            "delete events", "remove events", "delete event", "remove event",
            "delete any events", "remove any events", "delete expensive",
            "remove expensive", "delete paid", "remove paid"
        ]):
            # Extract criteria
            criteria = []
            if "expensive" in message_lower or "cost" in message_lower or "£" in message_lower or "$" in message_lower:
                criteria.append("expensive events")
            
            return ActionDecision(
                action_type=ActionType.DELETE_EVENTS,
                target="newsletter",
                parameters={"criteria": criteria},
                reasoning=f"User wants to delete events based on criteria: {', '.join(criteria) if criteria else 'user specification'}",
                confidence=0.8
            )
        
        # Search events patterns
        if any(phrase in message_lower for phrase in [
            "find events", "search events", "what events", "events happening",
            "events available", "show me events", "list events"
        ]):
            return ActionDecision(
                action_type=ActionType.SEARCH_EVENTS,
                target="chat",
                parameters={
                    "postcode": context.get("postcode", "TS1 3BA"),
                    "radius": 5.0,
                    "frequency": "weekly"
                },
                reasoning="User wants to search for events - providing information in chat",
                confidence=0.8
            )
        
        # Web search patterns
        if any(phrase in message_lower for phrase in [
            "search for", "look up", "find information", "what is",
            "tell me about", "search web", "google"
        ]):
            return ActionDecision(
                action_type=ActionType.SEARCH_WEB,
                target="chat",
                parameters={"query": user_message},
                reasoning="User wants web search information - providing results in chat",
                confidence=0.75
            )
        
        # Default to chat response for unclear requests
        return ActionDecision(
            action_type=ActionType.RESPOND_IN_CHAT,
            target="chat",
            parameters={},
            reasoning="Request pattern not clearly identified - providing helpful chat response",
            confidence=0.5
        )

    async def _execute_action(self, action: ActionDecision, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the determined action with full context awareness
        """
        try:
            if action.action_type == ActionType.GENERATE_NEWSLETTER:
                return await self._generate_newsletter(action.parameters, context)
            
            elif action.action_type == ActionType.SEARCH_EVENTS:
                return await self._search_family_events(action.parameters, context)
            
            elif action.action_type == ActionType.UPDATE_NEWSLETTER:
                return await self._update_newsletter(action.parameters, context)
            
            elif action.action_type == ActionType.CHANGE_TONE:
                return await self._change_newsletter_tone(action.parameters, context)
            
            elif action.action_type == ActionType.ADD_EVENTS:
                return await self._add_events_to_newsletter(action.parameters, context)
            
            elif action.action_type == ActionType.DELETE_EVENTS:
                return await self._delete_events_from_newsletter(action.parameters, context)
            
            elif action.action_type == ActionType.SEARCH_WEB:
                return await self._web_search(action.parameters, context)
            
            elif action.action_type == ActionType.RESPOND_IN_CHAT:
                return await self._generate_chat_response(action.parameters, context)
            
            else:
                return {"error": f"Unknown action type: {action.action_type}"}
                
        except Exception as e:
            logger.error(f"Error executing action {action.action_type}: {str(e)}")
            return {"error": str(e)}

    async def _generate_newsletter(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a new newsletter with context awareness"""
        try:
            # Import here to avoid circular imports
            from .enhanced_event_scraper import EnhancedEventScraper
            from .ai_service import AIService
            
            scraper = EnhancedEventScraper()
            ai_service = AIService()
            
            # Get events with expanded radius if needed
            events = await scraper.search_events(
                postcode=parameters["postcode"],
                radius=parameters.get("radius", 5.0),
                frequency=parameters["frequency"]
            )
            
            # Generate newsletter content
            newsletter_content = await ai_service.generate_newsletter_content(
                events=events,
                target_audience=parameters["target_audience"],
                tone=parameters.get("tone", "friendly and informative"),
                context=context
            )
            
            # Store newsletter state
            self.current_newsletter_state = {
                "content": newsletter_content,
                "events": events,
                "parameters": parameters,
                "created_at": datetime.now().isoformat()
            }
            
            return {
                "newsletter_content": newsletter_content,
                "events_found": len(events),
                "message": f"Generated newsletter with {len(events)} family-friendly events"
            }
            
        except Exception as e:
            logger.error(f"Error generating newsletter: {str(e)}")
            return {"error": str(e)}

    async def _search_family_events(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Search for family-friendly events with context"""
        try:
            from .enhanced_event_scraper import EnhancedEventScraper
            
            scraper = EnhancedEventScraper()
            events = await scraper.search_events(
                postcode=parameters["postcode"],
                radius=parameters.get("radius", 5.0),
                frequency=parameters["frequency"]
            )
            
            return {
                "events": events,
                "count": len(events),
                "message": f"Found {len(events)} family-friendly events"
            }
            
        except Exception as e:
            logger.error(f"Error searching events: {str(e)}")
            return {"error": str(e)}

    async def _update_newsletter(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing newsletter content"""
        if not self.current_newsletter_state:
            return {"error": "No newsletter to update. Please generate a newsletter first."}
        
        try:
            updates = parameters.get("updates", {})
            
            # Apply tone changes
            if "tone" in updates:
                await self._change_newsletter_tone({"tone": updates["tone"]}, context)
            
            # Add events
            if "add_events" in updates:
                await self._add_events_to_newsletter({"events": updates["add_events"]}, context)
            
            # Remove events
            if "remove_events" in updates:
                await self._delete_events_from_newsletter({"event_ids": updates["remove_events"]}, context)
            
            return {
                "message": "Newsletter updated successfully",
                "updates_applied": list(updates.keys())
            }
            
        except Exception as e:
            logger.error(f"Error updating newsletter: {str(e)}")
            return {"error": str(e)}

    async def _change_newsletter_tone(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Change the tone of the newsletter"""
        if not self.current_newsletter_state:
            return {"error": "No newsletter to modify. Please generate a newsletter first."}
        
        try:
            new_tone = parameters.get("tone", "friendly and informative")
            
            # Use GPT-4 to rewrite content with new tone
            system_prompt = f"""Rewrite the newsletter content with a {new_tone} tone while keeping all the events and information intact. 
            
            Maintain:
            - All event details (dates, times, locations, costs)
            - All factual information
            - Overall structure
            
            Change:
            - Writing style and tone to be {new_tone}
            - Language and phrasing
            - Introductory and connecting text"""
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Original newsletter content:\n\n{json.dumps(self.current_newsletter_state['content'], indent=2)}"}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            # Update the newsletter state
            updated_content = json.loads(response.choices[0].message.content)
            self.current_newsletter_state["content"] = updated_content
            self.current_newsletter_state["tone"] = new_tone
            
            return {
                "message": f"Newsletter tone changed to {new_tone}",
                "updated_content": updated_content
            }
            
        except Exception as e:
            logger.error(f"Error changing tone: {str(e)}")
            return {"error": str(e)}

    async def _add_events_to_newsletter(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Add more events to the newsletter"""
        try:
            # Search for additional events
            search_params = {
                "postcode": context.get("spatial", {}).get("postcode", "TS1 3BA"),
                "radius": parameters.get("radius", 10.0),  # Expand radius for more events
                "frequency": parameters.get("frequency", "weekly")
            }
            
            additional_events = await self._search_family_events(search_params, context)
            
            if self.current_newsletter_state and additional_events.get("events"):
                # Add new events to existing newsletter
                current_events = self.current_newsletter_state.get("events", [])
                new_events = additional_events["events"]
                
                # Avoid duplicates
                existing_titles = {event.get("event_title", "") for event in current_events}
                unique_new_events = [
                    event for event in new_events 
                    if event.get("event_title", "") not in existing_titles
                ]
                
                self.current_newsletter_state["events"].extend(unique_new_events)
                
                return {
                    "message": f"Added {len(unique_new_events)} new events to newsletter",
                    "new_events": unique_new_events
                }
            
            return additional_events
            
        except Exception as e:
            logger.error(f"Error adding events: {str(e)}")
            return {"error": str(e)}

    async def _delete_events_from_newsletter(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Delete specific events from newsletter"""
        if not self.current_newsletter_state:
            return {"error": "No newsletter to modify"}
        
        try:
            events_to_remove = parameters.get("event_ids", [])
            current_events = self.current_newsletter_state.get("events", [])
            
            # Remove events by title or ID
            filtered_events = [
                event for event in current_events
                if event.get("event_title", "") not in events_to_remove
                and str(event.get("id", "")) not in events_to_remove
            ]
            
            removed_count = len(current_events) - len(filtered_events)
            self.current_newsletter_state["events"] = filtered_events
            
            return {
                "message": f"Removed {removed_count} events from newsletter",
                "remaining_events": len(filtered_events)
            }
            
        except Exception as e:
            logger.error(f"Error deleting events: {str(e)}")
            return {"error": str(e)}

    async def _web_search(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform web search for current information"""
        try:
            query = parameters["query"]
            location = parameters.get("location", "")
            
            # Simple web search implementation
            search_url = f"https://www.google.com/search?q={query}+{location}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(search_url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                })
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    # Extract search results (simplified)
                    results = []
                    for result in soup.find_all('div', class_='g')[:5]:
                        title_elem = result.find('h3')
                        if title_elem:
                            results.append({
                                "title": title_elem.get_text(),
                                "snippet": result.get_text()[:200] + "..."
                            })
                    
                    return {
                        "query": query,
                        "results": results,
                        "message": f"Found {len(results)} search results"
                    }
            
            return {"error": "Search failed"}
            
        except Exception as e:
            logger.error(f"Error in web search: {str(e)}")
            return {"error": str(e)}

    async def _generate_chat_response(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a contextual chat response"""
        try:
            user_message = context["user_message"]
            
            system_prompt = """You are a helpful AI assistant specializing in newsletter generation and event discovery for social housing communities. 

            Provide helpful, accurate responses based on the context provided. If the user is asking about newsletter modifications, explain what can be done and offer to help.
            
            Be conversational but informative. Always consider the context of previous interactions."""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"""
User message: {user_message}

Context:
- Current newsletter exists: {self.current_newsletter_state is not None}
- Recent conversation: {json.dumps(context.get('conversation_history', [])[-3:], default=str)}
- User preferences: {json.dumps(context.get('user_preferences', {}), default=str)}

Please provide a helpful response.
"""}
            ]
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            return {
                "response": response.choices[0].message.content,
                "type": "chat_response"
            }
            
        except Exception as e:
            logger.error(f"Error generating chat response: {str(e)}")
            return {"error": str(e)}

    async def _update_context_memory(self, user_message: str, action: ActionDecision, result: Dict[str, Any]):
        """Update context memory with new interaction"""
        try:
            # Add to conversation history
            self.conversation_history.append({
                "timestamp": datetime.now().isoformat(),
                "user_message": user_message,
                "action_taken": action.action_type.value,
                "target": action.target,
                "result_summary": str(result)[:200] + "..." if len(str(result)) > 200 else str(result)
            })
            
            # Keep only last 50 conversations
            if len(self.conversation_history) > 50:
                self.conversation_history = self.conversation_history[-50:]
            
            # Add context items
            context_items = [
                ContextItem(
                    type=ContextType.USER_INTENT,
                    content={"message": user_message, "action": action.action_type.value},
                    timestamp=datetime.now(),
                    relevance_score=action.confidence,
                    importance=0.8
                ),
                ContextItem(
                    type=ContextType.CONVERSATION_HISTORY,
                    content={"action": action.action_type.value, "result": result},
                    timestamp=datetime.now(),
                    relevance_score=0.7,
                    importance=0.6
                )
            ]
            
            self.context_memory.extend(context_items)
            
            # Keep memory manageable
            if len(self.context_memory) > 100:
                # Remove oldest, least important items
                self.context_memory.sort(key=lambda x: (x.importance, x.timestamp), reverse=True)
                self.context_memory = self.context_memory[:100]
                
        except Exception as e:
            logger.error(f"Error updating context memory: {str(e)}")

    def get_current_newsletter_state(self) -> Optional[Dict[str, Any]]:
        """Get the current newsletter state"""
        return self.current_newsletter_state

    def set_user_preferences(self, preferences: Dict[str, Any]):
        """Set user preferences for context"""
        self.user_preferences.update(preferences)

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history"""
        return self.conversation_history[-10:]  # Last 10 interactions 