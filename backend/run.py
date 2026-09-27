#!/usr/bin/env python3
"""
FoodLoop AI - Independent Backend Server Runner
Usage:
    python run.py [--host 0.0.0.0] [--port 8000] [--reload]
"""
import sys
import os
import uvicorn

# Ensure the backend directory is in the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("=" * 70)
    print("  FOODLOOP AI — ENTERPRISE BACKEND SERVICE")
    print("  All 24 Enterprise API Modules Activated")
    print("  API Docs available at: http://localhost:8000/docs")
    print("  Health Probe: http://localhost:8000/health")
    print("  Readiness Probe: http://localhost:8000/ready")
    print("=" * 70)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
