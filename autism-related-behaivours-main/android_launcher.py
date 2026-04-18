#!/usr/bin/env python3
"""
Android Launcher for Early Screen ASD Kivy Application
This script provides a simple way to launch the Kivy application on Android devices.
"""

import sys
import os

def check_dependencies():
    """Check if required dependencies are available"""
    missing_deps = []
    
    # Core libraries
    deps = {
        "kivy": "Kivy",
        "numpy": "NumPy",
        "cv2": "OpenCV (opencv-python)",
        "torch": "PyTorch",
        "torchvision": "TorchVision",
        "PIL": "Pillow"
    }
    
    print("\nChecking system dependencies...")
    for module_name, display_name in deps.items():
        try:
            mod = __import__(module_name)
            version = getattr(mod, "__version__", "unknown")
            print(f"✓ {display_name} version: {version}")
        except ImportError:
            missing_deps.append(module_name)
    
    try:
        import sqlite3
        print("✓ SQLite3 available")
    except ImportError:
        missing_deps.append("sqlite3")
    
    if missing_deps:
        print(f"\n❌ Missing dependencies: {', '.join(missing_deps)}")
        print("\nTo install missing dependencies, run:")
        print("pip install " + " ".join(missing_deps))
        return False
    
    return True

def main():
    """Main launcher function"""
    print("\n" + "=" * 40)
    print("Early Screen ASD - Android Launcher")
    print("=" * 40)
    
    # Check if we're on Android
    if hasattr(sys, 'getandroidapilevel'):
        print("✓ Running on Android")
        android_level = sys.getandroidapilevel()
        print(f"✓ Android API Level: {android_level}")
    else:
        print("ℹ Running on desktop (development mode)")
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Cannot launch application due to missing dependencies")
        # In a real Android environment, we might want to show a UI error instead of exiting
        if not hasattr(sys, 'getandroidapilevel'):
            sys.exit(1)
    
    print("\n✓ All dependencies available")
    print("✓ Initializing AI Model and UI...")
    
    # Import and run the main application
    try:
        from kivy_app import EarlyScreenApp
        app = EarlyScreenApp()
        app.run()
    except ImportError as e:
        print(f"\n❌ Error importing application: {e}")
        print("Make sure all .py files are in the same directory")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error running application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
