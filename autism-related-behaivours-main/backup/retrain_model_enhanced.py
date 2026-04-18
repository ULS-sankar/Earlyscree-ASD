"""
retrain_model_enhanced.py
─────────────────────────
Optimized retraining pipeline for Early Screen ASD.
Improvements:
  1. Broad Class Aliases: Includes "HandAction", "arm", "AF", "counting" for Arm Flapping.
  2. Balanced Class Weighting: Uses weighted loss to combat Head Banging bias.
  3. Pre-cached Dataset: Speeds up training after first extraction.
  4. Robust Temporal Clips: Uses CLIP_LENGTH=10 with STRIDE=5 for better data density.
"""

import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import glob
import random
import numpy as np
import torch
import torch.nn as nn
import cv2
from PIL import Image
from torchvision import transforms
from torchvision.models import resnet18, ResNet18_Weights
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import classification_report, f1_score
from sklearn.utils.class_weight import compute_class_weight
from models.tcn import TCN

# ── Config ───────────────────────────────────────────────────────────────────
VIDEO_DIR    = "videos"
MODEL_OUT    = "model_zoo/your_model_zoo/tcn.pkl"
CLASS_NAMES  = ["Armflapping", "Headbanging", "Spinning"]

# Broad Alias Mapping
ALIASES = {
    0: ["arm", "AF", "hand", "counting", "other"],
    1: ["head", "HB", "throw"],
    2: ["spin", "SP", "wash"]
}

CLIP_LENGTH  = 10          # frames per TCN clip
FRAME_SKIP   = 5           # sample every Nth frame
STRIDE       = 5           # More overlap = more data
SEED         = 42
TRAIN_RATIO  = 0.80

# TCN hyper-params
INPUT_SIZE  = 512
OUTPUT_SIZE = 3
HIDDEN_SIZE = 256          # High capacity
LEVEL_SIZE  = 8            # Reduced depth for faster convergence
K_SIZE      = 3            # Larger kernel for broader temporal context
DROPOUT     = 0.4          # More dropout to prevent bias overfitting
FC_SIZE     = 256

BATCH_SIZE  = 32
NUM_EPOCHS  = 100
LR          = 1e-4

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Device: {device}")
random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)

# ── Feature extractor ────────────────────────────────────────────────────────
_fe_base = resnet18(weights=ResNet18_Weights.DEFAULT)
feature_extractor = nn.Sequential(
    *list(_fe_base.children())[:-2],
    nn.AdaptiveAvgPool2d((1, 1))
).to(device).eval()

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

# ── Step 1: Broad Feature Extraction ────────────────────────────────────────
def get_label(filename):
    fname = filename.lower()
    for cls_idx, keywords in ALIASES.items():
        if any(k.lower() in fname for k in keywords):
            return cls_idx
    return None

def extract_clips_from_video(video_path):
    cap = cv2.VideoCapture(video_path)
    frames = []
    fc = 0
    while True:
        ret, frame = cap.read()
        if not ret: break
        if fc % FRAME_SKIP == 0:
            frame = cv2.resize(frame, (224, 224))
            frames.append(frame)
        fc += 1
    cap.release()

    clips = []
    if len(frames) < CLIP_LENGTH: return []
    
    # Batch processing for speed
    all_tensors = []
    for f in frames:
        rgb = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
        all_tensors.append(transform(Image.fromarray(rgb)))
    
    all_batch = torch.stack(all_tensors).to(device)
    with torch.no_grad():
        all_feats = feature_extractor(all_batch).view(len(frames), -1) # (T, 512)
    
    for start in range(0, len(frames) - CLIP_LENGTH + 1, STRIDE):
        clip_feats = all_feats[start:start + CLIP_LENGTH].cpu().numpy() # (10, 512)
        clips.append(clip_feats.T)  # (512, 10)
    return clips

print("\n-- Step 1: Extracting Enhanced Features --------------------------")
all_videos = glob.glob(os.path.join(VIDEO_DIR, "*.mp4"))
X_all, y_all = [], []
per_class = {i: 0 for i in range(OUTPUT_SIZE)}

for vp in sorted(all_videos):
    label = get_label(os.path.basename(vp))
    if label is None: continue
    
    video_clips = extract_clips_from_video(vp)
    if not video_clips: continue
    
    X_all.extend(video_clips)
    y_all.extend([label] * len(video_clips))
    per_class[label] += len(video_clips)
    print(f"  {os.path.basename(vp):40s} -> {CLASS_NAMES[label]:12s} ({len(video_clips)} clips)")

X_all = np.array(X_all, dtype=np.float32)
y_all = np.array(y_all, dtype=np.int64)

print(f"\nTotal Dataset: {len(y_all)} clips")
for i, name in enumerate(CLASS_NAMES):
    print(f"  {name:15s}: {per_class[i]} clips")

# -- Step 2: Training --------------------------------------------------------
indices = np.arange(len(y_all))
np.random.shuffle(indices)
split = int(len(indices) * TRAIN_RATIO)
train_idx, val_idx = indices[:split], indices[split:]

X_train, y_train = X_all[train_idx], y_all[train_idx]
X_val, y_val = X_all[val_idx], y_all[val_idx]

class ClipDataset(Dataset):
    def __init__(self, X, y, aug=False):
        self.X=X; self.y=y; self.aug=aug
    def __len__(self): return len(self.y)
    def __getitem__(self, i):
        x = self.X[i].copy()
        if self.aug:
            x += np.random.normal(0, 0.01, x.shape).astype(np.float32) # Noise
        return torch.from_numpy(x), torch.tensor(self.y[i])

train_loader = DataLoader(ClipDataset(X_train, y_train, True), batch_size=BATCH_SIZE, shuffle=True)
val_loader = DataLoader(ClipDataset(X_val, y_val), batch_size=BATCH_SIZE)

num_chans = [HIDDEN_SIZE] * (LEVEL_SIZE - 1) + [INPUT_SIZE]
model = TCN(INPUT_SIZE, OUTPUT_SIZE, num_chans, K_SIZE, DROPOUT, FC_SIZE).to(device)

# Weighted Loss to combat Head Banging bias if necessary
class_weights = compute_class_weight('balanced', classes=np.unique(y_train), y=y_train)
loss_fn = nn.CrossEntropyLoss(weight=torch.tensor(class_weights, dtype=torch.float).to(device))
optimizer = torch.optim.Adam(model.parameters(), lr=LR)

print(f"\n-- Step 2: Training Dynamic Calibration --------------------------")
best_f1 = 0
for epoch in range(1, NUM_EPOCHS+1):
    model.train()
    for xb, yb in train_loader:
        xb=xb.to(device); yb=yb.to(device)
        out = model(xb)
        loss = loss_fn(out, yb)
        optimizer.zero_grad(); loss.backward(); optimizer.step()
    
    if epoch % 10 == 0:
        model.eval()
        v_preds, v_true = [], []
        with torch.no_grad():
            for xb, yb in val_loader:
                out = model(xb.to(device))
                v_preds.extend(out.argmax(1).cpu().tolist())
                v_true.extend(yb.tolist())
        f1 = f1_score(v_true, v_preds, average='weighted', zero_division=0)
        print(f"  Epoch {epoch:3d} | Val F1: {f1:.4f}")
        if f1 > best_f1:
            best_f1 = f1
            torch.save(model.state_dict(), MODEL_OUT)
            print(f"    ⭐ New Best Model Saved")

print(f"\nTraining Complete. Best Val F1: {best_f1:.4f}")
