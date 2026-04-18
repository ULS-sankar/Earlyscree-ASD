import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
import torch
import cv2
from models.tcn import TCN
from torchvision import transforms
from PIL import Image
from torchvision.models import resnet18, ResNet18_Weights
import glob

device = torch.device('cpu')
CLASS_NAMES = ['Armflapping', 'Headbanging', 'Spinning']
INPUT_SIZE=512; OUTPUT_SIZE=3; HIDDEN_SIZE=256; LEVEL_SIZE=10; K_SIZE=2; DROPOUT=0.3; FC_SIZE=256
NUM_CHANNELS = [HIDDEN_SIZE]*(LEVEL_SIZE-1)+[INPUT_SIZE]

model = TCN(INPUT_SIZE, OUTPUT_SIZE, NUM_CHANNELS, K_SIZE, DROPOUT, FC_SIZE)
model.load_state_dict(torch.load('model_zoo/your_model_zoo/tcn.pkl', map_location=device), strict=False)
model.eval()

fe = resnet18(weights=ResNet18_Weights.DEFAULT)
fe = torch.nn.Sequential(*list(fe.children())[:-2], torch.nn.AdaptiveAvgPool2d((1,1)))
fe.eval()

transform = transforms.Compose([
    transforms.Resize((224,224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])
])

videos = glob.glob('**/*.mp4', recursive=True)[:5]
print(f"Found {len(videos)} videos to test\n")

for vp in videos:
    cap = cv2.VideoCapture(vp)
    frames = []
    fc = 0
    while len(frames) < 10:
        ret, frame = cap.read()
        if not ret: break
        if fc % 10 == 0:
            frame = cv2.resize(frame, (224,224))
            frames.append(frame)
        fc += 1
    cap.release()
    if len(frames) < 10:
        print(f"{vp}: Not enough frames")
        continue

    clip = []
    for f in frames[:10]:
        r = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
        clip.append(transform(Image.fromarray(r)))
    batch = torch.stack(clip)

    with torch.no_grad():
        ff = fe(batch).view(10, -1)
        inp = ff.permute(1,0).unsqueeze(0)
        out = model(inp)
        probs = out[0]
        winner = CLASS_NAMES[probs.argmax().item()]
        print(f"Video: {os.path.basename(vp)}")
        for i, name in enumerate(CLASS_NAMES):
            print(f"  {name}: {probs[i].item():.4f} ({probs[i].item()*100:.1f}%)")
        print(f"  -> Winner: {winner}\n")
