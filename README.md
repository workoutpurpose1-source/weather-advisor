# AI Weather Advisor

A full-stack web app that gives you personalized, AI-generated advice
(clothing, umbrella, best time, safety tips) for any activity, based on
real weather data for your chosen city and date.

---

## 1. Folder structure

```
weather-advisor/
├── backend/
│   ├── app.py              Flask server + API routes
│   ├── ai_advisor.py       Generates AI advice (Gemini or rule-based fallback)
│   ├── database.py         SQLite table setup + save/read functions
│   ├── requirements.txt    Python packages needed
│   └── .env.example        Template for your secret API keys
└── frontend/
    ├── index.html           Page structure (form + results)
    ├── css/style.css        All visual styling & animations
    └── js/script.js         Talks to backend, updates the page
```

## 2. How the pieces connect

```
Browser (index.html + script.js)
        │  user fills form, clicks "Get AI Advice"
        ▼
fetch POST /api/advice  ──────────────►  Flask (app.py)
                                            │
                                            ├─► OpenWeather API (real weather)
                                            ├─► ai_advisor.py (Gemini or fallback logic)
                                            └─► database.py (saves the search)
        ◄───────────────────────────────  JSON response
        ▼
script.js fills in the result cards on the page
```

## 3. Setup instructions

### Step 1 — Install Python dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Step 2 — Add your API keys
```bash
cp .env.example .env
```
Then open `.env` and fill in:
- **OPENWEATHER_API_KEY** (required) — free key from https://openweathermap.org/api
- **GEMINI_API_KEY** (optional) — free key from https://aistudio.google.com/app/apikey
  - If you skip this, the app automatically uses a built-in rule-based
    advisor instead, so the app still works fully without it.

### Step 3 — Run the server
```bash
python app.py
```

### Step 4 — Open the app
Go to **http://localhost:5000** in your browser. The Flask server serves
both the API and the frontend, so this one URL is all you need.

---

## 4. File-by-file explanation

### `backend/app.py`
The main server. Defines:
- `GET /` → serves `index.html`
- `POST /api/advice` → the core feature: validates the form data, calls
  OpenWeather, calls the AI advisor, saves to the database, and returns
  a combined JSON response.
- `GET /api/history` → returns your last 10 searches (for future use,
  like a "recent searches" list).

### `backend/database.py`
Everything SQLite-related, isolated into one file:
- `init_db()` creates `weather.db` and a `searches` table if they don't exist.
- `save_search(...)` inserts one row per completed search.
- `get_history()` reads back the most recent rows.

### `backend/ai_advisor.py`
Turns raw numbers into advice:
- `generate_ai_advice()` is the entry point — tries Gemini first (if a
  key is configured), and automatically falls back to a rule-based
  advisor (plain if/else logic) if Gemini isn't set up or fails.
- This guarantees your app **never crashes** just because an AI key is missing.

### `frontend/index.html`
The page skeleton: navbar, hero banner, the input form (name, city, date,
time, activity), a loading spinner, and empty "result card" placeholders
that JavaScript fills in after the API responds.

### `frontend/css/style.css`
All the visual design: color variables at the top (easy to re-theme),
card shadows/hover effects, the loading spinner animation, a fade-in
animation for results, and `@media` rules at the bottom that rearrange
the grid into a single column on phones.

### `frontend/js/script.js`
The glue between the form and the backend:
1. Listens for form submit.
2. Sends a `fetch()` POST request with the form data to `/api/advice`.
3. Shows/hides the spinner and error box appropriately.
4. On success, writes the weather numbers and AI advice text into the
   matching HTML elements by their `id`.

---

## 5. Notes for beginners

- **Why Flask serves the frontend too:** it avoids CORS headaches and
  keeps deployment simple (one server, one port). CORS is still enabled
  in case you later split them into two separate servers.
- **Why the AI has a fallback:** relying on a single external service
  is risky — keys expire, quotas run out, networks fail. The fallback
  advisor means your demo always works.
- **The SQLite file (`weather.db`)** is created automatically the first
  time you run `app.py` — you don't need to create it manually.
