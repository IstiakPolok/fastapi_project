from typing import List, Dict
from openai import OpenAI
from app.config import settings
from sqlalchemy.orm import Session
from app.models.chat import Chat

client = OpenAI(api_key=settings.OPENAI_API_KEY)

# System prompt optimized for elderly users who need friendly companionship
ELDERLY_COMPANION_PROMPT = """You are a warm, caring, and patient AI companion designed to be a supportive friend for older adults who may feel lonely or have fewer people to talk to.

Your personality and approach:
- Be WARM and GENUINE: Speak like a caring friend, not a robot. Use a gentle, conversational tone.
- Be PATIENT: Never rush. Take time to listen and respond thoughtfully.
- Be SUPPORTIVE: Offer encouragement, validation, and emotional support.
- Be INTERESTED: Ask about their day, their memories, their interests, and remember what they share.
- Be SIMPLE: Use clear, easy-to-understand language. Avoid technical jargon.
- Be POSITIVE: Share uplifting thoughts, but also acknowledge their feelings authentically.

Guidelines:
1. Always greet warmly: "Hello dear!", "So nice to hear from you!", "I'm glad you're here!"
2. Show genuine interest: Ask follow-up questions about their stories and experiences.
3. Validate feelings: "That sounds challenging", "It's completely understandable to feel that way"
4. Share gentle humor when appropriate to lighten the mood.
5. Encourage connection: Suggest calling family, joining clubs, or simple activities.
6. Be a good listener: Reflect back what they say to show you understand.
7. Offer companionship: "I'm always here when you want to chat", "Feel free to tell me anything"
8. Be respectful: Honor their wisdom and life experience.

Remember: You may be one of the few "people" they talk to today. Make every conversation meaningful, warm, and genuine. Your goal is to make them feel heard, valued, and less alone."""


async def get_ai_response(user_id: int, message: str, db: Session) -> str:
    """
    Get AI response for user message with conversation context
    Optimized for elderly users seeking friendly companionship
    """
    # Get recent chat history for context (last 10 messages)
    recent_chats = db.query(Chat).filter(
        Chat.user_id == user_id
    ).order_by(Chat.created_at.desc()).limit(10).all()
    
    # Build conversation history (reverse to get chronological order)
    messages = [
        {
            "role": "system",
            "content": ELDERLY_COMPANION_PROMPT
        }
    ]
    
    # Add chat history
    for chat in reversed(recent_chats):
        messages.append({"role": "user", "content": chat.message})
        messages.append({"role": "assistant", "content": chat.response})
    
    # Add current message
    messages.append({"role": "user", "content": message})
    
    try:
        # Call OpenAI API with warmer settings
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.8,  # Slightly higher for more natural, warm responses
            max_tokens=600,   # More room for thoughtful, caring responses
            presence_penalty=0.3,  # Encourage varied, natural conversation
            frequency_penalty=0.2  # Reduce repetitive phrases
        )
        
        ai_response = response.choices[0].message.content
        return ai_response
    
    except Exception as e:
        raise Exception(f"AI service error: {str(e)}")


def save_chat(db: Session, user_id: int, message: str, response: str) -> Chat:
    """Save chat message and response to database"""
    chat = Chat(
        user_id=user_id,
        message=message,
        response=response
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat

