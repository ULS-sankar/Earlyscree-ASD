import torch
import torch.nn as nn
import argparse
import numpy as np
from utils import data_retrieval
from models.tcn import TCN

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--train_set_path', default='data/i3d_feature/train')
    parser.add_argument('--input_size', type=int, default=512)
    parser.add_argument('--output_size', type=int, default=3)
    parser.add_argument('--hidden_size', type=int, default=256)
    parser.add_argument('--level_size', type=int, default=10)
    parser.add_argument('--k_size', type=int, default=2)
    parser.add_argument('--drop_out', type=float, default=0.3)
    parser.add_argument('--fc_size', type=int, default=256)
    args = parser.parse_args()

    print("Step 1: Reading Features")
    print("=" * 60)

    PATH_train = args.train_set_path

    try:
        train_images, train_labels = data_retrieval.get_feature(PATH_train)
    except:
        print("Please check your feature file path")
        exit()

    print(f'Train features shape: {train_images.shape}')

    print("Step 2: Building Model")
    print("=" * 60)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")

    model = TCN(args.input_size, args.output_size, [args.hidden_size] * args.level_size,
                kernel_size=args.k_size, dropout=args.drop_out, fc_size=args.fc_size).to(device)

    print("Model created successfully")

    print("Step 3: Testing forward pass")
    print("=" * 60)

    # Test with a small batch
    test_input = torch.randn(2, 9, 512).to(device)  # batch_size=2, seq_len=9, features=512
    with torch.no_grad():
        output = model(test_input)
        print(f"Forward pass successful. Output shape: {output.shape}")

    print("Step 4: Testing optimizer")
    print("=" * 60)

    optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
    print("Optimizer created successfully")

    print("All tests passed!")