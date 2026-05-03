# agent.py

import os
import re
import json
from groq import Groq
from dotenv import load_dotenv
from tools import (
    live_web_search,
    find_nearest_facility,
    send_emergency_sos,
    save_to_evidence_vault,
    log_dashboard_analytics,
    TOOLS_SCHEMA
)
from memory import (
    get_or_create_user_id,
    load_memory,
    build_system_prompt,
    summarize_and_update_memory
)

load_dotenv()

# ──────────────────────────────────────────
# Model Selection
# ──────────────────────────────────────────
# English → fast and efficient
ENGLISH_MODEL = "llama-3.1-8b-instant"

# Urdu → mixtral is best free model for Urdu on Groq
# llama-3.3-70b-versatile is also good but slower
URDU_MODEL = "llama-3.3-70b-versatile"

# ──────────────────────────────────────────
# Groq Client
# ──────────────────────────────────────────
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# ──────────────────────────────────────────
# Tool Executor
# ──────────────────────────────────────────
def execute_tool(tool_name: str, tool_args: dict, user_id: str, user_email: str, trusted_email: str) -> str:
    if tool_name == "live_web_search":
        return live_web_search(tool_args["query"])
    elif tool_name == "find_nearest_facility":
        return find_nearest_facility(tool_args["location"], tool_args["facility_type"])
    elif tool_name == "send_emergency_sos":
        return send_emergency_sos(
            user_email=user_email,
            trusted_email=trusted_email,
            message=tool_args["message"],
            location=tool_args.get("location", "Unknown")
        )
    elif tool_name == "save_to_evidence_vault":
        return save_to_evidence_vault(
            user_id=user_id,
            incident_summary=tool_args["incident_summary"],
            severity=tool_args["severity"]
        )
    elif tool_name == "log_dashboard_analytics":
        return log_dashboard_analytics(
            category=tool_args["category"],
            city_zone=tool_args["city_zone"],
            recurrence=tool_args["recurrence"]
        )
    else:
        return f"Unknown tool: {tool_name}"


# ──────────────────────────────────────────
# Clean Response — Remove leaked tool text
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
# Auto Analytics Logger
# ──────────────────────────────────────────
def auto_log_analytics(user_message: str):
    """Silently detect and log safety incidents from user messages."""

    safety_keywords = [
        "harassment", "pictures", "photo", "tasveer", "peeche", "stalking",
        "maar", "violence", "hurt", "help", "danger", "scared", "dar",
        "college", "university", "school", "boys", "larke", "husband",
        "abuse", "threat", "zulm", "pareshaan", "problem", "takleef",
        "rape", "assault", "chhed", "chhairna", "follow", "peecha",
        "fire", "jail", "police", "FIR", "case", "court"
    ]

    user_lower = user_message.lower()

    if not any(kw in user_lower for kw in safety_keywords):
        return

    # ── Detect Category ──
    if any(w in user_lower for w in ["picture", "photo", "tasveer", "camera", "video"]):
        category = "Photography Harassment"
    elif any(w in user_lower for w in ["rape", "assault", "jabardasti"]):
        category = "Sexual Assault"
    elif any(w in user_lower for w in ["maar", "hit", "beat", "violence", "mara"]):
        category = "Physical Violence"
    elif any(w in user_lower for w in ["stalk", "follow", "peecha", "peeche"]):
        category = "Stalking"
    elif any(w in user_lower for w in ["college", "university", "school", "campus"]):
        category = "Educational Institution Harassment"
    elif any(w in user_lower for w in ["husband", "shauhar", "ghar", "sasural"]):
        category = "Domestic Abuse"
    elif any(w in user_lower for w in ["street", "road", "bazaar", "market"]):
        category = "Street Harassment"
    elif any(w in user_lower for w in ["office", "boss", "kaam", "job", "work"]):
        category = "Workplace Harassment"
    else:
        category = "General Harassment"

    # ── Detect Location ──
    location_map = {
        "islamia college peshawar": "Islamia College Peshawar",
        "peshawar":                 "Peshawar",
        "hayatabad":                "Hayatabad Peshawar",
        "saddar peshawar":          "Saddar Peshawar",
        "mardan":                   "Mardan",
        "swat":                     "Swat",
        "abbottabad":               "Abbottabad",
        "karachi":                  "Karachi",
        "defence":                  "DHA Karachi",
        "gulshan":                  "Gulshan Karachi",
        "lahore":                   "Lahore",
        "gulberg":                  "Gulberg Lahore",
        "islamabad":                "Islamabad",
        "f-10":                     "F-10 Islamabad",
        "g-9":                      "G-9 Islamabad",
        "rawalpindi":               "Rawalpindi",
        "quetta":                   "Quetta",
        "multan":                   "Multan",
        "faisalabad":               "Faisalabad",
        "hyderabad":                "Hyderabad",
        "sialkot":                  "Sialkot",
    }

    detected_zone = "Unknown"
    for key, value in location_map.items():
        if key in user_lower:
            detected_zone = value
            break

    # ── Detect Recurrence ──
    if any(w in user_lower for w in ["daily", "har roz", "everyday", "roz", "baar baar", "again", "keeps", "always", "hamesha"]):
        recurrence = "frequent"
    elif any(w in user_lower for w in ["kal", "yesterday", "last week", "pehle", "sometimes", "kabhi kabhi"]):
        recurrence = "occasional"
    else:
        recurrence = "first time"

    # ── Silently Log ──
    try:
        log_dashboard_analytics(category, detected_zone, recurrence)
        print(f"📊 Auto-logged: {category} | {detected_zone} | {recurrence}")
    except Exception as e:
        print(f"Analytics auto-log error: {e}")


# ──────────────────────────────────────────
# Muslim-Based System Prompt
# ──────────────────────────────────────────
MUSLIM_SYSTEM_PROMPT_EN = """
You are "Aapa" — a warm, wise, Muslim Pakistani elder sister AI companion
for women facing domestic violence, harassment, or emotional distress.

YOUR PERSONALITY:
- Begin responses with "Assalamu Alaikum" only on the very first message
- Use Islamic phrases naturally: "InshAllah", "Alhamdulillah", "Astaghfirullah"
- Speak like a caring Pakistani elder sister (Aapa/Baji)
- Use Urdu words naturally: "beti", "behen", "himmat", "sabar", "dua"
- Be warm, non-judgmental, and deeply compassionate
- Reference Islamic values: patience (sabar), justice (adl), protection of women in Islam
- Remind them: "Islam gives you the right to be safe and treated with dignity"
- Never shame them. Abuse is NEVER the woman's fault in Islam or in law.
- Respond in ENGLISH

STRICT RULES — NEVER BREAK THESE:
- NEVER output JSON, function names, or tool syntax in your response
- NEVER show raw tool results — convert to warm human language only
- NEVER start with assistant= or any code or brackets
- NEVER show {category: ...} or any dictionary in chat
- Call tools SILENTLY — user must never see tool mechanics
- Only speak in plain, warm, conversational language

YOUR ABILITIES (use silently, never mention them):
1. Search web for laws, helplines, Islamic rulings on divorce/rights
2. Find nearest hospital, police station, shelter
3. Send SOS emergency email to trusted contact
4. Save incident as legal evidence
5. Log anonymous data for city safety heatmap

ALWAYS:
- If user mentions danger offer SOS immediately
- Remind them of their Islamic rights as a woman
- Remind them Pakistan has laws protecting them (Protection Against Harassment Act 2010, CEDAW)
- Be their Aapa, their safe space
"""

MUSLIM_SYSTEM_PROMPT_UR = """
آپ "آپا" ہیں — ایک گرمجوش، سمجھدار، مسلمان پاکستانی بڑی بہن AI ساتھی
جو گھریلو تشدد، ہراسانی، یا جذباتی تکلیف کا سامنا کرنے والی خواتین کے لیے ہے۔

آپ کی شخصیت:
- پہلے پیغام میں "السلام علیکم" سے شروع کریں
- اسلامی جملے قدرتی طور پر استعمال کریں: "انشاءاللہ"، "الحمدللہ"، "استغفراللہ"
- ایک پیاری پاکستانی آپا/باجی کی طرح بات کریں
- گرمجوش، بغیر فیصلہ کیے، اور گہری ہمدردی کے ساتھ رہیں
- اسلامی اقدار کا حوالہ دیں: صبر، عدل، اسلام میں خواتین کا تحفظ
- انہیں یاد دلائیں: "اسلام آپ کو محفوظ رہنے کا حق دیتا ہے"
- انہیں کبھی شرمندہ نہ کریں۔ زیادتی کبھی بھی عورت کی غلطی نہیں
- صرف اردو میں جواب دیں

سخت اصول — کبھی نہ توڑیں:
- کبھی JSON، فنکشن کے نام، یا ٹول سنٹیکس ظاہر نہ کریں
- ٹول کے نتائج کو انسانی گرم زبان میں بدلیں
- assistant= یا کوئی کوڈ سے شروع نہ کریں
- صرف سادہ، گرم، بات چیت کی زبان میں بولیں

آپ کی صلاحیتیں (خاموشی سے استعمال کریں):
1. قوانین، ہیلپ لائنز، طلاق پر اسلامی احکام تلاش کریں
2. قریبی ہسپتال، پولیس اسٹیشن، پناہ گاہ تلاش کریں
3. قابل اعتماد شخص کو SOS ای میل بھیجیں
4. واقعہ کو قانونی ثبوت کے طور پر محفوظ کریں
5. شہر کی حفاظت کے ہیٹ میپ کے لیے گمنام ڈیٹا لاگ کریں

ہمیشہ:
- اگر خطرے کا ذکر ہو تو فوری SOS کی پیشکش کریں
- انہیں اسلام میں ان کے حقوق یاد دلائیں
- انہیں یاد دلائیں کہ پاکستان میں ان کی حفاظت کے قوانین ہیں
- ان کی آپا بنیں، ان کی محفوظ جگہ
"""


# ──────────────────────────────────────────
# Main Agentic Loop
# ──────────────────────────────────────────
def run_agent(
    user_message: str,
    chat_history: list,
    user_id: str,
    user_email: str,
    trusted_email: str,
    memory: str,
    language: str = "English"
) -> tuple[str, list]:

    # ── Pick model and prompt based on language ──
    if language == "Urdu":
        model_name = URDU_MODEL
        system_personality = MUSLIM_SYSTEM_PROMPT_UR
    else:
        model_name = ENGLISH_MODEL
        system_personality = MUSLIM_SYSTEM_PROMPT_EN

    print(f"🌐 Language: {language} | Model: {model_name}")

    # ── Auto log analytics silently FIRST ──
    auto_log_analytics(user_message)

    # Build system prompt with memory
    base_prompt = build_system_prompt(memory, user_email, trusted_email)
    full_system_prompt = system_personality + "\n\n" + base_prompt

    # Add user message to history
    chat_history.append({
        "role": "user",
        "content": user_message
    })

    # Build messages for Groq
    messages = [{"role": "system", "content": full_system_prompt}] + chat_history

    # ── First Groq Call ──
    response = groq_client.chat.completions.create(
        model=model_name,
        messages=messages,
        tools=TOOLS_SCHEMA,
        tool_choice="auto",
        max_tokens=1024
    )

    response_message = response.choices[0].message

    # ── Check if Groq wants to call a tool ──
    if response_message.tool_calls:

        chat_history.append({
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in response_message.tool_calls
            ]
        })

        for tool_call in response_message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            print(f"🔧 Agent calling tool: {tool_name} with {tool_args}")

            tool_result = execute_tool(
                tool_name=tool_name,
                tool_args=tool_args,
                user_id=user_id,
                user_email=user_email,
                trusted_email=trusted_email
            )

            chat_history.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_result
            })

        # ── Second Groq Call with tool results ──
        messages = [{"role": "system", "content": full_system_prompt}] + chat_history

        final_response = groq_client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=1024
        )

        final_message = final_response.choices[0].message.content or ""

    else:
        final_message = response_message.content or ""

    # ── Always clean the response ──
    final_message = clean_response(final_message)

    # ── Fallback if empty after cleaning ──
    if not final_message:
        if language == "Urdu":
            final_message = "میں یہاں ہوں آپا، آپ بات کر سکتی ہیں۔ اللہ آپ کا ہمیشہ ساتھ دے۔ 💜"
        else:
            final_message = "I am here for you Aapa. You can talk to me. Allah is always with you. 💜"

    # Add final response to history
    chat_history.append({
        "role": "assistant",
        "content": final_message
    })

    # ── Update memory every 10 messages ──
    if len(chat_history) % 10 == 0:
        existing_memory = load_memory(user_id)
        summarize_and_update_memory(user_id, chat_history, existing_memory)

    return final_message, chat_history