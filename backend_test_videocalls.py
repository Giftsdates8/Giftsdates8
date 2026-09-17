#!/usr/bin/env python3
"""
Backend Video Calls Toggle Persistence & Enforcement Test for GiftsDates
Tests video_calls_enabled flag persistence and enforcement in video call flow
"""
import requests
import json
import sys
from datetime import datetime

# Load backend URL from frontend .env
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BACKEND_URL = line.split('=', 1)[1].strip()
            break

BASE_URL = f"{BACKEND_URL}/api"
print(f"Testing backend at: {BASE_URL}\n")

# Test data - two realistic users
timestamp = int(datetime.now().timestamp())
USER_A = {
    "email": f"omar.khalid.{timestamp}@example.com",
    "password": "SecurePass123!",
    "name": "Omar Khalid",
    "age": 32,
    "gender": "male",
    "interested_in": "female",
    "orientation": "straight",
    "city": "Dubai",
    "country": "UAE",
    "bio": "Tech entrepreneur and travel enthusiast",
    "language": "en"
}

USER_B = {
    "email": f"fatima.ahmed.{timestamp}@example.com",
    "password": "SecurePass456!",
    "name": "Fatima Ahmed",
    "age": 28,
    "gender": "female",
    "interested_in": "male",
    "orientation": "straight",
    "city": "Dubai",
    "country": "UAE",
    "bio": "Fashion designer and coffee lover",
    "language": "en"
}

def register_user(user_data, user_label):
    """Register a new user and return token and user_id"""
    print(f"\nRegistering {user_label}: {user_data['email']}")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json=user_data,
            timeout=10
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("token")
            user = data.get("user")
            user_id = user.get("id") if user else None
            
            if token and user_id:
                print(f"✅ {user_label} registered successfully")
                print(f"   User ID: {user_id}")
                print(f"   Token: {token[:20]}...")
                return token, user_id
            else:
                print(f"❌ {user_label} registration failed: missing token or user_id")
                return None, None
        else:
            print(f"❌ {user_label} registration failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return None, None
    except Exception as e:
        print(f"❌ Error registering {user_label}: {e}")
        return None, None

def test_patch_video_calls_disabled(token, user_label):
    """Test 1: PATCH /api/auth/me to set video_calls_enabled=false"""
    print("\n" + "=" * 60)
    print(f"TEST 1: PATCH /api/auth/me - Set video_calls_enabled=false for {user_label}")
    print("=" * 60)
    
    try:
        response = requests.patch(
            f"{BASE_URL}/auth/me",
            json={"video_calls_enabled": False},
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            user = response.json()
            video_calls_enabled = user.get("video_calls_enabled")
            print(f"Response video_calls_enabled: {video_calls_enabled}")
            
            if video_calls_enabled is False:
                print(f"✅ PASS: video_calls_enabled set to False for {user_label}")
                return True
            else:
                print(f"❌ FAIL: video_calls_enabled is {video_calls_enabled}, expected False")
                return False
        else:
            print(f"❌ FAIL: PATCH failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ FAIL: Error during PATCH: {e}")
        return False

def test_get_video_calls_persistence(token, user_label):
    """Test 2: GET /api/auth/me to verify video_calls_enabled=false persists"""
    print("\n" + "=" * 60)
    print(f"TEST 2: GET /api/auth/me - Verify video_calls_enabled persistence for {user_label}")
    print("=" * 60)
    
    try:
        response = requests.get(
            f"{BASE_URL}/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            user = response.json()
            video_calls_enabled = user.get("video_calls_enabled")
            print(f"Response video_calls_enabled: {video_calls_enabled}")
            
            if video_calls_enabled is False:
                print(f"✅ PASS: video_calls_enabled persisted as False for {user_label}")
                return True
            else:
                print(f"❌ FAIL: video_calls_enabled is {video_calls_enabled}, expected False (not persisted)")
                return False
        else:
            print(f"❌ FAIL: GET failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ FAIL: Error during GET: {e}")
        return False

def test_video_call_disabled_enforcement(token_a, user_b_id):
    """Test 3: POST /api/videocalls/start should return 403 VIDEO_CALLS_DISABLED"""
    print("\n" + "=" * 60)
    print("TEST 3: POST /api/videocalls/start - Verify VIDEO_CALLS_DISABLED enforcement")
    print("=" * 60)
    print(f"User A attempting to start video call with User B (video_calls_enabled=false)")
    print(f"Target User B ID: {user_b_id}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/videocalls/start",
            json={"target_id": user_b_id, "minutes": 1},
            headers={"Authorization": f"Bearer {token_a}"},
            timeout=10
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 403:
            data = response.json()
            detail = data.get("detail")
            print(f"Error detail: {detail}")
            
            if detail == "VIDEO_CALLS_DISABLED":
                print("✅ PASS: Video call correctly blocked with VIDEO_CALLS_DISABLED")
                return True
            else:
                print(f"❌ FAIL: Got 403 but detail is '{detail}', expected 'VIDEO_CALLS_DISABLED'")
                return False
        else:
            print(f"❌ FAIL: Expected 403 VIDEO_CALLS_DISABLED, got status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ FAIL: Error during video call start: {e}")
        return False

def test_patch_video_calls_enabled(token, user_label):
    """Test 4: PATCH /api/auth/me to set video_calls_enabled=true"""
    print("\n" + "=" * 60)
    print(f"TEST 4: PATCH /api/auth/me - Set video_calls_enabled=true for {user_label}")
    print("=" * 60)
    
    try:
        response = requests.patch(
            f"{BASE_URL}/auth/me",
            json={"video_calls_enabled": True},
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            user = response.json()
            video_calls_enabled = user.get("video_calls_enabled")
            print(f"Response video_calls_enabled: {video_calls_enabled}")
            
            if video_calls_enabled is True:
                print(f"✅ PASS: video_calls_enabled set to True for {user_label}")
                return True
            else:
                print(f"❌ FAIL: video_calls_enabled is {video_calls_enabled}, expected True")
                return False
        else:
            print(f"❌ FAIL: PATCH failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ FAIL: Error during PATCH: {e}")
        return False

def test_video_call_enabled_no_disabled_error(token_a, user_b_id):
    """Test 5: POST /api/videocalls/start should NOT return VIDEO_CALLS_DISABLED"""
    print("\n" + "=" * 60)
    print("TEST 5: POST /api/videocalls/start - Verify no VIDEO_CALLS_DISABLED error")
    print("=" * 60)
    print(f"User A attempting to start video call with User B (video_calls_enabled=true)")
    print(f"Target User B ID: {user_b_id}")
    print("Note: May fail with insufficient coins, which is acceptable")
    
    try:
        response = requests.post(
            f"{BASE_URL}/videocalls/start",
            json={"target_id": user_b_id, "minutes": 1},
            headers={"Authorization": f"Bearer {token_a}"},
            timeout=10
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ PASS: Video call started successfully (User A had enough coins)")
            return True
        elif response.status_code == 400:
            data = response.json()
            detail = data.get("detail")
            print(f"Error detail: {detail}")
            
            if detail == "Insufficient coins":
                print("✅ PASS: Video call failed with insufficient coins (expected, not VIDEO_CALLS_DISABLED)")
                return True
            else:
                print(f"❌ FAIL: Got 400 with unexpected detail: {detail}")
                return False
        elif response.status_code == 403:
            data = response.json()
            detail = data.get("detail")
            print(f"Error detail: {detail}")
            
            if detail == "VIDEO_CALLS_DISABLED":
                print("❌ FAIL: Still getting VIDEO_CALLS_DISABLED after enabling")
                return False
            else:
                print(f"❌ FAIL: Got 403 with detail: {detail}")
                return False
        else:
            print(f"⚠️  WARNING: Unexpected status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ FAIL: Error during video call start: {e}")
        return False

def main():
    """Run all video calls toggle tests"""
    print("\n" + "=" * 60)
    print("GIFTSDATES VIDEO CALLS TOGGLE PERSISTENCE & ENFORCEMENT TEST")
    print("=" * 60)
    print(f"Backend URL: {BASE_URL}")
    print(f"Test started at: {datetime.now().isoformat()}")
    print("=" * 60)
    
    results = []
    
    # Register User A and User B
    print("\n" + "=" * 60)
    print("SETUP: Registering Test Users")
    print("=" * 60)
    
    token_a, user_a_id = register_user(USER_A, "User A")
    token_b, user_b_id = register_user(USER_B, "User B")
    
    if not (token_a and user_a_id and token_b and user_b_id):
        print("\n❌ CRITICAL: Failed to register test users. Cannot proceed with tests.")
        return 1
    
    print(f"\n✅ Setup complete:")
    print(f"   User A: {user_a_id}")
    print(f"   User B: {user_b_id}")
    
    # Test 1: Set video_calls_enabled=false for User B
    results.append(("Set video_calls_enabled=false", test_patch_video_calls_disabled(token_b, "User B")))
    
    # Test 2: Verify persistence of video_calls_enabled=false
    results.append(("Verify video_calls_enabled persistence", test_get_video_calls_persistence(token_b, "User B")))
    
    # Test 3: Attempt video call with User B (should get VIDEO_CALLS_DISABLED)
    results.append(("VIDEO_CALLS_DISABLED enforcement", test_video_call_disabled_enforcement(token_a, user_b_id)))
    
    # Test 4: Set video_calls_enabled=true for User B
    results.append(("Set video_calls_enabled=true", test_patch_video_calls_enabled(token_b, "User B")))
    
    # Test 5: Attempt video call with User B (should NOT get VIDEO_CALLS_DISABLED)
    results.append(("No VIDEO_CALLS_DISABLED after enable", test_video_call_enabled_no_disabled_error(token_a, user_b_id)))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
