"""Test script for Admin Dashboard APIs"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_admin_apis():
    print("=" * 60)
    print("ADMIN DASHBOARD API TESTS")
    print("=" * 60)
    
    # Test 1: Admin Signup
    print("\n1. Testing Admin Signup...")
    admin_data = {
        "name": "Admin User",
        "email": "admin@example.com",
        "password": "admin123",
        "confirm_password": "admin123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/admin/signup", json=admin_data)
        print(f"   Status: {response.status_code}")
        if response.status_code in [200, 201]:
            print("   ✅ Admin signup successful!")
        elif response.status_code == 400 and "already registered" in response.text:
            print("   ℹ️  Admin already exists")
        else:
            print(f"   ❌ Failed: {response.text[:100]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Admin Login
    print("\n2. Testing Admin Login...")
    login_data = {
        "email": "admin@example.com",
        "password": "admin123"
    }
    
    token = None
    try:
        response = requests.post(f"{BASE_URL}/api/admin/login", json=login_data)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            token = response.json().get("access_token")
            print("   ✅ Admin login successful!")
            print(f"   Token: {token[:30]}...")
        else:
            print(f"   ❌ Failed: {response.text[:100]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    if not token:
        print("\n❌ Cannot continue without token")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 3: Dashboard Stats
    print("\n3. Testing Dashboard Stats...")
    try:
        response = requests.get(f"{BASE_URL}/api/admin/dashboard/stats", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            stats = response.json()
            print(f"   ✅ Stats: {json.dumps(stats, indent=6)}")
        else:
            print(f"   ❌ Failed: {response.text[:100]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Revenue Chart
    print("\n4. Testing Revenue Chart...")
    try:
        response = requests.get(f"{BASE_URL}/api/admin/dashboard/revenue-chart", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Revenue chart data retrieved!")
        else:
            print(f"   ❌ Failed: {response.text[:100]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 5: User List
    print("\n5. Testing User List...")
    try:
        response = requests.get(f"{BASE_URL}/api/admin/users", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Found {data['total_count']} users")
        else:
            print(f"   ❌ Failed: {response.text[:100]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 6: Create Subscription Plan
    print("\n6. Testing Create Subscription Plan...")
    plan_data = {
        "name": "Premium Monthly",
        "description": "Premium features for one month",
        "price": 9.99,
        "duration_days": 30,
        "features": ["Feature 1", "Feature 2", "Feature 3"]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/admin/plans", json=plan_data, headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code in [200, 201]:
            print("   ✅ Subscription plan created!")
        elif response.status_code == 400:
            print("   ℹ️  Plan already exists")
        else:
            print(f"   ❌ Failed: {response.text[:100]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 7: List Plans
    print("\n7. Testing List Subscription Plans...")
    try:
        response = requests.get(f"{BASE_URL}/api/admin/plans", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Found {data['total_count']} plans")
        else:
            print(f"   ❌ Failed: {response.text[:100]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 8: Privacy Policy
    print("\n8. Testing Privacy Policy...")
    try:
        response = requests.get(f"{BASE_URL}/api/admin/settings/privacy-policy")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Privacy policy retrieved!")
        else:
            print(f"   ❌ Failed: {response.text[:100]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("TESTS COMPLETED!")
    print("=" * 60)

if __name__ == "__main__":
    test_admin_apis()
