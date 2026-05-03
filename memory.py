# memory.py

import os
import uuid
from groq import Groq
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────
# Clients
# ──────────────────────────────────────────
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# ──────────────────────────────────────────
# Generate or Get User ID
# ──────────────────────────────────────────
def get_or_create_user_id() -> str:
    """
    Generate a unique anonymous user ID and store it locally.
    If one already exists, return it.
    """
    id_file = ".user_id"

    if os.path.exists(id_file):
        with open(id_file, "r") as f:
            return f.read().strip()

    new_id = str(uuid.uuid4())
    with open(id_file, "w") as f:
        f.write(new_id)

    return new_id


# ──────────────────────────────────────────
# Load Memory from Supabase
# ──────────────────────────────────────────
def load_memory(user_id: str) -> str:
    """
    Fetch the user's summarized memory from Supabase.
    Returns empty string if no memory exists yet.
    """
    try:
        result = supabase.table("users_memory") \
            .select("memory_summary") \
            .eq("user_id", user_id) \
            .execute()

        if result.data:
            return result.data[0]["memory_summary"]
        return ""

    except Exception as e:
        print(f"Memory load error: {e}")
        return ""


# ──────────────────────────────────────────
# Save Memory to Supabase
# ──────────────────────────────────────────
def save_memory(user_id: str, memory_summary: str):
    """
    Save or update the user's memory summary in Supabase.
    Uses upsert so it creates if not exists, updates if exists.
    """
    try:
        supabase.table("users_memory").upsert({
            "user_id": user_id,
            "memory_summary": memory_summary
        }).execute()

    except Exception as e:
        print(f"Memory save error: {e}")


# ──────────────────────────────────────────
# Summarize Conversation & Update Memory
# ──────────────────────────────────────────
def summarize_and_update_memory(user_id: str, chat_history: list, existing_memory: str):
    """
    Every 10 messages, summarize the conversation using Groq
    and update the memory in Supabase.
    """
    try:
        # Build conversation text
        conversation_text = ""
        for msg in chat_history[-10:]:
            role = msg["role"].upper()
            content = msg["content"]
            conversation_text += f"{role}: {content}\n"

        # Ask Groq to summarize
        prompt = f"""
You are a memory summarizer for a women's safety AI assistant.

Existing memory about this user:
{existing_memory if existing_memory else "No previous memory."}

New conversation to integrate:
{conversation_text}

Write a SHORT, UPDATED summary (max 150 words) about this user's situation.
Include: who is hurting them, where they live, what kind of abuse, any names mentioned.
Be factual, compassionate, and anonymous (no last names).
Do NOT include chat timestamps or role labels.
Just write the summary paragraph.
        """

        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200
        )

        new_summary = response.choices[0].message.content.strip()
        save_memory(user_id, new_summary)
        print("✅ Memory updated.")

    except Exception as e:
        print(f"Memory summarization error: {e}")


# ──────────────────────────────────────────
# Build System Prompt with Memory
# ──────────────────────────────────────────
def build_system_prompt(memory: str, user_email: str, trusted_email: str) -> str:
    """
    Build the AI system prompt, injecting memory if it exists.
    - NEVER show raw tool call text or function names in your response to the user
    - NEVER show JSON or function syntax in chat
    - Call tools silently in background, only show the final human response
    """

    memory_injection = ""
    if memory:
        memory_injection = f"""
MEMORY OF THIS USER:
You have spoken to this user before. Here is their background:
{memory}
Do NOT ask them to repeat this information. Use it naturally in conversation.
"""

    return f"""
You are a compassionate, intelligent AI safety companion for Pakistani women 
facing domestic violence, harassment, or emotional distress.

You speak Urdu and English. Match the user's language naturally.

You have access to 5 tools:
1. live_web_search — Search for laws, helplines, news
2. find_nearest_facility — Find hospitals, police, shelters
3. send_emergency_sos — Send SOS email to trusted contact
4. save_to_evidence_vault — Log legal evidence
5. log_dashboard_analytics — Log anonymous data for policymakers

IMPORTANT RULES:
- Always be warm, non-judgmental, and trauma-informed
- Never minimize their experience
- If they mention danger, ALWAYS offer to send SOS
- Silently trigger log_dashboard_analytics whenever they mention any safety issue
- User's email: {user_email}
- Trusted contact email: {trusted_email}

{memory_injection}

You are their trusted companion. They are safe talking to you.
""".strip()