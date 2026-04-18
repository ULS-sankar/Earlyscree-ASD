#!/usr/bin/env python3
"""
Launcher script for Autism Behavior Recognition Streamlit App
"""

import subprocess
import sys
import os

def main():
    print("🚀 Starting Autism Behavior Recognition Streamlit App...")
    print("📱 The app will open in your default browser at: http://localhost:8501")
    print("Press Ctrl+C to stop the server")
    print("-" * 60)

    try:
        # Run streamlit
        cmd = [sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
               "--server.headless", "true",
               "--server.address", "0.0.0.0",
               "--server.port", "8501"]

        subprocess.run(cmd, cwd=os.getcwd())

    except KeyboardInterrupt:
        print("\n👋 App stopped by user")
    except Exception as e:
        print(f"❌ Error starting app: {e}")
        print("Make sure Streamlit is installed: pip install streamlit")

if __name__ == "__main__":
    main()