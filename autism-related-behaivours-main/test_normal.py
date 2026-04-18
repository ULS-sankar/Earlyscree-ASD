import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import sys
from inference import predict_video

videos = [
    r"c:\Users\sasi2\OneDrive\Documents\autism-related-behaivours-main\videos\normal\20260324_194341.mp4",
    r"c:\Users\sasi2\OneDrive\Documents\autism-related-behaivours-main\videos\normal\20260324_194408.mp4"
]

for v in videos:
    print(f"\n--- Analyzing: {v} ---")
    cls, conf, preds, pcts, frames = predict_video(v)
    print(f"Detected Class: {cls} (Confidence: {conf:.2f})")
    print(f"Percentages: {pcts}")
