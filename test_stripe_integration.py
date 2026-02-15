"""
Test script for Stripe payment integration

This script tests the Stripe checkout session creation endpoint.
Make sure to:
1. Add your Stripe API keys to .env file
2. Have the FastAPI server running (uvicorn app.main:app --reload)
3. Have a valid subscription plan in the database
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

# Test credentials - replace with your actual test user credentials
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpassword123"

# Test plan ID - replace with an actual plan ID from your database
TEST_PLAN_ID = 1


def login_user(email: str, password: str) -> str:
    """Login and get access token"""
    print(f"\n1. Logging in as {email}...")
    
    response = requests.post(
        f"{API_BASE}/auth/login",
        data={
            "username": email,
            "password": password
        }
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✓ Login successful! Token: {token[:20]}...")
        return token
    else:
        print(f"✗ Login failed: {response.status_code}")
        print(response.json())
        return None


def create_checkout_session(token: str, plan_id: int) -> dict:
    """Create a Stripe checkout session"""
    print(f"\n2. Creating checkout session for plan ID {plan_id}...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "plan_id": plan_id
    }
    
    response = requests.post(
        f"{API_BASE}/payment/create-checkout",
        headers=headers,
        json=payload
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Checkout session created successfully!")
        print(f"  Session ID: {data['session_id']}")
        print(f"  Checkout URL: {data['checkout_url']}")
        return data
    else:
        print(f"✗ Failed to create checkout session: {response.status_code}")
        print(response.json())
        return None


def test_payment_flow():
    """Test the complete payment flow"""
    print("=" * 60)
    print("STRIPE PAYMENT INTEGRATION TEST")
    print("=" * 60)
    
    # Step 1: Login
    token = login_user(TEST_EMAIL, TEST_PASSWORD)
    if not token:
        print("\n✗ Test failed: Could not login")
        return
    
    # Step 2: Create checkout session
    checkout_data = create_checkout_session(token, TEST_PLAN_ID)
    if not checkout_data:
        print("\n✗ Test failed: Could not create checkout session")
        return
    
    # Step 3: Instructions for manual testing
    print("\n" + "=" * 60)
    print("NEXT STEPS FOR MANUAL TESTING:")
    print("=" * 60)
    print(f"\n1. Open this URL in your browser:")
    print(f"   {checkout_data['checkout_url']}")
    print(f"\n2. Use Stripe test card:")
    print(f"   Card Number: 4242 4242 4242 4242")
    print(f"   Expiry: Any future date (e.g., 12/34)")
    print(f"   CVC: Any 3 digits (e.g., 123)")
    print(f"   ZIP: Any 5 digits (e.g., 12345)")
    print(f"\n3. Complete the payment")
    print(f"\n4. You should be redirected to:")
    print(f"   {BASE_URL}/payment/success?session_id={checkout_data['session_id']}")
    print(f"\n5. Check your database to verify the subscription was created/activated")
    print("\n" + "=" * 60)
    print("✓ Test completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_payment_flow()
    except Exception as e:
        print(f"\n✗ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
