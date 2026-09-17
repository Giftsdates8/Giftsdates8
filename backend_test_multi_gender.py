#!/usr/bin/env python3
"""
Test the new Browse multi-gender BASIC filter on GET /api/profiles.
Tests that the `genders` parameter (comma-separated) is NOT premium-gated
and correctly filters profiles by multiple genders.
"""
import requests
import time

BASE_URL = "https://gifts-secure-save.preview.emergentagent.com/api"

def register_user(email, password, name, age, gender, city="Dubai", country="UAE", interested_in="male"):
    """Register a new user and return token and user_id."""
    payload = {
        "email": email,
        "password": password,
        "name": name,
        "age": age,
        "gender": gender,
        "interested_in": interested_in,
        "city": city,
        "country": country,
        "lat": 25.2048,
        "lng": 55.2708
    }
    resp = requests.post(f"{BASE_URL}/auth/register", json=payload)
    print(f"Register {name} ({gender}): {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        return data["token"], data["user"]["id"]
    else:
        print(f"  Error: {resp.text}")
        return None, None

def get_profiles(token, params):
    """Call GET /api/profiles with given query params."""
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/profiles", headers=headers, params=params)
    return resp

def main():
    timestamp = int(time.time())
    
    print("=" * 80)
    print("TEST: Browse Multi-Gender BASIC Filter (GET /api/profiles?genders=a,b)")
    print("=" * 80)
    
    # Step 1: Register 3 target users with distinct genders
    print("\n[1] Registering 3 target users with distinct genders...")
    
    target_female_token, target_female_id = register_user(
        email=f"target.female.{timestamp}@test.com",
        password="TestPass123!",
        name="Layla Hassan",
        age=28,
        gender="female",
        interested_in="male"
    )
    
    target_male_token, target_male_id = register_user(
        email=f"target.male.{timestamp}@test.com",
        password="TestPass123!",
        name="Ahmed Al-Rashid",
        age=30,
        gender="male",
        interested_in="female"
    )
    
    target_nonbinary_token, target_nonbinary_id = register_user(
        email=f"target.nonbinary.{timestamp}@test.com",
        password="TestPass123!",
        name="Jordan Smith",
        age=26,
        gender="non_binary",
        interested_in="female"
    )
    
    if not all([target_female_id, target_male_id, target_nonbinary_id]):
        print("❌ FAILED: Could not register all target users")
        return
    
    print(f"✅ Target users registered:")
    print(f"   - Female: {target_female_id}")
    print(f"   - Male: {target_male_id}")
    print(f"   - Non-binary: {target_nonbinary_id}")
    
    # Step 2: Register a searching NON-premium user
    print("\n[2] Registering a NON-premium searching user...")
    
    searcher_token, searcher_id = register_user(
        email=f"searcher.{timestamp}@test.com",
        password="TestPass123!",
        name="Fatima Al Mazrouei",
        age=25,
        gender="female",
        interested_in="female"
    )
    
    if not searcher_id:
        print("❌ FAILED: Could not register searcher user")
        return
    
    print(f"✅ Searcher user registered: {searcher_id}")
    
    # Wait a moment for database consistency
    time.sleep(1)
    
    # Test 1: Multi-gender filter (female,non_binary) - should NOT require premium
    print("\n[3] TEST 1: GET /api/profiles?genders=female,non_binary")
    print("   Expected: HTTP 200 (NOT 403), includes female and non_binary, excludes male")
    
    resp = get_profiles(searcher_token, {
        "genders": "female,non_binary",
        "min_age": 18,
        "max_age": 99
    })
    
    print(f"   Status: {resp.status_code}")
    
    if resp.status_code == 403:
        print(f"   ❌ FAILED: Got 403 PREMIUM_REQUIRED - genders filter should be BASIC (not premium-gated)")
        print(f"   Response: {resp.text}")
    elif resp.status_code == 200:
        data = resp.json()
        # API returns a list directly
        profiles = data if isinstance(data, list) else data.get("profiles", [])
        profile_ids = [p["id"] for p in profiles]
        
        print(f"   Found {len(profiles)} profiles")
        
        has_female = target_female_id in profile_ids
        has_male = target_male_id in profile_ids
        has_nonbinary = target_nonbinary_id in profile_ids
        
        print(f"   - Female target present: {has_female}")
        print(f"   - Male target present: {has_male}")
        print(f"   - Non-binary target present: {has_nonbinary}")
        
        if has_female and has_nonbinary and not has_male:
            print("   ✅ PASSED: Correctly includes female and non_binary, excludes male")
        else:
            print("   ❌ FAILED: Incorrect filtering")
            if not has_female:
                print("      - Missing female target")
            if not has_nonbinary:
                print("      - Missing non_binary target")
            if has_male:
                print("      - Incorrectly includes male target")
    else:
        print(f"   ❌ FAILED: Unexpected status code {resp.status_code}")
        print(f"   Response: {resp.text}")
    
    # Test 2: Single gender in genders param (male)
    print("\n[4] TEST 2: GET /api/profiles?genders=male")
    print("   Expected: HTTP 200, includes only male target")
    
    resp = get_profiles(searcher_token, {
        "genders": "male",
        "min_age": 18,
        "max_age": 99
    })
    
    print(f"   Status: {resp.status_code}")
    
    if resp.status_code == 200:
        data = resp.json()
        # API returns a list directly
        profiles = data if isinstance(data, list) else data.get("profiles", [])
        profile_ids = [p["id"] for p in profiles]
        
        print(f"   Found {len(profiles)} profiles")
        
        has_female = target_female_id in profile_ids
        has_male = target_male_id in profile_ids
        has_nonbinary = target_nonbinary_id in profile_ids
        
        print(f"   - Female target present: {has_female}")
        print(f"   - Male target present: {has_male}")
        print(f"   - Non-binary target present: {has_nonbinary}")
        
        if has_male and not has_female and not has_nonbinary:
            print("   ✅ PASSED: Correctly includes only male target")
        else:
            print("   ❌ FAILED: Incorrect filtering")
            if not has_male:
                print("      - Missing male target")
            if has_female:
                print("      - Incorrectly includes female target")
            if has_nonbinary:
                print("      - Incorrectly includes non_binary target")
    else:
        print(f"   ❌ FAILED: Unexpected status code {resp.status_code}")
        print(f"   Response: {resp.text}")
    
    # Test 3: Backward compatibility - single gender param
    print("\n[5] TEST 3: GET /api/profiles?gender=female (backward compatibility)")
    print("   Expected: HTTP 200, includes female target")
    
    resp = get_profiles(searcher_token, {
        "gender": "female",
        "min_age": 18,
        "max_age": 99
    })
    
    print(f"   Status: {resp.status_code}")
    
    if resp.status_code == 200:
        data = resp.json()
        # API returns a list directly
        profiles = data if isinstance(data, list) else data.get("profiles", [])
        profile_ids = [p["id"] for p in profiles]
        
        print(f"   Found {len(profiles)} profiles")
        
        has_female = target_female_id in profile_ids
        
        print(f"   - Female target present: {has_female}")
        
        if has_female:
            print("   ✅ PASSED: Backward compatibility works - single gender param returns female")
        else:
            print("   ❌ FAILED: Female target not found with gender=female")
    else:
        print(f"   ❌ FAILED: Unexpected status code {resp.status_code}")
        print(f"   Response: {resp.text}")
    
    # Test 4: Omitting genders - should return all
    print("\n[6] TEST 4: GET /api/profiles (no gender filter)")
    print("   Expected: HTTP 200, includes all three targets")
    
    resp = get_profiles(searcher_token, {
        "min_age": 18,
        "max_age": 99
    })
    
    print(f"   Status: {resp.status_code}")
    
    if resp.status_code == 200:
        data = resp.json()
        # API returns a list directly
        profiles = data if isinstance(data, list) else data.get("profiles", [])
        profile_ids = [p["id"] for p in profiles]
        
        print(f"   Found {len(profiles)} profiles")
        
        has_female = target_female_id in profile_ids
        has_male = target_male_id in profile_ids
        has_nonbinary = target_nonbinary_id in profile_ids
        
        print(f"   - Female target present: {has_female}")
        print(f"   - Male target present: {has_male}")
        print(f"   - Non-binary target present: {has_nonbinary}")
        
        if has_female and has_male and has_nonbinary:
            print("   ✅ PASSED: All three targets returned when no gender filter applied")
        else:
            print("   ❌ FAILED: Not all targets returned")
            if not has_female:
                print("      - Missing female target")
            if not has_male:
                print("      - Missing male target")
            if not has_nonbinary:
                print("      - Missing non_binary target")
    else:
        print(f"   ❌ FAILED: Unexpected status code {resp.status_code}")
        print(f"   Response: {resp.text}")
    
    # Test 5: Verify it's NOT premium-gated (explicit check)
    print("\n[7] TEST 5: Verify genders filter is NOT premium-gated")
    print("   Confirming searcher is NON-premium and can use genders filter...")
    
    # Check user premium status
    headers = {"Authorization": f"Bearer {searcher_token}"}
    me_resp = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    
    if me_resp.status_code == 200:
        user_data = me_resp.json()
        is_premium = user_data.get("is_premium", False)
        is_vip = user_data.get("is_vip", False)
        is_premium_lite = user_data.get("is_premium_lite", False)
        
        print(f"   User premium status: is_premium={is_premium}, is_vip={is_vip}, is_premium_lite={is_premium_lite}")
        
        if not is_premium and not is_vip and not is_premium_lite:
            print("   ✅ CONFIRMED: User is NON-premium")
            
            # Try genders filter again to confirm no 403
            resp = get_profiles(searcher_token, {
                "genders": "female,non_binary",
                "min_age": 18,
                "max_age": 99
            })
            
            if resp.status_code == 200:
                print("   ✅ PASSED: NON-premium user can use genders filter (returns 200, not 403)")
            elif resp.status_code == 403:
                print("   ❌ FAILED: Got 403 PREMIUM_REQUIRED - genders should be a BASIC filter")
            else:
                print(f"   ❌ FAILED: Unexpected status {resp.status_code}")
        else:
            print("   ⚠️  WARNING: User has premium status - cannot verify non-premium access")
    else:
        print(f"   ❌ FAILED: Could not check user status - {me_resp.status_code}")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
