"""
AI Service — Single-Thread Senior Companion with RAG Memory.

This service builds every AI response by:
1. Constructing a personalised system prompt with the user's name
2. Injecting relevant long-term memories from ChromaDB (RAG)
3. Including the last 10 messages from PostgreSQL (sliding window)
4. Calling OpenAI to generate a warm, empathetic reply
5. Storing the new exchange in ChromaDB for future recall
6. Running the moderation filter on the exchange
"""

from typing import List, Dict, Optional
from openai import OpenAI
from sqlalchemy.orm import Session

from app.config import settings
from app.models.chat import Chat
from app.models.user import User
from app.services import memory_service, moderation_service

client = OpenAI(api_key=settings.OPENAI_API_KEY)


# --------------------------------------------------------------------------- #
#  System prompt builder
# --------------------------------------------------------------------------- #

def _build_system_prompt(user_name: str, memory_context: str) -> str:
    """
    Build a personalised system prompt that injects the user's name and
    any retrieved long-term memories.
    """
    base = f"""You are {user_name}'s lifelong best friend — a warm, caring, and patient AI companion.
You have known {user_name} for many years.  You always call them by their name and make
them feel heard, valued, and never alone.

Your personality:
- WARM & GENUINE: speak like a caring friend, never like a robot.
- PATIENT: never rush; take time to respond thoughtfully.
- EMPATHETIC: validate feelings — "That sounds tough", "I completely understand".
- REMEMBERING: proactively reference things {user_name} has told you before.
- SIMPLE ENGLISH: clear, easy-to-understand language; no jargon.
- POSITIVE but AUTHENTIC: share uplifting thoughts while acknowledging real feelings.
- PROACTIVE: gently ask about family, hobbies, daily life.

Important rules:
1. ALWAYS use {user_name}'s name naturally in your replies (at least once).
2. NEVER break character or reveal you are an AI language model.
3. NEVER reset or forget the conversation — this is one continuous friendship.
4. If {user_name} shares something personal, remember it and bring it up later.
5. Offer encouragement and suggest gentle activities (walks, calling family, hobbies).
6. Keep responses conversational — 2-4 sentences is usually perfect.
"""

    if memory_context:
        base += f"""
Here are things you remember about {user_name} from past conversations
(use them naturally — don't list them, just weave them in when relevant):
---
{memory_context}
---
"""

    return base


# --------------------------------------------------------------------------- #
#  Core AI pipeline
# --------------------------------------------------------------------------- #

async def get_ai_response(
    user_id: int,
    user_name: str,
    message: str,
    db: Session,
) -> str:
    """
    Generate an AI response using:
    • Long-term RAG memory (ChromaDB)
    • Short-term sliding window (last 10 DB messages)
    • Personalised system prompt with user name
    """

    # 1. Retrieve relevant long-term memories from ChromaDB
    memories = memory_service.search_relevant_memories(user_id, message, n_results=5)
    memory_context = "\n".join(memories) if memories else ""

    # 2. Build personalised system prompt
    system_prompt = _build_system_prompt(user_name, memory_context)

    messages: list[dict] = [{"role": "system", "content": system_prompt}]

    # 3. Sliding window — last 10 non-deleted messages from PostgreSQL
    recent_chats = (
        db.query(Chat)
        .filter(Chat.user_id == user_id, Chat.is_deleted == False)
        .order_by(Chat.created_at.desc())
        .limit(10)
        .all()
    )

    for chat in reversed(recent_chats):
        messages.append({"role": "user", "content": chat.message})
        messages.append({"role": "assistant", "content": chat.response})

    # 4. Append current user message
    messages.append({"role": "user", "content": message})

    # 5. Call OpenAI
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.8,
            max_tokens=600,
            presence_penalty=0.3,
            frequency_penalty=0.2,
        )
        ai_response = response.choices[0].message.content
        return ai_response
    except Exception as e:
        raise Exception(f"AI service error: {str(e)}")


# --------------------------------------------------------------------------- #
#  Persistence helpers
# --------------------------------------------------------------------------- #

def save_chat(db: Session, user_id: int, message: str, response: str) -> Chat:
    """Save the chat exchange to PostgreSQL and ChromaDB."""
    chat = Chat(user_id=user_id, message=message, response=response)
    db.add(chat)
    db.commit()
    db.refresh(chat)

    # Store in ChromaDB for long-term RAG retrieval
    try:
        memory_service.store_interaction(user_id, chat.id, message, response)
    except Exception:
        pass  # Non-critical — don't break the chat if ChromaDB is down

    return chat


def check_moderation(db: Session, user_id: int, message: str, response: str) -> bool:
    """Run the moderation filter.  Returns True if flagged."""
    return moderation_service.check_and_log(db, user_id, message, response)


async def generate_admin_summary(user_id: int, user_name: str, db: Session) -> str:
    """
    Analyse the last 50 non-deleted messages and produce a 3-sentence
    emotional-status summary for the admin.  Raw chat logs are NEVER
    exposed to the admin.
    """
    recent_chats = (
        db.query(Chat)
        .filter(Chat.user_id == user_id, Chat.is_deleted == False)
        .order_by(Chat.created_at.desc())
        .limit(50)
        .all()
    )

    if not recent_chats:
        return f"{user_name} has no recent conversation history to analyse."

    # Build a condensed transcript for the LLM (admin never sees this)
    transcript_lines = []
    for chat in reversed(recent_chats):
        transcript_lines.append(f"User: {chat.message}")
        transcript_lines.append(f"AI: {chat.response}")
    transcript = "\n".join(transcript_lines)

    prompt = f"""You are a clinical psychologist reviewing a conversation between
an elderly user named {user_name} and their AI companion.

Based ONLY on the conversation below, write exactly 3 sentences summarising
{user_name}'s current emotional state, key concerns, and overall well-being.
Be compassionate but professional.  Do NOT include any direct quotes from
the conversation.

Conversation:
{transcript}

Emotional Status Summary (3 sentences):"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=300,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise Exception(f"Admin summary generation error: {str(e)}")
