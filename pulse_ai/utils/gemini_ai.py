"""
gemini_ai.py
All Gemini API interactions for Pulse AI.
"""

import os
import json
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

try:
    import google.generativeai as genai
    _gemini_available = True
except ImportError:
    _gemini_available = False


def _get_model():
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key or not _gemini_available:
        return None
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-1.5-flash")


def _safe_call(prompt: str) -> str:
    """Call Gemini and return text, or a mock response if unavailable."""
    model = _get_model()
    if not model:
        return _mock_response(prompt)
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.warning(f"Gemini API error: {e}. Using mock data.")
        return _mock_response(prompt)


# ── Body Analysis ─────────────────────────────────────────────────────────────

def analyze_body_state(profile: dict) -> dict:
    """
    Given user profile, return a detailed body state analysis.
    Returns dict with: summary, bmi_category, nutrient_needs, health_flags
    """
    prompt = f"""
You are a certified nutritionist and fitness coach. Analyze this user's body state.

USER PROFILE:
- Name: {profile.get('name', 'User')}
- Age: {profile.get('age')} years
- Gender: {profile.get('gender')}
- Weight: {profile.get('weight_kg')} kg
- Height: {profile.get('height_cm')} cm
- Activity Level: {profile.get('activity_level')}
- Fitness Goal: {profile.get('goal')}
- Dietary Preference: {profile.get('diet_type')}
- Health Conditions: {profile.get('health_conditions', 'None')}
- Sleep Hours: {profile.get('sleep_hours')} hours/night

Calculate BMI and respond ONLY in this exact JSON format (no markdown, no code blocks):
{{
  "bmi": 22.5,
  "bmi_category": "Normal weight",
  "summary": "2-3 sentence friendly summary of their current body state",
  "body_fat_estimate": "18-22%",
  "tdee_calories": 2200,
  "health_flags": ["flag1", "flag2"],
  "nutrient_priorities": {{
    "Protein": {{ "daily_grams": 140, "priority": 95, "reason": "why" }},
    "Iron": {{ "daily_mg": 18, "priority": 70, "reason": "why" }},
    "Vitamin D": {{ "daily_iu": 2000, "priority": 85, "reason": "why" }},
    "Vitamin C": {{ "daily_mg": 90, "priority": 60, "reason": "why" }},
    "Vitamin A": {{ "daily_mcg": 900, "priority": 55, "reason": "why" }},
    "Vitamin E": {{ "daily_mg": 15, "priority": 50, "reason": "why" }},
    "Calcium": {{ "daily_mg": 1000, "priority": 65, "reason": "why" }},
    "Magnesium": {{ "daily_mg": 400, "priority": 60, "reason": "why" }}
  }},
  "motivational_insight": "One personal, encouraging sentence for this specific person"
}}
"""
    raw = _safe_call(prompt)
    return _parse_json(raw, _default_analysis(profile))


# ── Diet Plan ─────────────────────────────────────────────────────────────────

def generate_diet_plan(profile: dict, analysis: dict) -> dict:
    """Generate a weekly personalized meal plan with food recommendations."""
    prompt = f"""
You are a world-class nutritionist. Create a personalized weekly meal plan.

USER: {profile.get('name')}, {profile.get('age')}y, {profile.get('weight_kg')}kg
GOAL: {profile.get('goal')}
DIET TYPE: {profile.get('diet_type')}
TDEE: {analysis.get('tdee_calories', 2000)} calories/day
TOP NUTRIENT NEED: Protein {analysis.get('nutrient_priorities', {}).get('Protein', {}).get('daily_grams', 120)}g/day

Respond ONLY in this exact JSON format (no markdown):
{{
  "daily_calories_target": 2000,
  "macro_split": {{ "protein_pct": 30, "carbs_pct": 45, "fat_pct": 25 }},
  "key_foods": [
    {{
      "food": "Boiled Eggs",
      "why": "High protein, B12",
      "servings": "3 eggs/day",
      "nutrients": ["Protein: 18g", "Vitamin B12", "Healthy fats"],
      "emoji": "🥚"
    }},
    {{
      "food": "Salmon",
      "why": "Omega-3, Vitamin D",
      "servings": "150g, 3x/week",
      "nutrients": ["Protein: 30g", "Vitamin D", "Omega-3"],
      "emoji": "🐟"
    }},
    {{
      "food": "Spinach",
      "why": "Iron, Vitamin C",
      "servings": "1 cup daily",
      "nutrients": ["Iron: 6mg", "Vitamin C", "Folate"],
      "emoji": "🥬"
    }},
    {{
      "food": "Greek Yogurt",
      "why": "Calcium, Probiotics",
      "servings": "200g/day",
      "nutrients": ["Protein: 17g", "Calcium", "Probiotics"],
      "emoji": "🫙"
    }},
    {{
      "food": "Sweet Potato",
      "why": "Vitamin A, Carbs",
      "servings": "1 medium/day",
      "nutrients": ["Vitamin A", "Complex carbs", "Potassium"],
      "emoji": "🍠"
    }},
    {{
      "food": "Almonds",
      "why": "Vitamin E, Magnesium",
      "servings": "30g/day",
      "nutrients": ["Vitamin E: 7mg", "Magnesium", "Healthy fats"],
      "emoji": "🌰"
    }}
  ],
  "meal_schedule": {{
    "breakfast": "Sample breakfast matching their diet type",
    "mid_morning": "Snack suggestion",
    "lunch": "Sample lunch",
    "evening_snack": "Pre-workout snack if applicable",
    "dinner": "Sample dinner"
  }},
  "weekly_tip": "One actionable nutrition tip for this person's goal"
}}
"""
    raw = _safe_call(prompt)
    return _parse_json(raw, _default_diet_plan())


# ── Exercise Plan ─────────────────────────────────────────────────────────────

def generate_exercise_plan(profile: dict, analysis: dict, free_start: str, free_end: str) -> dict:
    """
    Generate a 7-day exercise plan that fits within the user's free time window.
    free_start / free_end are strings like "3:00 PM"
    """
    prompt = f"""
You are an elite personal trainer. Create a 7-day exercise plan.

USER PROFILE:
- Goal: {profile.get('goal')}
- Activity Level: {profile.get('activity_level')}
- Age: {profile.get('age')}, Weight: {profile.get('weight_kg')}kg
- Health Conditions: {profile.get('health_conditions', 'None')}
- FREE TIME: {free_start} to {free_end} (CRITICAL: all exercises must fit within this window)
- Max workout duration: 60 minutes (never exceed this)

RULES:
1. Never schedule more than 60 minutes of exercise per day
2. All exercises must be doable in the free time window: {free_start} to {free_end}
3. Include rest days appropriately
4. Each exercise needs: name, sets, reps/duration, rest_seconds, muscle_group

Respond ONLY in this exact JSON (no markdown):
{{
  "total_minutes_per_day": 45,
  "intensity": "Moderate",
  "week_plan": {{
    "Day 1": {{
      "day_name": "Monday",
      "focus": "Full Body",
      "is_rest": false,
      "exercises": [
        {{
          "name": "Push-ups",
          "sets": 3,
          "reps": "12",
          "rest_seconds": 60,
          "muscle_group": "Chest/Triceps",
          "duration_minutes": 5
        }}
      ],
      "total_duration_minutes": 45,
      "warmup": "5 min light jog/jumping jacks",
      "cooldown": "5 min stretching"
    }},
    "Day 2": {{}},
    "Day 3": {{}},
    "Day 4": {{}},
    "Day 5": {{}},
    "Day 6": {{}},
    "Day 7": {{ "day_name": "Sunday", "focus": "Rest", "is_rest": true, "exercises": [] }}
  }},
  "weekly_tip": "One motivational tip for this week"
}}
"""
    raw = _safe_call(prompt)
    return _parse_json(raw, _default_exercise_plan(free_start, free_end))


# ── Weekly Review & Comparison ────────────────────────────────────────────────

def generate_weekly_review(current_profile: dict, previous_snapshot: dict, week_number: int) -> dict:
    """Compare current week vs previous, generate progress review."""
    prompt = f"""
You are a supportive fitness coach doing a weekly progress review.

WEEK {week_number} (Current):
- Weight: {current_profile.get('weight_kg')} kg
- Goal: {current_profile.get('goal')}
- Activity Level: {current_profile.get('activity_level')}
- Sleep: {current_profile.get('sleep_hours')} hrs

WEEK {week_number - 1} (Previous):
- Weight: {previous_snapshot.get('profile', {}).get('weight_kg', 'N/A')} kg
- Goal: {previous_snapshot.get('profile', {}).get('goal', 'N/A')}

Respond ONLY in this exact JSON (no markdown):
{{
  "progress_status": "Improving / Plateau / Declining",
  "weight_change_kg": -0.5,
  "progress_message": "Warm, specific 2-sentence message about their progress this week",
  "what_worked": ["Achievement 1", "Achievement 2"],
  "what_to_improve": ["Focus area 1", "Focus area 2"],
  "next_week_adjustment": "What changes for next week's plan",
  "motivational_quote": "A short powerful quote for their journey"
}}
"""
    raw = _safe_call(prompt)
    return _parse_json(raw, _default_review())


# ── Gym Buddy Feedback ────────────────────────────────────────────────────────

def analyze_exercise_form(exercise: str, rep_count: int, feedback_flags: list) -> str:
    """Generate coaching feedback for exercise form."""
    prompt = f"""
You are a fitness coach analyzing {exercise} form.
Rep count so far: {rep_count}
Form issues detected: {', '.join(feedback_flags) if feedback_flags else 'None'}

Give exactly 2-3 sentences of direct, encouraging coaching feedback.
If form issues exist, explain how to fix them. Keep it simple and motivating.
"""
    return _safe_call(prompt)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_json(text: str, default: dict) -> dict:
    """Safely parse JSON from Gemini response."""
    try:
        text = text.strip()
        # Remove markdown code blocks if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except Exception:
        return default


def _mock_response(prompt: str) -> str:
    """Return mock data when Gemini is unavailable."""
    if "analyze" in prompt.lower() or "body state" in prompt.lower():
        return json.dumps(_default_analysis({}))
    if "diet" in prompt.lower() or "meal" in prompt.lower():
        return json.dumps(_default_diet_plan())
    if "exercise" in prompt.lower() or "workout" in prompt.lower():
        return json.dumps(_default_exercise_plan("6:00 AM", "7:00 AM"))
    if "review" in prompt.lower():
        return json.dumps(_default_review())
    return "Great work! Keep going."


def _default_analysis(profile: dict) -> dict:
    weight = profile.get("weight_kg", 70)
    height = profile.get("height_cm", 170)
    bmi = round(weight / ((height / 100) ** 2), 1) if height else 22.0
    return {
        "bmi": bmi,
        "bmi_category": "Normal weight",
        "summary": "Your body is in a good baseline state. With consistent effort toward your goal, you will see meaningful changes within 4-6 weeks.",
        "body_fat_estimate": "18-22%",
        "tdee_calories": 2100,
        "health_flags": ["Stay hydrated", "Prioritize sleep"],
        "nutrient_priorities": {
            "Protein": {"daily_grams": 140, "priority": 95, "reason": "Essential for muscle repair and growth"},
            "Vitamin D": {"daily_iu": 2000, "priority": 85, "reason": "Supports bone density and immunity"},
            "Iron": {"daily_mg": 18, "priority": 70, "reason": "Prevents fatigue and supports oxygen transport"},
            "Calcium": {"daily_mg": 1000, "priority": 65, "reason": "Bone health and muscle function"},
            "Magnesium": {"daily_mg": 400, "priority": 60, "reason": "Sleep quality and muscle recovery"},
            "Vitamin C": {"daily_mg": 90, "priority": 60, "reason": "Immunity and collagen synthesis"},
            "Vitamin A": {"daily_mcg": 900, "priority": 55, "reason": "Vision and immune function"},
            "Vitamin E": {"daily_mg": 15, "priority": 50, "reason": "Antioxidant protection"}
        },
        "motivational_insight": "You are one consistent week away from feeling a real difference."
    }


def _default_diet_plan() -> dict:
    return {
        "daily_calories_target": 2100,
        "macro_split": {"protein_pct": 30, "carbs_pct": 45, "fat_pct": 25},
        "key_foods": [
            {"food": "Boiled Eggs", "why": "Complete protein + B12", "servings": "3 eggs/day", "nutrients": ["Protein: 18g", "Vitamin B12", "Choline"], "emoji": "🥚"},
            {"food": "Salmon / Tuna", "why": "Omega-3 + Vitamin D", "servings": "150g, 3x/week", "nutrients": ["Protein: 30g", "Vitamin D", "Omega-3"], "emoji": "🐟"},
            {"food": "Spinach", "why": "Iron + Vitamin C", "servings": "1 cup daily", "nutrients": ["Iron: 6mg", "Vitamin C", "Folate"], "emoji": "🥬"},
            {"food": "Greek Yogurt", "why": "Calcium + Probiotics", "servings": "200g/day", "nutrients": ["Protein: 17g", "Calcium", "Probiotics"], "emoji": "🫙"},
            {"food": "Sweet Potato", "why": "Vitamin A + Energy", "servings": "1 medium/day", "nutrients": ["Vitamin A", "Complex carbs", "Potassium"], "emoji": "🍠"},
            {"food": "Almonds", "why": "Vitamin E + Magnesium", "servings": "30g/day", "nutrients": ["Vitamin E: 7mg", "Magnesium", "Healthy fats"], "emoji": "🌰"},
        ],
        "meal_schedule": {
            "breakfast": "3 boiled eggs + 1 slice whole wheat toast + 1 banana",
            "mid_morning": "Greek yogurt + handful of almonds",
            "lunch": "Grilled chicken / tofu + brown rice + spinach salad",
            "evening_snack": "Sweet potato + cottage cheese",
            "dinner": "Salmon / paneer + steamed vegetables + quinoa"
        },
        "weekly_tip": "Prep your meals on Sunday to stay consistent throughout the week."
    }


def _default_exercise_plan(free_start: str, free_end: str) -> dict:
    return {
        "total_minutes_per_day": 45,
        "intensity": "Moderate",
        "week_plan": {
            "Day 1": {
                "day_name": "Monday", "focus": "Upper Body", "is_rest": False,
                "warmup": "5 min jumping jacks", "cooldown": "5 min stretching",
                "total_duration_minutes": 40,
                "exercises": [
                    {"name": "Push-ups", "sets": 3, "reps": "12", "rest_seconds": 60, "muscle_group": "Chest", "duration_minutes": 8},
                    {"name": "Dumbbell Rows", "sets": 3, "reps": "10 each", "rest_seconds": 60, "muscle_group": "Back", "duration_minutes": 8},
                    {"name": "Shoulder Press", "sets": 3, "reps": "10", "rest_seconds": 60, "muscle_group": "Shoulders", "duration_minutes": 8},
                    {"name": "Plank", "sets": 3, "reps": "30 sec", "rest_seconds": 45, "muscle_group": "Core", "duration_minutes": 6},
                ]
            },
            "Day 2": {
                "day_name": "Tuesday", "focus": "Cardio", "is_rest": False,
                "warmup": "5 min walk", "cooldown": "5 min stretching",
                "total_duration_minutes": 40,
                "exercises": [
                    {"name": "Brisk Walk / Jog", "sets": 1, "reps": "20 min", "rest_seconds": 0, "muscle_group": "Cardio", "duration_minutes": 20},
                    {"name": "Jumping Jacks", "sets": 3, "reps": "30", "rest_seconds": 45, "muscle_group": "Full Body", "duration_minutes": 8},
                    {"name": "High Knees", "sets": 3, "reps": "30 sec", "rest_seconds": 45, "muscle_group": "Cardio", "duration_minutes": 7},
                ]
            },
            "Day 3": {
                "day_name": "Wednesday", "focus": "Rest / Light Stretch", "is_rest": True,
                "warmup": "", "cooldown": "",
                "total_duration_minutes": 0, "exercises": []
            },
            "Day 4": {
                "day_name": "Thursday", "focus": "Lower Body", "is_rest": False,
                "warmup": "5 min light jog", "cooldown": "5 min stretching",
                "total_duration_minutes": 45,
                "exercises": [
                    {"name": "Squats", "sets": 4, "reps": "15", "rest_seconds": 60, "muscle_group": "Quads/Glutes", "duration_minutes": 10},
                    {"name": "Lunges", "sets": 3, "reps": "12 each", "rest_seconds": 60, "muscle_group": "Legs", "duration_minutes": 8},
                    {"name": "Glute Bridges", "sets": 3, "reps": "15", "rest_seconds": 45, "muscle_group": "Glutes", "duration_minutes": 7},
                    {"name": "Calf Raises", "sets": 3, "reps": "20", "rest_seconds": 45, "muscle_group": "Calves", "duration_minutes": 5},
                ]
            },
            "Day 5": {
                "day_name": "Friday", "focus": "Full Body HIIT", "is_rest": False,
                "warmup": "5 min dynamic stretch", "cooldown": "5 min cool down",
                "total_duration_minutes": 40,
                "exercises": [
                    {"name": "Burpees", "sets": 3, "reps": "10", "rest_seconds": 60, "muscle_group": "Full Body", "duration_minutes": 8},
                    {"name": "Mountain Climbers", "sets": 3, "reps": "30 sec", "rest_seconds": 45, "muscle_group": "Core/Cardio", "duration_minutes": 7},
                    {"name": "Jump Squats", "sets": 3, "reps": "12", "rest_seconds": 60, "muscle_group": "Legs/Power", "duration_minutes": 7},
                    {"name": "Push-up to T", "sets": 3, "reps": "8 each", "rest_seconds": 60, "muscle_group": "Chest/Core", "duration_minutes": 8},
                ]
            },
            "Day 6": {
                "day_name": "Saturday", "focus": "Core & Flexibility", "is_rest": False,
                "warmup": "5 min walk", "cooldown": "10 min yoga",
                "total_duration_minutes": 35,
                "exercises": [
                    {"name": "Plank Variations", "sets": 3, "reps": "45 sec", "rest_seconds": 45, "muscle_group": "Core", "duration_minutes": 8},
                    {"name": "Bicycle Crunches", "sets": 3, "reps": "20", "rest_seconds": 45, "muscle_group": "Abs", "duration_minutes": 7},
                    {"name": "Dead Bug", "sets": 3, "reps": "10 each", "rest_seconds": 45, "muscle_group": "Core", "duration_minutes": 7},
                ]
            },
            "Day 7": {
                "day_name": "Sunday", "focus": "Rest", "is_rest": True,
                "warmup": "", "cooldown": "",
                "total_duration_minutes": 0, "exercises": []
            },
        },
        "weekly_tip": "Consistency beats perfection. Show up every day, even on rest days, with intention."
    }


def _default_review() -> dict:
    return {
        "progress_status": "Improving",
        "weight_change_kg": -0.3,
        "progress_message": "You made solid progress this week! Your consistency is already showing in your energy levels and endurance.",
        "what_worked": ["Completed most workout sessions", "Improved hydration"],
        "what_to_improve": ["Sleep consistency", "Protein intake at breakfast"],
        "next_week_adjustment": "Increase workout intensity slightly and add a protein-rich breakfast.",
        "motivational_quote": "The body achieves what the mind believes."
    }
