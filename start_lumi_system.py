#!/usr/bin/env python3
"""
Startup script for the complete Lumi Audio system
Starts both the Python backend API and the Next.js frontend
"""

import subprocess
import time
import os
import signal
import sys
from threading import Thread

def run_backend():
    """Run the Python Flask backend"""
    print("🚀 Starting Python Backend API...")
    try:
        subprocess.run([
            "python3", "backend_api.py"
        ], cwd="/Users/vaidehigupta/Desktop/GitHub/lumi_audio")
    except KeyboardInterrupt:
        print("\n🛑 Backend API stopped")

def run_frontend():
    """Run the Next.js frontend"""
    print("🌐 Starting Next.js Frontend...")
    time.sleep(3)  # Wait for backend to start
    try:
        subprocess.run([
            "npm", "run", "dev"
        ], cwd="/Users/vaidehigupta/Desktop/GitHub/lumi_audio/frontend")
    except KeyboardInterrupt:
        print("\n🛑 Frontend stopped")

def main():
    """Start both services"""
    print("=" * 60)
    print("🎭 LUMI AUDIO - Dynamic Museum Chatbot System")
    print("=" * 60)
    print("🔧 Starting integrated CedarOS frontend + Python AI backend")
    print()
    
    # Check if we have the required API keys
    if not os.getenv("GEMINI_API_KEY"):
        print("⚠️  WARNING: GEMINI_API_KEY not found in environment")
        print("   Set it in your .env file for AI chat functionality")
    
    if not os.getenv("ELEVENLABS_API_KEY"):
        print("⚠️  WARNING: ELEVENLABS_API_KEY not found in environment")
        print("   Set it in your .env file for audio/video generation")
    
    print()
    print("🚀 Starting services...")
    print("   Backend API: http://localhost:5000")
    print("   Frontend UI: http://localhost:3000")
    print()
    print("Press Ctrl+C to stop both services")
    print("=" * 60)
    
    # Start both services in separate threads
    backend_thread = Thread(target=run_backend, daemon=True)
    frontend_thread = Thread(target=run_frontend, daemon=True)
    
    backend_thread.start()
    frontend_thread.start()
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Lumi Audio system...")
        print("   Stopping backend and frontend services...")
        sys.exit(0)

if __name__ == "__main__":
    main()
