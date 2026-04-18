@echo off
echo ===================================================
echo Early Screen ASD - Final Android Build
echo ===================================================
echo.

echo Building Android APK using Docker...
echo This will create an APK file in the bin/ directory
echo.

REM Create a temporary script file to handle the interactive prompt
echo y > temp_answer.txt

REM Run Docker build with the answer file
docker run --rm -v "%CD%":/home/user/hostcwd kivy/buildozer android debug < temp_answer.txt

REM Clean up temporary file
del temp_answer.txt

if %errorlevel% equ 0 (
    echo.
    echo ✅ APK built successfully!
    echo Find your APK at: bin/earlyscreenasd-0.1-debug.apk
    echo.
    echo To install on Android device:
    echo 1. Install ADB from: https://developer.android.com/tools/releases/platform-tools
    echo 2. Enable USB debugging on your Android device
    echo 3. Connect device via USB
    echo 4. Run: adb install bin/earlyscreenasd-0.1-debug.apk
    echo.
    echo Alternative: Copy the APK file to your Android device and install manually
) else (
    echo ❌ Docker build failed
    echo Please check the error messages above
)

echo ===================================================
echo Build process completed
echo ===================================================
pause