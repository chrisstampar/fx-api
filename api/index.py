"""
Vercel serverless function entry point for FastAPI.
"""
import sys
import os

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the FastAPI app
from app.main import app

# For Vercel, we need to export the app directly
# Vercel should auto-detect it's an ASGI app
handler = app

