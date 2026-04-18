@echo off
echo ===================================================
echo Early Screen ASD - Windows Android Build
echo ===================================================
echo.

echo ⚠️  Docker Desktop is having issues on your system.
echo This script will attempt a native Windows build.
echo Note: This may require additional setup steps.
echo.

echo Checking Windows prerequisites...

REM Check if we're running as administrator
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ This script requires administrator privileges.
    echo Please run Command Prompt as Administrator.
    pause
    exit /b 1
)

echo ✓ Running as administrator

REM Check if WSL is available (recommended for Windows builds)
wsl --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ WSL (Windows Subsystem for Linux) found
    echo.
    echo 🎯 Recommended: Use WSL for better Android build support
    echo Run these commands in WSL:
    echo   sudo apt update
    echo   sudo apt install python3 python3-pip git
    echo   pip3 install buildozer
    echo   buildozer android debug
    echo.
    pause
    exit /b 0
) else (
    echo ⚠ WSL not found - attempting native Windows build
)

echo.
echo Attempting to install Buildozer on Windows...

REM Try to install Buildozer
pip install buildozer

if %errorlevel% equ 0 (
    echo ✓ Buildozer installed successfully
    goto :check_java
) else (
    echo ❌ Failed to install Buildozer
    echo Buildozer may not work well on Windows natively
    echo.
    echo 💡 Alternative solutions:
    echo 1. Install WSL: wsl --install
    echo 2. Use Linux/macOS machine for build
    echo 3. Use online APK building services
    echo.
    pause
    exit /b 1
)

:check_java
echo.
echo Checking Java installation...

java -version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Java found
    goto :build_attempt
) else (
    echo ❌ Java not found
    echo Please install Java JDK 11 or higher from:
    echo https://www.oracle.com/java/technologies/downloads/
    echo.
    pause
    exit /b 1
)

:build_attempt
echo.
echo Attempting Android build...
echo This may take 10-30 minutes and may fail on Windows
echo.

buildozer android debug

if %errorlevel% equ 0 (
    echo.
    echo ✅ APK built successfully!
    echo Find your APK at: bin/earlyscreenasd-0.1-debug.apk
    echo.
    echo To install on Android device:
    echo 1. Enable USB debugging on your Android device
    echo 2. Connect device via USB
    echo 3. Run: adb install bin/earlyscreenasd-0.1-debug.apk
    echo.
) else (
    echo ❌ Build failed
    echo Windows native builds are not well supported for Android
    echo.
    echo 💡 Recommended solutions:
    echo 1. Use WSL: wsl --install (then follow Linux instructions)
    echo 2. Use a Linux virtual machine
    echo 3. Use online APK building services
    echo 4. Try Docker Desktop with proper setup
)

echo.
echo ===================================================
echo Build process completed
echo ===================================================
pause