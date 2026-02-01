-- Schema migration for Turso database
-- Run this after connecting to Turso

-- Sessions table for persistent storage
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    policy_id TEXT NOT NULL,
    messages TEXT NOT NULL,
    context_built INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (policy_id) REFERENCES policies(id)
);

-- Create index for faster session lookups
CREATE INDEX IF NOT EXISTS idx_sessions_policy_id ON sessions(policy_id);

-- Trigger to update updated_at timestamp
CREATE TRIGGER IF NOT EXISTS update_sessions_timestamp 
AFTER UPDATE ON sessions
FOR EACH ROW
BEGIN
  UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id = NEW.session_id;
END;
