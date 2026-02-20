#!/usr/bin/env python3
"""
CLI AI Test Suite — Senior Companion MVP (Milestone 3)

Verifies:
  1. User can sign up / log in
  2. AI remembers a fact from a previous exchange (memory recall)
  3. AI uses the user's name (identity layer)

Usage:
    # Make sure the server is running on localhost:8000
    python tests/cli_ai_test.py
"""

import sys
import json
import time
import random
import string
import requests

BASE_URL = "http://localhost:8001"

# ── helpers ──────────────────────────────────────────────────────────────────

def _random_email() -> str:
    tag = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"testuser_{tag}@example.com"


def _print_result(label: str, passed: bool, detail: str = ""):
    icon = "✅" if passed else "❌"
    msg = f"  {icon}  {label}"
    if detail:
        msg += f"  —  {detail}"
    print(msg)


# ── test steps ───────────────────────────────────────────────────────────────

def test_signup_and_login() -> str:
    """Sign up a new user and return a JWT token."""
    email = _random_email()
    name = "Martha"
    password = "TestPass123!"

    print(f"\n{'='*60}")
    print(f"  TEST 1 — Sign Up & Login  (name={name})")
    print(f"{'='*60}")

    # Sign up
    resp = requests.post(f"{BASE_URL}/api/auth/signup", json={
        "name": name,
        "email": email,
        "password": password,
        "confirm_password": password,
    })

    if resp.status_code in (200, 201):
        token = resp.json().get("access_token")
        _print_result("Signup", True, f"email={email}")
        return token
    else:
        _print_result("Signup", False, resp.text)
        sys.exit(1)


def test_memory_recall(token: str) -> str:
    """Send a fact, then ask the AI to recall it."""
    headers = {"Authorization": f"Bearer {token}"}

    print(f"\n{'='*60}")
    print("  TEST 2 — Memory Recall")
    print(f"{'='*60}")

    # Send a unique fact
    fact_message = "I want to tell you something important — my granddaughter's name is Lily and she just turned 7!"
    print(f"  → Sending fact: \"{fact_message[:60]}...\"")

    resp1 = requests.post(
        f"{BASE_URL}/api/chat",
        json={"message": fact_message},
        headers=headers,
    )
    if resp1.status_code != 200:
        _print_result("Send fact", False, resp1.text)
        sys.exit(1)

    ai_reply_1 = resp1.json()["response"]
    print(f"  ← AI: \"{ai_reply_1[:80]}...\"")
    _print_result("Send fact", True)

    # Small delay to let embeddings settle
    time.sleep(1)

    # Ask the AI to recall the fact
    recall_message = "Do you remember my granddaughter's name? Can you tell me?"
    print(f"  → Asking recall: \"{recall_message}\"")

    resp2 = requests.post(
        f"{BASE_URL}/api/chat",
        json={"message": recall_message},
        headers=headers,
    )
    if resp2.status_code != 200:
        _print_result("Recall", False, resp2.text)
        sys.exit(1)

    ai_reply_2 = resp2.json()["response"]
    print(f"  ← AI: \"{ai_reply_2[:80]}...\"")

    # Check if "Lily" is in the response
    recall_passed = "lily" in ai_reply_2.lower()
    _print_result(
        "Memory recall (contains 'Lily')",
        recall_passed,
        "FOUND" if recall_passed else "NOT FOUND — AI may not have recalled the fact",
    )

    return ai_reply_2


def test_identity_layer(token: str) -> None:
    """Verify the AI uses the user's name."""
    headers = {"Authorization": f"Bearer {token}"}

    print(f"\n{'='*60}")
    print("  TEST 3 — Identity Layer (Name Usage)")
    print(f"{'='*60}")

    resp = requests.post(
        f"{BASE_URL}/api/chat",
        json={"message": "How are you doing today, my friend?"},
        headers=headers,
    )
    if resp.status_code != 200:
        _print_result("Identity", False, resp.text)
        sys.exit(1)

    ai_reply = resp.json()["response"]
    print(f"  ← AI: \"{ai_reply[:80]}...\"")

    name_used = "martha" in ai_reply.lower()
    _print_result(
        "AI uses user name ('Martha')",
        name_used,
        "FOUND" if name_used else "NOT FOUND — AI may not have used the name",
    )


def test_chat_history(token: str) -> None:
    """Verify the unified timeline returns messages."""
    headers = {"Authorization": f"Bearer {token}"}

    print(f"\n{'='*60}")
    print("  TEST 4 — Chat History (Unified Timeline)")
    print(f"{'='*60}")

    resp = requests.get(f"{BASE_URL}/api/chat/history", headers=headers)
    if resp.status_code != 200:
        _print_result("History", False, resp.text)
        return

    data = resp.json()
    total = data.get("total", 0)
    _print_result(
        "Chat history",
        total >= 3,
        f"{total} messages in timeline",
    )


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "=" * 60)
    print("  Senior Companion MVP — CLI Test Suite")
    print("=" * 60)

    try:
        requests.get(f"{BASE_URL}/health")
    except requests.ConnectionError:
        print(f"\n  ❌  Server not reachable at {BASE_URL}")
        print("     Start it with: uvicorn app.main:app --reload --port 8000")
        sys.exit(1)

    token = test_signup_and_login()
    test_memory_recall(token)
    test_identity_layer(token)
    test_chat_history(token)

    print(f"\n{'='*60}")
    print("  All tests complete!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
