#!/usr/bin/env python3
"""
Test agente con visualización de datos en Turso
Interactúa con la API y verifica qué se guarda en la BD
"""
import requests
import json
import time
import sys

sys.path.insert(0, '/Users/diegoemilioparma/Documents/aseguraOpen')

from src.db.connection import DatabaseConnection
from src.db.repository import PolicyRepository

BASE_URL = "http://localhost:8000"
DELAY = 1

def show_turso_state(title):
    """Muestra el estado actual de Turso"""
    print(f"\n📊 {title}")
    print("=" * 60)
    
    # Contar políticas
    result = DatabaseConnection.execute_query("SELECT COUNT(*) FROM policies")
    policies_count = result[0][0] if result else 0
    
    # Contar sesiones
    result = DatabaseConnection.execute_query("SELECT COUNT(*) FROM sessions")
    sessions_count = result[0][0] if result else 0
    
    # Contar clientes
    result = DatabaseConnection.execute_query("SELECT COUNT(*) FROM client_data")
    clients_count = result[0][0] if result else 0
    
    print(f"   Políticas: {policies_count}")
    print(f"   Sesiones: {sessions_count}")
    print(f"   Clientes: {clients_count}")
    print("=" * 60)

def main():
    """Test con visualización de Turso"""
    
    print("\n" + "=" * 60)
    print("🧪 TEST DE AGENTES + MONITOREO TURSO")
    print("=" * 60)
    
    # Estado inicial
    show_turso_state("ESTADO INICIAL")
    
    try:
        # Step 1: Iniciar sesión
        print("\n1️⃣  Iniciando sesión...")
        response = requests.post(f"{BASE_URL}/api/chat/start")
        assert response.status_code == 200, f"Error: {response.text}"
        
        data = response.json()
        session_id = data["session_id"]
        policy_id = data["policy_id"]
        
        print(f"   ✅ Session ID: {session_id}")
        print(f"   ✅ Policy ID: {policy_id}")
        time.sleep(DELAY)
        
        show_turso_state("DESPUÉS DE CREAR SESIÓN")
        
        # Mostrar detalles de la sesión
        print("\n📋 DETALLE SESIÓN GUARDADA:")
        result = DatabaseConnection.execute_query(
            "SELECT session_id, policy_id, created_at FROM sessions WHERE session_id = ?",
            (session_id,)
        )
        if result:
            row = result[0]
            print(f"   Session ID: {row[0]}")
            print(f"   Policy ID: {row[1]}")
            print(f"   Creada en: {row[2]}")
        
        # Mostrar detalles de la política
        print("\n📋 DETALLE POLÍTICA GUARDADA:")
        policy = PolicyRepository.get_policy(policy_id)
        if policy:
            print(f"   Policy ID: {policy.id}")
            print(f"   State: {policy.state}")
            print(f"   Created: {policy.created_at}")
        
        # Step 2: Enviar primer mensaje
        print("\n2️⃣  Enviando primer mensaje al agente...")
        message_payload = {
            "message": "Hola, me gustaría empezar el proceso de cotización"
        }
        response = requests.post(
            f"{BASE_URL}/api/chat/{session_id}/message",
            json=message_payload
        )
        assert response.status_code == 200, f"Error: {response.text}"
        
        agent_response = response.json()
        print(f"   ✅ Respuesta del agente recibida")
        print(f"   Agent: {agent_response.get('agent_name', 'Unknown')}")
        time.sleep(DELAY)
        
        show_turso_state("DESPUÉS DE ENVIAR MENSAJE")
        
        # Ver mensajes guardados
        print("\n📋 MENSAJES EN SESIÓN:")
        result = DatabaseConnection.execute_query(
            "SELECT COUNT(*), COUNT(DISTINCT session_id) FROM (SELECT session_id FROM sessions WHERE session_id = ?)",
            (session_id,)
        )
        
        session = PolicyRepository.get_session(session_id)
        if session:
            print(f"   Mensajes: {session.get('messages', [])}")
        
        # Step 3: Enviar segundo mensaje
        print("\n3️⃣  Enviando segundo mensaje...")
        message_payload = {
            "message": "Necesito cotizar un seguro para mi vehículo"
        }
        response = requests.post(
            f"{BASE_URL}/api/chat/{session_id}/message",
            json=message_payload
        )
        assert response.status_code == 200, f"Error: {response.text}"
        
        print(f"   ✅ Segundo mensaje procesado")
        time.sleep(DELAY)
        
        show_turso_state("DESPUÉS DE SEGUNDO MENSAJE")
        
        # Step 4: Obtener estado de la sesión
        print("\n4️⃣  Obteniendo estado actual de sesión...")
        response = requests.get(f"{BASE_URL}/api/chat/{session_id}")
        assert response.status_code == 200, f"Error: {response.text}"
        
        session_state = response.json()
        print(f"   ✅ Estado actual obtenido")
        print(f"   Agent current: {session_state.get('agent_name', 'Unknown')}")
        print(f"   Total messages: {len(session_state.get('messages', []))}")
        time.sleep(DELAY)
        
        show_turso_state("ESTADO FINAL")
        
        # Mostrar datos de cliente si existen
        print("\n📋 DATOS DE CLIENTE EN BD:")
        result = DatabaseConnection.execute_query(
            "SELECT id, policy_id, name, email, phone FROM client_data WHERE policy_id = ? LIMIT 1",
            (policy_id,)
        )
        if result:
            row = result[0]
            print(f"   Client ID: {row[0]}")
            print(f"   Policy ID: {row[1]}")
            print(f"   Name: {row[2]}")
            print(f"   Email: {row[3]}")
            print(f"   Phone: {row[4]}")
        else:
            print(f"   (Sin datos de cliente aún)")
        
        # Resumen
        print("\n" + "=" * 60)
        print("✅ TEST COMPLETADO EXITOSAMENTE")
        print("=" * 60)
        print(f"\nUsa Turso CLI para verificar:")
        print(f"  turso db shell aseguraopen-diegoparma --yes")
        print(f"  SELECT * FROM sessions WHERE session_id = '{session_id}';")
        print(f"  SELECT * FROM policies WHERE id = '{policy_id}';")
        print(f"  SELECT * FROM client_data WHERE policy_id = '{policy_id}';")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        DatabaseConnection.close()

if __name__ == "__main__":
    main()
