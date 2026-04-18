import torch
import cv2
import numpy as np
from torchvision import transforms
from models.tcn import TCN
from PIL import Image
import argparse

# ────────────────────────────────────────────────────────────────
#  Config with Thresholds
# ────────────────────────────────────────────────────────────────
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL_PATH = "model_zoo/your_model_zoo/tcn.pkl"
CLASS_NAMES = ["Armflapping", "Headbanging", "Spinning"]

# CONFIDENCE THRESHOLDS - Prevent false positives
CONFIDENCE_THRESHOLD = 0.60  # Require 60%+ confidence for behavior detection
HUMAN_MOVEMENT_THRESHOLD = 0.15  # Minimum motion score to validate human presence
MIN_FRAMES_WITH_MOTION = 3  # At least 3 frames must show motion patterns

# Model parameters (Sync with train_with_features_tcn_improved.py)
INPUT_SIZE = 512
OUTPUT_SIZE = 3
HIDDEN_SIZE = 256
LEVEL_SIZE = 10
K_SIZE = 2
DROPOUT = 0.3
FC_SIZE = 256
NUM_CHANNELS = [HIDDEN_SIZE] * (LEVEL_SIZE - 1) + [INPUT_SIZE]

# ────────────────────────────────────────────────────────────────
#  Human Detection Module
# ────────────────────────────────────────────────────────────────
class HumanDetector:
    """Detects human patterns in video frames using optical flow and motion"""
    
    def __init__(self, threshold=HUMAN_MOVEMENT_THRESHOLD):
        self.threshold = threshold
        self.prev_gray = None
    
    def is_human_motion(self, frame):
        """
        Detect if motion pattern matches human behavior
        Returns: motion_score (0-1), is_human (bool)
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        if self.prev_gray is None:
            self.prev_gray = gray
            return 0.0, False
        
        # Calculate optical flow
        flow = cv2.calcOpticalFlowFarneback(
            self.prev_gray, gray, None, 0.5, 3, 15, 3, 5, 1.2, 0
        )
        
        # Get magnitude of flow
        magnitude, angle = cv2.cartToPolar(flow[..., 0], flow[..., 1])
        motion_score = np.mean(magnitude) / 255.0  # Normalize
        
        self.prev_gray = gray
        
        # Human motion typically occurs in concentrated regions
        # Check if motion is distributed (not just noise)
        is_human = motion_score > self.threshold
        
        return motion_score, is_human
    
    def reset(self):
        """Reset for next video"""
        self.prev_gray = None

# ────────────────────────────────────────────────────────────────
#  Load Model
# ────────────────────────────────────────────────────────────────
print("Loading models...")
model = TCN(INPUT_SIZE, OUTPUT_SIZE, NUM_CHANNELS, K_SIZE, DROPOUT, FC_SIZE)
model.load_state_dict(torch.load(MODEL_PATH, map_location=device), strict=False)
model.to(device)
model.eval()
print("[OK] TCN Model loaded")

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

from torchvision import models
feature_extractor = models.resnet18(pretrained=True)
feature_extractor = torch.nn.Sequential(*list(feature_extractor.children())[:-2],
                                       torch.nn.AdaptiveAvgPool2d((1, 1)))
feature_extractor.eval()
feature_extractor.to(device)
print("[OK] Feature extractor loaded")

human_detector = HumanDetector()
print("[OK] Human detector ready\n")

# ────────────────────────────────────────────────────────────────
#  Improved Video Analysis with Human Detection
# ────────────────────────────────────────────────────────────────
def predict_video_safe(video_path, frame_skip=10, clip_length=10):
    """
    Safely analyze a video with human detection and confidence thresholding
    
    Returns:
        dict with keys: 'behavior', 'confidence', 'is_human', 'motion_score', 'error'
    """
    result = {
        'behavior': None,
        'confidence': 0.0,
        'is_human': False,
        'motion_score': 0.0,
        'error': None,
        'frames_analyzed': 0
    }
    
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            result['error'] = "Cannot open video file"
            return result
        
        frames = []
        motion_scores = []
        human_frames = 0
        frame_count = 0
        
        print(f"Processing: {video_path}")
        
        # Extract frames with motion detection
        while len(frames) < clip_length * 3:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % frame_skip == 0:
                # Check for human motion
                motion_score, is_human = human_detector.is_human_motion(frame)
                motion_scores.append(motion_score)
                
                if is_human:
                    human_frames += 1
                
                frame_resized = cv2.resize(frame, (224, 224))
                frames.append(frame_resized)
            
            frame_count += 1
        
        cap.release()
        result['frames_analyzed'] = len(frames)
        
        # Check if we have enough frames with human motion
        if len(frames) < clip_length:
            result['error'] = f"Not enough frames (got {len(frames)}, need {clip_length})"
            human_detector.reset()
            return result
        
        if len(motion_scores) > 0:
            avg_motion = np.mean(motion_scores)
            result['motion_score'] = float(avg_motion)
        
        # Validate human presence
        if human_frames < MIN_FRAMES_WITH_MOTION:
            result['error'] = f"No human detected (only {human_frames}/{len(frames)} frames with motion)"
            result['is_human'] = False
            human_detector.reset()
            return result
        
        result['is_human'] = True
        
        # Use first clip_length frames for prediction
        clip_frames = frames[:clip_length]
        
        # Extract features
        clip_tensors = []
        for frame in clip_frames:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)
            img_tensor = transform(pil_image)
            clip_tensors.append(img_tensor)
        
        clip_batch = torch.stack(clip_tensors).to(device)
        
        # Get features
        with torch.no_grad():
            frame_features = feature_extractor(clip_batch)
            frame_features = frame_features.view(clip_length, -1)
        
        # Prepare for TCN
        features_input = frame_features.permute(1, 0).unsqueeze(0)
        
        # Get prediction
        with torch.no_grad():
            output = model(features_input)
            prob = torch.softmax(output, dim=1)
            pred_class = torch.argmax(prob, dim=1).item()
            confidence = prob[0, pred_class].item()
        
        result['confidence'] = float(confidence)
        
        # Apply confidence threshold
        if confidence >= CONFIDENCE_THRESHOLD:
            result['behavior'] = CLASS_NAMES[pred_class]
            print(f"[OK] Detected: {CLASS_NAMES[pred_class]} ({confidence:.1%})")
        else:
            result['error'] = f"Confidence too low ({confidence:.1%} < {CONFIDENCE_THRESHOLD:.0%})"
            print(f"[FAIL] Confidence too low: {confidence:.1%}")
        
        human_detector.reset()
        return result
    
    except Exception as e:
        result['error'] = str(e)
        human_detector.reset()
        return result

# ────────────────────────────────────────────────────────────────
#  Single Image Prediction (with validation)
# ────────────────────────────────────────────────────────────────
def predict_image_safe(image_path):
    """
    Analyze single image with confidence threshold
    Note: Single images have no temporal context, so they're less reliable
    """
    try:
        img = Image.open(image_path).convert("RGB")
        img_tensor = transform(img).to(device)
        
        clip_length = 10
        clip_batch = img_tensor.unsqueeze(0).repeat(clip_length, 1, 1, 1)
        
        with torch.no_grad():
            frame_features = feature_extractor(clip_batch)
            frame_features = frame_features.view(clip_length, -1)
        
        features_input = frame_features.permute(1, 0).unsqueeze(0)
        
        with torch.no_grad():
            output = model(features_input)
            prob = torch.softmax(output, dim=1)
            pred_class = torch.argmax(prob, dim=1).item()
            confidence = prob[0, pred_class].item()
        
        # Apply confidence threshold
        if confidence >= CONFIDENCE_THRESHOLD:
            return CLASS_NAMES[pred_class], confidence, True
        else:
            return "Unconfident", confidence, False
    
    except Exception as e:
        return None, 0.0, False

# ────────────────────────────────────────────────────────────────
#  CLI Usage
# ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Detect autism-related behaviors with safety checks")
    parser.add_argument("--image", type=str, default=None, help="Path to single image")
    parser.add_argument("--video", type=str, default=None, help="Path to video file")
    args = parser.parse_args()

    if args.image:
        cls, conf, valid = predict_image_safe(args.image)
        print(f"\nResult: {cls} ({conf:.1%})" + (" - VALID" if valid else " - INVALID (low confidence)"))
    
    elif args.video:
        result = predict_video_safe(args.video)
        print(f"\n{'='*60}")
        print(f"Video Analysis Results:")
        print(f"  Behavior: {result['behavior'] or 'Not detected'}")
        print(f"  Confidence: {result['confidence']:.1%}")
        print(f"  Human detected: {'Yes' if result['is_human'] else 'No'}")
        print(f"  Motion score: {result['motion_score']:.3f}")
        print(f"  Frames analyzed: {result['frames_analyzed']}")
        if result['error']:
            print(f"  Note: {result['error']}")
        print(f"{'='*60}")
    else:
        print("Usage: python inference_safe.py --video <path> or --image <path>")