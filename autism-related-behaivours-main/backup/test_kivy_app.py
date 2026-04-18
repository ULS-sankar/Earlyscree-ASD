#!/usr/bin/env python3
"""
Test script to verify Kivy application runs correctly before Android build
"""

import sys
import os

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing module imports...")
    
    modules_to_test = [
        ('kivy', 'Kivy UI framework'),
        ('numpy', 'NumPy numerical library'),
        ('cv2', 'OpenCV computer vision'),
        ('torch', 'PyTorch deep learning'),
        ('sqlite3', 'SQLite database'),
        ('PIL', 'Pillow image processing')
    ]
    
    failed_imports = []
    
    for module_name, description in modules_to_test:
        try:
            if module_name == 'kivy':
                import kivy
            elif module_name == 'numpy':
                import numpy
            elif module_name == 'cv2':
                import cv2
            elif module_name == 'torch':
                import torch
            elif module_name == 'sqlite3':
                import sqlite3
            elif module_name == 'PIL':
                import PIL
            print(f"✓ {description}")
        except ImportError as e:
            print(f"❌ {description}: {e}")
            failed_imports.append(module_name)
    
    return failed_imports

def test_app_structure():
    """Test if the Kivy app structure is correct"""
    print("\nTesting application structure...")
    
    required_files = [
        'kivy_app.py',
        'false_positive_prevention.py',
        'inference.py',
        'models/tcn.py'
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✓ {file_path}")
        else:
            print(f"❌ {file_path} - Missing")
            missing_files.append(file_path)
    
    return missing_files

def test_model_files():
    """Test if model files exist"""
    print("\nTesting model files...")
    
    model_dir = 'model_zoo/your_model_zoo'
    model_file = os.path.join(model_dir, 'tcn.pkl')
    
    if os.path.exists(model_file):
        print(f"✓ Model file exists: {model_file}")
        return True
    else:
        print(f"❌ Model file missing: {model_file}")
        print("   Note: This will be created during first run or build")
        return False

def run_basic_app_test():
    """Try to run a basic version of the app"""
    print("\nTesting basic app functionality...")
    
    try:
        # Import the app
        from kivy_app import EarlyScreenApp
        
        # Try to create app instance
        app = EarlyScreenApp()
        print("✓ App instance created successfully")
        
        # Test database initialization
        import sqlite3
        conn = sqlite3.connect('test_results.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                timestamp TEXT,
                assessment TEXT,
                confidence REAL,
                behaviors TEXT,
                analysis_time REAL
            )
        ''')
        conn.close()
        print("✓ Database initialization test passed")
        
        return True
        
    except Exception as e:
        print(f"❌ App test failed: {e}")
        return False

def main():
    """Main test function"""
    print("=" * 50)
    print("Early Screen ASD - Kivy App Test")
    print("=" * 50)
    
    # Test imports
    failed_imports = test_imports()
    
    # Test app structure
    missing_files = test_app_structure()
    
    # Test model files
    model_exists = test_model_files()
    
    # Test basic functionality
    app_works = run_basic_app_test()
    
    print("\n" + "=" * 50)
    print("Test Results Summary")
    print("=" * 50)
    
    if failed_imports:
        print(f"❌ Failed imports: {', '.join(failed_imports)}")
        print("   Please install missing dependencies with: pip install " + " ".join(failed_imports))
    else:
        print("✓ All required modules imported successfully")
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
    else:
        print("✓ All required files present")
    
    if model_exists:
        print("✓ Model files ready")
    else:
        print("⚠ Model files will be generated during build")
    
    if app_works:
        print("✓ App functionality test passed")
    else:
        print("❌ App functionality test failed")
    
    print("\n" + "=" * 50)
    
    if not failed_imports and not missing_files and app_works:
        print("🎉 All tests passed! Your app is ready for Android build.")
        print("\nNext steps:")
        print("1. Run: build_android.bat")
        print("2. Install the generated APK on your Android device")
        return True
    else:
        print("⚠ Some tests failed. Please fix the issues above before building.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)