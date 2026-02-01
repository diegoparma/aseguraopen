"""
Setup Turso database with schema
Executes SQL migrations against Turso via HTTP API
"""
import os
import sys
import httpx
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# SQL Schema (same as init_db.py)
SCHEMA_STATEMENTS = [
    # Políticas (estado principal)
    """CREATE TABLE IF NOT EXISTS policies (
      id TEXT PRIMARY KEY,
      state TEXT NOT NULL,
      intention BOOLEAN DEFAULT 0,
      insurance_type TEXT,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    
    # Datos del cliente
    """CREATE TABLE IF NOT EXISTS client_data (
      id TEXT PRIMARY KEY,
      policy_id TEXT NOT NULL REFERENCES policies(id),
      name TEXT,
      email TEXT,
      phone TEXT,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    
    # Datos de exploración
    """CREATE TABLE IF NOT EXISTS exploration_data (
      id TEXT PRIMARY KEY,
      policy_id TEXT NOT NULL REFERENCES policies(id),
      validation_status TEXT,
      anomalies TEXT,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    
    # Datos del vehículo
    """CREATE TABLE IF NOT EXISTS vehicle_data (
      id TEXT PRIMARY KEY,
      policy_id TEXT NOT NULL REFERENCES policies(id),
      plate TEXT,
      make TEXT,
      model TEXT,
      year INTEGER,
      engine_number TEXT,
      chassis_number TEXT,
      engine_displacement INTEGER,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    
    # Datos de cotización
    """CREATE TABLE IF NOT EXISTS quotation_data (
      id TEXT PRIMARY KEY,
      policy_id TEXT NOT NULL REFERENCES policies(id),
      vehicle_id TEXT REFERENCES vehicle_data(id),
      coverage_type TEXT,
      coverage_level TEXT,
      monthly_premium DECIMAL,
      annual_premium DECIMAL,
      deductible DECIMAL,
      risk_level TEXT,
      selected BOOLEAN DEFAULT 0,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    
    # Cotizaciones base
    """CREATE TABLE IF NOT EXISTS quotation_templates (
      id TEXT PRIMARY KEY,
      insurance_type TEXT,
      coverage_type TEXT,
      coverage_level TEXT,
      base_monthly_premium DECIMAL,
      deductible DECIMAL,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    
    # Auditoría de cambios de estado
    """CREATE TABLE IF NOT EXISTS state_transitions (
      id TEXT PRIMARY KEY,
      policy_id TEXT NOT NULL REFERENCES policies(id),
      from_state TEXT,
      to_state TEXT,
      reason TEXT,
      agent TEXT,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    
    # Sessions para persistencia
    """CREATE TABLE IF NOT EXISTS sessions (
      session_id TEXT PRIMARY KEY,
      policy_id TEXT NOT NULL REFERENCES policies(id),
      messages TEXT NOT NULL,
      context_built INTEGER DEFAULT 0,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    
    # Índices
    "CREATE INDEX IF NOT EXISTS idx_policies_state ON policies(state)",
    "CREATE INDEX IF NOT EXISTS idx_client_data_policy ON client_data(policy_id)",
    "CREATE INDEX IF NOT EXISTS idx_exploration_data_policy ON exploration_data(policy_id)",
    "CREATE INDEX IF NOT EXISTS idx_quotation_data_policy ON quotation_data(policy_id)",
    "CREATE INDEX IF NOT EXISTS idx_state_transitions_policy ON state_transitions(policy_id)",
    "CREATE INDEX IF NOT EXISTS idx_sessions_policy_id ON sessions(policy_id)",
]

def execute_turso_query(database_url: str, auth_token: str, sql: str) -> dict:
    """Execute a single SQL statement on Turso"""
    # Convert libsql:// URL to https://
    api_url = database_url.replace("libsql://", "https://")
    api_url = f"{api_url}/v2/pipeline"
    
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "requests": [
            {
                "type": "execute",
                "stmt": {
                    "sql": sql
                }
            }
        ]
    }
    
    try:
        with httpx.Client(timeout=60, verify=False) as client:
            response = client.post(api_url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print(f"❌ Turso API Error: {e}")
        raise

def setup_turso():
    """Initialize Turso database with schema"""
    
    # Get credentials from environment
    database_url = os.getenv("TURSO_DATABASE_URL")
    auth_token = os.getenv("TURSO_AUTH_TOKEN")
    
    if not database_url or not auth_token:
        print("❌ Missing Turso credentials!")
        print("   Set TURSO_DATABASE_URL and TURSO_AUTH_TOKEN in .env")
        print("\n📖 Get these from: https://turso.tech")
        sys.exit(1)
    
    print("🚀 Setting up Turso database...")
    print(f"   Database: {database_url}")
    
    # Execute all schema statements
    success_count = 0
    error_count = 0
    
    for i, statement in enumerate(SCHEMA_STATEMENTS, 1):
        try:
            print(f"   [{i}/{len(SCHEMA_STATEMENTS)}] Executing...", end=" ", flush=True)
            result = execute_turso_query(database_url, auth_token, statement)
            
            # Check if there's an error in the response
            if result.get("results") and len(result["results"]) > 0:
                exec_result = result["results"][0]
                if exec_result.get("type") == "error":
                    error_msg = exec_result.get("error", "Unknown error")
                    print(f"⚠️  {error_msg}")
                    error_count += 1
                else:
                    print("✅")
                    success_count += 1
            else:
                print("✅")
                success_count += 1
        except Exception as e:
            print(f"❌ {e}")
            error_count += 1
    
    print(f"\n📊 Results:")
    print(f"   ✅ Successful: {success_count}")
    print(f"   ⚠️  Errors/Warnings: {error_count}")
    
    if error_count == 0:
        print(f"\n✅ Turso database schema initialized successfully!")
    else:
        print(f"\n⚠️  Some statements had warnings (usually 'table already exists')")
        print(f"   This is normal if you're re-running the setup")

if __name__ == "__main__":
    setup_turso()
