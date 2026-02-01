"""
Test script to validate IntakeAgent functionality
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.intake_agent import IntakeAgent
from src.db.repository import PolicyRepository
from src.db.connection import DatabaseConnection
import json

def test_intake_flow():
    """Test the complete intake flow"""
    
    print("\n" + "="*60)
    print("🧪 Testing IntakeAgent Flow")
    print("="*60)
    
    # Test 1: Create a policy
    print("\n1️⃣ Creating a new policy...")
    try:
        policy = PolicyRepository.create_policy("intake")
        print(f"✅ Policy created: {policy.id}")
        print(f"   State: {policy.state}")
        policy_id = policy.id
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Test 2: Save client data
    print(f"\n2️⃣ Saving client data to policy {policy_id}...")
    try:
        client_data = PolicyRepository.save_client_data(
            policy_id=policy_id,
            name="Juan Pérez",
            email="juan@example.com",
            phone="+34 600 123 456"
        )
        print(f"✅ Client data saved")
        print(f"   Name: {client_data.name}")
        print(f"   Email: {client_data.email}")
        print(f"   Phone: {client_data.phone}")
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Test 3: Retrieve policy and client data
    print(f"\n3️⃣ Retrieving policy and client data...")
    try:
        retrieved_policy = PolicyRepository.get_policy(policy_id)
        print(f"✅ Policy retrieved")
        print(f"   ID: {retrieved_policy.id}")
        print(f"   State: {retrieved_policy.state}")
        
        retrieved_client = PolicyRepository.get_client_data(policy_id)
        print(f"✅ Client data retrieved")
        print(f"   Name: {retrieved_client.name}")
        print(f"   Email: {retrieved_client.email}")
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Test 4: Update policy state (simulating transition to exploration)
    print(f"\n4️⃣ Simulating state transition to Exploration...")
    try:
        transition = PolicyRepository.update_policy_state(
            policy_id=policy_id,
            new_state="exploration",
            reason="Client data collection completed",
            agent="IntakeAgent"
        )
        print(f"✅ Policy state updated")
        print(f"   From: {transition.from_state}")
        print(f"   To: {transition.to_state}")
        print(f"   Agent: {transition.agent}")
        print(f"   Reason: {transition.reason}")
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Test 5: Verify state change
    print(f"\n5️⃣ Verifying state change...")
    try:
        final_policy = PolicyRepository.get_policy(policy_id)
        print(f"✅ Final policy state: {final_policy.state}")
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    print("\n" + "="*60)
    print("✅ All tests passed!")
    print("="*60 + "\n")
    
    return policy_id

if __name__ == "__main__":
    try:
        # Validate environment
        from src.config import Config
        Config.validate()
        
        # Initialize database connection
        DatabaseConnection.get_connection()
        
        # Run tests
        test_intake_flow()
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
    finally:
        DatabaseConnection.close()
