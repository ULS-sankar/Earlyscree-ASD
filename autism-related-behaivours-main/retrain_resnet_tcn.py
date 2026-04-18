"""
retrain_resnet_tcn.py  -  Fast, resumed, full-pipeline retraining
================================================================
Updates:
  - Caches each video's features in data/features_cache/ as individual .npy files
  - RESUMABLE: if you restart, it skips videos it already has features for
  - CAPS at MAX_CLIPS_PER_VIDEO (default 30)
  - Balanced training (Weighted Loss + Data Augmentation)
  - Saves best model to model_zoo/your_model_zoo/tcn.pkl
"""

import os, sys, glob, random, time
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import numpy as np
import torch
import torch.nn as nn
import cv2
from PIL import Image
from torchvision import transforms
from torchvision.models import resnet18, ResNet18_Weights
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import classification_report, f1_score, confusion_matrix
from sklearn.utils.class_weight import compute_class_weight
from models.tcn import TCN

# --- CONFIG (sync with inference.py) ---
VIDEO_DIR          = "videos"
CACHE_DIR          = "data/features_cache"
MODEL_OUT          = "model_zoo/your_model_zoo/tcn.pkl"
CLASS_NAMES        = ["Armflapping", "Headbanging", "Spinning", "Normal"]
PREFIX_MAP         = {"ArmFlapping": 0, "HandAction": 0, "HeadBanging": 1, "Spinning": 2, "normal": 3}

# TCN parameters (Must match inference.py)
CLIP_LENGTH        = 10
FRAME_SKIP         = 5
STRIDE             = CLIP_LENGTH
MAX_CLIPS_PER_VIDEO = 30 # Set to 30 for speed and balance

INPUT_SIZE, OUTPUT_SIZE = 512, 4 # Updated to 4
HIDDEN_SIZE, FC_SIZE = 256, 256
LEVEL_SIZE, K_SIZE = 10, 2
DROPOUT     = 0.3

# Training loop parameters
BATCH_SIZE, NUM_EPOCHS = 16, 50 # Reduced epochs for faster rebuild
LR, PATIENCE = 5e-4, 15
TRAIN_RATIO, VAL_RATIO = 0.70, 0.15
SEED = 42

random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Device: {device}")

# --- FEATURE EXTRACTOR ---
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

# --- RESUME LOGIC ---
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR, exist_ok=True)

def get_label(path):
    bn = os.path.basename(path).lower()
    for prefix, idx in PREFIX_MAP.items():
        if prefix.lower() in bn: return idx
    return None

def extract_clips(video_path, max_clips=MAX_CLIPS_PER_VIDEO):
    """Returns (N, 512, L) list of numpy arrays."""
    cap = cv2.VideoCapture(video_path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    skip  = FRAME_SKIP if total >= CLIP_LENGTH * FRAME_SKIP else 1
    
    # Auto-adjust skip for very long videos to stay near max_clips
    est_clips = total // (skip * CLIP_LENGTH)
    if est_clips > max_clips:
        skip = max(skip, total // (max_clips * CLIP_LENGTH))

    frames, fc = [], 0
    while True:
        ret, frame = cap.read()
        if not ret: break
        if fc % skip == 0:
            frames.append(cv2.resize(frame, (224, 224)))
        fc += 1
    cap.release()

    clips = []
    for start in range(0, len(frames) - CLIP_LENGTH + 1, STRIDE):
        if len(clips) >= max_clips: break
        clip_frames = frames[start: start + CLIP_LENGTH]
        tensors = [transform(Image.fromarray(cv2.cvtColor(f, cv2.COLOR_BGR2RGB))) for f in clip_frames]
        batch = torch.stack(tensors).to(device)
        with torch.no_grad():
            feats = feature_extractor(batch).view(CLIP_LENGTH, -1) # (L,512)
        clips.append(feats.permute(1, 0).cpu().numpy().astype(np.float32))
    return clips

# --- STEP 1: Feature Extraction with Resuming ---
print("\n" + "="*60)
print("STEP 1 - Feature Extraction (with Resuming)")
print("="*60)

all_videos = sorted(glob.glob(os.path.join(VIDEO_DIR, "**", "*.mp4"), recursive=True))
X_total, y_total = [], []

for vp in all_videos:
    label = get_label(vp)
    if label is None: continue
    
    cache_path = os.path.join(CACHE_DIR, f"{os.path.basename(vp)}.npy")
    if os.path.exists(cache_path):
        clips = np.load(cache_path)
    else:
        t0 = time.time()
        clips = extract_clips(vp)
        if not clips: continue
        clips = np.array(clips)
        np.save(cache_path, clips)
        print(f"  [EXTRACT] {os.path.basename(vp):<40s} -> {len(clips):3d} clips ({time.time()-t0:.1f}s)")
    
    X_total.extend(clips)
    y_total.extend([label] * len(clips))

X_total = np.array(X_total, dtype=np.float32)
y_total = np.array(y_total, dtype=np.int64)
print(f"\nCollected {len(y_total)} total clips (X shape: {X_total.shape})")

# Check distribution
counts = [np.sum(y_total == i) for i in range(OUTPUT_SIZE)]
for i, n in enumerate(CLASS_NAMES):
    print(f"  {n:12s}: {counts[i]:4d} clips ({counts[i]/len(y_total)*100:.1f}%)", flush=True)

# --- STEP 2: Splitting ---
print("\n" + "="*60)
print("STEP 2 - Splitting Dataset")
print("="*60)
indices = np.arange(len(y_total))
random.shuffle(indices)

n_te = int(len(indices) * 0.15)
n_va = int(len(indices) * 0.15)
test_idx = indices[:n_te]
val_idx  = indices[n_te:n_te+n_va]
train_idx = indices[n_te+n_va:]

X_tr, y_tr = X_total[train_idx], y_total[train_idx]
X_va, y_va = X_total[val_idx],   y_total[val_idx]
X_te, y_te = X_total[test_idx],  y_total[test_idx]
print(f"  Train: {len(y_tr)}  |  Val: {len(y_va)}  |  Test: {len(y_te)}")

# --- STEP 3: Dataset loader with Augmentation ---
class SimpleDataset(Dataset):
    def __init__(self, X, y, augment=False):
        self.X, self.y, self.augment = X, y, augment
    def __len__(self): return len(self.y)
    def __getitem__(self, idx):
        x = self.X[idx].copy()
        if self.augment:
            x += np.random.normal(0, 0.02, x.shape).astype(np.float32)
            if random.random() > 0.5: x = x[:, ::-1].copy()
        return torch.from_numpy(x), torch.tensor(self.y[idx])

train_loader = DataLoader(SimpleDataset(X_tr, y_tr, augment=True), batch_size=BATCH_SIZE, shuffle=True)
val_x, val_y = torch.from_numpy(X_va).to(device), torch.from_numpy(y_va).to(device)
test_x, test_y = torch.from_numpy(X_te).to(device), torch.from_numpy(y_te).to(device)

# --- STEP 4: Build Model ---
print("\n" + "="*60)
print("STEP 4 - Building TCN Model")
print("="*60)
model = TCN(INPUT_SIZE, OUTPUT_SIZE, [HIDDEN_SIZE]*9 + [INPUT_SIZE], K_SIZE, DROPOUT, FC_SIZE).to(device)

cw = compute_class_weight("balanced", classes=np.unique(y_tr), y=y_tr)
loss_fn = nn.CrossEntropyLoss(weight=torch.tensor(cw, dtype=torch.float).to(device), label_smoothing=0.1)
optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-4)
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=NUM_EPOCHS)

# --- STEP 5: Train ---
print("\n" + "="*60)
print(f"STEP 5 - Training ({NUM_EPOCHS} epochs max)")
print("="*60)
best_f1, patience_cnt = 0, 0

for epoch in range(1, NUM_EPOCHS + 1):
    model.train()
    for xb, yb in train_loader:
        xb, yb = xb.to(device), yb.to(device)
        out = model(xb)
        loss = loss_fn(out, yb)
        optimizer.zero_grad(); loss.backward(); optimizer.step()
    scheduler.step()
    
    model.eval()
    with torch.no_grad():
        v_out = model(val_x).argmax(1).cpu().numpy()
        v_f1 = f1_score(y_va, v_out, average="weighted", zero_division=0)
    
    if epoch % 5 == 0 or epoch == 1:
        print(f"  Ep {epoch:3d}/{NUM_EPOCHS}  Val_F1={v_f1:.4f}", flush=True)

    if v_f1 > best_f1:
        best_f1, patience_cnt = v_f1, 0
        torch.save(model.state_dict(), MODEL_OUT)
    else:
        patience_cnt += 1
        if patience_cnt >= PATIENCE: 
            print("  [STOP] Early stopping."); break

# --- STEP 6: Eval ---
print("\n" + "="*60)
print("STEP 6 - Test Results")
print("="*60)
model.load_state_dict(torch.load(MODEL_OUT))
model.eval()
with torch.no_grad():
    res = model(test_x).argmax(1).cpu().numpy()
print(classification_report(y_te, res, target_names=CLASS_NAMES))
print(f"Model saved -> {MODEL_OUT}")
