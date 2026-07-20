/* ==========================================================================
   script.js
   ==========================================================================
   This file makes the page INTERACTIVE. It:
     1. Listens for the form submit event.
     2. Sends the form data to our Flask backend (/api/advice).
     3. Shows a loading spinner while waiting.
     4. Displays the returned weather + AI advice on the page.
     5. Shows an error message if something goes wrong.
   ========================================================================== */

// Grab references to all the HTML elements we'll need to read from or update.
const form = document.getElementById("weatherForm");
const submitBtn = document.getElementById("submitBtn");
const loadingEl = document.getElementById("loading");
const resultsEl = document.getElementById("results");
const errorBox = document.getElementById("errorBox");

// Because our Flask server serves this frontend too, we can use a relative
// URL. If you ever host the frontend separately, change this to the full
// backend URL, e.g. "http://localhost:5000/api/advice".
const API_URL = "/api/advice";

// "submit" fires when the user clicks the button OR presses Enter in the form.
form.addEventListener("submit", async function (event) {
  event.preventDefault(); // Stops the browser's default page-reload behavior

  // ---- Step 1: Collect form values into a plain JS object ----
  const formData = {
    name: document.getElementById("name").value.trim(),
    city: document.getElementById("city").value.trim(),
    date: document.getElementById("date").value,
    time: document.getElementById("time").value,
    activity: document.getElementById("activity").value,
  };

  // ---- Step 2: Reset UI state before making the request ----
  hideError();
  resultsEl.classList.add("hidden");
  loadingEl.classList.remove("hidden");
  submitBtn.disabled = true;

  try {
    // ---- Step 3: Call our Flask backend ----
    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(formData),
    });

    const data = await response.json();

    if (!response.ok) {
      // The backend sends { "error": "..." } on failure
      throw new Error(data.error || "Something went wrong. Please try again.");
    }

    // ---- Step 4: Render the results on the page ----
    renderResults(data);

  } catch (err) {
    showError(err.message);
  } finally {
    // This always runs, whether it succeeded or failed
    loadingEl.classList.add("hidden");
    submitBtn.disabled = false;
  }
});

/**
 * Fills in all the result cards with data returned from the backend,
 * then reveals the results section.
 */
function renderResults(data) {
  const { weather, advice } = data;

  document.getElementById("statTemp").textContent = `${weather.temperature}°C`;
  document.getElementById("statCondition").textContent = capitalize(weather.condition);
  document.getElementById("statHumidity").textContent = `${weather.humidity}%`;
  document.getElementById("statWind").textContent = `${weather.wind_speed} m/s`;

  document.getElementById("adviceClothing").textContent = advice.clothing_suggestion;
  document.getElementById("adviceUmbrella").textContent = advice.umbrella_recommendation;
  document.getElementById("adviceBestTime").textContent = advice.best_time;
  document.getElementById("adviceSafety").textContent = advice.safety_tips;
  document.getElementById("adviceSummary").textContent = advice.summary;

  resultsEl.classList.remove("hidden");
  // Smoothly scroll the user down to see their results
  resultsEl.scrollIntoView({ behavior: "smooth", block: "start" });
}

function showError(message) {
  errorBox.textContent = message;
  errorBox.classList.remove("hidden");
}

function hideError() {
  errorBox.classList.add("hidden");
  errorBox.textContent = "";
}

/** Capitalizes the first letter of each word, e.g. "light rain" -> "Light Rain" */
function capitalize(str) {
  return str.replace(/\b\w/g, (char) => char.toUpperCase());
}
