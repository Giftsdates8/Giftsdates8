#!/usr/bin/env python3
"""
Backend API Testing for GiftsDates - Auth/Login Persistence Testing
Tests the core authentication flows after GitHub restore.
"""
import requests
import json
import sys
from datetime import datetime

# Get backend URL from frontend .env
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BACKEND_URL = line.split('=', 1)[1].strip()
            break

API_BASE = f"{BACKEND_URL}/api"

print(f"Testing GiftsDates Backend API")
print(f"Backend URL: {API_BASE}")
print(f"Test started at: {datetime.now().isoformat()}")
print("=" * 80)

# Test data - realistic user for Dubai
test_user = {
    "email": f"fatima.almazrouei.{datetime.now().timestamp()}@gmail.com",
    "password": "SecurePass2024!",
    "name": "Fatima Al Mazrouei",
    "age": 26,
    "gender": "female",
    "interested_in": "male",
    "orientation": "straight",
    "city": "Dubai",
    "country": "United Arab Emirates",
    "bio": "Love exploring new restaurants and beach walks",
    "lat": 25.2048,
    "lng": 55.2708
}

test_results = []
token = None
user_id = None

def test_api(name, method, endpoint, expected_status, **kwargs):
    """Helper function to test API endpoints"""
    global test_results
    url = f"{API_BASE}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=10, **kwargs)
        elif method == "POST":
            response = requests.post(url, timeout=10, **kwargs)
        elif method == "PATCH":
            response = requests.patch(url, timeout=10, **kwargs)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        success = response.status_code == expected_status
        
        result = {
            "test": name,
            "status": "PASS" if success else "FAIL",
            "expected": expected_status,
            "actual": response.status_code,
            "url": url,
            "response": None
        }
        
        try:
            result["response"] = response.json()
        except:
            result["response"] = response.text[:200]
        
        test_results.append(result)
        
        status_icon = "✅" if success else "❌"
        print(f"\n{status_icon} Test: {name}")
        print(f"   Expected: {expected_status}, Got: {response.status_code}")
        if not success:
            print(f"   Response: {result['response']}")
        
        return success, response
        
    except Exception as e:
        result = {
            "test": name,
            "status": "ERROR",
            "error": str(e),
            "url": url
        }
        test_results.append(result)
        print(f"\n❌ Test: {name}")
        print(f"   ERROR: {str(e)}")
        return False, None

print("\n" + "=" * 80)
print("TEST 1: Root Health Check - GET /api/")
print("=" * 80)
success, response = test_api(
    "Root Health Check",
    "GET",
    "/",
    200
)

if success and response:
    data = response.json()
    if data.get("service") == "GiftsDates" and data.get("ok") == True:
        print("   ✓ Health check response correct: {'service': 'GiftsDates', 'ok': True}")
    else:
        print(f"   ⚠ Unexpected response format: {data}")

print("\n" + "=" * 80)
print("TEST 2: User Registration - POST /api/auth/register")
print("=" * 80)
print(f"   Registering user: {test_user['name']} ({test_user['email']})")
print(f"   Location: {test_user['city']}, {test_user['country']}")

success, response = test_api(
    "User Registration",
    "POST",
    "/auth/register",
    200,
    json=test_user
)

if success and response:
    data = response.json()
    if "token" in data and "user" in data:
        token = data["token"]
        user_id = data["user"].get("id")
        print(f"   ✓ Registration successful")
        print(f"   ✓ JWT token received: {token[:20]}...")
        print(f"   ✓ User ID: {user_id}")
        print(f"   ✓ User email: {data['user'].get('email')}")
        print(f"   ✓ User name: {data['user'].get('name')}")
        
        # Check for spin bonus
        if "spin_bonus" in data:
            print(f"   ✓ Spin bonus: {data['spin_bonus']}")
    else:
        print(f"   ⚠ Missing token or user in response: {data.keys()}")

print("\n" + "=" * 80)
print("TEST 3: User Login - POST /api/auth/login")
print("=" * 80)
print(f"   Logging in with: {test_user['email']}")

success, response = test_api(
    "User Login",
    "POST",
    "/auth/login",
    200,
    json={
        "email": test_user["email"],
        "password": test_user["password"]
    }
)

if success and response:
    data = response.json()
    if "token" in data and "user" in data:
        login_token = data["token"]
        login_user_id = data["user"].get("id")
        print(f"   ✓ Login successful")
        print(f"   ✓ JWT token received: {login_token[:20]}...")
        print(f"   ✓ User ID matches registration: {login_user_id == user_id}")
        
        if login_user_id == user_id:
            print(f"   ✓ User persistence confirmed - same user ID")
        else:
            print(f"   ⚠ User ID mismatch! Registration: {user_id}, Login: {login_user_id}")
        
        # Update token to use login token
        token = login_token
    else:
        print(f"   ⚠ Missing token or user in response: {data.keys()}")

print("\n" + "=" * 80)
print("TEST 4: JWT Authentication - GET /api/auth/me")
print("=" * 80)
print(f"   Using JWT token from login")

if not token:
    print("   ⚠ No token available, skipping test")
    test_results.append({
        "test": "JWT Authentication",
        "status": "SKIP",
        "reason": "No token from previous tests"
    })
else:
    success, response = test_api(
        "JWT Authentication",
        "GET",
        "/auth/me",
        200,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if success and response:
        data = response.json()
        print(f"   ✓ JWT authentication successful")
        print(f"   ✓ User ID: {data.get('id')}")
        print(f"   ✓ Email: {data.get('email')}")
        print(f"   ✓ Name: {data.get('name')}")
        print(f"   ✓ Coins: {data.get('coins', 0)}")
        print(f"   ✓ Verified: {data.get('verified', False)}")
        
        # Verify it's the same user
        if data.get("id") == user_id and data.get("email") == test_user["email"]:
            print(f"   ✓ User data matches registration")
        else:
            print(f"   ⚠ User data mismatch!")

print("\n" + "=" * 80)
print("TEST 5: JWT Token Persistence - Multiple /auth/me Calls")
print("=" * 80)
print(f"   Testing token persistence across fresh requests")

if not token:
    print("   ⚠ No token available, skipping test")
    test_results.append({
        "test": "JWT Token Persistence",
        "status": "SKIP",
        "reason": "No token from previous tests"
    })
else:
    # Make 3 separate requests with the same token
    all_success = True
    for i in range(1, 4):
        print(f"\n   Request {i}/3:")
        success, response = test_api(
            f"JWT Persistence Check {i}",
            "GET",
            "/auth/me",
            200,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if success and response:
            data = response.json()
            if data.get("id") == user_id:
                print(f"      ✓ Token valid, user ID matches: {user_id}")
            else:
                print(f"      ⚠ User ID mismatch!")
                all_success = False
        else:
            all_success = False
    
    if all_success:
        print(f"\n   ✅ JWT token persistence confirmed - all 3 requests successful")
        print(f"   ✅ MongoDB session persistence working correctly")

print("\n" + "=" * 80)
print("TEST 6: Re-login to Verify User Persistence in MongoDB")
print("=" * 80)
print(f"   Logging in again to confirm user persists in database")

success, response = test_api(
    "Re-login Verification",
    "POST",
    "/auth/login",
    200,
    json={
        "email": test_user["email"],
        "password": test_user["password"]
    }
)

if success and response:
    data = response.json()
    if data.get("user", {}).get("id") == user_id:
        print(f"   ✅ User persists in MongoDB - re-login successful")
        print(f"   ✅ Same user ID returned: {user_id}")
    else:
        print(f"   ⚠ User ID changed after re-login!")

# Summary
print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)

passed = sum(1 for r in test_results if r.get("status") == "PASS")
failed = sum(1 for r in test_results if r.get("status") == "FAIL")
errors = sum(1 for r in test_results if r.get("status") == "ERROR")
skipped = sum(1 for r in test_results if r.get("status") == "SKIP")
total = len(test_results)

print(f"\nTotal Tests: {total}")
print(f"✅ Passed: {passed}")
print(f"❌ Failed: {failed}")
print(f"⚠️  Errors: {errors}")
print(f"⏭️  Skipped: {skipped}")

print("\nDetailed Results:")
for result in test_results:
    status_icon = {
        "PASS": "✅",
        "FAIL": "❌",
        "ERROR": "⚠️",
        "SKIP": "⏭️"
    }.get(result.get("status"), "❓")
    
    print(f"{status_icon} {result['test']}: {result.get('status')}")
    if result.get("status") == "FAIL":
        print(f"   Expected: {result.get('expected')}, Got: {result.get('actual')}")
    if result.get("error"):
        print(f"   Error: {result.get('error')}")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)

if failed == 0 and errors == 0:
    print("✅ ALL TESTS PASSED")
    print("✅ Auth/Login persistence is working correctly")
    print("✅ Users can register, login, and maintain authenticated sessions")
    print("✅ JWT tokens work consistently across multiple requests")
    print("✅ MongoDB persistence confirmed")
    sys.exit(0)
else:
    print("❌ SOME TESTS FAILED")
    print(f"   {failed} test(s) failed")
    print(f"   {errors} test(s) had errors")
    sys.exit(1)
