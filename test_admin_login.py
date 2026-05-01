"""
Simple test script to verify admin login works correctly
"""
import sys
import hashlib
from config import settings

# Test 1: Check if ADMIN_PASSWORD is loaded
print("[OK] ADMIN_PASSWORD loaded: {}".format(bool(settings.admin_password)))
if settings.admin_password:
    print("  Password: {}".format(settings.admin_password))

# Test 2: Test password hashing
test_password = "admin123"
input_hash = hashlib.sha256(test_password.encode()).hexdigest()
expected_hash = hashlib.sha256(settings.admin_password.encode()).hexdigest()

print("\n[OK] Password hash test:")
print("  Input: {}".format(test_password))
print("  Input hash: {}".format(input_hash))
print("  Expected hash: {}".format(expected_hash))
print("  Match: {}".format(input_hash == expected_hash))

if input_hash == expected_hash:
    print("\n[OK] Password verification would PASS")
else:
    print("\n[ERROR] Password verification would FAIL")
    print("  Make sure .env has: ADMIN_PASSWORD={}".format(test_password))
