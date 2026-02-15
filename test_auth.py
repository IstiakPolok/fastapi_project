import requests
import json

BASE_URL = "http://localhost:8000"

# Test 1: Signup
print("Testing Signup...")
signup_data = {
    "name": "Test User",
    "email": "testuser@example.com",
    "password": "password123",
    "confirm_password": "password123"
}

try:
    response = requests.post(f"{BASE_URL}/api/auth/signup", json=signup_data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print("✅ Signup successful!")
    else:
        print("❌ Signup failed!")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*50 + "\n")

# Test 2: Login
print("Testing Login...")
login_data = {
    "email": "testuser@example.com",
    "password": "password123"
}

try:
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print("✅ Login successful!")
    else:
        print("❌ Login failed!")
except Exception as e:
    print(f"Error: {e}")
