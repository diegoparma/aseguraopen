#!/usr/bin/env python3
"""
Simple Turso test - diagnóstico paso a paso
"""
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv("TURSO_DATABASE_URL")
token = os.getenv("TURSO_AUTH_TOKEN")

print("=" * 70)
print("🧪 DIAGNÓSTICO TURSO - TEST SIMPLE")
print("=" * 70)

# Convert URL
api_url = db_url.replace("libsql://", "https://")
api_url = f"{api_url}/v2/pipeline"

print(f"\n✅ URL convertida: {api_url[:60]}...")
print(f"✅ Token: {token[:30]}...")

# Test 1: SELECT COUNT(*) FROM policies
print("\n--- TEST 1: SELECT COUNT(*) FROM policies ---")
query1 = "SELECT COUNT(*) as cnt FROM policies"
payload1 = {
    "requests": [
        {
            "type": "execute",
            "stmt": {
                "sql": query1
            }
        }
    ]
}

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

try:
    with httpx.Client(timeout=60, verify=False) as client:
        resp = client.post(api_url, json=payload1, headers=headers)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.json()}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: INSERT simple
print("\n--- TEST 2: INSERT INTO policies ---")
query2 = "INSERT INTO policies (id, state, intention, created_at, updated_at) VALUES ('test-id-1', 'intake', 0, '2026-01-31T00:00:00', '2026-01-31T00:00:00')"

payload2 = {
    "requests": [
        {
            "type": "execute",
            "stmt": {
                "sql": query2
            }
        }
    ]
}

try:
    with httpx.Client(timeout=60, verify=False) as client:
        resp = client.post(api_url, json=payload2, headers=headers)
        print(f"Status: {resp.status_code}")
        result = resp.json()
        print(f"Response: {result}")
        
        # Check if it was successful
        if result.get("results") and len(result["results"]) > 0:
            exec_result = result["results"][0]
            if exec_result.get("type") == "error":
                print(f"❌ SQL Error: {exec_result.get('error')}")
            else:
                print(f"✅ INSERT successful")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 3: SELECT the inserted row
print("\n--- TEST 3: SELECT the row we just inserted ---")
query3 = "SELECT id, state, intention FROM policies WHERE id = 'test-id-1'"

payload3 = {
    "requests": [
        {
            "type": "execute",
            "stmt": {
                "sql": query3
            }
        }
    ]
}

try:
    with httpx.Client(timeout=60, verify=False) as client:
        resp = client.post(api_url, json=payload3, headers=headers)
        print(f"Status: {resp.status_code}")
        result = resp.json()
        print(f"Response: {result}")
        
        if result.get("results") and len(result["results"]) > 0:
            exec_result = result["results"][0]
            if exec_result.get("type") == "error":
                print(f"❌ SQL Error: {exec_result.get('error')}")
            elif exec_result.get("response"):
                print(f"✅ SELECT successful, rows found: {len(exec_result['response'].get('rows', []))}")
                for row in exec_result["response"].get("rows", []):
                    print(f"   Row: {row}")
            else:
                print(f"⚠️ No rows returned")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 70)
