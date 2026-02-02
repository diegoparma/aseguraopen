"""
Database initialization script
Creates the schema locally for testing
"""
import sqlite3
import os
from pathlib import Path

# SQL Schema
SCHEMA = """
-- Políticas (estado principal)
CREATE TABLE IF NOT EXISTS policies (
  id TEXT PRIMARY KEY,
  state TEXT NOT NULL,              -- intake, exploration, quotation, acceptance, emission, finalization, closed
  intention BOOLEAN DEFAULT 0,      -- Si el cliente tiene intención de comprar
  insurance_type TEXT,              -- auto, moto
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Datos del cliente (Intake)
CREATE TABLE IF NOT EXISTS client_data (
  id TEXT PRIMARY KEY,
  policy_id TEXT NOT NULL REFERENCES policies(id),
  name TEXT,
  email TEXT,
  phone TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Datos de exploración/validación
CREATE TABLE IF NOT EXISTS exploration_data (
  id TEXT PRIMARY KEY,
  policy_id TEXT NOT NULL REFERENCES policies(id),
  validation_status TEXT,  -- pending, suspicious, validated
  anomalies TEXT,          -- JSON
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Datos del vehículo
CREATE TABLE IF NOT EXISTS vehicle_data (
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
);

-- Datos de cotización
CREATE TABLE IF NOT EXISTS quotation_data (
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
);

-- Cotizaciones base disponibles
CREATE TABLE IF NOT EXISTS quotation_templates (
  id TEXT PRIMARY KEY,
  insurance_type TEXT,
  coverage_type TEXT,
  coverage_level TEXT,
  base_monthly_premium DECIMAL,
  deductible DECIMAL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Auditoría de cambios de estado
CREATE TABLE IF NOT EXISTS state_transitions (
  id TEXT PRIMARY KEY,
  policy_id TEXT NOT NULL REFERENCES policies(id),
  from_state TEXT,
  to_state TEXT,
  reason TEXT,
  agent TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sessions para persistencia de conversaciones
CREATE TABLE IF NOT EXISTS sessions (
  session_id TEXT PRIMARY KEY,
  policy_id TEXT NOT NULL REFERENCES policies(id),
  messages TEXT NOT NULL,
  context_built INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Payments (Mercado Pago integration)
CREATE TABLE IF NOT EXISTS payments (
  id TEXT PRIMARY KEY,
  policy_id TEXT NOT NULL REFERENCES policies(id),
  quotation_id TEXT REFERENCES quotation_data(id),
  amount DECIMAL,
  preference_id TEXT,  -- Mercado Pago preference ID
  payment_link TEXT,  -- Link de pago (init_point)
  payment_status TEXT DEFAULT 'pending',  -- pending, approved, rejected, cancelled
  payment_id TEXT,  -- Mercado Pago payment ID (después del pago)
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para mejorar queries
CREATE INDEX IF NOT EXISTS idx_policies_state ON policies(state);
CREATE INDEX IF NOT EXISTS idx_client_data_policy ON client_data(policy_id);
CREATE INDEX IF NOT EXISTS idx_exploration_data_policy ON exploration_data(policy_id);
CREATE INDEX IF NOT EXISTS idx_quotation_data_policy ON quotation_data(policy_id);
CREATE INDEX IF NOT EXISTS idx_state_transitions_policy ON state_transitions(policy_id);
CREATE INDEX IF NOT EXISTS idx_sessions_policy_id ON sessions(policy_id);
CREATE INDEX IF NOT EXISTS idx_payments_policy_id ON payments(policy_id);
CREATE INDEX IF NOT EXISTS idx_payments_preference_id ON payments(preference_id);
CREATE INDEX IF NOT EXISTS idx_payments_payment_id ON payments(payment_id);
"""

def init_db(db_path: str = "aseguraopen.db"):
    """Initialize local SQLite database with schema"""
    
    # Create database file
    db_file = Path(db_path)
    
    try:
        # Remove existing database if requested
        if db_file.exists():
            print(f"⚠️  Database already exists at {db_path}")
            response = input("   Do you want to reinitialize it? (y/n): ")
            if response.lower() != 'y':
                print("✅ Using existing database")
                return True
            db_file.unlink()
        
        # Connect to SQLite
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()
        
        # Execute schema
        cursor.executescript(SCHEMA)
        conn.commit()
        
        print(f"✅ Database schema initialized at {db_path}")
        
        # List created tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"\n📊 Created tables:")
        for table in tables:
            print(f"  - {table[0]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        raise

if __name__ == "__main__":
    # Initialize local database for testing
    init_db()
