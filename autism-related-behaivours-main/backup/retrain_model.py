"""
retrain_model.py
────────────────
Full pipeline:
  1. Extract ResNet18 features from every video in videos/
  2. Build train / val / test splits
  3. Retrain the TCN on those features
  4. Save the new model to model_zoo/your_model_zoo/tcn.pkl
     (overwrites the old, poor-quality model)

Run:
  python retrain_model.py
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
# Map filename prefix → class index
PREFIX_MAP   = {"ArmFlapping": 0, "HeadBanging": 1, "Spinning": 2}

CLIP_LENGTH  = 10          # frames per TCN clip
FRAME_SKIP   = 5           # sample every Nth frame from each video
SEED         = 42
TRAIN_RATIO  = 0.70
VAL_RATIO    = 0.15
# test = remaining 15 %

# TCN hyper-params (must match inference.py exactly)
INPUT_SIZE  = 512
OUTPUT_SIZE = 3
HIDDEN_SIZE = 256          # was 128 in old model — gives more capacity
LEVEL_SIZE  = 10
K_SIZE      = 2
DROPOUT     = 0.3
FC_SIZE     = 256

BATCH_SIZE  = 16
NUM_EPOCHS  = 150
LR          = 1e-4
PATIENCE    = 25           # early-stopping epochs without improvement

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Device: {device}")
random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)

# ── Feature extractor (ResNet18, same as inference.py) ───────────────────────
_fe_base = resnet18(weights=ResNet18_Weights.DEFAULT)
feature_extractor = nn.Sequential(
    *list(_fe_base.children())[:-2],
    nn.AdaptiveAvgPool2d((1, 1))
).to(device).eval()

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225]),
])

# ── Step 1: Extract features from every video ────────────────────────────────
def extract_clips_from_video(video_path):
    """Return list of (clip_feature_tensor [512, CLIP_LENGTH]) arrays."""
    cap = cv2.VideoCapture(video_path)
    frames = []
    fc = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if fc % FRAME_SKIP == 0:
            frame = cv2.resize(frame, (224, 224))
            frames.append(frame)
        fc += 1
    cap.release()

    clips = []
    for start in range(0, len(frames) - CLIP_LENGTH + 1, CLIP_LENGTH):
        clip_frames = frames[start:start + CLIP_LENGTH]
        tensors = []
        for f in clip_frames:
            rgb = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
            tensors.append(transform(Image.fromarray(rgb)))
        batch = torch.stack(tensors).to(device)
        with torch.no_grad():
            feats = feature_extractor(batch).view(CLIP_LENGTH, -1)  # (L, 512)
        clips.append(feats.permute(1, 0).cpu().numpy())             # (512, L)
    return clips


def get_label(filename):
    """Return class index from filename, or None if unrecognised."""
    for prefix, idx in PREFIX_MAP.items():
        if prefix.lower() in filename.lower():
            return idx
    return None


print("\n── Step 1: Extracting features from videos ──────────────────────────")
all_videos = glob.glob(os.path.join(VIDEO_DIR, "*.mp4"))
print(f"Found {len(all_videos)} videos in {VIDEO_DIR}/")

X_all, y_all = [], []
per_class = {i: 0 for i in range(OUTPUT_SIZE)}

for vp in sorted(all_videos):
    label = get_label(os.path.basename(vp))
    if label is None:
        print(f"  [SKIP] {os.path.basename(vp)} — no class prefix found")
        continue
    clips = extract_clips_from_video(vp)
    if not clips:
        print(f"  [SKIP] {os.path.basename(vp)} — too short")
        continue
    X_all.extend(clips)
    y_all.extend([label] * len(clips))
    per_class[label] += len(clips)
    print(f"  {os.path.basename(vp):45s}  →  {CLASS_NAMES[label]:12s}  clips: {len(clips)}")

X_all = np.array(X_all, dtype=np.float32)   # (N, 512, 10)
y_all = np.array(y_all, dtype=np.int64)

print(f"\nTotal clips: {len(y_all)}")
for i, name in enumerate(CLASS_NAMES):
    print(f"  {name}: {per_class[i]} clips ({per_class[i]/len(y_all)*100:.1f}%)")

# ── Step 2: Train / Val / Test split ─────────────────────────────────────────
print("\n── Step 2: Splitting dataset ────────────────────────────────────────")

indices = np.arange(len(y_all))
np.random.shuffle(indices)
n = len(indices)
n_train = int(n * TRAIN_RATIO)
n_val   = int(n * VAL_RATIO)

train_idx = indices[:n_train]
val_idx   = indices[n_train:n_train + n_val]
test_idx  = indices[n_train + n_val:]

X_train, y_train = X_all[train_idx], y_all[train_idx]
X_val,   y_val   = X_all[val_idx],   y_all[val_idx]
X_test,  y_test  = X_all[test_idx],  y_all[test_idx]

print(f"  Train: {len(y_train)}  |  Val: {len(y_val)}  |  Test: {len(y_test)}")


class ClipDataset(Dataset):
    def __init__(self, X, y, augment=False):
        self.X = X; self.y = y; self.augment = augment

    def __len__(self):
        return len(self.y)

    def __getitem__(self, idx):
        x = self.X[idx].copy()
        if self.augment:
            x += np.random.normal(0, 0.01, x.shape).astype(np.float32)
            if random.random() > 0.5:
                x = x[:, ::-1].copy()          # reverse temporal order
        return torch.from_numpy(x).float(), torch.tensor(self.y[idx], dtype=torch.long)


train_loader = DataLoader(ClipDataset(X_train, y_train, augment=True),
                          batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
val_x   = torch.from_numpy(X_val).float().to(device)
val_y   = torch.from_numpy(y_val).long().to(device)
test_x  = torch.from_numpy(X_test).float().to(device)
test_y  = torch.from_numpy(y_test).long().to(device)

# ── Step 3: Build model ───────────────────────────────────────────────────────
print("\n── Step 3: Building TCN model ───────────────────────────────────────")
num_chans = [HIDDEN_SIZE] * (LEVEL_SIZE - 1) + [INPUT_SIZE]
model = TCN(INPUT_SIZE, OUTPUT_SIZE, num_chans, K_SIZE, DROPOUT, FC_SIZE).to(device)
print(f"  Parameters: {sum(p.numel() for p in model.parameters()):,}")

# Class-weighted loss to combat imbalance
cw = compute_class_weight("balanced", classes=np.unique(y_train), y=y_train)
loss_fn   = nn.CrossEntropyLoss(weight=torch.tensor(cw, dtype=torch.float).to(device),
                                 label_smoothing=0.05)
optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-4)
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=NUM_EPOCHS)

# ── Step 4: Training loop ─────────────────────────────────────────────────────
print(f"\n── Step 4: Training ({NUM_EPOCHS} epochs max, patience={PATIENCE}) ──")
best_val_f1   = 0.0
patience_cnt  = 0
best_path     = MODEL_OUT

for epoch in range(1, NUM_EPOCHS + 1):
    # --- train ---
    model.train()
    t_loss, t_preds, t_true = 0.0, [], []
    for xb, yb in train_loader:
        xb, yb = xb.to(device), yb.to(device)
        out = model(xb)
        loss = loss_fn(out, yb)
        optimizer.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        t_loss += loss.item()
        t_preds.extend(out.argmax(1).cpu().tolist())
        t_true.extend(yb.cpu().tolist())
    scheduler.step()

    t_f1   = f1_score(t_true, t_preds, average="weighted", zero_division=0)

    # --- validate ---
    model.eval()
    with torch.no_grad():
        v_out  = model(val_x)
        v_loss = loss_fn(v_out, val_y).item()
        v_preds = v_out.argmax(1).cpu().tolist()
        v_true  = val_y.cpu().tolist()
    v_f1 = f1_score(v_true, v_preds, average="weighted", zero_division=0)

    if epoch % 10 == 0 or epoch == 1:
        print(f"  Epoch {epoch:3d}/{NUM_EPOCHS}  "
              f"TrainLoss={t_loss/len(train_loader):.4f}  TrainF1={t_f1:.3f}  "
              f"ValLoss={v_loss:.4f}  ValF1={v_f1:.3f}")

    if v_f1 > best_val_f1:
        best_val_f1 = v_f1
        patience_cnt = 0
        torch.save(model.state_dict(), best_path)
        print(f"    ✓ Best model saved (ValF1={v_f1:.3f})")
    else:
        patience_cnt += 1
        if patience_cnt >= PATIENCE:
            print(f"\nEarly stopping at epoch {epoch}. Best ValF1={best_val_f1:.3f}")
            break

# ── Step 5: Test evaluation ───────────────────────────────────────────────────
print("\n── Step 5: Final Test Evaluation ────────────────────────────────────")
model.load_state_dict(torch.load(best_path, map_location=device))
model.eval()
with torch.no_grad():
    test_out   = model(test_x)
    test_preds = test_out.argmax(1).cpu().numpy()
    test_true  = y_test

print(classification_report(test_true, test_preds,
                             target_names=CLASS_NAMES, zero_division=0))
print(f"\nFinal Test F1: {f1_score(test_true, test_preds, average='weighted', zero_division=0):.4f}")
print(f"\nModel saved to: {best_path}")
print("You can now restart desktop_app.py — it will use the new model automatically.")
