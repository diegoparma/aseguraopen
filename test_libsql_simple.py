#!/usr/bin/env python3
"""
Minimal test - just connect
"""
import os
from dotenv import load_dotenv
import libsql_client

load_dotenv()

url = os.getenv("TURSO_DATABASE_URL")
token = os.getenv("TURSO_AUTH_TOKEN")

print(f"URL: {url}")
print(f"Token: {token[:20]}..." if token else "No token")

print("\nConnecting...")
try:
    conn = libsql_client.create_client_sync(url=url, auth_token=token)
    print("✅ Connected!")
    
    cursor = conn.cursor()
    print("\nTesting SELECT...")
    result = cursor.execute("SELECT COUNT(*) FROM policies")
    rows = result.fetchall()
    print(f"✅ Result: {rows}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
