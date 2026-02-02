"""
Vercel entry point for FastAPI application
"""
from app import app

# Export the app for Vercel (ASGI)
__all__ = ["app"]
