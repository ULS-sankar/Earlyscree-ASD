@echo off
echo ===================================================
echo Early Screen ASD - Docker Android Build
echo ===================================================
echo.

echo Building Android APK using Docker...
echo This will create an APK file in the bin/ directory
echo.

REM Create a script that automatically answers the root confirmation
echo y | docker run --rm -v "%CD%":/home/user/hostcwd kivy/buildozer android debug

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

echo ===================================================
echo Build process completed
echo ===================================================
pause