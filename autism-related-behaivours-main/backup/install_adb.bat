@echo off
echo ===================================================
echo Android ADB Installation Guide
echo ===================================================
echo.

echo ADB (Android Debug Bridge) is required to install APKs on Android devices.
echo.

echo Download ADB Platform Tools:
echo 1. Visit: https://developer.android.com/tools/releases/platform-tools
echo 2. Download the package for Windows
echo 3. Extract to: C:\Android\platform-tools\
echo 4. Add to PATH: C:\Android\platform-tools\
echo.

echo Alternative: Use Chocolatey (if installed)
echo   choco install adb
echo.

echo After installing ADB, you can install your APK with:
echo   adb install bin/earlyscreenasd-0.1-debug.apk
echo.

echo Or manually copy the APK to your Android device and install it.
echo.

pause