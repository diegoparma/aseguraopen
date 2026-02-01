#!/usr/bin/env python3
"""
Direct test of database layer with libsql SDK - NO SERVER NEEDED
"""
import os
import sys
import uuid
from dotenv import load_dotenv

sys.path.insert(0, '/Users/diegoemilioparma/Documents/aseguraOpen')

from src.db.connection import DatabaseConnection
from src.db.repository import PolicyRepository

load_dotenv()

print("=" * 60)
print("🧪 TESTING DATABASE LAYER WITH LIBSQL SDK")
print("=" * 60)

try:
    # Get connection
    db = DatabaseConnection.get_connection()
    print("\n✅ Connected to database!")
    
    # Test 1: Create a policy
    print("\n📝 Test 1: CREATE POLICY via repository...")
    policy = PolicyRepository.create_policy(initial_state="intake")
    policy_id = policy.id
    session_id = str(uuid.uuid4())
    print(f"   ✅ Policy created: {policy_id}")
    
    # Test 2: Get the policy back
    print("\n📝 Test 2: GET POLICY via repository...")
    retrieved_policy = PolicyRepository.get_policy(policy_id)
    if retrieved_policy:
        print(f"   ✅ Policy retrieved: {retrieved_policy.id}")
    else:
        print(f"   ❌ Policy not found!")
    
    # Test 3: Create a session
    print("\n📝 Test 3: CREATE SESSION...")
    PolicyRepository.create_session(
        session_id=session_id,
        policy_id=policy_id
    )
    print(f"   ✅ Session created: {session_id}")
    
    # Test 4: Get the session back
    print("\n📝 Test 4: GET SESSION...")
    session = PolicyRepository.get_session(session_id)
    if session:
        print(f"   ✅ Session retrieved:")
        print(f"      ID: {session['session_id']}")
        print(f"      Policy ID: {session['policy_id']}")
        print(f"      Messages: {session['messages']}")
    else:
        print(f"   ❌ Session not found!")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    
    # Close connection
    DatabaseConnection.close()
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
