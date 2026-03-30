from typing import Dict, List, Optional

def build_response(
    recommendations: List[Dict],
    ai_message: str,
    user_profile: Optional[Dict] = None
) -> Dict:
    """
    Build structured response from AI recommendations
    
    Args:
        recommendations: List of vitamin recommendations
        ai_message: Raw AI response message
        user_profile: User profile for personalization
        
    Returns:
        Structured response with schedule
    """
    # Initialize schedule
    schedule = {
        "morning": [],
        "dinner": [],
        "evening": []
    }
    
    # Process recommendations
    processed_recommendations = []
    for rec in recommendations:
        vitamin_name = rec.get("vitamin", "")
        time_of_day = rec.get("time", "morning")
        
        # Add to schedule
        if time_of_day in schedule:
            schedule[time_of_day].append(vitamin_name)
        
        # Prepare structured recommendation
        processed_recommendations.append({
            "vitamin": vitamin_name,
            "time": time_of_day,
            "dosage": rec.get("dosage"),
            "notes": rec.get("notes"),
            "priority": rec.get("priority", "medium")
        })
    
    # Personalize message if profile exists
    personalized_message = ai_message
    if user_profile and user_profile.get("health_goals"):
        goals = user_profile["health_goals"][:2]
        if goals:
            personalized_message = f"Враховуючи ваші цілі: {', '.join(goals)}.\n\n{ai_message}"
    
    return {
        "message": personalized_message,
        "recommendations": processed_recommendations,
        "schedule": schedule
    }