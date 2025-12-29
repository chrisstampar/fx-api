"""
Vercel serverless function entry point for FastAPI.
"""
from app.main import app

# Export the app for Vercel
handler = app

