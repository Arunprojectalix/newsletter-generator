import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import openai
from openai import OpenAI

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
    target: str
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
        if self._client is None:
            try:
                self._client = OpenAI()
            except Exception as e:
                logger.warning(f"OpenAI client not available: {e}")
                raise e
        return self._client
        
    async def process_user_request(self, user_message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        try:
            enriched_context = await self._extract_context(user_message, context or {})
            action_decision = await self._analyze_intent_and_decide_action(user_message, enriched_context)
            result = await self._execute_action(action_decision, enriched_context)
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
                "fallback_response": "I encountered an error processing your request."
            }

    async def _extract_context(self, user_message: str, provided_context: Dict[str, Any]) -> Dict[str, Any]:
        context = {
            "user_message": user_message,
            "timestamp": datetime.now(),
            "conversation_history": self.conversation_history[-10:],
            "current_newsletter": self.current_newsletter_state,
            "user_preferences": self.user_preferences,
            **provided_context
        }
        
        context["temporal"] = {
            "current_time": datetime.now().isoformat(),
            "day_of_week": datetime.now().strftime("%A"),
            "is_weekend": datetime.now().weekday() >= 5
        }
        
        if "postcode" in provided_context:
            context["spatial"] = {
                "postcode": provided_context["postcode"],
                "region": provided_context.get("region", "UK")
            }
        
        return context

    async def _analyze_intent_and_decide_action(self, user_message: str, context: Dict[str, Any]) -> ActionDecision:
        rule_based_decision = self._rule_based_intent_analysis(user_message, context)
        return rule_based_decision

    def _rule_based_intent_analysis(self, user_message: str, context: Dict[str, Any]) -> ActionDecision:
        message_lower = user_message.lower()
        
        if any(phrase in message_lower for phrase in [
            "generate newsletter", "create newsletter", "make newsletter", 
            "new newsletter", "generate a newsletter", "create a newsletter"
        ]):
            postcode = context.get("postcode", "TS1 3BA")
            radius = 5.0
            frequency = "weekly" if "weekly" in message_lower else "monthly" if "monthly" in message_lower else "weekly"
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
        
        return ActionDecision(
            action_type=ActionType.RESPOND_IN_CHAT,
            target="chat",
            parameters={},
            reasoning="Request pattern not clearly identified - providing helpful chat response",
            confidence=0.5
        )

    async def _execute_action(self, action: ActionDecision, context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if action.action_type == ActionType.GENERATE_NEWSLETTER:
                return await self._generate_newsletter(action.parameters, context)
            elif action.action_type == ActionType.RESPOND_IN_CHAT:
                return await self._generate_chat_response(action.parameters, context)
            else:
                return {"error": f"Unknown action type: {action.action_type}"}
                
        except Exception as e:
            logger.error(f"Error executing action {action.action_type}: {str(e)}")
            return {"error": str(e)}

    async def _generate_newsletter(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from .enhanced_event_scraper import EnhancedEventScraper
            from .ai_service import AIService
            
            scraper = EnhancedEventScraper()
            ai_service = AIService()
            
            events = await scraper.search_events(
                postcode=parameters["postcode"],
                radius=parameters.get("radius", 5.0),
                frequency=parameters["frequency"]
            )
            
            newsletter_content = await ai_service.generate_newsletter_content(
                events=events,
                target_audience=parameters["target_audience"],
                tone=parameters.get("tone", "friendly and informative"),
                context=context
            )
            
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

    async def _generate_chat_response(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            user_message = context["user_message"]
            
            return {
                "response": f"I understand you said: {user_message}. How can I help you with newsletter generation?",
                "type": "chat_response"
            }
            
        except Exception as e:
            logger.error(f"Error generating chat response: {str(e)}")
            return {"error": str(e)}

    async def _update_context_memory(self, user_message: str, action: ActionDecision, result: Dict[str, Any]):
        try:
            self.conversation_history.append({
                "timestamp": datetime.now().isoformat(),
                "user_message": user_message,
                "action_taken": action.action_type.value,
                "target": action.target,
                "result_summary": str(result)[:200] + "..." if len(str(result)) > 200 else str(result)
            })
            
            if len(self.conversation_history) > 50:
                self.conversation_history = self.conversation_history[-50:]
                
        except Exception as e:
            logger.error(f"Error updating context memory: {str(e)}")

    def get_current_newsletter_state(self) -> Optional[Dict[str, Any]]:
        return self.current_newsletter_state

    def set_user_preferences(self, preferences: Dict[str, Any]):
        self.user_preferences.update(preferences)

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        return self.conversation_history[-10:] 