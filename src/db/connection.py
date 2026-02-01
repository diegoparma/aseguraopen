"""
Database connection and session management
Uses Turso (libSQL) for persistent cloud storage
"""
import sqlite3
import os
import time
from dotenv import load_dotenv
import libsql_client
from src.config import Config

load_dotenv()

class DatabaseConnection:
    """Manage connection to Turso or local SQLite database"""
    
    _instance = None
    _conn = None
    _turso_url = None
    _turso_token = None
    _use_turso = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def get_connection(cls):
        """Get or create database connection"""
        if cls._conn is None:
            try:
                Config.validate()
                
                # Check for Turso credentials
                cls._turso_url = os.getenv("TURSO_DATABASE_URL")
                cls._turso_token = os.getenv("TURSO_AUTH_TOKEN")
                
                if cls._turso_url and cls._turso_token:
                    # Use Turso with official libsql SDK (sync mode)
                    # Convert libsql:// to https:// (HTTP instead of WebSocket)
                    cls._use_turso = True
                    https_url = cls._turso_url.replace("libsql://", "https://")
                    
                    cls._conn = libsql_client.create_client_sync(
                        url=https_url,
                        auth_token=cls._turso_token
                    )
                    print("✅ Connected to Turso using libsql SDK (HTTP)")
                    print(f"   Database: {https_url}")
                else:
                    # Fallback to local SQLite for development
                    if not os.path.exists("aseguraopen.db"):
                        print("⚠️  Creating local database (use .env for Turso)")
                    
                    cls._conn = sqlite3.connect("aseguraopen.db", check_same_thread=False)
                    cls._conn.row_factory = sqlite3.Row
                    cls._use_turso = False
                    print("✅ Connected to local SQLite database")
                
            except Exception as e:
                print(f"❌ Error connecting to database: {e}")
                raise
        return cls._conn
    
    @classmethod
    def close(cls):
        """Close database connection"""
        if cls._conn:
            try:
                if cls._use_turso:
                    # libsql client has close() method
                    cls._conn.close()
                else:
                    cls._conn.close()
                cls._conn = None
                print("🔌 Database connection closed")
            except Exception as e:
                print(f"⚠️  Error closing connection: {e}")
    
    @classmethod
    def execute_query(cls, query, params=None):
        """Execute a SELECT query and return results as tuples"""
        # Add small delay to prevent rate limiting
        db_delay = float(os.getenv("DB_QUERY_DELAY", "0"))
        if db_delay > 0:
            time.sleep(db_delay)
        
        if cls._use_turso:
            # libsql sync client - execute() returns ResultSet with .rows attribute
            try:
                if params:
                    result = cls._conn.execute(query, params)
                else:
                    result = cls._conn.execute(query)
                # libsql ResultSet.rows returns list of Row objects (behaves like tuples)
                return result.rows if hasattr(result, 'rows') else []
            except Exception as e:
                print(f"❌ Query error: {e}")
                raise
        else:
            conn = cls.get_connection()
            cursor = conn.cursor()
            try:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                return cursor.fetchall()
            except Exception as e:
                print(f"❌ Query error: {e}")
                raise
    
    @classmethod
    def execute_update(cls, query, params=None):
        """Execute an INSERT/UPDATE/DELETE query"""
        # Add small delay to prevent rate limiting
        db_delay = float(os.getenv("DB_QUERY_DELAY", "0"))
        if db_delay > 0:
            time.sleep(db_delay)
        
        if cls._use_turso:
            try:
                if params:
                    cls._conn.execute(query, params)
                else:
                    cls._conn.execute(query)
                return None  # libsql doesn't return lastrowid the same way
            except Exception as e:
                print(f"❌ Update error: {e}")
                raise
        else:
            conn = cls.get_connection()
            cursor = conn.cursor()
            try:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                conn.commit()
                return cursor.lastrowid
            except Exception as e:
                print(f"❌ Update error: {e}")
                raise

def get_db():
    """Dependency for getting database connection"""
    return DatabaseConnection.get_connection()
