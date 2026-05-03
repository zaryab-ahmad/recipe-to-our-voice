# pages/1_Safety_Dashboard.py

import streamlit as st
import os
import random
import pandas as pd
import requests
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────
# Page Config
# ──────────────────────────────────────────
st.set_page_config(
    page_title="Pakistan Women Safety Dashboard",
    page_icon="📊",
    layout="wide"
)

# ──────────────────────────────────────────
# Supabase Client
# ──────────────────────────────────────────
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# ──────────────────────────────────────────
# Known Pakistani City Coordinates
# ──────────────────────────────────────────
KNOWN_COORDS = {
    "islamia college peshawar": (34.0084, 71.5785),
    "peshawar":                 (34.0151, 71.5249),
    "hayatabad peshawar":       (33.9987, 71.4600),
    "saddar peshawar":          (34.0050, 71.5430),
    "mardan":                   (34.1986, 72.0404),
    "swat":                     (35.2227, 72.4258),
    "abbottabad":               (34.1463, 73.2117),
    "karachi":                  (24.8607, 67.0011),
    "dha karachi":              (24.8069, 67.0650),
    "gulshan karachi":          (24.9215, 67.0977),
    "lahore":                   (31.5497, 74.3436),
    "gulberg lahore":           (31.5204, 74.3587),
    "islamabad":                (33.6844, 73.0479),
    "f-10 islamabad":           (33.7040, 73.0231),
    "g-9 islamabad":            (33.6938, 73.0551),
    "rawalpindi":               (33.5651, 73.0169),
    "quetta":                   (30.1798, 66.9750),
    "multan":                   (30.1575, 71.5249),
    "faisalabad":               (31.4504, 73.1350),
    "hyderabad":                (25.3960, 68.3578),
    "sialkot":                  (32.4945, 74.5229),
    "unknown":                  (30.3753, 69.3451),  # Center of Pakistan
}


def get_coordinates(city_zone: str) -> tuple:
    """Get lat/lon — first check known coords, then OpenStreetMap."""
    zone_lower = city_zone.lower().strip()

    # Check known coords first (fast, no API call)
    for key, coords in KNOWN_COORDS.items():
        if key in zone_lower or zone_lower in key:
            return coords

    # Fallback to OpenStreetMap
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": f"{city_zone}, Pakistan", "format": "json", "limit": 1}
        headers = {"User-Agent": "RecipeToOurVoice/1.0"}
        res = requests.get(url, params=params, headers=headers, timeout=5)
        data = res.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except:
        pass

    # Default to center of Pakistan
    return 30.3753, 69.3451


# ──────────────────────────────────────────
# Fetch Data
# ──────────────────────────────────────────
@st.cache_data(ttl=60)
def fetch_analytics():
    try:
        result = supabase.table("dashboard_analytics").select("*").execute()
        return pd.DataFrame(result.data)
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        return pd.DataFrame()


# ──────────────────────────────────────────
# Main Dashboard
# ──────────────────────────────────────────
def main():

    st.markdown("""
        <style>
        .stApp { background-color: #0a0a1a; }
        .dash-title { font-size: 2rem; font-weight: bold; color: #c39bd3; }
        .dash-sub { color: #888; font-size: 0.9rem; }
        html, body, .stApp, p, span, div, label {
            color: #f0f0f0 !important;
        }
        .stMetric { background: #1a1a2e; border-radius: 10px; padding: 10px;
                    border: 1px solid #6c3483; }
        </style>
    """, unsafe_allow_html=True)

    # ── Header ──
    st.markdown('<div class="dash-title">📊 Pakistan Women Safety — Live Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="dash-sub">Anonymous, aggregated data for policymakers, NGOs, and law enforcement. No personal information is stored.</div>', unsafe_allow_html=True)
    st.markdown("---")

    # ── Refresh button ──
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    # ── Fetch Data ──
    df = fetch_analytics()

    if df.empty:
        st.info("📭 No incidents logged yet. Data will appear here as users interact with the app.")
        return

    # ── Top Metrics ──
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📍 Total Incidents", len(df))
    with col2:
        top_cat = df["problem_category"].value_counts().idxmax() if "problem_category" in df.columns else "N/A"
        st.metric("⚠️ Most Common Issue", top_cat)
    with col3:
        top_zone = df["city_zone"].value_counts().idxmax() if "city_zone" in df.columns else "N/A"
        st.metric("📌 Highest Risk Zone", top_zone)
    with col4:
        frequent = df[df["frequency_flag"] == "frequent"].shape[0] if "frequency_flag" in df.columns else 0
        st.metric("🔴 Frequent Cases", frequent)

    st.markdown("---")

    # ── Charts ──
    left, right = st.columns(2)

    with left:
        st.markdown("### 📊 Incidents by Category")
        if "problem_category" in df.columns:
            cat_counts = df["problem_category"].value_counts().reset_index()
            cat_counts.columns = ["Category", "Count"]
            st.bar_chart(cat_counts.set_index("Category"))

    with right:
        st.markdown("### 📍 Incidents by City / Zone")
        if "city_zone" in df.columns:
            zone_counts = df["city_zone"].value_counts().reset_index()
            zone_counts.columns = ["Zone", "Count"]
            st.bar_chart(zone_counts.set_index("Zone"))

    st.markdown("---")

    # ── Live Map ──
    st.markdown("### 🗺️ Live Incident Map — Pakistan")
    st.markdown("*Each dot = one anonymized report. Spread shows approximate area.*")

    if "city_zone" in df.columns:
        map_data = []

        for zone in df["city_zone"].unique():
            count = df[df["city_zone"] == zone].shape[0]
            lat, lon = get_coordinates(zone)

            for _ in range(min(count, 15)):
                map_data.append({
                    "lat": lat + random.uniform(-0.02, 0.02),
                    "lon": lon + random.uniform(-0.02, 0.02)
                })

        if map_data:
            map_df = pd.DataFrame(map_data)
            st.map(map_df, zoom=5)
        else:
            st.info("No map data yet.")

    st.markdown("---")

    # ── Recurrence ──
    st.markdown("### 🔁 Recurrence Analysis")
    if "frequency_flag" in df.columns:
        freq_counts = df["frequency_flag"].value_counts().reset_index()
        freq_counts.columns = ["Frequency", "Count"]
        st.bar_chart(freq_counts.set_index("Frequency"))

    st.markdown("---")

    # ── Raw Table ──
    st.markdown("### 📋 Anonymous Incident Log")
    st.markdown("*No names, no emails, no personal details — only patterns for policy action.*")

    display_cols = ["problem_category", "city_zone", "frequency_flag", "timestamp"]
    available_cols = [c for c in display_cols if c in df.columns]
    st.dataframe(df[available_cols], use_container_width=True)

    st.markdown("---")
    st.markdown("*Data auto-refreshes every 60 seconds. Built with 💜 for safer cities.*")


if __name__ == "__main__":
    main()