import sys
from inference import predict_video

v = r"c:\Users\sasi2\OneDrive\Documents\autism-related-behaivours-main\test 1.mp4"
print(f"--- Analyzing: {v} ---")
cls, conf, preds, pcts, frames = predict_video(v)
print(f"Detected Class: {cls} (Confidence: {conf:.2f})")
print(f"Percentages: {pcts}")
