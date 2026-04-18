"""
fine_tune_full_model.py
────────────────────────
Advanced training pipeline that unfreezes the ResNet feature extractor 
and trains it jointly with the TCN. This is much slower but achieves 
maximum accuracy for subtle behavioral traits.
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
from torchvision import transforms, models
from torchvision.models import ResNet18_Weights
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import classification_report, f1_score
from models.tcn import TCN

# ── Config ───────────────────────────────────────────────────────────────────
VIDEO_DIR    = "videos"
MODEL_OUT    = "model_zoo/your_model_zoo/tcn_finetuned.pkl"
CLASS_NAMES  = ["Armflapping", "Headbanging", "Spinning"]

ALIASES = {
    0: ["arm", "AF", "hand", "counting", "other"],
    1: ["head", "HB", "throw"],
    2: ["spin", "SP", "wash"]
}

CLIP_LENGTH  = 10
FRAME_SKIP   = 5
STRIDE       = 2           # Dense training for "perfect" accuracy
BATCH_SIZE   = 8           # Smaller batch because we're training ResNet too
NUM_EPOCHS   = 30          # Enough for fine-tuning
LR_RESNET    = 1e-5        # Very low LR for fine-tuning base
LR_TCN       = 1e-4        # Standard LR for temporal layers
SEED         = 42

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Device: {device}")
random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)

# ── Transformation & Augmentation ───────────────────────────────────────────
train_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(10),
    transforms.ColorJitter(brightness=0.1, contrast=0.1),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

val_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

# ── Full Stack Model ─────────────────────────────────────────────────────────
class FullStackModel(nn.Module):
    def __init__(self, tcn_model):
        super(FullStackModel, self).__init__()
        # Load and unfreeze ResNet18
        res = models.resnet18(weights=ResNet18_Weights.DEFAULT)
        self.feature_extractor = nn.Sequential(
            *list(res.children())[:-2],
            nn.AdaptiveAvgPool2d((1, 1))
        )
        self.tcn = tcn_model
        
        # Fine-tune only the last 2 ResNet blocks to save time/memory
        for param in self.feature_extractor.parameters():
            param.requires_grad = False
        
        # Unfreeze layer3 and layer4
        # self.feature_extractor[6] is layer3, [7] is layer4
        for param in self.feature_extractor[6].parameters(): param.requires_grad = True
        for param in self.feature_extractor[7].parameters(): param.requires_grad = True

    def forward(self, x):
        # x: (Batch, CLIP_LENGTH, 3, 224, 224)
        b, l, c, h, w = x.shape
        x = x.view(b * l, c, h, w)
        feats = self.feature_extractor(x).view(b, l, -1) # (B, L, 512)
        feats = feats.permute(0, 2, 1) # (B, 512, L)
        return self.tcn(feats)

# ── Dataset (Raw Frames for Augmentation) ───────────────────────────────────
class VideoClipDataset(Dataset):
    def __init__(self, video_paths, labels, transform=None):
        self.data = []
        # Pre-detect clips but don't load frames yet
        for vp, lab in zip(video_paths, labels):
            cap = cv2.VideoCapture(vp)
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.release()
            
            # Estimate frames after skip
            n_frames = total // FRAME_SKIP
            for start in range(0, n_frames - CLIP_LENGTH + 1, STRIDE):
                self.data.append((vp, start, lab))
        
        self.transform = transform
        print(f"Dataset initialized with {len(self.data)} clips")

    def __len__(self):
        return len(self.data)

    def __getitem__(self, i):
        vp, start_idx, lab = self.data[i]
        cap = cv2.VideoCapture(vp)
        frames = []
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_idx * FRAME_SKIP)
        for _ in range(CLIP_LENGTH):
            ret, frame = cap.read()
            if not ret: break
            # Skip subsequent frames manually to maintain FRAME_SKIP
            for _ in range(FRAME_SKIP - 1): cap.read()
            
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            if self.transform:
                frame = self.transform(Image.fromarray(frame))
            frames.append(frame)
        cap.release()
        
        if len(frames) < CLIP_LENGTH:
            # Pad if needed
            while len(frames) < CLIP_LENGTH: frames.append(frames[-1])
            
        return torch.stack(frames), torch.tensor(lab)

# ── Training Script ────────────────────────────────────────────────────────
def train():
    print("\n-- Step 1: Loading Dataset --------------------------------------")
    all_videos = glob.glob(os.path.join(VIDEO_DIR, "*.mp4"))
    video_paths, labels = [], []
    
    def get_label(filename):
        fname = filename.lower()
        for idx, keywords in ALIASES.items():
            if any(k.lower() in fname for k in keywords): return idx
        return None

    for vp in all_videos:
        lab = get_label(os.path.basename(vp))
        if lab is not None:
            video_paths.append(vp)
            labels.append(lab)

    # Split videos (not clips) to avoid temporal leakage
    indices = list(range(len(video_paths)))
    random.shuffle(indices)
    split = int(0.8 * len(indices))
    train_idx, val_idx = indices[:split], indices[split:]
    
    train_ds = VideoClipDataset([video_paths[i] for i in train_idx], [labels[i] for i in train_idx], train_transform)
    val_ds = VideoClipDataset([video_paths[i] for i in val_idx], [labels[i] for i in val_idx], val_transform)
    
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE)

    # Build Model
    tcn_base = TCN(512, 3, [256]*9 + [512], 2, 0.3, 256)
    model = FullStackModel(tcn_base).to(device)
    
    # Differential Learning Rates
    optimizer = torch.optim.Adam([
        {'params': model.feature_extractor.parameters(), 'lr': LR_RESNET},
        {'params': model.tcn.parameters(), 'lr': LR_TCN}
    ])
    loss_fn = nn.CrossEntropyLoss()

    print("\n-- Step 2: Intensive Fine-Tuning --------------------------------")
    best_f1 = 0
    for epoch in range(1, NUM_EPOCHS + 1):
        model.train()
        train_loss = 0
        for i, (xb, yb) in enumerate(train_loader):
            xb, yb = xb.to(device), yb.to(device)
            out = model(xb)
            loss = loss_fn(out, yb)
            optimizer.zero_grad(); loss.backward(); optimizer.step()
            train_loss += loss.item()
            if i % 10 == 0:
                print(f"  Batch {i}/{len(train_loader)} | Loss: {loss.item():.4f}", flush=True)

        # Validation
        model.eval()
        preds, trues = [], []
        with torch.no_grad():
            for xb, yb in val_loader:
                out = model(xb.to(device))
                preds.extend(out.argmax(1).cpu().tolist())
                trues.extend(yb.tolist())
        
        f1 = f1_score(trues, preds, average='weighted', zero_division=0)
        print(f"Epoch {epoch:2d} | Loss: {train_loss/len(train_loader):.4f} | Val F1: {f1:.4f}", flush=True)
        
        if f1 > best_f1:
            best_f1 = f1
            torch.save(tcn_base.state_dict(), MODEL_OUT) # Save only the TCN for inference.py compat
            print(f"  ⭐ Best Model Saved! Accuracy increased.")

    print(f"\nTraining Complete. Best F1: {best_f1:.4f}")

if __name__ == "__main__":
    train()
