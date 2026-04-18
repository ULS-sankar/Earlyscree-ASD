@echo off
echo Testing Desktop App CLI...
echo.

REM Set environment variable to fix OpenMP issue
set KMP_DUPLICATE_LIB_OK=TRUE

echo Available behaviors:
python desktop_app_cli.py --list-behaviors
echo.

echo Testing with sample video...
python desktop_app_cli.py --video videos/v_ArmFlapping_01.mp4
echo.

echo Test completed!
pause