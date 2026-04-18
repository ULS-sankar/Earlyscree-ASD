# Early Screen ASD - Android Development Guide

This guide will help you build and deploy the Early Screen ASD application to Android devices.

## Quick Start

### Option 1: Using Docker (Recommended - Works on Windows, macOS, Linux)

1. **Install Docker Desktop**
   - Download from: https://www.docker.com/products/docker-desktop
   - Follow installation instructions for your platform

2. **Build the APK**
   ```bash
   # Run the build script
   build_android.bat
   ```

3. **Install on Android Device**
   ```bash
   # Enable USB debugging on your Android device
   # Connect device via USB
   adb install bin/earlyscreenasd-0.1-debug.apk
   ```

### Option 2: Native Build (Linux/macOS recommended)

1. **Install Prerequisites**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install python3 python3-pip git zip unzip openjdk-11-jdk
   
   # macOS (with Homebrew)
   brew install python3 git
   ```

2. **Install Buildozer**
   ```bash
   pip3 install buildozer
   ```

3. **Build the APK**
   ```bash
   buildozer android debug
   ```

## Prerequisites

### For Docker Method
- Docker Desktop installed and running
- Android device with USB debugging enabled
- ADB (Android Debug Bridge) installed

### For Native Method
- Linux or macOS (Windows users should use WSL or Docker)
- Python 3.8+
- Java Development Kit (JDK 11+)
- Android SDK (automatically downloaded by Buildozer)

## Installation Steps

### 1. Set up the Environment

```bash
# Clone or navigate to your project directory
cd autism-related-behaivours-main

# Install Python dependencies
install.bat
```

### 2. Build the APK

```bash
# Use the automated build script
build_android.bat
```

### 3. Install on Android Device

1. **Enable Developer Options**
   - Go to Settings → About Phone
   - Tap "Build Number" 7 times

2. **Enable USB Debugging**
   - Go to Settings → Developer Options
   - Enable "USB Debugging"

3. **Install the APK**
   ```bash
   adb install bin/earlyscreenasd-0.1-debug.apk
   ```

## Troubleshooting

### Common Issues

**"adb not recognized"**
```bash
# Install ADB
# Windows: Download from Android SDK Platform Tools
# macOS: brew install android-platform-tools
# Linux: sudo apt install adb
```

**Build fails with missing dependencies**
```bash
# Ensure all prerequisites are installed
# Try Docker method if native build fails
```

**App crashes on startup**
```bash
# Check Android logs
adb logcat

# Ensure device has sufficient storage
# Try reinstalling the APK
```

### Getting Help

1. **Check build logs** - Look for specific error messages
2. **Verify Android version** - App requires Android 7.0+ (API 24+)
3. **Check permissions** - App needs Camera, Storage, and Internet permissions

## App Features

### Main Screens
1. **Home Screen** - Logo and navigation buttons
2. **Upload Screen** - Video selection and analysis
3. **Reports Screen** - History of previous analyses
4. **Learn Screen** - Information about autism detection

### Key Features
- **Video Analysis** - Upload and analyze videos for autism-related behaviors
- **False Positive Prevention** - AI system to detect non-human content
- **Database Storage** - Local SQLite database for analysis history
- **Progress Tracking** - Real-time analysis progress display

## Performance Optimization

### For Better Performance
- Use videos under 2 minutes for faster analysis
- Ensure good lighting conditions for video capture
- Use stable camera positioning during recording

### Memory Management
- App automatically manages memory usage
- Large videos are processed in chunks
- Temporary files are cleaned up after analysis

## Development Notes

### Build Configuration
- **Target Android API**: 33
- **Minimum Android API**: 21 (Android 5.0+)
- **Architecture**: arm64-v8a (optimized for modern devices)
- **Python Version**: 3.8+
- **Kivy Version**: 2.3.0

### Dependencies
- Kivy 2.3.0 (UI framework)
- PyTorch 2.0.1 (AI inference)
- OpenCV 4.8.0 (video processing)
- NumPy 1.24.3 (numerical computations)

## Support

If you encounter issues:

1. **Check the logs** - Use `adb logcat` to see detailed error messages
2. **Verify setup** - Ensure all prerequisites are properly installed
3. **Try Docker method** - More reliable than native builds on Windows
4. **Check Android version** - Ensure device meets minimum requirements

## Legal Notice

This application is for educational and research purposes only. It is not a medical diagnostic tool and should not be used as a substitute for professional medical evaluation.

## License

This project is licensed under the terms specified in the LICENSE file.