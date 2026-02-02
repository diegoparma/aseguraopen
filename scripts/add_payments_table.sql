-- Add payments table for Mercado Pago integration
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

-- Índice para búsquedas por policy_id
CREATE INDEX IF NOT EXISTS idx_payments_policy_id ON payments(policy_id);
-- Índice para búsquedas por preference_id
CREATE INDEX IF NOT EXISTS idx_payments_preference_id ON payments(preference_id);
-- Índice para búsquedas por payment_id
CREATE INDEX IF NOT EXISTS idx_payments_payment_id ON payments(payment_id);
