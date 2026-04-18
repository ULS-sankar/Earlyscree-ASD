# Android Development Setup Guide

This guide will help you set up Android development environment for building the Early Screen ASD application.

## Prerequisites

### 1. Install Android SDK Platform Tools

The `adb` command is part of Android SDK Platform Tools. Here's how to install it:

#### Option A: Download from Google (Recommended)

1. **Download Android SDK Platform Tools**:
   - Visit: https://developer.android.com/tools/releases/platform-tools
   - Download the package for your operating system (Windows, macOS, Linux)

2. **Extract the package**:
   - Extract to a folder like `C:\Android\platform-tools\`

3. **Add to PATH**:
   - **Windows**:
     - Open System Properties → Advanced → Environment Variables
     - Add `C:\Android\platform-tools\` to your PATH
   - **macOS/Linux**:
     - Add to `~/.bashrc` or `~/.zshrc`:
       ```bash
       export PATH=$PATH:/path/to/platform-tools
       ```

4. **Verify installation**:
   ```bash
   adb --version
   ```

#### Option B: Install Android Studio

1. **Download Android Studio**:
   - Visit: https://developer.android.com/studio
   - Download and install Android Studio

2. **SDK Location**:
   - Android Studio installs SDK tools automatically
   - Default location:
     - **Windows**: `C:\Users\[user]\AppData\Local\Android\Sdk\platform-tools\`
     - **macOS**: `~/Library/Android/sdk/platform-tools/`
     - **Linux**: `~/Android/Sdk/platform-tools/`

3. **Add to PATH**:
   - Add the platform-tools directory to your PATH environment variable

### 2. Enable USB Debugging on Android Device

1. **Enable Developer Options**:
   - Go to Settings → About Phone
   - Tap "Build Number" 7 times
   - You'll see "You are now a developer!"

2. **Enable USB Debugging**:
   - Go to Settings → Developer Options
   - Enable "USB Debugging"
   - Enable "Install via USB" (if available)

### 3. Install Required Dependencies

#### For Buildozer (Linux/macOS recommended)

1. **Install Python and pip**:
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install python3 python3-pip
   
   # macOS (with Homebrew)
   brew install python3
   ```

2. **Install Buildozer**:
   ```bash
   pip3 install buildozer
   ```

3. **Install Android dependencies**:
   ```bash
   # Ubuntu/Debian
   sudo apt install -y git zip unzip openjdk-11-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev
   
   # macOS
   brew install autoconf libtool pkg-config
   ```

### 4. Alternative: Use Docker (Easiest)

If you don't want to set up the full Android development environment:

```bash
# Install Docker first, then run:
docker run --rm -v "$PWD":/home/user/hostcwd kivy/buildozer android debug
```

## Building the APK

### Method 1: Using Buildozer (Linux/macOS)

1. **Navigate to project directory**:
   ```bash
   cd autism-related-behaivours-main
   ```

2. **Initialize Buildozer**:
   ```bash
   buildozer init
   # (The buildozer.spec file is already provided)
   ```

3. **Build the APK**:
   ```bash
   buildozer android debug
   ```

4. **Find the APK**:
   - Location: `bin/earlyscreenasd-0.1-debug.apk`

### Method 2: Using Docker

```bash
# Run in project directory
docker run --rm -v "$PWD":/home/user/hostcwd kivy/buildozer android debug
```

## Installing on Android Device

### Method 1: Using ADB

1. **Connect your Android device via USB**

2. **Verify connection**:
   ```bash
   adb devices
   # Should show your device
   ```

3. **Install the APK**:
   ```bash
   adb install bin/earlyscreenasd-0.1-debug.apk
   ```

### Method 2: Manual Installation

1. **Copy APK to device**:
   - Transfer the APK file to your Android device
   - Use USB, email, or cloud storage

2. **Install manually**:
   - Open File Manager on your Android device
   - Navigate to the APK file
   - Tap to install
   - If blocked, enable "Install unknown apps" for your file manager

## Troubleshooting

### Common Issues

1. **"adb not recognized"**:
   - Ensure Android SDK Platform Tools is installed
   - Check PATH environment variable
   - Restart terminal/command prompt

2. **"Device not found"**:
   - Check USB connection
   - Ensure USB debugging is enabled
   - Try different USB cable/port

3. **Build failures**:
   - Ensure all dependencies are installed
   - Check available disk space (need ~10GB)
   - Try Docker method if native build fails

4. **Installation blocked**:
   - Enable "Install unknown apps" in Android settings
   - Check app permissions

### Getting Help

1. **Check logs**:
   ```bash
   adb logcat
   ```

2. **Buildozer logs**:
   - Check terminal output during build
   - Look for specific error messages

3. **Kivy logs**:
   - Check device logs for Kivy-specific issues

## Quick Start Checklist

- [ ] Install Android SDK Platform Tools
- [ ] Add adb to PATH
- [ ] Enable USB debugging on Android device
- [ ] Install Python and pip
- [ ] Install Buildozer
- [ ] Install Android dependencies
- [ ] Connect Android device via USB
- [ ] Run: `buildozer android debug`
- [ ] Install APK: `adb install bin/earlyscreenasd-0.1-debug.apk`

## Alternative: Pre-built APK

If you prefer not to build from source, you can:
1. Use the Docker method for easier building
2. Request a pre-built APK from the development team
3. Use online APK building services

---

**Note**: Building Android APKs requires a Linux environment for best results. Windows users may encounter issues and should consider using WSL (Windows Subsystem for Linux) or Docker.