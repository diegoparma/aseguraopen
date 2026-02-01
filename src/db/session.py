"""
Session management with AdvancedSQLiteSession
Persists agent context between runs
"""
from agents.extensions.memory import AdvancedSQLiteSession
import os

# Create sessions directory if it doesn't exist
SESSIONS_DIR = os.path.join(os.path.dirname(__file__), "../../sessions")
os.makedirs(SESSIONS_DIR, exist_ok=True)

def get_session_storage(policy_id: str):
    """
    Get session storage for a policy
    
    Args:
        policy_id: The policy ID to create session for
    
    Returns:
        AdvancedSQLiteSession instance
    """
    session_path = os.path.join(SESSIONS_DIR, f"policy_{policy_id}.db")
    
    session = AdvancedSQLiteSession(
        session_id=policy_id,
        db_path=session_path,
        create_tables=True
    )
    
    return session

def clear_session(policy_id: str):
    """Clear session for a policy"""
    session_path = os.path.join(SESSIONS_DIR, f"policy_{policy_id}.db")
    if os.path.exists(session_path):
        os.remove(session_path)
        print(f"✅ Session cleared for policy {policy_id}")
