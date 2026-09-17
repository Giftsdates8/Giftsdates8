#!/usr/bin/env python3
"""
Test script for hide_distance profile setting gating change.
Previously VIP-only, now allows PREMIUM and VIP users.

Test scenarios:
1. Non-premium, non-VIP user setting hide_distance=true → 403 PREMIUM_REQUIRED
2. PREMIUM user setting hide_distance=true → 200 success
3. VIP user setting hide_distance=true → 200 success
4. Non-premium user setting hide_distance=false → 200 success (no gating on disable)
5. PREMIUM_LITE user setting hide_distance=true → 403 PREMIUM_REQUIRED
"""

import requests
import time
from datetime import datetime, timezone, timedelta

BASE_URL = "https://gifts-secure-save.preview.emergentagent.com/api"

def register_user(name, age, gender, city="Dubai", country="United Arab Emirates"):
    """Register a new user and return token and user data."""
    timestamp = int(time.time() * 1000)
    email = f"{name.lower().replace(' ', '.')}.{timestamp}@gmail.com"
    password = "SecurePass2024!"
    
    payload = {
        "email": email,
        "password": password,
        "name": name,
        "age": age,
        "gender": gender,
        "city": city,
        "country": country,
        "lat": 25.2048,
        "lng": 55.2708,
        "interested_in": "female"  # Required field
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=payload)
    print(f"  Register {name}: {response.status_code}")
    
    if response.status_code != 200:
        print(f"  ERROR: {response.text}")
        return None, None
    
    data = response.json()
    return data["token"], data["user"]

def fund_coins_mongodb(user_id, amount):
    """Fund coins directly via MongoDB for testing."""
    from motor.motor_asyncio import AsyncIOMotorClient
    import asyncio
    import os
    from dotenv import load_dotenv
    from pathlib import Path
    
    ROOT_DIR = Path(__file__).parent / "backend"
    if not ROOT_DIR.exists():
        ROOT_DIR = Path(__file__).parent
    load_dotenv(ROOT_DIR / '.env')
    
    mongo_url = os.environ['MONGO_URL']
    db_name = os.environ['DB_NAME']
    
    async def _fund():
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        await db.users.update_one(
            {"id": user_id},
            {"$inc": {"coins": amount}}
        )
        client.close()
    
    asyncio.run(_fund())
    print(f"  Funded {amount} coins to user {user_id}")

def buy_premium_tier(token, tier, expected_status=200):
    """Buy premium tier with coins."""
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"tier": tier}
    
    response = requests.post(f"{BASE_URL}/premium/buy-with-coins", json=payload, headers=headers)
    print(f"  Buy {tier} tier: {response.status_code}")
    
    if response.status_code != expected_status:
        print(f"  ERROR: Expected {expected_status}, got {response.status_code}")
        print(f"  Response: {response.text}")
        return False
    
    return response.status_code == 200

def patch_profile(token, updates, expected_status=200):
    """Update user profile via PATCH /api/auth/me."""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.patch(f"{BASE_URL}/auth/me", json=updates, headers=headers)
    print(f"  PATCH /auth/me {updates}: {response.status_code}")
    
    if response.status_code != expected_status:
        print(f"  ERROR: Expected {expected_status}, got {response.status_code}")
        if response.status_code >= 400:
            try:
                print(f"  Detail: {response.json().get('detail', 'N/A')}")
            except:
                print(f"  Response: {response.text}")
        return None
    
    return response.json() if response.status_code == 200 else None

def get_profile(token):
    """Get current user profile via GET /api/auth/me."""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    
    if response.status_code != 200:
        print(f"  ERROR getting profile: {response.status_code}")
        return None
    
    return response.json()

def test_scenario_1():
    """Test 1: Non-premium, non-VIP user setting hide_distance=true → 403 PREMIUM_REQUIRED"""
    print("\n" + "="*80)
    print("TEST 1: Non-premium, non-VIP user setting hide_distance=true")
    print("="*80)
    
    # Register a regular user
    token, user = register_user("Aisha Al Nahyan", 27, "female")
    if not token:
        print("❌ FAILED: Could not register user")
        return False
    
    print(f"  User ID: {user['id']}")
    print(f"  is_premium: {user.get('is_premium', False)}")
    print(f"  is_vip: {user.get('is_vip', False)}")
    
    # Try to set hide_distance=true (should fail with 403)
    result = patch_profile(token, {"hide_distance": True}, expected_status=403)
    
    if result is None:
        # Check if we got the correct error
        response = requests.patch(
            f"{BASE_URL}/auth/me",
            json={"hide_distance": True},
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 403:
            try:
                detail = response.json().get("detail", "")
                if detail == "PREMIUM_REQUIRED":
                    print("✅ PASSED: Non-premium user correctly blocked with 403 PREMIUM_REQUIRED")
                    return True
                else:
                    print(f"❌ FAILED: Got 403 but wrong detail: {detail}")
                    return False
            except:
                print(f"❌ FAILED: Got 403 but could not parse detail")
                return False
        else:
            print(f"❌ FAILED: Expected 403, got {response.status_code}")
            return False
    else:
        print("❌ FAILED: Non-premium user was allowed to set hide_distance=true")
        return False

def test_scenario_2():
    """Test 2: PREMIUM user setting hide_distance=true → 200 success"""
    print("\n" + "="*80)
    print("TEST 2: PREMIUM user setting hide_distance=true")
    print("="*80)
    
    # Register a user
    token, user = register_user("Mariam Al Falasi", 29, "female")
    if not token:
        print("❌ FAILED: Could not register user")
        return False
    
    user_id = user['id']
    print(f"  User ID: {user_id}")
    
    # Fund 300 coins
    fund_coins_mongodb(user_id, 300)
    
    # Buy premium tier
    if not buy_premium_tier(token, "premium"):
        print("❌ FAILED: Could not buy premium tier")
        return False
    
    # Verify premium status
    profile = get_profile(token)
    if not profile:
        print("❌ FAILED: Could not get profile")
        return False
    
    print(f"  is_premium: {profile.get('is_premium', False)}")
    print(f"  premium_until: {profile.get('premium_until', 'N/A')}")
    
    if not profile.get('is_premium'):
        print("❌ FAILED: User is not premium after purchase")
        return False
    
    # Try to set hide_distance=true (should succeed)
    result = patch_profile(token, {"hide_distance": True}, expected_status=200)
    
    if result is None:
        print("❌ FAILED: Could not set hide_distance=true")
        return False
    
    # Verify hide_distance is set
    profile = get_profile(token)
    if profile and profile.get('hide_distance') == True:
        print("✅ PASSED: PREMIUM user successfully set hide_distance=true")
        return True
    else:
        print(f"❌ FAILED: hide_distance not set correctly. Value: {profile.get('hide_distance') if profile else 'N/A'}")
        return False

def test_scenario_3():
    """Test 3: VIP user setting hide_distance=true → 200 success"""
    print("\n" + "="*80)
    print("TEST 3: VIP user setting hide_distance=true")
    print("="*80)
    
    # Register a user
    token, user = register_user("Noura Al Maktoum", 31, "female")
    if not token:
        print("❌ FAILED: Could not register user")
        return False
    
    user_id = user['id']
    print(f"  User ID: {user_id}")
    
    # Fund 500 coins
    fund_coins_mongodb(user_id, 500)
    
    # Buy VIP tier
    if not buy_premium_tier(token, "vip"):
        print("❌ FAILED: Could not buy VIP tier")
        return False
    
    # Verify VIP status
    profile = get_profile(token)
    if not profile:
        print("❌ FAILED: Could not get profile")
        return False
    
    print(f"  is_vip: {profile.get('is_vip', False)}")
    print(f"  vip_until: {profile.get('vip_until', 'N/A')}")
    
    if not profile.get('is_vip'):
        print("❌ FAILED: User is not VIP after purchase")
        return False
    
    # Try to set hide_distance=true (should succeed)
    result = patch_profile(token, {"hide_distance": True}, expected_status=200)
    
    if result is None:
        print("❌ FAILED: Could not set hide_distance=true")
        return False
    
    # Verify hide_distance is set
    profile = get_profile(token)
    if profile and profile.get('hide_distance') == True:
        print("✅ PASSED: VIP user successfully set hide_distance=true")
        return True
    else:
        print(f"❌ FAILED: hide_distance not set correctly. Value: {profile.get('hide_distance') if profile else 'N/A'}")
        return False

def test_scenario_4():
    """Test 4: Non-premium user setting hide_distance=false → 200 success (no gating on disable)"""
    print("\n" + "="*80)
    print("TEST 4: Non-premium user setting hide_distance=false (no gating on disable)")
    print("="*80)
    
    # Register a regular user
    token, user = register_user("Hessa Al Qasimi", 25, "female")
    if not token:
        print("❌ FAILED: Could not register user")
        return False
    
    print(f"  User ID: {user['id']}")
    print(f"  is_premium: {user.get('is_premium', False)}")
    print(f"  is_vip: {user.get('is_vip', False)}")
    
    # Try to set hide_distance=false (should succeed - no gating on disabling)
    result = patch_profile(token, {"hide_distance": False}, expected_status=200)
    
    if result is None:
        print("❌ FAILED: Could not set hide_distance=false")
        return False
    
    # Verify hide_distance is set to false
    profile = get_profile(token)
    if profile and profile.get('hide_distance') == False:
        print("✅ PASSED: Non-premium user successfully set hide_distance=false (no gating)")
        return True
    else:
        print(f"❌ FAILED: hide_distance not set correctly. Value: {profile.get('hide_distance') if profile else 'N/A'}")
        return False

def test_scenario_5():
    """Test 5: PREMIUM_LITE user setting hide_distance=true → 403 PREMIUM_REQUIRED"""
    print("\n" + "="*80)
    print("TEST 5: PREMIUM_LITE user setting hide_distance=true")
    print("="*80)
    
    # Register a user
    token, user = register_user("Shamma Al Dhaheri", 26, "female")
    if not token:
        print("❌ FAILED: Could not register user")
        return False
    
    user_id = user['id']
    print(f"  User ID: {user_id}")
    
    # Fund 150 coins
    fund_coins_mongodb(user_id, 150)
    
    # Buy premium_lite tier
    if not buy_premium_tier(token, "premium_lite"):
        print("❌ FAILED: Could not buy premium_lite tier")
        return False
    
    # Verify premium_lite status
    profile = get_profile(token)
    if not profile:
        print("❌ FAILED: Could not get profile")
        return False
    
    print(f"  is_premium_lite: {profile.get('is_premium_lite', False)}")
    print(f"  is_premium: {profile.get('is_premium', False)}")
    print(f"  is_vip: {profile.get('is_vip', False)}")
    print(f"  premium_lite_until: {profile.get('premium_lite_until', 'N/A')}")
    
    if not profile.get('is_premium_lite'):
        print("❌ FAILED: User is not premium_lite after purchase")
        return False
    
    # Try to set hide_distance=true (should fail with 403 - only full Premium and VIP allowed)
    result = patch_profile(token, {"hide_distance": True}, expected_status=403)
    
    if result is None:
        # Check if we got the correct error
        response = requests.patch(
            f"{BASE_URL}/auth/me",
            json={"hide_distance": True},
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 403:
            try:
                detail = response.json().get("detail", "")
                if detail == "PREMIUM_REQUIRED":
                    print("✅ PASSED: PREMIUM_LITE user correctly blocked with 403 PREMIUM_REQUIRED")
                    return True
                else:
                    print(f"❌ FAILED: Got 403 but wrong detail: {detail}")
                    return False
            except:
                print(f"❌ FAILED: Got 403 but could not parse detail")
                return False
        else:
            print(f"❌ FAILED: Expected 403, got {response.status_code}")
            return False
    else:
        print("❌ FAILED: PREMIUM_LITE user was allowed to set hide_distance=true")
        return False

def main():
    print("\n" + "="*80)
    print("HIDE_DISTANCE GATING TEST SUITE")
    print("Testing the change from VIP-only to PREMIUM+VIP gating")
    print("="*80)
    
    results = []
    
    # Run all test scenarios
    results.append(("Test 1: Non-premium user blocked", test_scenario_1()))
    results.append(("Test 2: PREMIUM user allowed", test_scenario_2()))
    results.append(("Test 3: VIP user allowed", test_scenario_3()))
    results.append(("Test 4: Non-premium can disable", test_scenario_4()))
    results.append(("Test 5: PREMIUM_LITE user blocked", test_scenario_5()))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! The hide_distance gating change is working correctly.")
        print("   - Non-premium users: BLOCKED ✅")
        print("   - PREMIUM users: ALLOWED ✅")
        print("   - VIP users: ALLOWED ✅")
        print("   - Disabling (false): NO GATING ✅")
        print("   - PREMIUM_LITE users: BLOCKED ✅")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the output above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
