#!/usr/bin/env python
"""
Entry point to run the Startup Idea Validator AI application.
Usage:
    python run.py
"""
import sys
from app import create_app
from config import Config

app = create_app()

if __name__ == "__main__":
    print(f"===========================================================")
    print(f"  Startup Idea Validator AI — Multi-Agent Validation Engine ")
    print(f"===========================================================")
    print(f"  Host: http://{Config.HOST}:{Config.PORT}")
    print(f"  Mode: {'Demo / Simulation' if Config.DEMO_MODE else 'Live API'}")
    print(f"  Groq API Configured: {bool(Config.GROQ_API_KEY)}")
    print(f"  Tavily API Configured: {bool(Config.TAVILY_API_KEY)}")
    print(f"  Active Model: {Config.GROQ_MODEL}")
    print(f"===========================================================\n")
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
