#!/bin/bash
# Quick start script for the API

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "Starting f(x) Protocol API..."
echo "Working directory: $(pwd)"
echo "Access at: http://127.0.0.1:8000"
echo "Docs at: http://127.0.0.1:8000/docs"
echo ""
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

