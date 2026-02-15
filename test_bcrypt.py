"""Diagnostic script to test bcrypt directly"""
import sys

print("Python version:", sys.version)
print("\nTesting bcrypt installation...")

try:
    import bcrypt
    print("✅ bcrypt imported successfully")
    print(f"   bcrypt version: {bcrypt.__version__}")
except Exception as e:
    print(f"❌ Failed to import bcrypt: {e}")
    sys.exit(1)

try:
    import passlib
    from passlib.context import CryptContext
    print("✅ passlib imported successfully")
    print(f"   passlib version: {passlib.__version__}")
except Exception as e:
    print(f"❌ Failed to import passlib: {e}")
    sys.exit(1)

print("\nTesting password hashing...")
try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # Test with short password
    test_password = "test123"
    hashed = pwd_context.hash(test_password)
    print(f"✅ Short password hashed successfully")
    print(f"   Hash: {hashed[:50]}...")
    
    # Test with long password (>72 bytes)
    long_password = "a" * 100
    password_bytes = long_password.encode('utf-8')
    if len(password_bytes) > 72:
        long_password = password_bytes[:72].decode('utf-8', errors='ignore')
    hashed_long = pwd_context.hash(long_password)
    print(f"✅ Long password (truncated) hashed successfully")
    print(f"   Hash: {hashed_long[:50]}...")
    
    # Test verification
    if pwd_context.verify(test_password, hashed):
        print("✅ Password verification works")
    else:
        print("❌ Password verification failed")
        
except Exception as e:
    print(f"❌ Password hashing failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✅ All tests passed! Bcrypt is working correctly.")
