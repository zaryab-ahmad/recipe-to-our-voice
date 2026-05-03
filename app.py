# app.py

import streamlit as st
import os
import re
from dotenv import load_dotenv
from memory import get_or_create_user_id, load_memory
from agent import run_agent

load_dotenv()

SECRET_PHRASE = os.getenv("SECRET_PHRASE", "help me cook")

# ──────────────────────────────────────────
# Page Config
# ──────────────────────────────────────────
st.set_page_config(
    page_title="Zaika Recipes",
    page_icon="🍽️",
    layout="wide"
)

# ──────────────────────────────────────────
# Session State Initialization
# ──────────────────────────────────────────
if "unlocked" not in st.session_state:
    st.session_state.unlocked = False

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "user_id" not in st.session_state:
    st.session_state.user_id = get_or_create_user_id()

if "memory" not in st.session_state:
    st.session_state.memory = load_memory(st.session_state.user_id)

if "user_email" not in st.session_state:
    st.session_state.user_email = ""

if "trusted_email" not in st.session_state:
    st.session_state.trusted_email = ""

if "setup_done" not in st.session_state:
    st.session_state.setup_done = False

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

if "language" not in st.session_state:
    st.session_state.language = "English"


# ──────────────────────────────────────────
# Theme Colors
# ──────────────────────────────────────────
def get_theme():
    if st.session_state.dark_mode:
        return {
            "bg":             "#0f0f1a",
            "card_bg":        "#1a1a2e",
            "card_border":    "#6c3483",
            "text":           "#f0f0f0",
            "subtext":        "#b0b0c0",
            "user_msg_bg":    "#6c3483",
            "user_msg_text":  "#ffffff",
            "ai_msg_bg":      "#1e3a2f",
            "ai_msg_text":    "#ffffff",
            "header_color":   "#c39bd3",
            "accent":         "#9b59b6",
            "btn_bg":         "#6c3483",
            "input_bg":       "#1a1a2e",
            "recipe_card":    "#1a1a2e",
            "recipe_text":    "#f0f0f0",
            "mode_icon":      "☀️",
            "mode_label":     "Light Mode",
        }
    else:
        return {
            "bg":             "#f5f0ff",
            "card_bg":        "#ffffff",
            "card_border":    "#9b59b6",
            "text":           "#1a1a2e",
            "subtext":        "#555566",
            "user_msg_bg":    "#9b59b6",
            "user_msg_text":  "#ffffff",
            "ai_msg_bg":      "#e8f8f0",
            "ai_msg_text":    "#1a1a2e",
            "header_color":   "#6c3483",
            "accent":         "#6c3483",
            "btn_bg":         "#9b59b6",
            "input_bg":       "#ffffff",
            "recipe_card":    "#ffffff",
            "recipe_text":    "#1a1a2e",
            "mode_icon":      "🌙",
            "mode_label":     "Dark Mode",
        }


# ──────────────────────────────────────────
# Global Style Injector
# ──────────────────────────────────────────
def inject_global_styles():
    t = get_theme()
    st.markdown(f"""
        <style>
        .stApp {{
            background-color: {t['bg']} !important;
        }}
        html, body, .stApp, .stMarkdown, p, span, label, div {{
            color: {t['text']} !important;
        }}
        section[data-testid="stSidebar"] {{
            background-color: {t['card_bg']} !important;
        }}
        .stTextInput input, .stChatInput textarea {{
            background-color: {t['input_bg']} !important;
            color: {t['text']} !important;
            border: 1px solid {t['accent']} !important;
            border-radius: 10px !important;
        }}
        .stButton > button {{
            background-color: {t['btn_bg']} !important;
            color: #ffffff !important;
            border-radius: 10px !important;
            border: none !important;
            font-weight: bold !important;
        }}
        .recipe-card {{
            background: {t['recipe_card']};
            border-radius: 14px;
            padding: 20px;
            margin: 10px 0;
            box-shadow: 0 4px 15px rgba(108, 52, 131, 0.2);
            border: 1px solid {t['card_border']};
            color: {t['recipe_text']} !important;
        }}
        .recipe-card h3, .recipe-card p {{
            color: {t['recipe_text']} !important;
        }}
        .user-msg {{
            background: {t['user_msg_bg']};
            border-radius: 18px 18px 4px 18px;
            padding: 12px 18px;
            margin: 8px 0;
            text-align: right;
            color: {t['user_msg_text']} !important;
            font-size: 1rem;
            max-width: 80%;
            margin-left: auto;
        }}
        .ai-msg {{
            background: {t['ai_msg_bg']};
            border-radius: 18px 18px 18px 4px;
            padding: 12px 18px;
            margin: 8px 0;
            color: {t['ai_msg_text']} !important;
            font-size: 1rem;
            max-width: 80%;
            border-left: 3px solid {t['accent']};
        }}
        .chat-header {{
            font-size: 1.8rem;
            font-weight: bold;
            color: {t['header_color']} !important;
        }}
        .recipe-title {{
            font-size: 2.5rem;
            font-weight: bold;
            color: {t['header_color']} !important;
        }}
        .lang-badge {{
            display: inline-block;
            background: {t['accent']};
            color: #fff !important;
            border-radius: 20px;
            padding: 4px 14px;
            font-size: 0.85rem;
            font-weight: bold;
            margin-left: 10px;
        }}
        .stForm {{
            background: {t['card_bg']} !important;
            border-radius: 14px !important;
            padding: 20px !important;
            border: 1px solid {t['card_border']} !important;
        }}
        hr {{
            border-color: {t['accent']} !important;
            opacity: 0.3;
        }}
        </style>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────
# Clean AI response
# ──────────────────────────────────────────
def clean_response(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'\{[^{}]*\}', '', text, flags=re.DOTALL)
    text = re.sub(r'\(function=\w+>.*', '', text, flags=re.DOTALL)
    text = re.sub(r'log_dashboard_analytics>.*', '', text, flags=re.DOTALL)
    text = re.sub(r'live_web_search>.*', '', text, flags=re.DOTALL)
    text = re.sub(r'find_nearest_facility>.*', '', text, flags=re.DOTALL)
    text = re.sub(r'send_emergency_sos>.*', '', text, flags=re.DOTALL)
    text = re.sub(r'save_to_evidence_vault>.*', '', text, flags=re.DOTALL)
    text = re.sub(r'assistant=.*', '', text, flags=re.DOTALL)
    text = re.sub(r'"name"\s*:\s*"assistant".*', '', text, flags=re.DOTALL)
    text = re.sub(r'<tool_call>.*?</tool_call>', '', text, flags=re.DOTALL)
    text = re.sub(r'<\|.*?\|>', '', text, flags=re.DOTALL)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


# ──────────────────────────────────────────
# DECOY UI — Recipe App
# ──────────────────────────────────────────
def show_recipe_app():
    inject_global_styles()
    t = get_theme()

    # Top bar
    c1, c2 = st.columns([6, 1])
    with c2:
        if st.button(f"{t['mode_icon']}"):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()

    st.markdown('<div class="recipe-title">🍽️ Zaika — Pakistani Recipes</div>', unsafe_allow_html=True)
    st.markdown("*Ghar jaisa khana, har din*")
    st.markdown("---")

    search = st.text_input(
        "🔍 Search recipes...",
        key="search_bar",
        placeholder="Try: Biryani, Karahi, Halwa Puri..."
    )

    if search.strip().lower() == SECRET_PHRASE.strip().lower():
        st.session_state.unlocked = True
        st.rerun()

    st.markdown("### 🌟 Popular Recipes Today")

    recipes = [
        {"emoji": "🍚", "name": "Chicken Biryani", "time": "60 mins", "desc": "Aromatic rice with tender chicken"},
        {"emoji": "🥘", "name": "Mutton Karahi",   "time": "45 mins", "desc": "Spicy tomato-based karahi"},
        {"emoji": "🍞", "name": "Halwa Puri",       "time": "30 mins", "desc": "Classic Sunday breakfast"},
        {"emoji": "🍲", "name": "Daal Makhani",     "time": "40 mins", "desc": "Creamy lentils slow cooked"},
        {"emoji": "🥩", "name": "Seekh Kebab",      "time": "25 mins", "desc": "Grilled minced meat skewers"},
        {"emoji": "🍛", "name": "Nihari",            "time": "3 hrs",  "desc": "Slow cooked beef stew"},
    ]

    cols = st.columns(3)
    for i, recipe in enumerate(recipes):
        with cols[i % 3]:
            st.markdown(f"""
                <div class="recipe-card">
                    <div style="font-size:3rem">{recipe['emoji']}</div>
                    <h3>{recipe['name']}</h3>
                    <p>⏱️ {recipe['time']}</p>
                    <p>{recipe['desc']}</p>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("*© 2024 Zaika Recipes — Lahore, Pakistan*")


# ──────────────────────────────────────────
# SETUP SCREEN
# ──────────────────────────────────────────
def show_setup_screen():
    inject_global_styles()

    st.markdown("### 🔒 Safe Space Setup")
    st.markdown("This information stays private and is only used to help you.")
    st.markdown("---")

    with st.form("setup_form"):
        user_email = st.text_input("📧 Your Email Address", placeholder="yourname@gmail.com")
        trusted_email = st.text_input("💙 Trusted Contact's Email", placeholder="mom/sister/friend@gmail.com")
        st.markdown("*This person will receive an email if you trigger an SOS alert.*")
        submitted = st.form_submit_button("✅ Save & Continue")

        if submitted:
            if not user_email or not trusted_email:
                st.error("Please fill in both email addresses.")
            elif "@" not in user_email or "@" not in trusted_email:
                st.error("Please enter valid email addresses.")
            else:
                st.session_state.user_email = user_email
                st.session_state.trusted_email = trusted_email
                st.session_state.setup_done = True

                from memory import save_memory
                existing = st.session_state.memory or ""
                updated = existing + f"\nUser email: {user_email}. Trusted contact: {trusted_email}."
                save_memory(st.session_state.user_id, updated)
                st.rerun()


# ──────────────────────────────────────────
# CHAT UI
# ──────────────────────────────────────────
def show_chat():
    inject_global_styles()
    t = get_theme()

    # ── Top Header Row ──
    col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
    with col1:
        lang_badge = f'<span class="lang-badge">{"🇬🇧 EN" if st.session_state.language == "English" else "🇵🇰 اردو"}</span>'
        st.markdown(f'<div class="chat-header">💜 Your Safe Space {lang_badge}</div>', unsafe_allow_html=True)
        st.markdown("*I am here for you. You are not alone.*")
    with col2:
        if st.button(f"{t['mode_icon']}", key="theme_btn"):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()
    with col3:
        if st.button("🚪 Exit", key="exit_btn"):
            st.session_state.unlocked = False
            st.session_state.chat_history = []
            st.rerun()
    with col4:
        pass

    st.markdown("---")

    # ── Language Toggle ──
    lang_col1, lang_col2, lang_col3 = st.columns([1, 1, 4])
    with lang_col1:
        en_style = "primary" if st.session_state.language == "English" else "secondary"
        if st.button("🇬🇧 English", type=en_style, key="eng_btn"):
            st.session_state.language = "English"
            st.rerun()
    with lang_col2:
        ur_style = "primary" if st.session_state.language == "Urdu" else "secondary"
        if st.button("🇵🇰 اردو", type=ur_style, key="urd_btn"):
            st.session_state.language = "Urdu"
            st.rerun()
    with lang_col3:
        if st.session_state.language == "English":
            st.markdown("*Using fast English model — llama-3.1-8b-instant*")
        else:
            st.markdown("*اردو کے لیے بہتر ماڈل استعمال ہو رہا ہے — llama-3.3-70b*")

    st.markdown("---")

    # ── Memory Indicator ──
    if st.session_state.memory:
        if st.session_state.language == "Urdu":
            st.success("💜 مجھے آپ کی بات یاد ہے۔ دوبارہ بتانے کی ضرورت نہیں۔")
        else:
            st.success("💜 I remember you. You don't need to repeat yourself.")

    # ── SOS Button ──
    sos_label = "🚨 ابھی SOS بھیجیں" if st.session_state.language == "Urdu" else "🚨 SEND SOS NOW"
    if st.button(sos_label, type="primary", use_container_width=True):
        with st.spinner("Sending emergency alert..." if st.session_state.language == "English" else "ایمرجنسی الرٹ بھیجا جا رہا ہے..."):
            from tools import send_emergency_sos
            result = send_emergency_sos(
                user_email=st.session_state.user_email,
                trusted_email=st.session_state.trusted_email,
                message="I need immediate help. Please contact me or emergency services.",
                location="Unknown"
            )
            if "✅" in result:
                st.success(result)
            else:
                st.error(result)

    st.markdown("---")

    # ── Chat History ──
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(
                f'<div class="user-msg">🧕 {msg["content"]}</div>',
                unsafe_allow_html=True
            )
        elif msg["role"] == "assistant":
            cleaned = clean_response(msg["content"])
            if cleaned:
                st.markdown(
                    f'<div class="ai-msg">💜 {cleaned}</div>',
                    unsafe_allow_html=True
                )

    st.markdown("---")

    # ── Input Box ──
    placeholder = "یہاں لکھیں..." if st.session_state.language == "Urdu" else "Type here... (Urdu or English)"
    user_input = st.chat_input(placeholder)

    if user_input:
        thinking_msg = "سوچ رہی ہوں..." if st.session_state.language == "Urdu" else "💜 Thinking..."
        with st.spinner(thinking_msg):
            response, updated_history = run_agent(
                user_message=user_input,
                chat_history=st.session_state.chat_history,
                user_id=st.session_state.user_id,
                user_email=st.session_state.user_email,
                trusted_email=st.session_state.trusted_email,
                memory=st.session_state.memory,
                language=st.session_state.language
            )
            st.session_state.chat_history = updated_history
            st.rerun()


# ──────────────────────────────────────────
# MAIN ROUTER
# ──────────────────────────────────────────
def main():
    if not st.session_state.unlocked:
        show_recipe_app()
    elif not st.session_state.setup_done:
        show_setup_screen()
    else:
        show_chat()


if __name__ == "__main__":
    main()