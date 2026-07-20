"""
ai_advisor.py
=============
This file is responsible for turning raw weather numbers into
human-friendly, personalized advice.

It tries TWO approaches:
  1. If you've set a GEMINI_API_KEY in your .env file, it asks Google's
     Gemini AI model to write the advice (smarter, more natural language).
  2. If no key is set (or the API call fails for any reason), it falls
     back to a RULE-BASED advisor we wrote ourselves using simple
     if/else logic. This means the app ALWAYS works, even with zero
     API keys configured -- perfect for testing as a beginner.

Why split this into its own file?
  Same reason as database.py: separation of concerns. app.py doesn't
  need to know HOW advice is generated, only that it can call
  generate_ai_advice(...) and get a result back.
"""

import os
import requests

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
# This is Google's REST endpoint for the Gemini 2.0 Flash model (fast + free tier)
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent"
)


def generate_ai_advice(weather, activity, name):
    """
    Main entry point. Returns a dictionary with these keys:
        clothing_suggestion, umbrella_recommendation,
        best_time, safety_tips, summary

    'weather' is a dict like:
        {"temperature": 27.5, "condition": "light rain",
         "humidity": 80, "wind_speed": 4.2}
    """
    if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
        try:
            return _ask_gemini(weather, activity, name)
        except Exception as e:
            # If the AI call fails (bad key, no internet, quota, etc.)
            # we don't want the whole app to crash -- we just fall back.
            print(f"[ai_advisor] Gemini call failed, using fallback: {e}")
            return _rule_based_advice(weather, activity, name)
    else:
        return _rule_based_advice(weather, activity, name)


def _ask_gemini(weather, activity, name):
    """
    Sends the weather + activity details to Gemini and asks it to
    respond in a STRICT JSON format so we can easily display it on
    the frontend without messy text-parsing.
    """
    prompt = f"""
You are a friendly weather advisor AI. A user named {name} is planning
a "{activity}" activity. Here is the forecasted weather:

- Temperature: {weather['temperature']}°C
- Condition: {weather['condition']}
- Humidity: {weather['humidity']}%
- Wind speed: {weather['wind_speed']} m/s

Respond ONLY with a valid JSON object (no markdown, no backticks, no
extra text) with exactly these keys:
{{
  "clothing_suggestion": "short practical clothing advice",
  "umbrella_recommendation": "Yes/No plus one short reason",
  "best_time": "best time window for this activity given the weather",
  "safety_tips": "1-2 short, concrete safety tips",
  "summary": "one warm, encouraging sentence summarizing the advice"
}}
"""

    response = requests.post(
        f"{GEMINI_URL}?key={GEMINI_API_KEY}",
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()

    # Dig into Gemini's response structure to get the raw text it wrote
    text = data["candidates"][0]["content"]["parts"][0]["text"]

    # Clean up in case the model wraps the JSON in ```json ... ``` fences
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    import json
    parsed = json.loads(text)
    return parsed


def _rule_based_advice(weather, activity, name):
    """
    A simple, dependable, no-API-key-needed advisor.
    Uses plain if/else logic based on temperature, rain, wind, and humidity.
    This guarantees the app is always demoable, even offline from AI services.
    """
    temp = weather["temperature"]
    condition = weather["condition"].lower()
    humidity = weather["humidity"]
    wind = weather["wind_speed"]

    is_rainy = any(word in condition for word in ["rain", "drizzle", "storm", "thunder"])
    is_hot = temp >= 32
    is_cold = temp <= 15
    is_windy = wind >= 8

    # --- Clothing suggestion ---
    if is_cold:
        clothing = "Wear warm layers, a jacket, and closed shoes."
    elif is_hot:
        clothing = "Wear light, breathable cotton clothing and a hat for sun protection."
    else:
        clothing = "Comfortable light clothing should work well today."

    # --- Umbrella recommendation ---
    if is_rainy:
        umbrella = "Yes — rain is expected, carry an umbrella or raincoat."
    elif humidity >= 80:
        umbrella = "Maybe — humidity is high, a light umbrella is a safe bet."
    else:
        umbrella = "No — low chance of rain based on current conditions."

    # --- Best time for activity ---
    activity_lower = activity.lower()
    if is_hot and activity_lower in ["cricket", "beach", "picnic", "travel"]:
        best_time = "Early morning (before 10 AM) or evening (after 5 PM) to avoid peak heat."
    elif is_rainy:
        best_time = "Keep a flexible backup slot — weather may shift during the day."
    else:
        best_time = "Most of the day looks favorable for your activity."

    # --- Safety tips ---
    tips = []
    if is_hot:
        tips.append("Stay hydrated and avoid direct sun for long periods.")
    if is_windy:
        tips.append("Secure loose items — wind speeds are on the higher side.")
    if is_rainy:
        tips.append("Watch for slippery surfaces and possible waterlogging.")
    if not tips:
        tips.append("Conditions look generally safe — enjoy your activity!")
    safety_tips = " ".join(tips)

    # --- Overall summary ---
    summary = (
        f"Hi {name}, conditions for your {activity.lower()} look "
        f"{'a bit challenging' if (is_rainy or is_hot or is_windy) else 'quite pleasant'} "
        f"— plan accordingly and have a great time!"
    )

    return {
        "clothing_suggestion": clothing,
        "umbrella_recommendation": umbrella,
        "best_time": best_time,
        "safety_tips": safety_tips,
        "summary": summary,
    }
