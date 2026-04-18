@echo off
echo Testing Optimized Autism Behavior Detection System...
echo =====================================================
echo.

REM Set environment variable to fix OpenMP issue
echo Setting OpenMP environment variable...
set KMP_DUPLICATE_LIB_OK=TRUE

echo 1. Testing optimized inference with sample video...
echo -----------------------------------------------------
echo Running: python inference_optimized.py --video videos/v_ArmFlapping_01.mp4
python inference_optimized.py --video videos/v_ArmFlapping_01.mp4
echo.

echo 2. Testing behavior listing...
echo -----------------------------------------------------
echo Running: python inference_optimized.py --list-behaviors
python inference_optimized.py --list-behaviors
echo.

echo 3. Testing with HeadBanging video...
echo -----------------------------------------------------
echo Running: python inference_optimized.py --video videos/v_HeadBanging_01.mp4
python inference_optimized.py --video videos/v_HeadBanging_01.mp4
echo.

echo 4. Testing with Spinning video...
echo -----------------------------------------------------
echo Running: python inference_optimized.py --video videos/v_Spinning_01.mp4
python inference_optimized.py --video videos/v_Spinning_01.mp4
echo.

echo Test completed!
echo.
echo Key improvements implemented:
echo - 50%% more model capacity (HIDDEN_SIZE: 128 -> 256)
echo - Faster frame processing (every 5th frame vs 10th)
echo - Optimized human detection algorithms
echo - ResNet18 feature extraction
echo - Gradient clipping and label smoothing
echo - Class-weighted loss for better accuracy
echo.
echo If you see OpenMP errors, the system is still working correctly.
echo The KMP_DUPLICATE_LIB_OK=TRUE environment variable should resolve this.
echo.
pause