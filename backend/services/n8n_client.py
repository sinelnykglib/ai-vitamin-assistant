# backend/services/n8n_client.py

import aiohttp
import asyncio
import json
from typing import Dict, List, Optional
from utils.logger import get_logger
from utils.config import get_settings

logger = get_logger(__name__)
settings = get_settings()

class N8NClient:
    """Client for integrating with n8n workflows"""
    
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or settings.N8N_WEBHOOK_URL
        self.api_key = settings.N8N_API_KEY
        
        # Prompt builders for different intent types
        self.prompt_builders = {
            "recommendation": self._build_recommendation_prompt,
            "timing": self._build_timing_prompt,
            "dosage": self._build_dosage_prompt,
            "safety": self._build_safety_prompt,
            "general": self._build_general_prompt
        }
    
    async def send_request(
        self,
        preprocessed: Dict,
        user_profile: Dict,
        session_history: List
    ) -> Dict:
        """
        Send request to n8n workflow
        
        Args:
            preprocessed: Preprocessed request data
            user_profile: User profile information
            session_history: Recent conversation history
            
        Returns:
            Response from n8n workflow
        """
        try:
            # Get intent type
            intent = preprocessed.get("intent", "general")
            
            # Build prompt using appropriate builder
            prompt_builder = self.prompt_builders.get(intent, self.prompt_builders["general"])
            prompt = prompt_builder(preprocessed, user_profile, session_history)
            
            # Build payload for n8n
            payload = {
                "intent": intent,
                "prompt": prompt,
                "system_prompt": preprocessed.get("system_prompt", ""),
                "user_context": {
                    "age": user_profile.get("age"),
                    "gender": user_profile.get("gender"),
                    "weight": user_profile.get("weight"),
                    "health_goals": user_profile.get("health_goals", []),
                    "allergies": user_profile.get("allergies", []),
                    "current_supplements": user_profile.get("current_supplements", []),
                    "medical_conditions": user_profile.get("medical_conditions", []),
                    "medications": user_profile.get("medications", [])
                },
                "parsed_request": preprocessed.get("parsed_request", {}),
                "conversation_history": session_history[-3:] if session_history else [],
                "original_message": preprocessed.get("original_message", "")
            }
            
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["X-API-Key"] = self.api_key
            
            logger.info(f"Sending request to n8n with intent: {intent}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"n8n response received successfully for intent: {intent}")
                        
                        # Add metadata to response
                        result["confidence"] = result.get("confidence", settings.DEFAULT_CONFIDENCE)
                        result["intent"] = intent
                        
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"n8n error {response.status}: {error_text}")
                        return self._get_fallback_response(intent)
                        
        except asyncio.TimeoutError:
            logger.error("n8n request timeout after 30 seconds")
            return self._get_fallback_response(intent)
        except aiohttp.ClientError as e:
            logger.error(f"n8n client error: {str(e)}")
            return self._get_fallback_response(intent)
        except Exception as e:
            logger.error(f"Unexpected error calling n8n: {str(e)}", exc_info=True)
            return self._get_fallback_response("general")
    
    def _build_recommendation_prompt(self, preprocessed: Dict, user_profile: Dict, history: List) -> str:
        """Build prompt for vitamin recommendations"""
        parsed = preprocessed.get("parsed_request", {})
        context = preprocessed.get("context", {})
        
        prompt = f"""Provide personalized vitamin and supplement recommendations.

USER INFORMATION:
- Age: {user_profile.get('age', 'not specified')}
- Gender: {user_profile.get('gender', 'not specified')}
- Weight: {user_profile.get('weight', 'not specified')} kg
- Health Goals: {', '.join(user_profile.get('health_goals', [])) or 'not specified'}
- Current Supplements: {', '.join(user_profile.get('current_supplements', [])) or 'none'}
- Allergies: {', '.join(user_profile.get('allergies', [])) or 'none'}
- Medical Conditions: {', '.join(user_profile.get('medical_conditions', [])) or 'none'}
- Medications: {', '.join(user_profile.get('medications', [])) or 'none'}

USER QUERY: {preprocessed.get('original_message', '')}

MENTIONED SUPPLEMENTS: {', '.join(parsed.get('mentioned_vitamins', [])) or 'none'}
SYMPTOMS REPORTED: {', '.join(parsed.get('symptoms', [])) or 'none'}

CONVERSATION CONTEXT: {json.dumps(history[-2:] if history else [], ensure_ascii=False)}

Provide recommendations in JSON format with:
- message: empathetic, personalized response
- recommendations: array with vitamin, time (morning/dinner/evening), dosage, priority (high/medium/low), reason, notes
- warnings: safety warnings and contraindications
- questions: clarifying questions if needed
- disclaimer: standard medical disclaimer

Ensure all recommendations follow evidence-based guidelines and consider potential interactions with existing medications and conditions."""
        
        return prompt
    
    def _build_timing_prompt(self, preprocessed: Dict, user_profile: Dict, history: List) -> str:
        """Build prompt for timing optimization"""
        parsed = preprocessed.get("parsed_request", {})
        
        prompt = f"""Optimize supplement timing for maximum effectiveness.

SUPPLEMENTS TO SCHEDULE: {', '.join(parsed.get('mentioned_vitamins', [])) or 'from user query'}
CURRENT SUPPLEMENTS: {', '.join(user_profile.get('current_supplements', [])) or 'none'}
USER QUERY: {preprocessed.get('original_message', '')}

TIMING GUIDELINES:
- Morning (with breakfast): B-complex, Vitamin D3+K2, Iron, CoQ10, Vitamin C
- Dinner (with meal): Omega-3, Zinc, Calcium, Vitamin K2, Magnesium (if not sleep-related)
- Evening (before bed): Magnesium glycinate, Melatonin, GABA, L-theanine, 5-HTP

CONFLICT RULES:
- Calcium and Iron: separate by 2-3 hours
- Zinc and Copper: take separately or use balanced complex
- Iron and coffee/tea: separate by 1-2 hours
- Thyroid medication: separate from calcium/iron by 4 hours

Provide JSON output with:
- optimized_schedule: morning, dinner, evening arrays with supplement names
- conflicts: list of potential interactions to avoid
- suggestions: absorption tips and best practices
- food_pairings: recommended food combinations"""
        
        return prompt
    
    def _build_dosage_prompt(self, preprocessed: Dict, user_profile: Dict, history: List) -> str:
        """Build prompt for dosage recommendations"""
        parsed = preprocessed.get("parsed_request", {})
        
        prompt = f"""Provide appropriate supplement dosages.

USER AGE: {user_profile.get('age', 'not specified')}
USER WEIGHT: {user_profile.get('weight', 'not specified')} kg
USER CONDITION: {', '.join(user_profile.get('medical_conditions', [])) or 'none'}
SUPPLEMENT: {', '.join(parsed.get('mentioned_vitamins', [])) or 'from user query'}
USER QUERY: {preprocessed.get('original_message', '')}

STANDARD DAILY DOSAGES:
- Vitamin D3: 600-4000 IU (maintenance), up to 10,000 IU (deficiency)
- Vitamin C: 250-1000 mg (maintenance), up to 2000 mg (acute)
- Vitamin B12: 2.4-1000 mcg (depends on form and absorption)
- Magnesium: 200-400 mg (glycinate for sleep, citrate for constipation)
- Zinc: 8-30 mg (with copper if taking long-term)
- Iron: 8-27 mg (elemental iron, based on deficiency)
- Omega-3: 1000-3000 mg EPA+DHA combined
- Calcium: 500-1200 mg (from food + supplements)

UPPER LIMITS:
- Vitamin D3: 4000 IU daily long-term
- Vitamin C: 2000 mg daily
- Zinc: 40 mg daily
- Iron: 45 mg daily

Provide JSON output with:
- message: personalized dosing guidance
- dosages: array with supplement, standard_dosage, optimal_dosage, max_dosage, timing_notes
- warnings: toxicity risks and interactions
- monitoring_advice: what to watch for"""
        
        return prompt
    
    def _build_safety_prompt(self, preprocessed: Dict, user_profile: Dict, history: List) -> str:
        """Build prompt for safety assessment"""
        parsed = preprocessed.get("parsed_request", {})
        
        prompt = f"""Assess supplement safety and potential interactions.

USER PROFILE:
- Age: {user_profile.get('age', 'not specified')}
- Gender: {user_profile.get('gender', 'not specified')}
- Medications: {', '.join(user_profile.get('medications', [])) or 'none'}
- Medical Conditions: {', '.join(user_profile.get('medical_conditions', [])) or 'none'}
- Allergies: {', '.join(user_profile.get('allergies', [])) or 'none'}
- Pregnancy/Lactation: {user_profile.get('pregnancy_status', 'not specified')}
- Current Supplements: {', '.join(user_profile.get('current_supplements', [])) or 'none'}

SUPPLEMENT TO ASSESS: {', '.join(parsed.get('mentioned_vitamins', [])) or 'from user query'}
USER QUERY: {preprocessed.get('original_message', '')}

KNOWN INTERACTIONS:
- Vitamin K: with warfarin/coumadin (contraindicated)
- St. John's Wort: with antidepressants, birth control, immunosuppressants
- High-dose Vitamin A: pregnancy (risk of birth defects)
- Iron: with levothyroxine (separate by 4 hours)
- Calcium: with bisphosphonates (separate by 2 hours)
- Magnesium: with antibiotics (separate by 2-4 hours)

Provide JSON output with:
- message: safety assessment summary
- is_safe: true/false/conditional
- contraindications: absolute contraindications present
- interactions: array with with, severity, mechanism, recommendation
- precautions: special considerations
- monitoring_required: what to monitor
- alternative_suggestions: safer alternatives if applicable"""
        
        return prompt
    
    def _build_general_prompt(self, preprocessed: Dict, user_profile: Dict, history: List) -> str:
        """Build general prompt for other queries"""
        parsed = preprocessed.get("parsed_request", {})
        
        prompt = f"""Provide helpful information about vitamins and supplements.

USER QUERY: {preprocessed.get('original_message', '')}
MENTIONED SUPPLEMENTS: {', '.join(parsed.get('mentioned_vitamins', [])) or 'none'}

Provide a helpful response in JSON format with:
- message: informative and friendly response
- recommendations: array of relevant supplements if applicable
- questions: clarifying questions if needed
- resources: suggested further reading if applicable

Keep response concise but informative. Include a standard disclaimer about consulting healthcare providers."""
        
        return prompt
    
    def _get_fallback_response(self, intent: str) -> Dict:
        """Return fallback response when n8n is unavailable"""
        
        fallbacks = {
            "recommendation": {
                "message": "I apologize, but I'm having trouble connecting to my recommendation system. For personalized supplement advice, please consult with a healthcare provider. You can also try again in a few moments.",
                "recommendations": [],
                "confidence": 0.5,
                "intent": intent,
                "fallback": True
            },
            "timing": {
                "message": "I'm currently experiencing technical issues. For optimal supplement timing, general guidelines are: energizing supplements in the morning, fat-soluble with meals, and calming supplements in the evening. Please consult a healthcare provider for personalized advice.",
                "optimized_schedule": {"morning": [], "dinner": [], "evening": []},
                "confidence": 0.5,
                "intent": intent,
                "fallback": True
            },
            "dosage": {
                "message": "I'm having technical difficulties. Standard dosages vary by age, weight, and health status. Please consult the supplement label and your healthcare provider for appropriate dosing guidance.",
                "dosages": [],
                "confidence": 0.5,
                "intent": intent,
                "fallback": True
            },
            "safety": {
                "message": "Safety assessment is temporarily unavailable. Always check with your healthcare provider about potential interactions between supplements and your current medications or health conditions.",
                "is_safe": "unknown",
                "confidence": 0.5,
                "intent": intent,
                "fallback": True
            },
            "general": {
                "message": "I'm currently experiencing connection issues. Please try again in a moment. In the meantime, remember that supplement recommendations should always be discussed with a healthcare provider who knows your medical history.",
                "recommendations": [],
                "confidence": 0.5,
                "intent": intent,
                "fallback": True
            }
        }
        
        return fallbacks.get(intent, fallbacks["general"])
    
    async def health_check(self) -> Dict:
        """Check n8n service health status"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.webhook_url,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return {
                        "status": "healthy" if response.status < 500 else "unhealthy",
                        "status_code": response.status,
                        "url": self.webhook_url,
                        "response_time_ms": response.raw_headers.get("X-Response-Time", "unknown")
                    }
        except asyncio.TimeoutError:
            return {
                "status": "unhealthy",
                "error": "Connection timeout",
                "url": self.webhook_url
            }
        except aiohttp.ClientError as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "url": self.webhook_url
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": f"Unexpected error: {str(e)}",
                "url": self.webhook_url
            }

# Global client instance
n8n_client = N8NClient()