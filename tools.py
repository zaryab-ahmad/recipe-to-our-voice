# tools.py

import os
import hashlib
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from duckduckgo_search import DDGS
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────
# Supabase client
# ──────────────────────────────────────────
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# ──────────────────────────────────────────
# TOOL 1: Live Web Search
# ──────────────────────────────────────────
def live_web_search(query: str) -> str:
    """Search the web for real-time laws, helplines, or news."""
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=3):
                results.append(f"- {r['title']}: {r['body']}")
        return "\n".join(results) if results else "No results found."
    except Exception as e:
        return f"Search failed: {str(e)}"


# ──────────────────────────────────────────
# TOOL 2: Find Nearest Facility
# ──────────────────────────────────────────
def find_nearest_facility(location: str, facility_type: str) -> str:
    """Find nearest hospital, police station, or safe house via OpenStreetMap."""
    try:
        # Map facility type to OSM amenity tag
        amenity_map = {
            "hospital": "hospital",
            "police": "police",
            "safe house": "social_facility",
            "shelter": "social_facility",
        }
        amenity = amenity_map.get(facility_type.lower(), "hospital")

        # First get coordinates of the location
        geo_url = "https://nominatim.openstreetmap.org/search"
        geo_params = {
            "q": location,
            "format": "json",
            "limit": 1
        }
        headers = {"User-Agent": "RecipeToOurVoice/1.0"}
        geo_res = requests.get(geo_url, params=geo_params, headers=headers)
        geo_data = geo_res.json()

        if not geo_data:
            return f"Could not find location: {location}"

        lat = geo_data[0]["lat"]
        lon = geo_data[0]["lon"]

        # Now search for nearby facility
        osm_url = "https://overpass-api.de/api/interpreter"
        query_osm = f"""
        [out:json];
        node["amenity"="{amenity}"](around:5000,{lat},{lon});
        out 3;
        """
        osm_res = requests.post(osm_url, data=query_osm)
        osm_data = osm_res.json()

        if not osm_data["elements"]:
            return f"No {facility_type} found near {location}."

        results = []
        for el in osm_data["elements"][:3]:
            name = el.get("tags", {}).get("name", "Unnamed facility")
            el_lat = el.get("lat", "N/A")
            el_lon = el.get("lon", "N/A")
            results.append(f"- {name} (lat: {el_lat}, lon: {el_lon})")

        return f"Nearest {facility_type} near {location}:\n" + "\n".join(results)

    except Exception as e:
        return f"Map search failed: {str(e)}"


# ──────────────────────────────────────────
# TOOL 3: Send Emergency SOS Email
# ──────────────────────────────────────────
def send_emergency_sos(user_email: str, trusted_email: str, message: str, location: str = "Unknown") -> str:
    """Send an SOS email to the user's trusted contact."""
    try:
        sender = os.getenv("SOS_SENDER_EMAIL")
        password = os.getenv("SOS_SENDER_PASSWORD")

        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = trusted_email
        msg["Subject"] = "🚨 EMERGENCY SOS ALERT 🚨"

        body = f"""
⚠️ EMERGENCY ALERT ⚠️

Someone you trust needs immediate help.

Message: {message}
Last Known Location: {location}

Please check on them immediately or contact emergency services.

— Recipe to Our Voice Safety System
        """

        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, trusted_email, msg.as_string())

        return "✅ SOS email sent successfully to your trusted contact."

    except Exception as e:
        return f"❌ SOS failed: {str(e)}"


# ──────────────────────────────────────────
# TOOL 4: Save to Evidence Vault
# ──────────────────────────────────────────
def save_to_evidence_vault(user_id: str, incident_summary: str, severity: str) -> str:
    """Hash and store incident as court-admissible evidence in Supabase."""
    try:
        # SHA-256 hash of the incident
        hash_value = hashlib.sha256(incident_summary.encode()).hexdigest()

        data = {
            "user_id": user_id,
            "incident_summary": incident_summary,
            "severity": severity,
            "sha256_hash": hash_value,
        }

        supabase.table("evidence_vault").insert(data).execute()

        return f"✅ Incident saved to Evidence Vault.\nVerification Hash: {hash_value[:20]}..."

    except Exception as e:
        return f"❌ Evidence vault failed: {str(e)}"


# ──────────────────────────────────────────
# TOOL 5: Log Dashboard Analytics
# ──────────────────────────────────────────
def log_dashboard_analytics(category: str, city_zone: str, recurrence: str) -> str:
    """Log anonymous abuse data for the policymaker heatmap."""
    try:
        data = {
            "problem_category": category,
            "city_zone": city_zone,
            "frequency_flag": recurrence,
        }

        supabase.table("dashboard_analytics").insert(data).execute()

        return f"✅ Anonymous data logged for {category} in {city_zone}."

    except Exception as e:
        return f"❌ Analytics log failed: {str(e)}"


# ──────────────────────────────────────────
# Tool Schemas for Groq Agent
# ──────────────────────────────────────────
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "live_web_search",
            "description": "Search the web for real-time information about laws, helplines, news, or resources for women in Pakistan.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_nearest_facility",
            "description": "Find the nearest hospital, police station, or safe house for a given location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City or area name"},
                    "facility_type": {"type": "string", "description": "Type: hospital, police, safe house, shelter"}
                },
                "required": ["location", "facility_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_emergency_sos",
            "description": "Send an emergency SOS email to the user's trusted contact when they are in danger.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_email": {"type": "string", "description": "The user's email"},
                    "trusted_email": {"type": "string", "description": "Trusted contact's email"},
                    "message": {"type": "string", "description": "Emergency message"},
                    "location": {"type": "string", "description": "User's current location"}
                },
                "required": ["user_email", "trusted_email", "message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_to_evidence_vault",
            "description": "Save a cryptographically hashed record of an incident as legal evidence.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "Anonymous user ID"},
                    "incident_summary": {"type": "string", "description": "Description of the incident"},
                    "severity": {"type": "string", "description": "Severity: low, medium, high, critical"}
                },
                "required": ["user_id", "incident_summary", "severity"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "log_dashboard_analytics",
            "description": "Silently log anonymous abuse data to the policymaker heatmap dashboard.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "Type of abuse: domestic violence, harassment, financial abuse, etc."},
                    "city_zone": {"type": "string", "description": "Area or zone in the city"},
                    "recurrence": {"type": "string", "description": "How often: first time, occasional, frequent"}
                },
                "required": ["category", "city_zone", "recurrence"]
            }
        }
    }
]