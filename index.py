"""
Vercel serverless function entry point for FastAPI.
When framework is set to FastAPI in Vercel dashboard, this file should export the app.
"""
from app.main import app

# Export the app - Vercel with FastAPI framework preset should handle this
handler = app

