#!/usr/bin/env python3
"""
Launcher script for Autism Behavior Recognition Desktop App
"""

import subprocess
import sys
import os

def main():
    print("🖥️ Starting Autism Behavior Recognition Desktop App...")
    print("💻 The app window will open shortly")
    print("Close the window to exit the application")
    print("-" * 60)

    try:
        # Run the desktop app
        cmd = [sys.executable, "desktop_app.py"]
        subprocess.run(cmd, cwd=os.getcwd())

    except KeyboardInterrupt:
        print("\n👋 App closed by user")
    except Exception as e:
        print(f"❌ Error starting app: {e}")
        print("Make sure Tkinter is available (usually built-in with Python)")

if __name__ == "__main__":
    main()