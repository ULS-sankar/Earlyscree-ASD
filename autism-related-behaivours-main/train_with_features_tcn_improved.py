import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import f1_score, precision_score, recall_score, classification_report, confusion_matrix
from sklearn.utils.class_weight import compute_class_weight
from utils import data_loader, data_retrieval
from models.tcn import TCN
import numpy as np
import argparse

class FeatureAugmentationDataset(Dataset):
    """Dataset with feature-level data augmentation"""
    def __init__(self, features, labels, augment=False):
        self.features = features.copy()
        self.labels = labels.copy()
        self.augment = augment
    
    def __len__(self):
        return len(self.labels)
    
    def __getitem__(self, idx):
        feature = self.features[idx].copy()
        label = self.labels[idx]
        
        # Feature-level augmentation (adding small noise)
        if self.augment:
            noise = np.random.normal(0, 0.02, feature.shape)
            feature = feature + noise
            
            # Random temporal shift
            if np.random.rand() > 0.5:
                shift = np.random.randint(-2, 3)
                if shift > 0:
                    feature = np.roll(feature, shift, axis=1)
                elif shift < 0:
                    feature = np.roll(feature, shift, axis=1)
        
        return torch.from_numpy(feature).float(), torch.tensor(label, dtype=torch.long)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--train_set_path', default='data/i3d_feature/train')
    parser.add_argument('--val_set_path', default="data/i3d_feature/val")
    parser.add_argument('--test_set_path', default="data/i3d_feature/test")
    parser.add_argument('--input_size', type=int, default=512)
    parser.add_argument('--output_size', type=int, default=3)
    parser.add_argument('--hidden_size', type=int, default=256)  # Increased from 128
    parser.add_argument('--level_size', type=int, default=10)
    parser.add_argument('--k_size', type=int, default=2)
    parser.add_argument('--drop_out', type=float, default=0.3)  # Increased from 0.1
    parser.add_argument('--fc_size', type=int, default=256)  # Increased from 128
    parser.add_argument('--batch_size', type=int, default=8)  # Reduced for better gradient updates
    parser.add_argument('--num_epochs', type=int, default=100)  # Restored from 5
    parser.add_argument('--learning_rate', type=float, default=1e-4)  # Increased from 3e-5
    args = parser.parse_args()
    
    # ────────────────────────────────────────────────────────────────
    # 1. Read features
    # ────────────────────────────────────────────────────────────────
    print("Step 1: Reading Features")
    print("=" * 60)
    
    PATH_train = args.train_set_path
    PATH_val = args.val_set_path
    PATH_test = args.test_set_path
    
    try:
        train_images, train_labels = data_retrieval.get_feature(PATH_train)
        val_images, val_labels = data_retrieval.get_feature(PATH_val)
        test_images, test_labels = data_retrieval.get_feature(PATH_test)
    except Exception as e:
        print(f"Error reading features: {e}")
        exit(1)
    
    print(f'Train features shape: {train_images.shape}')
    print(f'Val features shape: {val_images.shape}')
    print(f'Test features shape: {test_images.shape}')
    
    # ────────────────────────────────────────────────────────────────
    # 2. Analyze class distribution
    # ────────────────────────────────────────────────────────────────
    print("\nStep 2: Analyzing Class Distribution")
    print("=" * 60)
    
    unique, counts = np.unique(train_labels, return_counts=True)
    print(f"Training data class distribution:")
    for cls, cnt in zip(unique, counts):
        print(f"  Class {cls}: {cnt} samples ({cnt/len(train_labels)*100:.1f}%)")
    
    # Compute class weights for imbalanced data
    class_weights = compute_class_weight(
        'balanced',
        classes=np.unique(train_labels),
        y=train_labels
    )
    class_weights = torch.from_numpy(class_weights).float()
    print(f"\nClass weights: {class_weights}")
    
    # ────────────────────────────────────────────────────────────────
    # 3. Prepare datasets with augmentation
    # ────────────────────────────────────────────────────────────────
    print("\nStep 3: Preparing Datasets")
    print("=" * 60)
    
    # Prepare validation and test sets
    val_x = torch.from_numpy(val_images).float()
    val_y = torch.tensor(val_labels, dtype=torch.long)
    val_x.transpose_(1, 2)  # (N, L, C) -> (N, C, L)
    
    test_x = torch.from_numpy(test_images).float()
    test_y = torch.tensor(test_labels, dtype=torch.long)
    test_x.transpose_(1, 2)
    
    # Prepare training set with augmentation
    train_dataset = FeatureAugmentationDataset(train_images, train_labels, augment=True)
    train_loader = DataLoader(
        dataset=train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=0
    )
    
    print(f"Training batches per epoch: {len(train_loader)}")
    
    # ────────────────────────────────────────────────────────────────
    # 4. Setup model
    # ────────────────────────────────────────────────────────────────
    print("\nStep 4: Building Model")
    print("=" * 60)
    
    use_cuda = torch.cuda.is_available()
    device = torch.device("cuda" if use_cuda else "cpu")
    print(f"Using device: {device}")
    
    input_size = args.input_size
    output_size = args.output_size
    k_size = args.k_size
    hidden_size = args.hidden_size
    level_size = args.level_size
    num_chans = [hidden_size] * (level_size - 1) + [input_size]
    dropout = args.drop_out
    fc_size = args.fc_size
    
    model = TCN(input_size, output_size, num_chans, k_size, dropout, fc_size)
    model.to(device)
    print(f"Model: TCN")
    print(f"  Input size: {input_size}, Output size: {output_size}")
    print(f"  Hidden size: {hidden_size}, FC size: {fc_size}")
    print(f"  Dropout: {dropout}, Kernel size: {k_size}")
    
    # ────────────────────────────────────────────────────────────────
    # 5. Setup optimizer and loss with improvements
    # ────────────────────────────────────────────────────────────────
    print("\nStep 5: Setting Up Training")
    print("=" * 60)
    
    optimizer = torch.optim.Adam(model.parameters(), lr=args.learning_rate)
    loss_fn = nn.CrossEntropyLoss(weight=class_weights.to(device), label_smoothing=0.1)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=50, gamma=0.5)
    
    print(f"Optimizer: Adam (lr={args.learning_rate})")
    print(f"Loss: CrossEntropyLoss with class weights & label smoothing")
    print(f"Learning rate scheduler: StepLR (every 50 epochs, gamma=0.5)")
    
    # ────────────────────────────────────────────────────────────────
    # 6. Training loop with early stopping
    # ────────────────────────────────────────────────────────────────
    print("\nStep 6: Training Model")
    print("=" * 60)
    
    max_val_f1 = 0
    best_epoch = 0
    patience_counter = 0
    max_patience = 20
    PATH = "model_zoo/your_model_zoo/tcn_improved.pkl"
    
    train_losses = []
    val_losses = []
    train_f1_scores = []
    val_f1_scores = []
    
    for epoch in range(args.num_epochs):
        # ──────── Training ────────
        model.train()
        train_loss = 0.0
        train_preds = []
        train_trues = []
        
        for batch_idx, (x, y) in enumerate(train_loader):
            x = x.to(device)
            x = x.transpose(1, 2)  # (N, C, L)
            y = y.to(device)
            
            # Forward pass
            outputs = model(x)
            loss = loss_fn(outputs, y)
            
            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)  # Gradient clipping
            optimizer.step()
            
            train_loss += loss.item()
            train_preds.extend(torch.argmax(outputs, dim=1).cpu().numpy())
            train_trues.extend(y.cpu().numpy())
        
        train_loss /= len(train_loader)
        train_f1 = f1_score(train_trues, train_preds, average='weighted', zero_division=0)
        
        # ──────── Validation ────────
        model.eval()
        val_loss = 0.0
        val_preds = []
        val_trues = []
        
        with torch.no_grad():
            val_x_device = val_x.to(device)
            val_y_device = val_y.to(device)
            val_outputs = model(val_x_device)
            val_loss = loss_fn(val_outputs, val_y_device).item()
            
            val_preds = torch.argmax(val_outputs, dim=1).cpu().numpy()
            val_trues = val_y.cpu().numpy()
        
        val_f1 = f1_score(val_trues, val_preds, average='weighted', zero_division=0)
        
        # ──────── Logging ────────
        train_losses.append(train_loss)
        val_losses.append(val_loss)
        train_f1_scores.append(train_f1)
        val_f1_scores.append(val_f1)
        
        if (epoch + 1) % 10 == 0 or epoch == 0:
            print(f"Epoch {epoch+1:3d}/{args.num_epochs} | "
                  f"Train Loss: {train_loss:.4f} | Train F1: {train_f1:.4f} | "
                  f"Val Loss: {val_loss:.4f} | Val F1: {val_f1:.4f}")
        
        # ──────── Model saving & early stopping ────────
        if val_f1 > max_val_f1:
            max_val_f1 = val_f1
            best_epoch = epoch
            patience_counter = 0
            torch.save(model.state_dict(), PATH)
            print(f"  ✓ New best model saved! (Val F1: {val_f1:.4f})")
        else:
            patience_counter += 1
        
        # Learning rate scheduling (every 50 epochs)
        if epoch > 0 and epoch % 50 == 0:
            scheduler.step()
            new_lr = optimizer.param_groups[0]['lr']
            print(f"  📉 Learning rate reduced to: {new_lr:.6f}")
        
        # Early stopping
        if patience_counter >= max_patience:
            print(f"\nEarly stopping at epoch {epoch+1} (patience={max_patience} exceeded)")
            print(f"Best model from epoch {best_epoch+1} with Val F1: {max_val_f1:.4f}")
            break
    
    # ────────────────────────────────────────────────────────────────
    # 7. Test evaluation
    # ────────────────────────────────────────────────────────────────
    print("\nStep 7: Test Evaluation")
    print("=" * 60)
    
    model.load_state_dict(torch.load(PATH, map_location=device))
    model.eval()
    
    with torch.no_grad():
        test_x_device = test_x.to(device)
        test_y_device = test_y.to(device)
        test_outputs = model(test_x_device)
        test_loss = loss_fn(test_outputs, test_y_device).item()
        
        test_preds = torch.argmax(test_outputs, dim=1).cpu().numpy()
        test_trues = test_y.cpu().numpy()
    
    test_f1 = f1_score(test_trues, test_preds, average='weighted', zero_division=0)
    test_precision = precision_score(test_trues, test_preds, average='weighted', zero_division=0)
    test_recall = recall_score(test_trues, test_preds, average='weighted', zero_division=0)
    
    print(f"\nTest Results:")
    print(f"  Loss: {test_loss:.4f}")
    print(f"  F1-Score: {test_f1:.4f}")
    print(f"  Precision: {test_precision:.4f}")
    print(f"  Recall: {test_recall:.4f}")
    
    print(f"\nDetailed Classification Report:")
    print(classification_report(test_trues, test_preds, zero_division=0))
    
    print(f"\nConfusion Matrix:")
    print(confusion_matrix(test_trues, test_preds))
    
    print("\n" + "=" * 60)
    print(f"Training complete! Best model saved to: {PATH}")
    print(f"Best validation F1-Score: {max_val_f1:.4f} (Epoch {best_epoch+1})")