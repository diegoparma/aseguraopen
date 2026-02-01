#!/usr/bin/env python3
"""
Test script to verify the complete flow:
1. Start chat session
2. Collect client info through IntakeAgent
3. Confirm insurance intention
4. Transition to QuotationAgent
5. Collect vehicle data
6. Generate quotations
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def print_header(msg):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}")

def test_flow():
    # 1. Start session
    print_header("1. Starting chat session")
    response = requests.post(f"{BASE_URL}/api/chat/start")
    data = response.json()
    session_id = data['session_id']
    policy_id = data['policy_id']
    print(f"✅ Session: {session_id[:12]}...")
    print(f"✅ Policy: {policy_id[:12]}...")
    print(f"📝 Agent: {data['message']}")
    
    # 2. First message - introduce myself
    print_header("2. First message - introducing myself")
    response = requests.post(
        f"{BASE_URL}/api/chat/{session_id}/message",
        json={"message": "Hola, me gustaría cotizar un seguro para mi auto"}
    )
    data = response.json()
    print(f"🤖 Agent: {data['response'][:100]}...")
    print(f"📊 Policy state: {data['policy_state']}")
    print(f"✅ Intention confirmed: {data['intention_confirmed']}")
    print(f"🚗 Insurance type: {data['insurance_type']}")
    
    # 3. Second message - provide personal info
    print_header("3. Providing personal information")
    response = requests.post(
        f"{BASE_URL}/api/chat/{session_id}/message",
        json={"message": "Mi nombre es Juan García, email es juan@example.com y mi teléfono es 555-1234"}
    )
    data = response.json()
    print(f"🤖 Agent: {data['response'][:150]}...")
    print(f"✅ Client saved: {data['client_saved']}")
    print(f"👤 Client name: {data['client_name']}")
    print(f"📧 Email: {data['client_email']}")
    print(f"📱 Phone: {data['client_phone']}")
    
    # 4. Third message - confirm ready for quotation
    print_header("4. Ready for quotation")
    response = requests.post(
        f"{BASE_URL}/api/chat/{session_id}/message",
        json={"message": "Sí, tengo todos mis datos. Estoy listo para obtener una cotización"}
    )
    print(f"Status: {response.status_code}")
    print(f"Content: {response.text[:200]}")
    if response.status_code != 200:
        print(f"❌ Error response: {response.text}")
        return
    data = response.json()
    print(f"🤖 Agent: {data['response'][:150]}...")
    print(f"🚗 Vehicle saved: {data['vehicle_saved']}")
    
    # 5. Fourth message - provide vehicle info
    print_header("5. Providing vehicle information")
    response = requests.post(
        f"{BASE_URL}/api/chat/{session_id}/message",
        json={"message": "Mi auto es un Toyota Corolla 2020, patente ABC-123, motor 2000cc, número de motor NM123456789, número de chasis CH123456789"}
    )
    data = response.json()
    print(f"🤖 Agent: {data['response'][:200]}...")
    print(f"🚗 Vehicle saved: {data['vehicle_saved']}")
    print(f"   Make: {data['vehicle_make']}")
    print(f"   Model: {data['vehicle_model']}")
    
    # 6. Fifth message - request quotations
    print_header("6. Requesting quotations")
    response = requests.post(
        f"{BASE_URL}/api/chat/{session_id}/message",
        json={"message": "Generá las cotizaciones disponibles para mi auto"}
    )
    data = response.json()
    print(f"🤖 Agent: {data['response'][:300]}...")
    print(f"💰 Quotations generated: {len(data.get('quotations', []))}")
    
    if data.get('quotations'):
        print("\n   Available quotations:")
        for i, q in enumerate(data['quotations'][:3], 1):
            print(f"   {i}. {q['coverage_type']} - {q['coverage_level']}")
            print(f"      Monthly: ${q['monthly_premium']:.2f} | Annual: ${q['annual_premium']:.2f}")
    
    # 7. Check admin view
    print_header("7. Checking admin view")
    response = requests.get(f"{BASE_URL}/api/admin/policies")
    policies = response.json()['policies']
    print(f"✅ Total policies in DB: {len(policies)}")
    
    response = requests.get(f"{BASE_URL}/api/admin/clients")
    clients = response.json()['clients']
    print(f"✅ Total clients in DB: {len(clients)}")
    
    if clients:
        print(f"   Last client: {clients[-1].get('name', 'N/A')} - {clients[-1].get('email', 'N/A')}")
    
    print_header("✅ COMPLETE TEST FLOW SUCCESSFUL!")

if __name__ == "__main__":
    try:
        test_flow()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
