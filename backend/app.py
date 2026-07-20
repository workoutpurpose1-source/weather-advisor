"""
app.py
======
This is the heart of the backend. It's a Flask web server that:

  1. Serves the frontend (HTML/CSS/JS) so you can open one URL in your
     browser and everything works.
  2. Exposes an API endpoint (/api/advice) that the frontend's
     JavaScript calls when the user clicks "Get AI Advice".
  3. Talks to the OpenWeather API to get real weather data.
  4. Passes that weather data to ai_advisor.py to generate advice.
  5. Saves every completed search into the SQLite database.

How to run this file:
  1. cd backend
  2. pip install -r requirements.txt
  3. Copy .env.example to .env and add your API keys
  4. python app.py
  5. Open http://localhost:5000 in your browser
"""

import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import requests

import database
import ai_advisor

# Load variables from the .env file (like OPENWEATHER_API_KEY) into
# the environment so os.getenv() can find them.
load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"

# -------------------------------------------------------------------
# FRONTEND_FOLDER points Flask at our ../frontend directory so it can
# serve index.html, style.css, and script.js directly. This means we
# don't need a separate frontend server -- one Flask app does both jobs.
# -------------------------------------------------------------------
FRONTEND_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")

app = Flask(__name__, static_folder=FRONTEND_FOLDER, static_url_path="")
CORS(app)  # Allows the frontend JS to call this API without being blocked by the browser

# Make sure the database + table exist before the app starts accepting requests
database.init_db()


# ---------------------------------------------------------------------------
# ROUTE: Serve the homepage
# ---------------------------------------------------------------------------
@app.route("/")
def serve_index():
    """Sends index.html to the browser when someone visits http://localhost:5000/"""
    return send_from_directory(FRONTEND_FOLDER, "index.html")


# ---------------------------------------------------------------------------
# ROUTE: Get AI weather advice (the main feature)
# ---------------------------------------------------------------------------
@app.route("/api/advice", methods=["POST"])
def get_advice():
    """
    Expects a JSON body like:
        {
          "name": "Sarthak",
          "city": "Goa",
          "date": "2026-07-20",
          "time": "16:00",
          "activity": "Beach"
        }

    Returns a JSON response containing weather data + AI advice, or
    an error message with an appropriate HTTP status code.
    """
    data = request.get_json(silent=True) or {}

    # --- Step 1: Validate input ---
    name = data.get("name", "").strip()
    city = data.get("city", "").strip()
    date = data.get("date", "").strip()
    time = data.get("time", "").strip()
    activity = data.get("activity", "").strip()

    if not all([name, city, date, time, activity]):
        return jsonify({"error": "All fields (name, city, date, time, activity) are required."}), 400

    if not OPENWEATHER_API_KEY or OPENWEATHER_API_KEY == "your_openweather_api_key_here":
        return jsonify({
            "error": "OpenWeather API key is missing. Add it to backend/.env as OPENWEATHER_API_KEY."
        }), 500

    # --- Step 2: Fetch live weather data from OpenWeather ---
    try:
        weather_response = requests.get(
            OPENWEATHER_URL,
            params={
                "q": city,
                "appid": OPENWEATHER_API_KEY,
                "units": "metric",  # gives us Celsius instead of Kelvin
            },
            timeout=10,
        )
    except requests.exceptions.RequestException:
        return jsonify({"error": "Could not reach the weather service. Check your internet connection."}), 502

    if weather_response.status_code == 404:
        return jsonify({"error": f"City '{city}' not found. Please check the spelling."}), 404
    if weather_response.status_code != 200:
        return jsonify({"error": "Failed to fetch weather data. Please try again."}), 502

    weather_json = weather_response.json()

    # Extract just the fields we care about into a clean dictionary
    weather = {
        "temperature": weather_json["main"]["temp"],
        "condition": weather_json["weather"][0]["description"],
        "humidity": weather_json["main"]["humidity"],
        "wind_speed": weather_json["wind"]["speed"],
    }

    # --- Step 3: Ask the AI advisor for personalized advice ---
    advice = ai_advisor.generate_ai_advice(weather, activity, name)

    # --- Step 4: Save this search into the database ---
    database.save_search(
        name=name, city=city, date=date, time=time, activity=activity,
        temperature=weather["temperature"], condition=weather["condition"],
        humidity=weather["humidity"], wind_speed=weather["wind_speed"],
        ai_advice=advice.get("summary", ""),
    )

    # --- Step 5: Send everything back to the frontend ---
    return jsonify({
        "weather": weather,
        "advice": advice,
        "city": city,
        "name": name,
    })


# ---------------------------------------------------------------------------
# ROUTE: Get search history (optional, for a "recent searches" feature)
# ---------------------------------------------------------------------------
@app.route("/api/history", methods=["GET"])
def get_history():
    history = database.get_history(limit=10)
    return jsonify(history)


# ---------------------------------------------------------------------------
# Entry point: run the Flask development server
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # debug=True auto-reloads the server when you edit code, and shows
    # detailed error pages -- great for learning, turn off in production.
    app.run(debug=True, port=5000)
