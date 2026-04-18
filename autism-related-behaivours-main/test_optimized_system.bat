@echo off
echo Testing Optimized Autism Behavior Detection System...
echo =====================================================
echo.

REM Set environment variable to fix OpenMP issue
set KMP_DUPLICATE_LIB_OK=TRUE

echo 1. Testing optimized inference with sample video...
echo -----------------------------------------------------
python inference_optimized.py --video videos/v_ArmFlapping_01.mp4
echo.

echo 2. Testing behavior listing...
echo -----------------------------------------------------
python inference_optimized.py --list-behaviors
echo.

echo 3. Comparing processing times...
echo -----------------------------------------------------
echo Running optimized version:
python -c "import time; start=time.time(); exec(open('inference_optimized.py').read()); print(f'Optimized processing completed in {time.time()-start:.2f} seconds')"
echo.

echo 4. Testing with different video types...
echo -----------------------------------------------------
echo Testing HeadBanging video:
python inference_optimized.py --video videos/v_HeadBanging_01.mp4
echo.

echo Testing Spinning video:
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
pause