@echo off
echo ===================================================
echo Docker Desktop Restart and Android Build Guide
echo ===================================================
echo.
echo Docker Desktop needs to be running for the build to work.
echo.
echo Step 1: Restart Docker Desktop
echo 1. Open Docker Desktop application
echo 2. Wait for it to show "Docker Desktop is running"
echo 3. Check the Docker icon in system tray shows green
echo.
echo Step 2: Verify Docker is working
echo Run this command in a new terminal:
echo   docker --version
echo.
echo Step 3: Run the Android build
echo After Docker is running, execute:
echo   build_android_final.bat
echo.
echo Step 4: Install the APK
echo Once build completes, the APK will be at:
echo   bin/earlyscreenasd-0.1-debug.apk
echo.
echo Alternative: Use WSL for build
echo If Docker continues to have issues:
echo 1. Install WSL2: wsl --install
echo 2. Install Ubuntu from Microsoft Store
echo 3. Run build in WSL terminal
echo.
echo For immediate testing, you can also:
echo - Use the desktop app: python desktop_app.py
echo - Use the web app: streamlit run streamlit_app.py
echo.
pause