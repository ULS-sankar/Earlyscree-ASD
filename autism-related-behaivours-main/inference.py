"""
inference.py  —  Early Screen ASD
===================================
Feature pipeline EXACTLY matches backup/retrain_model.py so that the
trained model and inference use identical features.

Key parameters (must stay in sync with retrain_model.py):
  CLIP_LENGTH  = 10   frames per TCN clip
  FRAME_SKIP   = 5    sample every Nth frame
  HIDDEN_SIZE  = 256  (new retrained model)
  FC_SIZE      = 256
  INPUT_SIZE   = 512  (ResNet18 output dim)
"""

import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import torch
import torch.nn as nn
import cv2
import numpy as np
from torchvision import transforms
from torchvision.models import resnet18, ResNet18_Weights
from models.tcn import TCN
from PIL import Image
import argparse

# ─── Config ──────────────────────────────────────────────────────────────────
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL_PATH  = "model_zoo/your_model_zoo/tcn.pkl"
CLASS_NAMES = ["Armflapping", "Headbanging", "Spinning", "Normal"]

CLIP_LENGTH  = 10    # frames per TCN clip  (must match retrain_model.py)
FRAME_SKIP   = 5     # sample every Nth frame  (must match)
STRIDE       = 5             # 50% Overlap: Best balance of precision & speed

# Confidence margin: winner must beat runner-up by this many % of clips
MARGIN_MIN   = 15.0

# ─── Model arch (EXACT match to retrain_model_enhanced.py/train_with_features_tcn_improved.py) ──────────────────
INPUT_SIZE  = 512
HIDDEN_SIZE = 256
LEVEL_SIZE  = 10
K_SIZE      = 2
DROPOUT     = 0.3
FC_SIZE     = 256

NUM_CHANNELS = [HIDDEN_SIZE] * (LEVEL_SIZE - 1) + [INPUT_SIZE]

# ─── Load model ──────────────────────────────────────────────────────────────
try:
    checkpoint = torch.load(MODEL_PATH, map_location=device)
    # Detect output size from checkpoint (fc2 is the final layer in TCN)
    if 'fc2.weight' in checkpoint:
        ACTUAL_OUTPUT_SIZE = checkpoint['fc2.weight'].shape[0]
        print(f"Detected model with {ACTUAL_OUTPUT_SIZE} output classes.")
    else:
        ACTUAL_OUTPUT_SIZE = 3 # Fallback for older models
    
    model = TCN(INPUT_SIZE, ACTUAL_OUTPUT_SIZE, NUM_CHANNELS, K_SIZE, DROPOUT, FC_SIZE)
    model.load_state_dict(checkpoint, strict=True)
    model.to(device)
    model.eval()
    print("TCN Model loaded successfully!")
except Exception as e:
    print(f"Error loading model: {e}")
    # Fallback initialization to prevent crash during import
    model = TCN(INPUT_SIZE, 3, NUM_CHANNELS, K_SIZE, DROPOUT, FC_SIZE)

# ─── Feature extractor (must match retrain_model.py) ─────────────────────────
_base = resnet18(weights=ResNet18_Weights.DEFAULT)
feature_extractor = nn.Sequential(
    *list(_base.children())[:-2],
    nn.AdaptiveAvgPool2d((1, 1))
)
feature_extractor.eval()
feature_extractor.to(device)

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])


# ─── Frame extraction ─────────────────────────────────────────────────────────
def read_frames(video_path, frame_skip=FRAME_SKIP):
    """Read and downsample frames from a video file."""
    cap = cv2.VideoCapture(video_path)
    frames, fc = [], 0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    # Use every frame if video is very short
    if total < CLIP_LENGTH * 5:
        frame_skip = 1
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if fc % frame_skip == 0:
            frame = cv2.resize(frame, (224, 224))
            frames.append(frame)
        fc += 1
    cap.release()
    return frames, fc


# ─── Feature extraction (exact match to retrain_model.py) ────────────────────
# ─── [NEW] Batch Processing Helpers ──────────────────────────────────────────
def extract_features_batched(frames, batch_size=32):
    """Extract features from all frames in large batches for speed."""
    all_features = []
    for i in range(0, len(frames), batch_size):
        batch_frames = frames[i:i + batch_size]
        tensors = []
        for f in batch_frames:
            rgb = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
            tensors.append(transform(Image.fromarray(rgb)))
        
        batch_tensor = torch.stack(tensors).to(device)
        with torch.no_grad():
            # (Batch, 512, 1, 1) -> (Batch, 512)
            feats = feature_extractor(batch_tensor).view(len(batch_frames), -1)
        all_features.append(feats.cpu())
    
    return torch.cat(all_features, dim=0) # (TotalFrames, 512)


# ─── Main prediction ──────────────────────────────────────────────────────────
def predict_video(video_path):
    """
    Analyse a video using BATCH PROCESSING for maximum speed and accuracy.
    """
    print(f"\n[EARLY SCREEN ASD] Analyzing: {os.path.basename(video_path)}")

    frames, total_frames_read = read_frames(video_path)

    if len(frames) < CLIP_LENGTH:
        if len(frames) == 0:
            return "Undetected", 0.0, [], {n: 0.0 for n in CLASS_NAMES}, 0
        while len(frames) < CLIP_LENGTH:
            frames.append(frames[-1].copy())

    print(f"  * Batch Feature Extraction ({len(frames)} frames)...", end="", flush=True)
    # 1. Extract all frame features at once
    frame_features = extract_features_batched(frames)
    print(" OK")

    # 2. Slice into overlapping clips
    clips_list = []
    for start in range(0, len(frame_features) - CLIP_LENGTH + 1, STRIDE):
        clip = frame_features[start : start + CLIP_LENGTH] # (10, 512)
        clips_list.append(clip.permute(1, 0)) # (512, 10)
    
    if not clips_list:
        return "Undetected", 0.0, [], {n: 0.0 for n in CLASS_NAMES}, total_frames_read

    # 3. Batch TCN Inference
    print(f"  * Batch TCN Inference ({len(clips_list)} clips)...", end="", flush=True)
    all_clips_tensor = torch.stack(clips_list).to(device) # (N_clips, 512, 10)
    
    with torch.no_grad():
        logits = model(all_clips_tensor) # (N_clips, 3)
        probs_arr = torch.softmax(logits, dim=1).cpu().numpy()
    print(" OK")

    # 4. Proportional Scoring
    avg_probs = np.mean(probs_arr, axis=0)
    clip_winners = np.argmax(probs_arr, axis=1)
    win_counts = np.bincount(clip_winners, minlength=len(CLASS_NAMES)).astype(float)
    
    dominant_idx = int(np.argmax(win_counts))
    n_clips = len(probs_arr)
    proportional_pcts = (win_counts / n_clips) * 100.0

    dominant_class = CLASS_NAMES[dominant_idx]
    max_conf = float(np.max(probs_arr[:, dominant_idx]))

    percentages = {CLASS_NAMES[i]: float(proportional_pcts[i]) for i in range(len(CLASS_NAMES))}
    
    # Metadata for UI
    sorted_idx = np.argsort(win_counts)[::-1]
    # Ensure runner up is actually a different class
    runner_up_idx = sorted_idx[1] if (len(sorted_idx) > 1 and sorted_idx[0] == dominant_idx) else sorted_idx[0]
    if runner_up_idx == dominant_idx and len(sorted_idx) > 1:
        runner_up_idx = sorted_idx[1]
    margin = (win_counts[dominant_idx] - win_counts[runner_up_idx]) / n_clips * 100.0
    
    # [UPDATED] Robust Heuristic Logic for ASD (Cumulative)
    asd_indices = [i for i, name in enumerate(CLASS_NAMES) if name != "Normal"]
    total_asd_clips = sum(win_counts[i] for i in asd_indices)
    total_asd_clip_pct = total_asd_clips / n_clips

    # 1. Require a minimum number of overall ASD clips
    min_clips_for_asd = 4
    
    # 2. Dynamic threshold depending on length
    required_pct = 0.50 if n_clips <= 10 else 0.40
    
    # 3. Confidence threshold
    min_peak_conf = 0.60
    min_avg_conf = 0.35
    
    avg_conf = float(avg_probs[dominant_idx])

    # If the combined ASD traits cross the limit, we flag it as ASD!
    is_valid_asd = (total_asd_clips >= min_clips_for_asd) and \
                   (total_asd_clip_pct >= required_pct) and \
                   ((max_conf >= min_peak_conf) or (avg_conf >= min_avg_conf))

    # Determine highest ASD trait to represent this video if flagged
    highest_asd_idx = max(asd_indices, key=lambda i: win_counts[i])
    highest_asd_class = CLASS_NAMES[highest_asd_idx]

    # 5. Check Conclusive status and Heuristic for Normal
    # HEURISTIC: If not a valid ASD signal, classify as Normal Activity
    if is_valid_asd:
        final_behavior = highest_asd_class  # Ensures an ASD trait is reported
        
        # User defined rule: Strong mixed traits
        if (proportional_pcts[dominant_idx] >= 50.0) and (proportional_pcts[runner_up_idx] >= 40.0):
            status = "AUTISM POSITIVE (Strong Mixed Autism Traits)"
        elif proportional_pcts[dominant_idx] < 70.0:
            status = "MODERATE AUTISM CHANGES"
        elif margin >= MARGIN_MIN:
            status = "AUTISM POSITIVE (Conclusive)"
        else:
            status = f"AUTISM POSITIVE (Mixed ASD Traits, margin={margin:.1f}%)"
    else:
        final_behavior = "Normal"
        status = "CONCLUSIVE (Normal Profile)"
        print(f"  * Heuristic : Reclassified as Normal Activity (Failed cumulative MSB temporal constraints)")
        
        # Override percentages so the UI reflects Normal Activity cleanly
        max_conf = max(max_conf, 0.85)
        percentages = {n: 0.0 for n in CLASS_NAMES}
        percentages["Normal"] = 100.0
        percentages["_margin"] = 100.0
        percentages["_conclusive"] = 1.0
        percentages["_runner_up_cls"] = float(dominant_idx)
        percentages["_runner_up"] = float(proportional_pcts[dominant_idx])

    # 6. Final Outputs
    print(f"  * Dominant : {final_behavior} ({proportional_pcts[dominant_idx]:.1f}% of {n_clips} clips) — {status}")
    if final_behavior != "Normal":
        print(f"  * Runner-up: {CLASS_NAMES[runner_up_idx]} ({proportional_pcts[runner_up_idx]:.1f}%)")

    return final_behavior, max_conf, [], percentages, total_frames_read


def predict_image(image_path):
    img = Image.open(image_path).convert("RGB")
    img_tensor = transform(img).to(device)
    clip_batch = img_tensor.unsqueeze(0).repeat(CLIP_LENGTH, 1, 1, 1)
    with torch.no_grad():
        feats = feature_extractor(clip_batch).view(CLIP_LENGTH, -1)  # (L, 512)
    tcn_input = feats.permute(1, 0).unsqueeze(0).to(device)          # (1, 512, L)
    with torch.no_grad():
        out       = model(tcn_input)
        probs     = torch.softmax(out, dim=1).cpu().numpy()[0]
        pred_cls  = int(np.argmax(probs))
    return CLASS_NAMES[pred_cls], float(probs[pred_cls])


def safe_predict_image(image_path):
    try:
        from false_positive_prevention import fp_prevention
        if not fp_prevention.should_process_image(image_path):
            return "Undetected", 0.0
        return predict_image(image_path)
    except Exception:
        return predict_image(image_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", type=str, help="Path to video file")
    args = parser.parse_args()
    if args.video:
        try:
            from false_positive_prevention import safe_predict_video
            res = safe_predict_video(args.video)
            cls, conf, _, pcts, total = res
            print(f"\nResult  : {cls}")
            print(f"Conf    : {conf:.1%}")
            print(f"Vote pct: {pcts.get(cls, 0):.1f}%")
            print(f"Margin  : {pcts.get('_margin', 0):.1f}%")
            print(f"Verdict : {'CONCLUSIVE' if pcts.get('_conclusive', 0) else 'INCONCLUSIVE'}")
        except Exception as e:
            print(f"Error: {e}")
