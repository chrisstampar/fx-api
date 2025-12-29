"""
Vercel serverless function entry point for FastAPI.
Uses Mangum to wrap FastAPI for serverless compatibility.
"""
from mangum import Mangum
from app.main import app

# Wrap FastAPI app with Mangum for Vercel/Lambda compatibility
handler = Mangum(app, lifespan="off")

