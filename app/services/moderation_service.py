"""
Moderation Service — Lightweight keyword filter for AI responses.

Checks every AI response against a configurable list of flagged keywords.
If a match is found, logs the exchange to the ModerationLog table for
Admin review.  This avoids an extra LLM call for every message.
"""

import re
from sqlalchemy.orm import Session
from app.models.moderation_log import ModerationLog

# --------------------------------------------------------------------------- #
#  Configurable flag-word list  (extend as needed)
# --------------------------------------------------------------------------- #

FLAGGED_KEYWORDS: list[str] = [
    # Self-harm / crisis
    "suicide", "self-harm", "kill myself", "end my life", "want to die",
    # Abuse-related
    "abuse", "molest", "assault",
    # Extreme profanity (sample)
    "fuck you", "go to hell",
    # Medical misinformation signals
    "stop taking your medication", "don't see a doctor",
]

# Pre-compile a single case-insensitive regex for speed
_FLAG_PATTERN = re.compile(
    "|".join(re.escape(kw) for kw in FLAGGED_KEYWORDS),
    re.IGNORECASE,
)


# --------------------------------------------------------------------------- #
#  Public API
# --------------------------------------------------------------------------- #

def check_and_log(
    db: Session,
    user_id: int,
    user_message: str,
    ai_response: str,
) -> bool:
    """
    Scan the AI response (and optionally the user message) for flagged
    content.  Returns ``True`` if the exchange was flagged.

    A ``ModerationLog`` record is created for every match so admins can
    review it.
    """
    flagged_parts: list[str] = []

    # Check user message
    user_matches = _FLAG_PATTERN.findall(user_message)
    if user_matches:
        flagged_parts.append(f"User message contained: {', '.join(set(user_matches))}")

    # Check AI response
    ai_matches = _FLAG_PATTERN.findall(ai_response)
    if ai_matches:
        flagged_parts.append(f"AI response contained: {', '.join(set(ai_matches))}")

    if not flagged_parts:
        return False

    reason = "; ".join(flagged_parts)

    log_entry = ModerationLog(
        user_id=user_id,
        message_content=user_message,
        ai_response=ai_response,
        reason=reason,
    )
    db.add(log_entry)
    db.commit()

    return True
