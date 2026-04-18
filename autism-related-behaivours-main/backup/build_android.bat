@echo off
echo ===================================================
echo Early Screen ASD - Android Build Script
echo ===================================================
echo.

echo Checking prerequisites...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

REM Check if pip is available
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ pip not found. Please install pip.
    pause
    exit /b 1
)

echo ✓ Python and pip found

REM Check if Docker is available (recommended for Android builds)
docker --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Docker found - using Docker for Android build
    goto :use_docker
) else (
    echo ⚠ Docker not found - attempting native build (Linux/macOS recommended)
    goto :check_buildozer
)

:use_docker
echo.
echo Building Android APK using Docker...
echo This will create an APK file in the bin/ directory
echo.

REM Create Docker build script
echo Building APK with Docker...
docker run --rm -v "%CD%":/home/user/hostcwd kivy/buildozer android debug

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
    echo ❌ Docker build failed
    echo Please check the error messages above
)

goto :end

:check_buildozer
echo.
echo Attempting native Buildozer build...
echo Note: Native builds work best on Linux/macOS
echo.

REM Check if buildozer is installed
pip show buildozer >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Buildozer found
    goto :build_native
) else (
    echo ❌ Buildozer not found
    echo Installing Buildozer...
    pip install buildozer
    if %errorlevel% equ 0 (
        echo ✓ Buildozer installed
        goto :build_native
    ) else (
        echo ❌ Failed to install Buildozer
        echo Please install Buildozer manually: pip install buildozer
        goto :end
    )
)

:build_native
echo.
echo Building Android APK using native Buildozer...
echo This may take 10-30 minutes on first run
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
    echo ❌ Native build failed
    echo Please check the error messages above
    echo Consider using Docker method instead
)

:end
echo.
echo ===================================================
echo Build process completed
echo ===================================================
pause