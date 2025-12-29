"""
Vercel serverless function entry point for FastAPI.
When framework is set to FastAPI in Vercel dashboard, this file should export the app.
"""
import sys
import os

# Add parent directory to path so we can import app
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import the FastAPI app
from app.main import app

# Export the app - Vercel with FastAPI framework preset should handle this
handler = app

