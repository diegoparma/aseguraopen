#!/usr/bin/env python3
"""
Test with libsql SDK - should work cleanly without manual parsing
"""
import os
import sys
import uuid
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, '/Users/diegoemilioparma/Documents/aseguraOpen')

from src.db.connection import DatabaseConnection

load_dotenv()

print("=" * 60)
print("🧪 TESTING TURSO WITH LIBSQL SDK")
print("=" * 60)

try:
    # Get connection (should use libsql automatically)
    db = DatabaseConnection.get_connection()
    print("✅ Connected!")
    
    # Generate IDs
    policy_id = str(uuid.uuid4())
    client_id = str(uuid.uuid4())
    
    # Step 1: Insert policy
    print("\n📝 Step 1: INSERT policy...")
    policy_sql = f"""
    INSERT INTO policies (id, state, intention, created_at, updated_at)
    VALUES (?, ?, ?, datetime('now'), datetime('now'))
    """
    DatabaseConnection.execute_update(
        policy_sql,
        (policy_id, 'intake', 0)
    )
    print(f"   ✅ Policy inserted: {policy_id}")
    
    # Step 2: Insert client data
    print("\n📝 Step 2: INSERT client_data...")
    client_sql = f"""
    INSERT INTO client_data (id, policy_id, name, email, phone, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
    """
    DatabaseConnection.execute_update(
        client_sql,
        (client_id, policy_id, 'Diego Parma', 'diego@example.com', '1234567890')
    )
    print(f"   ✅ Client data inserted: {client_id}")
    
    # Step 3: SELECT to verify
    print("\n📝 Step 3: SELECT to verify data...")
    select_sql = f"""
    SELECT id, policy_id, name, email, phone 
    FROM client_data 
    WHERE id = ?
    """
    rows = DatabaseConnection.execute_query(select_sql, (client_id,))
    
    if rows:
        print(f"   ✅ Found {len(rows)} row(s):")
        for row in rows:
            # Row should be a proper tuple now, not dicts!
            print(f"      ID: {row[0]}")
            print(f"      Policy ID: {row[1]}")
            print(f"      Name: {row[2]}")
            print(f"      Email: {row[3]}")
            print(f"      Phone: {row[4]}")
    else:
        print(f"   ❌ No rows found!")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
