from pathlib import Path
from typing import Dict, List, Optional
import json

class PromptManager:
    """Manager for loading and formatting prompts"""
    
    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = Path(prompts_dir)
        self.cache = {}
    
    def load_prompt(self, name: str) -> str:
        """Load prompt from file"""
        if name in self.cache:
            return self.cache[name]
        
        prompt_file = self.prompts_dir / f"{name}.txt"
        if prompt_file.exists():
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt = f.read()
                self.cache[name] = prompt
                return prompt
        return ""
    
    def format_prompt(self, name: str, **kwargs) -> str:
        """Load and format prompt with variables"""
        prompt = self.load_prompt(name)
        try:
            return prompt.format(**kwargs)
        except KeyError as e:
            # Return unformatted prompt if keys missing
            return prompt

class Preprocessor:
    """Request preprocessing service"""
    
    def __init__(self):
        self.prompt_manager = PromptManager()
    
    def preprocess_request(
        self,
        message: str,
        user_profile: Optional[Dict] = None,
        conversation_history: Optional[List] = None,
        context: Optional[Dict] = None
    ) -> Dict:
        """Preprocess user request before sending to LLM"""
        
        # Parse user request
        parsed = self._parse_user_request(message, user_profile)
        intent = parsed.get("intent", "general")
        
        # Build prompts
        system_prompt = self.prompt_manager.load_prompt("system_prompt")
        
        # Select appropriate prompt template
        if intent == "recommendation":
            user_prompt = self.prompt_manager.format_prompt(
                "recommendation",
                age=user_profile.get("age", "not specified") if user_profile else "not specified",
                gender=user_profile.get("gender", "not specified") if user_profile else "not specified",
                health_goals=", ".join(user_profile.get("health_goals", [])) if user_profile else "none",
                current_supplements=", ".join(user_profile.get("current_supplements", [])) if user_profile else "none",
                allergies=", ".join(user_profile.get("allergies", [])) if user_profile else "none",
                medical_conditions=", ".join(user_profile.get("medical_conditions", [])) if user_profile else "none",
                user_message=message,
                conversation_history=json.dumps(conversation_history[-3:] if conversation_history else [], ensure_ascii=False)
            )
        elif intent == "timing":
            user_prompt = self.prompt_manager.format_prompt(
                "timing_optimizer",
                vitamins=", ".join(parsed.get("mentioned_vitamins", [])),
                context=json.dumps(user_profile or {}, ensure_ascii=False)
            )
        elif intent == "dosage":
            user_prompt = self.prompt_manager.format_prompt(
                "dosage",
                age=user_profile.get("age", "not specified") if user_profile else "not specified",
                weight=user_profile.get("weight", "not specified") if user_profile else "not specified",
                condition=", ".join(parsed.get("health_conditions", [])),
                supplement=", ".join(parsed.get("mentioned_vitamins", [])),
                user_message=message
            )
        elif intent == "safety":
            user_prompt = self.prompt_manager.format_prompt(
                "safety",
                age=user_profile.get("age", "not specified") if user_profile else "not specified",
                gender=user_profile.get("gender", "not specified") if user_profile else "not specified",
                medications=", ".join(user_profile.get("medications", [])) if user_profile else "none",
                conditions=", ".join(user_profile.get("medical_conditions", [])) if user_profile else "none",
                allergies=", ".join(user_profile.get("allergies", [])) if user_profile else "none",
                pregnancy_status=user_profile.get("pregnancy_status", "not applicable") if user_profile else "not applicable",
                current_supplements=", ".join(user_profile.get("current_supplements", [])) if user_profile else "none",
                supplement=", ".join(parsed.get("mentioned_vitamins", [])),
                dosage=parsed.get("dosage_mentioned", "not specified"),
                user_message=message
            )
        else:
            user_prompt = self.prompt_manager.format_prompt(
                "parsing",
                user_message=message
            )
        
        return {
            "intent": intent,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "parsed_request": parsed,
            "context": {
                "user_profile": user_profile,
                "conversation_history": conversation_history
            },
            "original_message": message
        }
    
    def _parse_user_request(self, message: str, user_profile: Optional[Dict]) -> Dict:
        """Parse user request (basic extraction)"""
        
        message_lower = message.lower()
        
        # Intent detection
        recommendation_keywords = ["recommend", "suggest", "what should i take", "need", "help", "vitamins"]
        timing_keywords = ["when", "time", "morning", "evening", "with food", "empty stomach"]
        dosage_keywords = ["how much", "dosage", "mg", "iu", "quantity", "amount"]
        safety_keywords = ["safe", "interaction", "allergy", "side effect", "contraindication"]
        
        if any(kw in message_lower for kw in recommendation_keywords):
            intent = "recommendation"
        elif any(kw in message_lower for kw in timing_keywords):
            intent = "timing"
        elif any(kw in message_lower for kw in dosage_keywords):
            intent = "dosage"
        elif any(kw in message_lower for kw in safety_keywords):
            intent = "safety"
        else:
            intent = "general"
        
        # Extract mentioned vitamins
        vitamin_keywords = {
            "vitamin d": "Vitamin D3", "vitamin c": "Vitamin C", "vitamin b12": "Vitamin B12",
            "magnesium": "Magnesium", "zinc": "Zinc", "iron": "Iron", "calcium": "Calcium",
            "omega-3": "Omega-3", "probiotics": "Probiotics", "coq10": "CoQ10",
            "melatonin": "Melatonin", "ashwagandha": "Ashwagandha"
        }
        
        mentioned_vitamins = []
        for keyword, vitamin in vitamin_keywords.items():
            if keyword in message_lower:
                mentioned_vitamins.append(vitamin)
        
        return {
            "intent": intent,
            "mentioned_vitamins": mentioned_vitamins,
            "dosage_mentioned": self._extract_dosage(message),
            "health_conditions": [],
            "questions": [],
            "urgency": "medium",
            "missing_info": self._identify_missing_info(intent, user_profile)
        }
    
    def _extract_dosage(self, message: str) -> Optional[str]:
        """Extract dosage information from message"""
        import re
        dosage_pattern = r'(\d+)\s*(mg|mcg|mcg|iu|g)'
        match = re.search(dosage_pattern, message.lower())
        return match.group(0) if match else None
    
    def _identify_missing_info(self, intent: str, user_profile: Optional[Dict]) -> List[str]:
        """Identify missing information for recommendations"""
        missing = []
        
        if not user_profile:
            missing.append("user_profile")
            return missing
        
        if intent == "recommendation":
            if not user_profile.get("health_goals"):
                missing.append("health_goals")
            if not user_profile.get("age"):
                missing.append("age")
        
        return missing

# Global instance
preprocessor = Preprocessor()

def preprocess_request(
    message: str,
    user_profile: Optional[Dict] = None,
    conversation_history: Optional[List] = None,
    context: Optional[Dict] = None
) -> Dict:
    """Wrapper function for compatibility"""
    return preprocessor.preprocess_request(
        message=message,
        user_profile=user_profile,
        conversation_history=conversation_history,
        context=context
    )