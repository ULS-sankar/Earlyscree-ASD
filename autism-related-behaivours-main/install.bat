@echo off
echo ===================================================
echo Autism Behavior Recognition System - Setup
echo ===================================================
echo.

echo [1/3] Creating virtual environment...
python -m venv venv

echo [2/3] Activating virtual environment and installing dependencies...
call venv\Scripts\activate
pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install opencv-python numpy Pillow scikit-learn kivy==2.3.0

echo [3/3] Generating initial model skeleton for inference...
python -c "import torch, os; from models.tcn import TCN; os.makedirs('model_zoo/your_model_zoo', exist_ok=True); INPUT_SIZE = 512; OUTPUT_SIZE = 3; HIDDEN_SIZE = 128; LEVEL_SIZE = 10; K_SIZE = 2; DROPOUT = 0.1; FC_SIZE = 128; NUM_CHANNELS = [HIDDEN_SIZE] * (LEVEL_SIZE - 1) + [INPUT_SIZE]; model = TCN(INPUT_SIZE, OUTPUT_SIZE, NUM_CHANNELS, K_SIZE, DROPOUT, FC_SIZE); torch.save(model.state_dict(), 'model_zoo/your_model_zoo/tcn.pkl')"

echo.
echo ===================================================
echo Setup complete! You can now run the app using run_app.bat
echo ===================================================
pause
