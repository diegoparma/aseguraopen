#!/usr/bin/env python3
"""
Test simple INSERT en client_data with FOREIGN KEY
"""
import httpx
import os
import json
from dotenv import load_dotenv
import uuid

load_dotenv()

db_url = os.getenv("TURSO_DATABASE_URL")
token = os.getenv("TURSO_AUTH_TOKEN")

print(f"🔧 Turso URL: {db_url}")

# Convert to HTTPS
api_url = db_url.replace("libsql://", "https://")
api_url = f"{api_url}/v2/pipeline"

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Generate IDs
client_id = str(uuid.uuid4())
policy_id = str(uuid.uuid4())
name = "Diego Parma"
email = "diego@example.com"
phone = "1234567890"

# First: Insert policy
policy_insert_sql = f"""
INSERT INTO policies (id, state, intention, created_at, updated_at)
VALUES ('{policy_id}', 'intake', 0, datetime('now'), datetime('now'))
"""

print("\n📝 Step 1: Inserting POLICY...")
print(f"   Policy ID: {policy_id}")
print(f"   SQL: {policy_insert_sql[:80]}...\n")

payload_policy = {
    "requests": [
        {
            "type": "execute",
            "stmt": {
                "sql": policy_insert_sql
            }
        }
    ]
}

try:
    with httpx.Client(timeout=60, verify=False) as client:
        response_policy = client.post(api_url, json=payload_policy, headers=headers)
        result_policy = response_policy.json()
        status = result_policy['results'][0]['type']
        print(f"   Status: {status}")
        
        if status == 'error':
            print(f"   ❌ Error: {result_policy['results'][0]['error']['message']}")
            exit(1)
        
        print(f"   ✅ Policy inserted successfully!")
        
        # Now: Insert client_data
        insert_sql = f"""
INSERT INTO client_data (id, policy_id, name, email, phone, created_at)
VALUES ('{client_id}', '{policy_id}', '{name}', '{email}', '{phone}', datetime('now'))
"""
        
        print(f"\n📝 Step 2: Inserting CLIENT_DATA...")
        print(f"   Client ID: {client_id}")
        print(f"   SQL: {insert_sql[:80]}...\n")
        
        payload_client = {
            "requests": [
                {
                    "type": "execute",
                    "stmt": {
                        "sql": insert_sql
                    }
                }
            ]
        }
        
        response_client = client.post(api_url, json=payload_client, headers=headers)
        result_client = response_client.json()
        status = result_client['results'][0]['type']
        print(f"   Status: {status}")
        
        if status == 'error':
            print(f"   ❌ Error: {result_client['results'][0]['error']['message']}")
            exit(1)
        
        print(f"   ✅ Client data inserted successfully!")
        
        # Finally: SELECT para verificar
        select_sql = f"SELECT id, name, email, phone FROM client_data WHERE id = '{client_id}'"
        
        print(f"\n🔍 Step 3: SELECT to verify...")
        print(f"   SQL: {select_sql[:80]}...\n")
        
        payload_select = {
            "requests": [
                {
                    "type": "execute",
                    "stmt": {
                        "sql": select_sql
                    }
                }
            ]
        }
        
        response_select = client.post(api_url, json=payload_select, headers=headers)
        result_select = response_select.json()
        
        if result_select['results'][0]['type'] == 'ok':
            rows = result_select['results'][0]['response']['result']['rows']
            if rows:
                print(f"   ✅ Found {len(rows)} row(s):")
                print(f"      {json.dumps(rows, indent=6)}")
            else:
                print(f"   ❌ No rows found!")
        if result_select['results'][0]['type'] == 'ok':
            rows = result_select['results'][0]['response']['result']['rows']
            if rows:
                print(f"   ✅ Found {len(rows)} row(s):")
                print(f"      {json.dumps(rows, indent=6)}")
            else:
                print(f"   ❌ No rows found!")
        else:
            print(f"   ❌ Error: {result_select['results'][0]['error']['message']}")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
