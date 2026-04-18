import torch
from torch.utils.data import Dataset, DataLoader, random_split
from torchvision import datasets, transforms
from sklearn.metrics import f1_score
from models.spatial_temporal_model import efficientnet_tcn
import argparse
import os
import sys

# ────────────────────────────────────────────────────────────────
#  Custom Dataset Wrapper for Temporal Dimension
# ────────────────────────────────────────────────────────────────
class TemporalImageDataset(Dataset):
    """
    Wraps an ImageFolder dataset to create temporal sequences from single images.
    Repeats each image to create a temporal dimension (batch, timesteps, channels, height, width)
    """
    def __init__(self, base_dataset, num_frames=5):
        self.base_dataset = base_dataset
        self.num_frames = num_frames  # Number of times to repeat each image

    def __len__(self):
        return len(self.base_dataset)

    def __getitem__(self, idx):
        img, label = self.base_dataset[idx]
        # img shape: (3, 224, 224)
        # Repeat to create temporal dimension: (num_frames, 3, 224, 224)
        img_temporal = img.unsqueeze(0).repeat(self.num_frames, 1, 1, 1)
        return img_temporal, label


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_root', default='data/images',
                        help='Root folder containing Armflapping / Headbanging / Spinning / Normal subfolders')
    parser.add_argument('--batch_size', type=int, default=16)
    parser.add_argument('--num_epochs', type=int, default=20)
    parser.add_argument('--output_size', type=int, default=4)
    parser.add_argument('--hidden_size', type=int, default=128)
    parser.add_argument('--fc_size', type=int, default=128)
    parser.add_argument('--dropout', type=float, default=0.1)
    parser.add_argument('--k_size', type=int, default=2)
    parser.add_argument('--level_size', type=int, default=10)
    args = parser.parse_args()

    # ────────────────────────────────────────────────────────────────
    #  Data loading with ImageFolder + automatic train/val/test split
    # ────────────────────────────────────────────────────────────────
    print("0. Loading images from class folders...")

    transform = transforms.Compose([
        transforms.RandomHorizontalFlip(p=0.5),  # Augmentation: Random flip
        transforms.ColorJitter(brightness=0.2, contrast=0.2),  # Augmentation: Color variation
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    try:
        full_dataset = datasets.ImageFolder(
            root=args.data_root,
            transform=transform
        )
    except Exception as e:
        print(f"Failed to load ImageFolder from {args.data_root}")
        print("Error:", e)
        print("Expected structure:")
        print("  data/images/")
        print("  ├── Armflapping/")
        print("  ├── Headbanging/")
        print("  ├── Spinning/")
        print("  └── Normal/")
        print("Make sure each subfolder has at least a few .jpg / .png images.")
        sys.exit(1)

    classes = full_dataset.classes
    print(f"Classes detected: {classes}")
    print(f"Found {len(full_dataset)} images in {len(classes)} classes")

    if len(full_dataset) == 0:
        print("No images found at all. Check the folder structure and files.")
        sys.exit(1)

    # Split: 80% train, 10% val, 10% test
    n = len(full_dataset)
    train_size = int(0.8 * n)
    val_size = (n - train_size) // 2
    test_size = n - train_size - val_size

    train_ds, val_ds, test_ds = random_split(full_dataset, [train_size, val_size, test_size])

    # Wrap datasets with TemporalImageDataset to add temporal dimension
    train_ds = TemporalImageDataset(train_ds, num_frames=5)
    val_ds = TemporalImageDataset(val_ds, num_frames=5)
    test_ds = TemporalImageDataset(test_ds, num_frames=5)

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=0)
    val_loader   = DataLoader(val_ds,   batch_size=args.batch_size, shuffle=False, num_workers=0)
    test_loader  = DataLoader(test_ds,  batch_size=args.batch_size, shuffle=False, num_workers=0)

    print(f"Train: {len(train_ds)} | Val: {len(val_ds)} | Test: {len(test_ds)} samples")
    print(f"Input shape per batch: (batch_size, timesteps=5, channels=3, height=224, width=224)")

    # ────────────────────────────────────────────────────────────────
    #  Model & Training
    # ────────────────────────────────────────────────────────────────
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    model = efficientnet_tcn(
        num_classes=args.output_size,
        hidden_size=args.hidden_size,
        fc_size=args.fc_size,
        dropout=args.dropout,
        k_size=args.k_size,
        level_Size=args.level_size
    ).to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=3e-5)
    criterion = torch.nn.CrossEntropyLoss()

    print("1. Model loaded")

    best_val_f1 = -1
    PATH = "model_zoo/your_model_zoo/best_model_images.pkl"

    for epoch in range(args.num_epochs):
        model.train()
        train_loss = 0.0
        train_preds, train_trues = [], []

        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)

            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            train_loss += loss.item() * images.size(0)
            _, preds = torch.max(outputs, 1)
            train_preds.extend(preds.cpu().numpy())
            train_trues.extend(labels.cpu().numpy())

        train_loss /= len(train_ds)
        train_f1 = f1_score(train_trues, train_preds, average='weighted')

        # Validation
        model.eval()
        val_loss = 0.0
        val_preds, val_trues = [], []

        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                loss = criterion(outputs, labels)
                val_loss += loss.item() * images.size(0)
                _, preds = torch.max(outputs, 1)
                val_preds.extend(preds.cpu().numpy())
                val_trues.extend(labels.cpu().numpy())

        val_loss /= len(val_ds)
        val_f1 = f1_score(val_trues, val_preds, average='weighted')

        print(f"Epoch {epoch+1}/{args.num_epochs} | "
              f"Train Loss: {train_loss:.4f} | Train F1: {train_f1:.4f} | "
              f"Val Loss: {val_loss:.4f} | Val F1: {val_f1:.4f}")

        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            torch.save(model.state_dict(), PATH)
            print(f"  → Saved new best model (Val F1 = {val_f1:.4f})")

    # ────────────────────────────────────────────────────────────────
    #  Test Evaluation
    # ────────────────────────────────────────────────────────────────
    model.eval()
    test_loss = 0.0
    test_preds, test_trues = [], []
    with torch.no_grad():
        for images, labels in test_loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            loss = criterion(outputs, labels)
            test_loss += loss.item() * images.size(0)
            _, preds = torch.max(outputs, 1)
            test_preds.extend(preds.cpu().numpy())
            test_trues.extend(labels.cpu().numpy())

    test_loss /= len(test_ds)
    test_f1 = f1_score(test_trues, test_preds, average='weighted')
    print(f"\nFinal Test F1: {test_f1:.4f} | Test Loss: {test_loss:.4f}")
    from sklearn.metrics import classification_report
    print("Classification Report:")
    print(classification_report(test_trues, test_preds, target_names=classes))

    print("Training finished.")
    print(f"Best model saved to: {PATH}")