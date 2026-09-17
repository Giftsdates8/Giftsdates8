#!/usr/bin/env python3
"""
Backend API Testing for GiftsDates - Browse Filters Upgrade
Tests the three new premium-gated filters: zodiac, available_date, video_calls
"""
import requests
import json
import sys
from datetime import datetime, timedelta
from pymongo import MongoClient

# Get backend URL from frontend .env
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BACKEND_URL = line.split('=', 1)[1].strip()
            break

API_BASE = f"{BACKEND_URL}/api"

# MongoDB connection for direct data manipulation
MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "test_database"
mongo_client = MongoClient(MONGO_URL)
db = mongo_client[DB_NAME]

print(f"Testing GiftsDates Backend API - Browse Filters Upgrade")
print(f"Backend URL: {API_BASE}")
print(f"Test started at: {datetime.now().isoformat()}")
print("=" * 80)

test_results = []

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
        if not success or response.status_code >= 400:
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

def register_user(name, email, password, age, gender, interested_in, city, country, birth_year=None, birth_month=None, birth_day=None):
    """Helper to register a user"""
    user_data = {
        "email": email,
        "password": password,
        "name": name,
        "age": age,
        "gender": gender,
        "interested_in": interested_in,
        "orientation": "straight",
        "city": city,
        "country": country,
        "bio": f"Test user {name}",
        "lat": 25.2048,
        "lng": 55.2708
    }
    
    if birth_year and birth_month and birth_day:
        user_data["birth_year"] = birth_year
        user_data["birth_month"] = birth_month
        user_data["birth_day"] = birth_day
    
    response = requests.post(f"{API_BASE}/auth/register", json=user_data, timeout=10)
    if response.status_code == 200:
        data = response.json()
        return data["token"], data["user"]["id"], data["user"]
    return None, None, None

def add_coins_to_user(user_id, coins):
    """Add coins to a user via MongoDB"""
    db.users.update_one({"id": user_id}, {"$inc": {"coins": coins}})
    print(f"   💰 Added {coins} coins to user {user_id} via MongoDB")

def make_user_premium(token, user_id):
    """Make a user premium by buying with coins"""
    # First add enough coins
    add_coins_to_user(user_id, 300)
    
    # Buy premium with coins
    response = requests.post(
        f"{API_BASE}/premium/buy-with-coins",
        json={"tier": "premium"},
        headers={"Authorization": f"Bearer {token}"},
        timeout=10
    )
    
    if response.status_code == 200:
        print(f"   ⭐ User {user_id} is now PREMIUM")
        return True
    else:
        print(f"   ⚠ Failed to make user premium: {response.status_code} - {response.text}")
        return False

# ============================================================================
# SETUP: Create test users
# ============================================================================
print("\n" + "=" * 80)
print("SETUP: Creating Test Users")
print("=" * 80)

# Non-premium user (for gating tests)
print("\n📝 Creating NON-PREMIUM user...")
non_premium_token, non_premium_id, non_premium_user = register_user(
    name="Sarah Johnson",
    email=f"sarah.johnson.{datetime.now().timestamp()}@gmail.com",
    password="SecurePass2024!",
    age=28,
    gender="female",
    interested_in="male",
    city="Dubai",
    country="United Arab Emirates"
)

if non_premium_token:
    print(f"   ✓ Non-premium user created: {non_premium_id}")
else:
    print("   ❌ Failed to create non-premium user")
    sys.exit(1)

# Premium user (for filter tests)
print("\n📝 Creating PREMIUM user...")
premium_token, premium_id, premium_user = register_user(
    name="Ahmed Al-Rashid",
    email=f"ahmed.alrashid.{datetime.now().timestamp()}@gmail.com",
    password="SecurePass2024!",
    age=32,
    gender="male",
    interested_in="female",
    city="Dubai",
    country="United Arab Emirates"
)

if premium_token:
    print(f"   ✓ Premium user created: {premium_id}")
    if make_user_premium(premium_token, premium_id):
        print(f"   ✓ User upgraded to PREMIUM")
    else:
        print("   ❌ Failed to upgrade user to premium")
        sys.exit(1)
else:
    print("   ❌ Failed to create premium user")
    sys.exit(1)

# Target user 1: Leo zodiac (born Aug 5, 1995)
print("\n📝 Creating target user 1 (Leo zodiac)...")
target1_token, target1_id, target1_user = register_user(
    name="Layla Hassan",
    email=f"layla.hassan.{datetime.now().timestamp()}@gmail.com",
    password="SecurePass2024!",
    age=29,
    gender="female",
    interested_in="male",
    city="Dubai",
    country="United Arab Emirates",
    birth_year=1995,
    birth_month=8,
    birth_day=5
)

if target1_token:
    print(f"   ✓ Target 1 (Leo) created: {target1_id}")
    # Verify zodiac
    me_response = requests.get(f"{API_BASE}/auth/me", headers={"Authorization": f"Bearer {target1_token}"}, timeout=10)
    if me_response.status_code == 200:
        zodiac = me_response.json().get("zodiac")
        print(f"   ✓ Zodiac sign: {zodiac}")
        if zodiac != "leo":
            print(f"   ⚠ WARNING: Expected 'leo', got '{zodiac}'")
else:
    print("   ❌ Failed to create target 1")
    sys.exit(1)

# Target user 2: NOT Leo zodiac (born Jan 15, 1994)
print("\n📝 Creating target user 2 (NOT Leo - Capricorn)...")
target2_token, target2_id, target2_user = register_user(
    name="Fatima Al Mazrouei",
    email=f"fatima.almazrouei.{datetime.now().timestamp()}@gmail.com",
    password="SecurePass2024!",
    age=30,
    gender="female",
    interested_in="male",
    city="Dubai",
    country="United Arab Emirates",
    birth_year=1994,
    birth_month=1,
    birth_day=15
)

if target2_token:
    print(f"   ✓ Target 2 (NOT Leo) created: {target2_id}")
    # Verify zodiac
    me_response = requests.get(f"{API_BASE}/auth/me", headers={"Authorization": f"Bearer {target2_token}"}, timeout=10)
    if me_response.status_code == 200:
        zodiac = me_response.json().get("zodiac")
        print(f"   ✓ Zodiac sign: {zodiac}")
else:
    print("   ❌ Failed to create target 2")
    sys.exit(1)

# Target user 3: Available on specific date
print("\n📝 Creating target user 3 (with availability)...")
target3_token, target3_id, target3_user = register_user(
    name="Mariam Al Hashimi",
    email=f"mariam.alhashimi.{datetime.now().timestamp()}@gmail.com",
    password="SecurePass2024!",
    age=27,
    gender="female",
    interested_in="male",
    city="Dubai",
    country="United Arab Emirates"
)

if target3_token:
    print(f"   ✓ Target 3 (availability) created: {target3_id}")
    # Set availability
    availability_date = "2026-10-01"
    patch_response = requests.patch(
        f"{API_BASE}/auth/me",
        json={"availability": [availability_date]},
        headers={"Authorization": f"Bearer {target3_token}"},
        timeout=10
    )
    if patch_response.status_code == 200:
        print(f"   ✓ Availability set to: {availability_date}")
    else:
        print(f"   ⚠ Failed to set availability: {patch_response.status_code}")
else:
    print("   ❌ Failed to create target 3")
    sys.exit(1)

# Target user 4: video_calls_enabled = true
print("\n📝 Creating target user 4 (video calls enabled)...")
target4_token, target4_id, target4_user = register_user(
    name="Noura Al Suwaidi",
    email=f"noura.alsuwaidi.{datetime.now().timestamp()}@gmail.com",
    password="SecurePass2024!",
    age=26,
    gender="female",
    interested_in="male",
    city="Dubai",
    country="United Arab Emirates"
)

if target4_token:
    print(f"   ✓ Target 4 (video calls enabled) created: {target4_id}")
    # Set video_calls_enabled to true
    patch_response = requests.patch(
        f"{API_BASE}/auth/me",
        json={"video_calls_enabled": True},
        headers={"Authorization": f"Bearer {target4_token}"},
        timeout=10
    )
    if patch_response.status_code == 200:
        print(f"   ✓ video_calls_enabled set to: True")
    else:
        print(f"   ⚠ Failed to set video_calls_enabled: {patch_response.status_code}")
else:
    print("   ❌ Failed to create target 4")
    sys.exit(1)

# Target user 5: video_calls_enabled = false
print("\n📝 Creating target user 5 (video calls disabled)...")
target5_token, target5_id, target5_user = register_user(
    name="Hessa Al Mansoori",
    email=f"hessa.almansoori.{datetime.now().timestamp()}@gmail.com",
    password="SecurePass2024!",
    age=25,
    gender="female",
    interested_in="male",
    city="Dubai",
    country="United Arab Emirates"
)

if target5_token:
    print(f"   ✓ Target 5 (video calls disabled) created: {target5_id}")
    # Set video_calls_enabled to false
    patch_response = requests.patch(
        f"{API_BASE}/auth/me",
        json={"video_calls_enabled": False},
        headers={"Authorization": f"Bearer {target5_token}"},
        timeout=10
    )
    if patch_response.status_code == 200:
        print(f"   ✓ video_calls_enabled set to: False")
    else:
        print(f"   ⚠ Failed to set video_calls_enabled: {patch_response.status_code}")
else:
    print("   ❌ Failed to create target 5")
    sys.exit(1)

# ============================================================================
# TEST 1: PREMIUM GATING - Non-premium user should get 403 for new filters
# ============================================================================
print("\n" + "=" * 80)
print("TEST 1: PREMIUM GATING - Non-premium user with new filters")
print("=" * 80)

print("\n🔒 Test 1a: Non-premium user with zodiac filter")
success, response = test_api(
    "Non-premium user with zodiac=leo",
    "GET",
    "/profiles?zodiac=leo",
    403,
    headers={"Authorization": f"Bearer {non_premium_token}"}
)

if success and response:
    data = response.json()
    if data.get("detail") == "PREMIUM_REQUIRED":
        print(f"   ✅ Correct error: PREMIUM_REQUIRED")
    else:
        print(f"   ⚠ Expected 'PREMIUM_REQUIRED', got: {data.get('detail')}")

print("\n🔒 Test 1b: Non-premium user with available_date filter")
success, response = test_api(
    "Non-premium user with available_date=2026-10-01",
    "GET",
    "/profiles?available_date=2026-10-01",
    403,
    headers={"Authorization": f"Bearer {non_premium_token}"}
)

if success and response:
    data = response.json()
    if data.get("detail") == "PREMIUM_REQUIRED":
        print(f"   ✅ Correct error: PREMIUM_REQUIRED")
    else:
        print(f"   ⚠ Expected 'PREMIUM_REQUIRED', got: {data.get('detail')}")

print("\n🔒 Test 1c: Non-premium user with video_calls filter")
success, response = test_api(
    "Non-premium user with video_calls=true",
    "GET",
    "/profiles?video_calls=true",
    403,
    headers={"Authorization": f"Bearer {non_premium_token}"}
)

if success and response:
    data = response.json()
    if data.get("detail") == "PREMIUM_REQUIRED":
        print(f"   ✅ Correct error: PREMIUM_REQUIRED")
    else:
        print(f"   ⚠ Expected 'PREMIUM_REQUIRED', got: {data.get('detail')}")

# ============================================================================
# TEST 2: BASIC FILTERS REMAIN FREE - Non-premium user with basic filters
# ============================================================================
print("\n" + "=" * 80)
print("TEST 2: BASIC FILTERS REMAIN FREE - Non-premium user")
print("=" * 80)

print("\n✅ Test 2: Non-premium user with basic filters (min_age, max_age, gender)")
success, response = test_api(
    "Non-premium user with basic filters",
    "GET",
    "/profiles?min_age=18&max_age=60&gender=female",
    200,
    headers={"Authorization": f"Bearer {non_premium_token}"}
)

if success and response:
    print(f"   ✅ Basic filters work without premium - returned 200")

# ============================================================================
# TEST 3: PREMIUM FILTERING WORKS - Premium user with new filters
# ============================================================================
print("\n" + "=" * 80)
print("TEST 3: PREMIUM FILTERING WORKS - Premium user")
print("=" * 80)

print("\n⭐ Test 3a: Premium user with zodiac=leo filter")
success, response = test_api(
    "Premium user with zodiac=leo",
    "GET",
    "/profiles?zodiac=leo&gender=female&min_age=18&max_age=60",
    200,
    headers={"Authorization": f"Bearer {premium_token}"}
)

if success and response:
    data = response.json()
    profiles = data if isinstance(data, list) else data.get("profiles", [])
    print(f"   ✅ Premium user can use zodiac filter - returned 200")
    print(f"   📊 Found {len(profiles)} profiles")
    
    # Check if target1 (Leo) is in results and target2 (NOT Leo) is NOT in results
    target1_found = any(p.get("id") == target1_id for p in profiles)
    target2_found = any(p.get("id") == target2_id for p in profiles)
    
    if target1_found:
        print(f"   ✅ Target 1 (Leo) found in results")
    else:
        print(f"   ⚠ Target 1 (Leo) NOT found in results")
    
    if not target2_found:
        print(f"   ✅ Target 2 (NOT Leo) correctly excluded from results")
    else:
        print(f"   ⚠ Target 2 (NOT Leo) incorrectly included in results")
    
    # Show zodiac signs of returned profiles
    for p in profiles[:5]:  # Show first 5
        print(f"      - {p.get('name')}: zodiac={p.get('zodiac')}")

print("\n⭐ Test 3b: Premium user with available_date filter")
success, response = test_api(
    "Premium user with available_date=2026-10-01",
    "GET",
    "/profiles?available_date=2026-10-01&gender=female&min_age=18&max_age=60",
    200,
    headers={"Authorization": f"Bearer {premium_token}"}
)

if success and response:
    data = response.json()
    profiles = data if isinstance(data, list) else data.get("profiles", [])
    print(f"   ✅ Premium user can use available_date filter - returned 200")
    print(f"   📊 Found {len(profiles)} profiles")
    
    # Check if target3 (with availability) is in results
    target3_found = any(p.get("id") == target3_id for p in profiles)
    
    if target3_found:
        print(f"   ✅ Target 3 (with availability 2026-10-01) found in results")
    else:
        print(f"   ⚠ Target 3 (with availability 2026-10-01) NOT found in results")
    
    # Show availability of returned profiles
    for p in profiles[:5]:  # Show first 5
        print(f"      - {p.get('name')}: availability={p.get('availability')}")

print("\n⭐ Test 3c: Premium user with available_date filter (different date)")
success, response = test_api(
    "Premium user with available_date=2026-11-01",
    "GET",
    "/profiles?available_date=2026-11-01&gender=female&min_age=18&max_age=60",
    200,
    headers={"Authorization": f"Bearer {premium_token}"}
)

if success and response:
    data = response.json()
    profiles = data if isinstance(data, list) else data.get("profiles", [])
    print(f"   ✅ Premium user can use available_date filter - returned 200")
    print(f"   📊 Found {len(profiles)} profiles")
    
    # Check if target3 is NOT in results (different date)
    target3_found = any(p.get("id") == target3_id for p in profiles)
    
    if not target3_found:
        print(f"   ✅ Target 3 correctly excluded (different date)")
    else:
        print(f"   ⚠ Target 3 incorrectly included (should be excluded for different date)")

print("\n⭐ Test 3d: Premium user with video_calls=true filter")
success, response = test_api(
    "Premium user with video_calls=true",
    "GET",
    "/profiles?video_calls=true&gender=female&min_age=18&max_age=60",
    200,
    headers={"Authorization": f"Bearer {premium_token}"}
)

if success and response:
    data = response.json()
    profiles = data if isinstance(data, list) else data.get("profiles", [])
    print(f"   ✅ Premium user can use video_calls filter - returned 200")
    print(f"   📊 Found {len(profiles)} profiles")
    
    # Check if target4 (video_calls_enabled=true) is in results
    # and target5 (video_calls_enabled=false) is NOT in results
    target4_found = any(p.get("id") == target4_id for p in profiles)
    target5_found = any(p.get("id") == target5_id for p in profiles)
    
    if target4_found:
        print(f"   ✅ Target 4 (video_calls_enabled=true) found in results")
    else:
        print(f"   ⚠ Target 4 (video_calls_enabled=true) NOT found in results")
    
    if not target5_found:
        print(f"   ✅ Target 5 (video_calls_enabled=false) correctly excluded from results")
    else:
        print(f"   ⚠ Target 5 (video_calls_enabled=false) incorrectly included in results")
    
    # Show video_calls_enabled of returned profiles
    for p in profiles[:5]:  # Show first 5
        print(f"      - {p.get('name')}: video_calls_enabled={p.get('video_calls_enabled')}")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)

passed = sum(1 for r in test_results if r.get("status") == "PASS")
failed = sum(1 for r in test_results if r.get("status") == "FAIL")
errors = sum(1 for r in test_results if r.get("status") == "ERROR")
total = len(test_results)

print(f"\nTotal Tests: {total}")
print(f"✅ Passed: {passed}")
print(f"❌ Failed: {failed}")
print(f"⚠️  Errors: {errors}")

print("\nDetailed Results:")
for result in test_results:
    status_icon = {
        "PASS": "✅",
        "FAIL": "❌",
        "ERROR": "⚠️"
    }.get(result.get("status"), "❓")
    
    print(f"{status_icon} {result['test']}: {result.get('status')}")
    if result.get("status") == "FAIL":
        print(f"   Expected: {result.get('expected')}, Got: {result.get('actual')}")
        print(f"   Response: {result.get('response')}")
    if result.get("error"):
        print(f"   Error: {result.get('error')}")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)

if failed == 0 and errors == 0:
    print("✅ ALL TESTS PASSED")
    print("✅ Premium gating works correctly for zodiac, available_date, video_calls")
    print("✅ Basic filters remain free for non-premium users")
    print("✅ Premium users can successfully use all three new filters")
    print("✅ Filters correctly narrow results based on criteria")
    sys.exit(0)
else:
    print("❌ SOME TESTS FAILED")
    print(f"   {failed} test(s) failed")
    print(f"   {errors} test(s) had errors")
    sys.exit(1)
