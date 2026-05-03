```markdown
# 🍽️ The Recipe to Our Voice (Zaika Recipes)

> **A stealth-mode AI companion for women's safety that hides in plain sight as a recipe app to bypass device confiscation.**

"The Recipe to Our Voice" is an autonomous AI agent disguised as a daily Pakistani recipe application. When unlocked via a secret phrase, it transforms into a localized, empathetic AI companion ("Aapa") capable of detecting emotional distress, searching live local laws, logging cryptographically-sealed evidence, and triggering real-world SOS alerts—all without leaving a trace.

Built for the **Hackathon 2026** to combat domestic violence and street harassment through accessible, frugal, and invisible technology.

---

## ✨ Key Features

*   **Stealth UI (Decoy App):** Opens as "Zaika Recipes." The AI chat is only revealed when the user types a secret trigger phrase (e.g., `help me cook`) into the search bar.
*   **Zero-RAG Agentic AI:** Uses **Groq (LLaMA 3)** and function-calling to actively scrape the live web (DuckDuckGo) and maps (OpenStreetMap) rather than relying on a static database.
*   **Bilingual Empathy Engine:** The AI speaks naturally in both **English** and **Urdu**, acting as a warm, trauma-informed elder sister ("Aapa"). 
*   **Cryptographic Evidence Vault:** Automatically hashes incident reports using SHA-256 and saves them to a secure Supabase database, creating court-admissible evidence.
*   **Emergency SOS Routing:** Instantly dispatches emergency emails to a trusted contact with the user's location.
*   **Silent Analytics Logger:** Automatically detects keywords and silently logs anonymized abuse data (Category, Zone, Frequency) to build city-wide heatmaps for policymakers.
*   **Persistent Long-Term Memory:** Summarizes chat history every 10 messages and stores it securely, so the user never has to repeat their trauma.

---

## 🛠️ Tech Stack

*   **Frontend/UI:** [Streamlit](https://streamlit.io/) (Python)
*   **LLM Engine:** [Groq API](https://groq.com/) (`llama-3.1-8b-instant` & `llama-3.3-70b-versatile`)
*   **Database & Auth:** [Supabase](https://supabase.com/) (PostgreSQL)
*   **Live Web Search:** `duckduckgo-search` (No API key needed)
*   **Geolocation:** OpenStreetMap (Nominatim & Overpass APIs)
*   **SOS Alerts:** Python `smtplib` (Secure Email Routing)

---

## 🚀 Setup & Installation

### 1. Clone the Repository
```bash
git clone [https://github.com/yourusername/recipe-to-our-voice.git](https://github.com/yourusername/recipe-to-our-voice.git)
cd recipe-to-our-voice
```

### 2. Create a Virtual Environment
```bash
python -m venv .venv
# On Windows
.venv\Scripts\activate
# On Mac/Linux
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Variables
Create a `.env` file in the root directory and add the following keys:
```ini
# Groq API for the Agentic Brain
GROQ_API_KEY=your_groq_api_key_here

# Supabase for Database & Vault
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_anon_key_here

# Secret phrase to unlock the Stealth UI
SECRET_PHRASE="help me cook"

# SMTP Settings for SOS Emails (Use an App Password if using Gmail)
SOS_SENDER_EMAIL=your_bot_email@gmail.com
SOS_SENDER_PASSWORD=your_gmail_app_password
```

### 5. Supabase Database Schema
Run the following SQL in your Supabase SQL Editor to set up the tables:
```sql
CREATE TABLE users_memory (
    user_id TEXT PRIMARY KEY,
    memory_summary TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE evidence_vault (
    id SERIAL PRIMARY KEY,
    user_id TEXT,
    incident_summary TEXT,
    severity TEXT,
    sha256_hash TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE dashboard_analytics (
    id SERIAL PRIMARY KEY,
    problem_category TEXT,
    city_zone TEXT,
    frequency_flag TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 💻 How to Run

Start the Streamlit application:
```bash
streamlit run app.py
```

1. The app will open showing the **Zaika Recipes** interface.
2. In the search bar, type `help me cook` and press Enter to unlock the AI.
3. Fill out the Safe Space setup with your emergency contact.
4. Start chatting with Aapa!

---

## 🔒 Security & Privacy Protocol
*   **Zero Device History:** The chat history is cleared upon exiting the app.
*   **Anonymous UUIDs:** Users are assigned an anonymous local UUID. No real names or phone numbers are stored on the server.
*   **Tamper-Proof Logging:** Evidence logs generate a one-way cryptographic hash to prove the data was not manipulated post-incident.

---

*Built with empathy for Hackathon 2026. Empowering voices, protecting lives.*
```
