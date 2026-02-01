import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL")
    TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    
    @classmethod
    def validate(cls):
        """Validate that all required environment variables are set"""
        required = ["TURSO_DATABASE_URL", "TURSO_AUTH_TOKEN", "OPENAI_API_KEY"]
        missing = [var for var in required if not getattr(cls, var)]
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        return True

if __name__ == "__main__":
    Config.validate()
    print("✅ All environment variables are set correctly")
