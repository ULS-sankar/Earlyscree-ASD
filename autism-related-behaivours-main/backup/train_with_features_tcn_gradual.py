import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import f1_score, precision_score, recall_score, classification_report, confusion_matrix
from sklearn.utils.class_weight import compute_class_weight
from utils import data_loader, data_retrieval
from models.tcn import TCN
import numpy as np
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--train_set_path', default='data/i3d_feature/train')
    parser.add_argument('--val_set_path', default="data/i3d_feature/val")
    parser.add_argument('--test_set_path', default="data/i3d_feature/test")
    parser.add_argument('--input_size', type=int, default=512)
    parser.add_argument('--output_size', type=int, default=3)
    parser.add_argument('--num_chans', type=int, default=256)
    parser.add_argument('--k_size', type=int, default=2)
    parser.add_argument('--drop_out', type=float, default=0.1)
    parser.add_argument('--fc_size', type=int, default=128)
    parser.add_argument('--batch_size', type=int, default=16)
    parser.add_argument('--num_epochs', type=int, default=5)  # Reduced for testing
    args = parser.parse_args()

    PATH_train = args.train_set_path
    PATH_val = args.val_set_path
    PATH_test = args.test_set_path

    input_size = args.input_size
    output_size = args.output_size
    num_chans = [args.num_chans] * 10
    k_size = args.k_size
    dropout = args.drop_out
    fc_size = args.fc_size
    batch_size = args.batch_size
    num_epochs = args.num_epochs
    learning_rate = 3 * 1e-5

    print("0. Begin to read features")
    try:
        train_images, train_labels = data_retrieval.get_feature(PATH_train)
        val_images, val_labels = data_retrieval.get_feature(PATH_val)
        test_images, test_labels = data_retrieval.get_feature(PATH_test)
    except:
        print("Please check your feature file path")

    print(f'0. received train image size: {train_images.shape}')
    print(f'0. received val image size: {val_images.shape}')
    print(f'0. received test image size: {test_images.shape}')

    # ────────────────────────────────────────────────────────────────
    # IMPROVEMENT 1: Class weights for imbalanced data
    # ────────────────────────────────────────────────────────────────
    print("\nAnalyzing class distribution...")
    unique_labels, counts = np.unique(train_labels, return_counts=True)
    class_weights = compute_class_weight('balanced', classes=unique_labels, y=train_labels)
    class_weights = torch.tensor(class_weights, dtype=torch.float)

    print(f"Training data class distribution:")
    for i, (label, count) in enumerate(zip(unique_labels, counts)):
        print(f"  Class {label}: {count} samples ({count/len(train_labels)*100:.1f}%)")
    print(f"Class weights: {class_weights}")

    val_x = torch.from_numpy(val_images).float()
    val_y = torch.tensor(val_labels, dtype=torch.float).long()
    val_x.transpose_(2, 1)

    test_x = torch.from_numpy(test_images).float()
    test_y = torch.tensor(test_labels, dtype=torch.float).long()
    test_x.transpose_(2, 1)

    train_dataset = data_loader.NumpyDataset(train_images, train_labels)
    train_loader = torch.utils.data.DataLoader(dataset=train_dataset, batch_size=batch_size, shuffle=True)
    print("0. Finished dataset preparation")

    use_cuda = torch.cuda.is_available()
    device = torch.device("cuda" if use_cuda else "cpu")
    model = TCN(input_size, output_size, num_chans, k_size, dropout, fc_size)
    print("1. Model TCN loaded")

    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    # ────────────────────────────────────────────────────────────────
    # IMPROVEMENT 2: Use class weights in loss function
    # ────────────────────────────────────────────────────────────────
    loss_f = torch.nn.CrossEntropyLoss(weight=class_weights.to(device))

    print("2. Start training")
    model.to(device)
    model.train()
    n_total_steps = len(train_loader)
    PATH = "model_zoo/your_model_zoo/tcn_improved.pkl"
    max_val_f1_score = None
    train_loss = []
    val_loss = []
    f1_score_ = []
    train_f1_score_ = []

    for epoch in range(num_epochs):
        train_l = 0
        val_l = 0
        f1_ = 0
        train_f1 = 0
        for i, (x, y) in enumerate(train_loader):
            # forward
            train_set = x.to(device)
            train_set.transpose_(2, 1)
            ground_truth = y.to(device)
            outputs = model(train_set)
            print(outputs.shape)
            loss = loss_f(outputs, ground_truth)

            optimizer.zero_grad()

            # backtrack
            loss.backward()
            optimizer.step()

            train_l += loss.item()

            # Calculate training F1 score
            _, predicted = torch.max(outputs.data, 1)
            train_f1 += f1_score(ground_truth.cpu(), predicted.cpu(), average='macro')

        # Validation
        model.eval()
        with torch.no_grad():
            val_outputs = model(val_x.to(device))
            val_loss_epoch = loss_f(val_outputs, val_y.to(device))
            val_l = val_loss_epoch.item()

            _, predicted = torch.max(val_outputs.data, 1)
            f1_ = f1_score(val_y.cpu(), predicted.cpu(), average='macro')

        model.train()

        train_loss.append(train_l / n_total_steps)
        val_loss.append(val_l)
        f1_score_.append(f1_)
        train_f1_score_.append(train_f1 / n_total_steps)

        print(f' epoch {epoch+1}/{num_epochs}, step {i+1}/{n_total_steps}, train loss {train_l/n_total_steps:.4f}, val loss {val_l:.4f}, val f1-score {f1_:.4f}')

        if max_val_f1_score is None or f1_ > max_val_f1_score:
            max_val_f1_score = f1_
            torch.save(model.state_dict(), PATH)
            print(f"  -> Saved best model with F1: {f1_:.4f}")

    print("\n3. Training completed!")
    print(f"Best validation F1-score: {max_val_f1_score:.4f}")

    # ────────────────────────────────────────────────────────────────
    # IMPROVEMENT 3: Comprehensive evaluation on test set
    # ────────────────────────────────────────────────────────────────
    print("\n4. Final evaluation on test set")
    model.load_state_dict(torch.load(PATH))
    model.eval()

    with torch.no_grad():
        test_outputs = model(test_x.to(device))
        _, predicted = torch.max(test_outputs.data, 1)

        test_f1 = f1_score(test_y.cpu(), predicted.cpu(), average='macro')
        test_precision = precision_score(test_y.cpu(), predicted.cpu(), average='macro')
        test_recall = recall_score(test_y.cpu(), predicted.cpu(), average='macro')

        print(f"Test Results:")
        print(f"  F1 Score: {test_f1:.4f}")
        print(f"  Precision: {test_precision:.4f}")
        print(f"  Recall: {test_recall:.4f}")

        print("\nDetailed Classification Report:")
        print(classification_report(test_y.cpu(), predicted.cpu(), target_names=['Armflapping', 'Headbanging', 'Spinning']))

        print("\nConfusion Matrix:")
        cm = confusion_matrix(test_y.cpu(), predicted.cpu())
        print(cm)