"""
Vercel serverless function entry point for FastAPI.
Uses Mangum to wrap FastAPI for serverless compatibility.
"""
import sys
import os

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mangum import Mangum
from app.main import app

# Wrap FastAPI app with Mangum for Vercel/Lambda compatibility
handler = Mangum(app, lifespan="off")

