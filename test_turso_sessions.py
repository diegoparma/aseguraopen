#!/usr/bin/env python3
"""
Test script to verify Turso/SQLite persistence
Tests session creation, message handling, and data persistence
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"
DELAY = 0.5  # seconds between requests to prevent rate limiting

def test_session_flow():
    """Test complete session flow"""
    
    print("\n🧪 TESTING SESSION PERSISTENCE\n")
    print("=" * 60)
    
    # Step 1: Start a new chat
    print("\n1️⃣  Starting a new chat session...")
    response = requests.post(f"{BASE_URL}/api/chat/start")
    assert response.status_code == 200, f"Failed to start chat: {response.text}"
    
    start_data = response.json()
    session_id = start_data["session_id"]
    policy_id = start_data["policy_id"]
    
    print(f"   ✅ Session created: {session_id}")
    print(f"   ✅ Policy ID: {policy_id}")
    time.sleep(DELAY)
    
    # Step 2: Verify session was saved to database
    print("\n2️⃣  Verifying session was saved to database...")
    response = requests.get(f"{BASE_URL}/api/chat/{session_id}")
    assert response.status_code == 200, f"Failed to retrieve session: {response.text}"
    
    session_data = response.json()
    print(f"   ✅ Session retrieved from DB")
    print(f"   ✅ Messages in DB: {len(session_data['messages'])}")
    time.sleep(DELAY)
    
    # Step 3: Send first message
    print("\n3️⃣  Sending first message to agent...")
    message_data = {"message": "Hola, quiero un seguro de auto"}
    response = requests.post(
        f"{BASE_URL}/api/chat/{session_id}/message",
        json=message_data
    )
    assert response.status_code == 200, f"Failed to send message: {response.text}"
    
    message_response = response.json()
    print(f"   ✅ Message sent and processed")
    print(f"   ✅ Agent response: {message_response['response'][:100]}...")
    print(f"   ✅ Messages in session: {len(message_response['messages'])}")
    time.sleep(DELAY)
    
    # Step 4: Restore session and verify messages persisted
    print("\n4️⃣  Restoring session to verify message persistence...")
    response = requests.get(f"{BASE_URL}/api/chat/{session_id}/restore")
    assert response.status_code == 200, f"Failed to restore session: {response.text}"
    
    restored_data = response.json()
    message_count = len(restored_data["messages"])
    print(f"   ✅ Session restored from DB")
    print(f"   ✅ Messages persisted: {message_count}")
    assert message_count == 2, f"Expected 2 messages, got {message_count}"
    
    # Print message history
    print("\n   📋 Message history:")
    for i, msg in enumerate(restored_data["messages"], 1):
        role = msg["role"].upper()
        content = msg["content"][:80]
        print(f"      {i}. [{role}] {content}...")
    
    time.sleep(DELAY)
    
    # Step 5: Check admin sessions endpoint
    print("\n5️⃣  Checking admin sessions endpoint...")
    response = requests.get(f"{BASE_URL}/api/admin/sessions")
    if response.status_code == 200:
        admin_data = response.json()
        sessions_list = admin_data.get("sessions", [])
        print(f"   ✅ Admin endpoint working")
        print(f"   ✅ Total sessions in DB: {len(sessions_list)}")
        
        # Find our session
        our_session = next((s for s in sessions_list if s["session_id"] == session_id), None)
        if our_session:
            print(f"   ✅ Our session found in admin list")
            print(f"      - Messages: {our_session['messages_count']}")
            print(f"      - Created: {our_session['created_at']}")
    else:
        print(f"   ⚠️  Admin endpoint not available: {response.status_code}")
    
    time.sleep(DELAY)
    
    # Step 6: Send another message
    print("\n6️⃣  Sending second message...")
    message_data = {"message": "Mi auto es un Toyota Corolla 2020"}
    response = requests.post(
        f"{BASE_URL}/api/chat/{session_id}/message",
        json=message_data
    )
    assert response.status_code == 200, f"Failed to send second message: {response.text}"
    
    message_response = response.json()
    print(f"   ✅ Second message processed")
    print(f"   ✅ Total messages now: {len(message_response['messages'])}")
    assert len(message_response["messages"]) == 4, "Should have 4 messages total"
    
    time.sleep(DELAY)
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("\n📊 Summary:")
    print(f"   - Session ID: {session_id}")
    print(f"   - Policy ID: {policy_id}")
    print(f"   - Messages persisted: ✅")
    print(f"   - Database working: ✅")
    print(f"   - Session restoration: ✅")
    print("\n💾 Sessions are now being persisted to the database!")
    print("   Ready for Turso cloud deployment.")

if __name__ == "__main__":
    try:
        test_session_flow()
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
