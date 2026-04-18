@echo off
echo ===================================================
echo Early Screen ASD - Project Cleanup
echo ===================================================
echo.
echo This will organize your project and remove unnecessary files
echo for the Android build. Essential files will be preserved.
echo.
echo Files that will be REMOVED:
echo - Test files (*.test.py, test_*.py)
echo - Debug files (debug_*.py, debug_output.txt)
echo - Development scripts (*.bat files except essential ones)
echo - Documentation files (README.md, guides)
echo - TV app files (tv_app/)
echo - Desktop app files (desktop_app.py)
echo - Streamlit app files (streamlit_app.py)
echo - Training files (train_*.py)
echo - Development utilities
echo.
echo Files that will be PRESERVED:
echo - Core app files (kivy_app.py, inference.py)
echo - Model files and weights
echo - Buildozer configuration
echo - Essential requirements
echo - Videos and data
echo.
pause
echo.
echo Starting cleanup...

REM Create backup directory
if not exist "backup" mkdir backup

REM Move test files to backup
echo Moving test files...
move test_*.py backup\ 2>nul
move *.test.py backup\ 2>nul

REM Move debug files to backup
echo Moving debug files...
move debug_*.py backup\ 2>nul
move debug_output.txt backup\ 2>nul

REM Move development scripts (keep only essential ones)
echo Moving development scripts...
move install_adb.bat backup\ 2>nul
move install_apk_manual.bat backup\ 2>nul
move restart_docker_and_build.bat backup\ 2>nul
move simple_test_app.py backup\ 2>nul
move build_android_docker.bat backup\ 2>nul
move build_android_windows.bat backup\ 2>nul
move build_android.bat backup\ 2>nul

REM Move documentation files to backup
echo Moving documentation files...
move ANDROID_BUILD_GUIDE.md backup\ 2>nul
move ANDROID_BUILD_SUMMARY.md backup\ 2>nul
move ANDROID_README.md backup\ 2>nul
move android_setup_guide.md backup\ 2>nul
move FINAL_ANDROID_BUILD_GUIDE.md backup\ 2>nul
move README.md backup\ 2>nul

REM Move TV app to backup
echo Moving TV app...
move tv_app\ backup\ 2>nul

REM Move desktop and web apps to backup
echo Moving desktop and web apps...
move desktop_app.py backup\ 2>nul
move streamlit_app.py backup\ 2>nul

REM Move training files to backup
echo Moving training files...
move train_*.py backup\ 2>nul
move retrain_model.py backup\ 2>nul

REM Move development utilities
echo Moving development utilities...
move enhanced_feature_extractor.py backup\ 2>nul
move extract_features_from_videos.py backup\ 2>nul
move extract_ssbd_frames.py backup\ 2>nul
move quick_extract_features.py backup\ 2>nul
move pytorch_test.py backup\ 2>nul

echo.
echo ✅ Cleanup completed!
echo.
echo Essential files for Android build:
echo - kivy_app.py (main Android app)
echo - inference.py (AI inference)
echo - false_positive_prevention.py
echo - buildozer.spec (Android build config)
echo - requirements.txt (Python dependencies)
echo - kivy_requirements.txt (Kivy dependencies)
echo - models/ (AI models)
echo - videos/ (sample videos)
echo - data/ (training data)
echo.
echo Backup created at: backup/
echo.
echo To run the Android build:
echo   build_android_final.bat
echo.
pause