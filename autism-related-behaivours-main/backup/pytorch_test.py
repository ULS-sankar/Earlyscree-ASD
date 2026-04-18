import torch
import torch.nn as nn

print("PyTorch version:", torch.__version__)
print("CUDA available:", torch.cuda.is_available())

# Simple test
x = torch.randn(2, 3)
print("Tensor test:", x)

# Simple model test
model = nn.Linear(3, 2)
output = model(x)
print("Model test successful:", output.shape)

# Optimizer test
optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
loss = nn.MSELoss()
target = torch.randn(2, 2)
loss_val = loss(output, target)
loss_val.backward()
optimizer.step()
print("Optimizer test successful")