# backend/services/postprocess.py

import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime

class Postprocessor:
    """Class for post-processing LLM responses"""
    
    def __init__(self):
        # Static rules for supplement timing
        self.timing_rules = {
            # Morning supplements
            "vitamin d": "morning",
            "vitamin d3": "morning",
            "vitamin b12": "morning",
            "vitamin b complex": "morning",
            "vitamin b1": "morning",
            "vitamin b2": "morning",
            "vitamin b3": "morning",
            "vitamin b5": "morning",
            "vitamin b6": "morning",
            "vitamin b7": "morning",
            "vitamin b9": "morning",
            "vitamin c": "morning",
            "iron": "morning",
            "coq10": "morning",
            "ashwagandha": "morning",
            "rhodiola": "morning",
            "green tea extract": "morning",
            "caffeine": "morning",
            
            # Dinner supplements
            "vitamin k2": "dinner",
            "vitamin k": "dinner",
            "calcium": "dinner",
            "magnesium glycinate": "dinner",
            "digestive enzymes": "dinner",
            "probiotics": "dinner",
            "turmeric": "dinner",
            "curcumin": "dinner",
            "omega 3": "dinner",
            "fish oil": "dinner",
            "zinc": "dinner",
            "selenium": "dinner",
            "chromium": "dinner",
            "alpha lipoic acid": "dinner",
            "milk thistle": "dinner",
            "resveratrol": "dinner",
            
            # Evening supplements
            "magnesium": "evening",
            "magnesium citrate": "evening",
            "magnesium oxide": "evening",
            "magnesium l threonate": "evening",
            "melatonin": "evening",
            "gaba": "evening",
            "l theanine": "evening",
            "5 htp": "evening",
            "valerian root": "evening",
            "chamomile": "evening",
            "passion flower": "evening",
            "glycine": "evening",
            "zma": "evening",
            "ashwagandha evening": "evening",
            "reishi mushroom": "evening",
            "holy basil": "evening"
        }
        
        # Default dosages by supplement
        self.default_dosages = {
            "vitamin d": "1000-2000 IU",
            "vitamin d3": "1000-4000 IU",
            "vitamin c": "500-1000 mg",
            "vitamin b12": "1000-2000 mcg",
            "magnesium": "200-400 mg",
            "zinc": "15-30 mg",
            "iron": "18-27 mg",
            "calcium": "500-600 mg",
            "omega 3": "1000-2000 mg",
            "coq10": "100-200 mg",
            "probiotics": "10-50 billion CFU",
            "melatonin": "0.5-5 mg"
        }
        
        # Conflict rules
        self.conflict_rules = [
            {
                "supplements": ["calcium", "iron"],
                "severity": "high",
                "message": "Calcium and iron should not be taken together as calcium inhibits iron absorption. Take them 2-3 hours apart.",
                "recommendation": "Take iron in the morning on an empty stomach and calcium with dinner."
            },
            {
                "supplements": ["zinc", "copper"],
                "severity": "medium",
                "message": "Long-term high-dose zinc can deplete copper levels. Consider a zinc-copper balanced supplement or take them separately.",
                "recommendation": "If taking zinc long-term, supplement with 1-2 mg copper or use a balanced formula."
            },
            {
                "supplements": ["iron", "coffee"],
                "severity": "medium",
                "message": "Coffee and tea significantly reduce iron absorption.",
                "recommendation": "Take iron 1 hour before or 2 hours after consuming coffee or tea."
            },
            {
                "supplements": ["calcium", "thyroid_medication"],
                "severity": "high",
                "message": "Calcium supplements can interfere with thyroid medication absorption.",
                "recommendation": "Take thyroid medication 4 hours apart from calcium supplements."
            },
            {
                "supplements": ["vitamin k", "warfarin"],
                "severity": "critical",
                "message": "Vitamin K can interfere with warfarin (blood thinner) effectiveness.",
                "recommendation": "Consult your doctor before taking vitamin K supplements. Maintain consistent vitamin K intake from food."
            },
            {
                "supplements": ["magnesium", "antibiotics"],
                "severity": "high",
                "message": "Magnesium can bind to certain antibiotics, reducing absorption.",
                "recommendation": "Take magnesium 2-4 hours apart from antibiotics."
            },
            {
                "supplements": ["iron", "zinc"],
                "severity": "medium",
                "message": "High doses of iron and zinc can compete for absorption.",
                "recommendation": "Take iron and zinc at different times of the day."
            }
        ]
    
    def postprocess_recommendations(
        self,
        llm_response: Any,
        user_profile: Optional[Dict] = None
    ) -> Dict:
        """
        Post-process LLM response into structured format
        
        Args:
            llm_response: Response from LLM (string or dict)
            user_profile: User profile for personalization
        
        Returns:
            Structured response with recommendations
        """
        # 1. Parse LLM response
        parsed_response = self._parse_llm_response(llm_response)
        
        # 2. Process recommendations
        processed_recommendations = []
        for rec in parsed_response.get("recommendations", []):
            processed_rec = self._apply_timing_rules(rec)
            processed_rec = self._add_default_dosage(processed_rec)
            processed_rec = self._normalize_priority(processed_rec)
            processed_recommendations.append(processed_rec)
        
        # 3. Check for conflicts
        conflicts = self._check_conflicts(processed_recommendations, user_profile)
        
        # 4. Optimize schedule
        optimized_schedule = self._optimize_schedule(processed_recommendations)
        
        # 5. Generate warnings
        warnings = self._generate_warnings(
            recommendations=processed_recommendations,
            user_profile=user_profile,
            conflicts=conflicts
        )
        
        # 6. Build final response
        return {
            "message": parsed_response.get("message", self._generate_default_message(processed_recommendations)),
            "recommendations": processed_recommendations,
            "schedule": optimized_schedule,
            "warnings": warnings,
            "questions": parsed_response.get("questions", []),
            "disclaimer": parsed_response.get("disclaimer", self._get_standard_disclaimer()),
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_recommendations": len(processed_recommendations),
                "has_conflicts": len(conflicts) > 0,
                "confidence": parsed_response.get("confidence", 0.85)
            }
        }
    
    def _parse_llm_response(self, response: Any) -> Dict:
        """Parse LLM response, extracting JSON"""
        
        # If response is already a dict
        if isinstance(response, dict):
            return response
        
        # If response is a string
        if isinstance(response, str):
            # Try to find JSON in the text
            json_patterns = [
                r'```json\s*(\{.*?\})\s*```',  # JSON in code block
                r'```\s*(\{.*?\})\s*```',       # Code block without json specifier
                r'(\{.*\})',                    # Any JSON-like structure
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, response, re.DOTALL)
                for match in matches:
                    try:
                        parsed = json.loads(match)
                        return parsed
                    except json.JSONDecodeError:
                        continue
            
            # If no JSON found, create a simple response
            return {
                "message": response.strip(),
                "recommendations": []
            }
        
        # Fallback for other types
        return {
            "message": str(response),
            "recommendations": []
        }
    
    def _apply_timing_rules(self, recommendation: Dict) -> Dict:
        """Apply static timing rules to recommendation"""
        vitamin_name = recommendation.get("vitamin", "").lower().strip()
        
        # Check exact match
        if vitamin_name in self.timing_rules:
            recommendation["time"] = self.timing_rules[vitamin_name]
        else:
            # Check partial match
            for rule_vitamin, time in self.timing_rules.items():
                if rule_vitamin in vitamin_name or vitamin_name in rule_vitamin:
                    recommendation["time"] = time
                    break
        
        # Default to morning if no rule matches
        if "time" not in recommendation:
            recommendation["time"] = "morning"
        
        # Validate time value
        if recommendation["time"] not in ["morning", "dinner", "evening"]:
            recommendation["time"] = "morning"
        
        return recommendation
    
    def _add_default_dosage(self, recommendation: Dict) -> Dict:
        """Add default dosage if not provided"""
        if "dosage" not in recommendation or not recommendation["dosage"]:
            vitamin_name = recommendation.get("vitamin", "").lower()
            
            # Check exact match
            if vitamin_name in self.default_dosages:
                recommendation["dosage"] = self.default_dosages[vitamin_name]
            else:
                # Check partial match
                for rule_vitamin, dosage in self.default_dosages.items():
                    if rule_vitamin in vitamin_name:
                        recommendation["dosage"] = dosage
                        break
        
        return recommendation
    
    def _normalize_priority(self, recommendation: Dict) -> Dict:
        """Normalize priority field"""
        if "priority" not in recommendation:
            recommendation["priority"] = "medium"
        
        priority = recommendation["priority"].lower()
        if priority not in ["high", "medium", "low"]:
            recommendation["priority"] = "medium"
        
        return recommendation
    
    def _check_conflicts(self, recommendations: List[Dict], user_profile: Optional[Dict]) -> List[Dict]:
        """Check for conflicts between recommendations and user profile"""
        conflicts = []
        
        # Get set of recommended supplements
        recommended_set = {r.get("vitamin", "").lower() for r in recommendations}
        
        # Check supplement interactions
        for rule in self.conflict_rules:
            supplements_in_rule = set(rule["supplements"])
            if supplements_in_rule.issubset(recommended_set):
                conflicts.append({
                    "type": "interaction",
                    "severity": rule["severity"],
                    "supplements": list(supplements_in_rule),
                    "message": rule["message"],
                    "recommendation": rule["recommendation"]
                })
        
        # Check user profile conditions
        if user_profile:
            # Check allergies
            allergies = [a.lower() for a in user_profile.get("allergies", [])]
            for rec in recommendations:
                vitamin = rec.get("vitamin", "").lower()
                for allergy in allergies:
                    if allergy in vitamin or vitamin in allergy:
                        conflicts.append({
                            "type": "allergy",
                            "severity": "high",
                            "supplement": rec.get("vitamin"),
                            "allergy": allergy,
                            "message": f"This supplement may contain {allergy} or be contraindicated with {allergy} allergy.",
                            "recommendation": "Avoid this supplement. Consult your healthcare provider for alternatives."
                        })
            
            # Check pregnancy
            if user_profile.get("pregnancy_status") == "pregnant":
                for rec in recommendations:
                    vitamin = rec.get("vitamin", "").lower()
                    if "vitamin a" in vitamin or "retinol" in vitamin:
                        conflicts.append({
                            "type": "pregnancy",
                            "severity": "critical",
                            "supplement": rec.get("vitamin"),
                            "message": "High-dose vitamin A can cause birth defects.",
                            "recommendation": "Avoid high-dose vitamin A during pregnancy. Use prenatal vitamins only."
                        })
        
        return conflicts
    
    def _optimize_schedule(self, recommendations: List[Dict]) -> Dict:
        """Optimize daily schedule from recommendations"""
        schedule = {
            "morning": [],
            "dinner": [],
            "evening": []
        }
        
        for rec in recommendations:
            time_slot = rec.get("time", "morning")
            schedule[time_slot].append({
                "name": rec.get("vitamin", ""),
                "dosage": rec.get("dosage", ""),
                "priority": rec.get("priority", "medium"),
                "notes": rec.get("notes", "")
            })
        
        return schedule
    
    def _generate_warnings(
        self,
        recommendations: List[Dict],
        user_profile: Optional[Dict],
        conflicts: List[Dict]
    ) -> List[str]:
        """Generate warning messages"""
        warnings = []
        
        # Add conflict warnings
        for conflict in conflicts:
            if conflict["severity"] in ["critical", "high"]:
                warnings.append(f"⚠️ {conflict['message']} {conflict.get('recommendation', '')}")
        
        # Add general warnings for high priority supplements
        high_priority_count = sum(1 for r in recommendations if r.get("priority") == "high")
        if high_priority_count > 3:
            warnings.append("⚠️ Starting with multiple high-priority supplements simultaneously may make it difficult to identify which works best. Consider introducing them one at a time.")
        
        # Add warnings about medication interactions
        if user_profile and user_profile.get("medications"):
            warnings.append("⚠️ You mentioned taking medications. Always consult your healthcare provider before adding supplements to ensure no interactions.")
        
        # Add warning about starting low and slow
        if recommendations:
            warnings.append("💡 Start with lower doses to assess tolerance, then gradually increase as needed.")
        
        # Add standard disclaimer
        warnings.append("📋 This information is for educational purposes only. Not medical advice.")
        
        return warnings
    
    def _generate_default_message(self, recommendations: List[Dict]) -> str:
        """Generate default message if none provided"""
        if not recommendations:
            return "Based on your query, I don't have specific supplement recommendations at this time. Could you provide more information about your health goals or concerns?"
        
        count = len(recommendations)
        return f"Based on your health profile and goals, I recommend considering {count} supplement(s). Please review the schedule below for timing and dosage information."
    
    def _get_standard_disclaimer(self) -> str:
        """Get standard medical disclaimer"""
        return "This information is for educational purposes only and is not intended as medical advice. Always consult with a qualified healthcare provider before starting any new supplement regimen, especially if you are pregnant, nursing, taking medications, or have existing health conditions."

# Global instance
postprocessor = Postprocessor()

def postprocess_recommendations(
    llm_response: Any,
    user_profile: Optional[Dict] = None
) -> Dict:
    """Wrapper function for compatibility"""
    return postprocessor.postprocess_recommendations(llm_response, user_profile)