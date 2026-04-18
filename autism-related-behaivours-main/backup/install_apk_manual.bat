@echo off
echo ===================================================
echo Early Screen ASD - Manual APK Installation
echo ===================================================
echo.
echo Your APK is ready at: bin/earlyscreenasd-0.1-debug.apk
echo.
echo Since ADB is not installed, here are manual installation options:
echo.
echo Option 1: USB Transfer
echo 1. Connect your Android device to your computer via USB
echo 2. Copy the APK file to your device:
echo    copy "bin\earlyscreenasd-0.1-debug.apk" "YourDeviceName\Downloads\"
echo 3. On your Android device:
echo    - Go to Settings > Security > Enable "Unknown sources"
echo    - Open Downloads folder and tap the APK file to install
echo.
echo Option 2: Email/Cloud Transfer
echo 1. Email the APK file to yourself or upload to cloud storage
echo 2. Download it on your Android device
echo 3. Enable "Unknown sources" in Settings > Security
echo 4. Install the downloaded APK
echo.
echo Option 3: Wireless Transfer Apps
echo Use apps like:
echo - SHAREit
echo - Xender
echo - Files by Google
echo - Send Anywhere
echo.
echo APK Location: %CD%\bin\earlyscreenasd-0.1-debug.apk
echo.
echo To view the APK file location in File Explorer:
explorer.exe "%CD%\bin"
echo.
pause