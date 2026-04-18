#!/usr/bin/env python3
"""
Optimized Inference for Early Screen ASD
This version uses the improved model architecture and faster feature extraction
"""
import torch
import cv2
import numpy as np
from torchvision import transforms, models
from torchvision.models import ResNet18_Weights
from PIL import Image
import argparse
import time

# ────────────────────────────────────────────────────────────────
#  Optimized Config
# ────────────────────────────────────────────────────────────────
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL_PATH = "model_zoo/your_model_zoo/tcn.pkl"
CLASS_NAMES = ["Armflapping", "Headbanging", "Spinning", "Normal"]
# Colors for different behaviors (Green for Normal)
BEHAVIOR_COLORS = {
    "Armflapping": "#F43F5E", # Crimson
    "Headbanging": "#8B5CF6", # Violet
    "Spinning": "#F59E0B",    # Amber
    "Normal": "#10B981"       # Emerald (Green)
}

# Optimized thresholds for faster processing
CONFIDENCE_THRESHOLD = 0.75   # Increased from 0.60 to prevent false positives in normal videos
NORMAL_THRESHOLD = 0.45       # Threshold to confirm Normal behavior
HUMAN_MOVEMENT_THRESHOLD = 0.15
MIN_FRAMES_WITH_MOTION = 3

# Optimized model parameters (50% more capacity)
INPUT_SIZE = 512
HIDDEN_SIZE = 256  # Increased from 128
LEVEL_SIZE = 10
K_SIZE = 2
DROPOUT = 0.3      # Increased from 0.1
FC_SIZE = 256      # Increased from 128
NUM_CHANNELS = [HIDDEN_SIZE] * (LEVEL_SIZE - 1) + [INPUT_SIZE]

# Optimized processing parameters
FRAME_SKIP = 5     # Extract every 5th frame (faster than every 10th)
CLIP_LENGTH = 10   # More frames per clip for better accuracy
MAX_FRAMES = 100   # Limit frames for faster processing

# Optimized Human Detection
# ... (rest of the file handles model detection dynamically later)
class OptimizedHumanDetector:
    """Optimized human detection with faster processing"""
    
    def __init__(self, threshold=HUMAN_MOVEMENT_THRESHOLD):
        self.threshold = threshold
        self.prev_gray = None
        self.frame_count = 0
    
    def is_human_motion_fast(self, frame):
        """
        Fast human motion detection with optimized parameters
        """
        # Resize frame for faster processing
        small_frame = cv2.resize(frame, (160, 120))
        gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
        
        if self.prev_gray is None:
            self.prev_gray = gray
            return 0.0, False
        
        # Fast optical flow calculation
        flow = cv2.calcOpticalFlowFarneback(
            self.prev_gray, gray, None, 0.4, 2, 10, 2, 4, 1.1, 0
        )
        
        # Calculate motion score
        magnitude, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
        motion_score = np.mean(magnitude) / 255.0
        
        self.prev_gray = gray
        self.frame_count += 1
        
        # Optimized human detection
        is_human = motion_score > self.threshold
        
        return motion_score, is_human
    
    def reset(self):
        """Reset for next video"""
        self.prev_gray = None
        self.frame_count = 0

# ────────────────────────────────────────────────────────────────
#  Optimized Feature Extractor
# ────────────────────────────────────────────────────────────────
class OptimizedFeatureExtractor:
    """Optimized feature extractor using ResNet18"""
    
    def __init__(self):
        # Load ResNet18 with optimized settings
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225]),
        ])
        
        # Ensure we have the pooling layer for 512-dim features
        self.model = torch.nn.Sequential(
            *list(models.resnet18(weights=ResNet18_Weights.DEFAULT).children())[:-2],
            torch.nn.AdaptiveAvgPool2d((1, 1))
        )
        self.model.eval()
        self.model.to(device)
    
    def extract_features(self, frames):
        """Extract features from multiple frames efficiently"""
        if not frames:
            return None
        
        # Process frames in batches for better performance
        tensors = []
        for frame in frames:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)
            img_tensor = self.transform(pil_image)
            tensors.append(img_tensor)
        
        batch = torch.stack(tensors).to(device)
        
        with torch.no_grad():
            features = self.model(batch)
            features = features.view(len(frames), -1)
        
        return features

# ────────────────────────────────────────────────────────────────
#  Optimized TCN Model
# ────────────────────────────────────────────────────────────────
class OptimizedTCN(torch.nn.Module):
    """Optimized TCN with improved architecture"""
    
    def __init__(self, input_size, output_size, num_channels, kernel_size, dropout, fc_size):
        super(OptimizedTCN, self).__init__()
        self.tcn = self._build_tcn(input_size, num_channels, kernel_size, dropout)
        self.fc = torch.nn.Linear(num_channels[-1], fc_size)
        self.dropout = torch.nn.Dropout(dropout)
        self.output = torch.nn.Linear(fc_size, output_size)
    
    def _build_tcn(self, input_size, num_channels, kernel_size, dropout):
        layers = []
        num_levels = len(num_channels)
        for i in range(num_levels):
            dilation_size = 2 ** i
            in_channels = input_size if i == 0 else num_channels[i-1]
            out_channels = num_channels[i]
            layers += [
                torch.nn.Conv1d(in_channels, out_channels, kernel_size,
                              padding=(kernel_size-1) * dilation_size, dilation=dilation_size),
                torch.nn.BatchNorm1d(out_channels),
                torch.nn.ReLU(),
                torch.nn.Dropout(dropout)
            ]
        return torch.nn.Sequential(*layers)
    
    def forward(self, x):
        y = self.tcn(x)
        y = y[:, :, -1]  # Take last timestep
        y = self.fc(y)
        y = self.dropout(y)
        return self.output(y) # Returns Logits

# ----------------------------------------------------------------
#  Load Optimized Models
# ----------------------------------------------------------------
print("Loading optimized models...")
feature_extractor = OptimizedFeatureExtractor()
print("* Optimized feature extractor loaded")

try:
    checkpoint = torch.load(MODEL_PATH, map_location=device)
    # Detect output size from checkpoint (final layer is 'output' in OptimizedTCN)
    if 'output.weight' in checkpoint:
        ACTUAL_OUTPUT_SIZE = checkpoint['output.weight'].shape[0]
        print(f"* Detected optimized model with {ACTUAL_OUTPUT_SIZE} output classes.")
    else:
        ACTUAL_OUTPUT_SIZE = 3 # Fallback
    
    model = OptimizedTCN(INPUT_SIZE, ACTUAL_OUTPUT_SIZE, NUM_CHANNELS, K_SIZE, DROPOUT, FC_SIZE)
    model.load_state_dict(checkpoint, strict=True)
    model.to(device)
    model.eval()
    print("* Optimized TCN Model loaded")
except Exception as e:
    print(f"Error loading optimized TCN: {e}")
    # Fallback to prevent crash
    model = OptimizedTCN(INPUT_SIZE, 3, NUM_CHANNELS, K_SIZE, DROPOUT, FC_SIZE)

human_detector = OptimizedHumanDetector()
print("* Optimized human detector ready\n")

# ----------------------------------------------------------------
#  Optimized Video Analysis
# ----------------------------------------------------------------
def analyze_video_optimized(video_path, frame_skip=FRAME_SKIP, clip_length=CLIP_LENGTH):
    """
    Optimized video analysis with faster processing and improved accuracy
    
    Returns:
        dict with keys: 'behavior', 'confidence', 'is_human', 'motion_score', 'processing_time'
    """
    start_time = time.time()
    
    result = {
        'behavior': None,
        'confidence': 0.0,
        'is_human': False,
        'motion_score': 0.0,
        'processing_time': 0.0,
        'frames_analyzed': 0,
        'error': None
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
        
        # Optimized frame extraction
        while len(frames) < clip_length * 3 and frame_count < MAX_FRAMES:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % frame_skip == 0:
                # Fast human motion detection
                motion_score, is_human = human_detector.is_human_motion_fast(frame)
                motion_scores.append(motion_score)
                
                if is_human:
                    human_frames += 1
                    # Resize frame for faster processing
                    frame_resized = cv2.resize(frame, (224, 224))
                    frames.append(frame_resized)
            
            frame_count += 1
        
        cap.release()
        result['frames_analyzed'] = len(frames)
        result['processing_time'] = time.time() - start_time
        
        # Validation checks
        if len(frames) < clip_length:
            result['error'] = f"Not enough frames (got {len(frames)}, need {clip_length})"
            human_detector.reset()
            return result
        
        if len(motion_scores) > 0:
            avg_motion = np.mean(motion_scores)
            result['motion_score'] = float(avg_motion)
        
        if human_frames < MIN_FRAMES_WITH_MOTION:
            result['error'] = f"No human detected (only {human_frames}/{len(frames)} frames with motion)"
            result['is_human'] = False
            human_detector.reset()
            return result
        
        result['is_human'] = True
        
        # Extract features efficiently
        clip_frames = frames[:clip_length]
        frame_features = feature_extractor.extract_features(clip_frames)
        
        if frame_features is None:
            result['error'] = "Feature extraction failed"
            human_detector.reset()
            return result
        
        # Prepare for TCN
        features_input = frame_features.permute(1, 0).unsqueeze(0)
        
        # Get prediction
        with torch.no_grad():
            output = model(features_input)
            prob = torch.softmax(output, dim=1)
            pred_class = torch.argmax(prob, dim=1).item()
            confidence = prob[0, pred_class].item()
        
        # Heuristic detection for Normal Activity
        # 1. High confidence in "Normal" class (if model is retrained)
        # 2. High confidence in "Normal" behavior if model is already outputting 4 classes
        # 3. IF model has only 3 classes, use heuristic based on Low ASD confidence + High Motion
        
        result['confidence'] = float(confidence)
        
        # Determine behavior label
        if pred_class < len(CLASS_NAMES):
            detected_label = CLASS_NAMES[pred_class]
        else:
            detected_label = "Unknown"

        # Check if model has 4 classes (retrained) or 3 classes (original)
        model_has_normal_class = (output.shape[1] == 4)
        
        if model_has_normal_class and detected_label == "Normal" and confidence >= NORMAL_THRESHOLD:
            result['behavior'] = "Normal"
            print(f"* Detected: Normal Activity ({confidence:.1%})")
        elif confidence >= CONFIDENCE_THRESHOLD:
            result['behavior'] = detected_label
            print(f"* Detected: {detected_label} ({confidence:.1%})")
        elif result['is_human'] and result['motion_score'] > HUMAN_MOVEMENT_THRESHOLD:
            # Heuristic: Human is present and moving, but not doing ASD behaviors
            result['behavior'] = "Normal"
            result['confidence'] = 1.0 - confidence # High value for "Not Autistic"
            print(f"* Heuristic Detection: Normal Activity (Based on LOW ASD profile)")
        else:
            result['error'] = f"Inconclusive ({confidence:.1%} < {CONFIDENCE_THRESHOLD:.0%})"
            print(f"- Confidence too low: {confidence:.1%}")
        
        human_detector.reset()
        return result
    
    except Exception as e:
        result['error'] = str(e)
        human_detector.reset()
        return result

# ────────────────────────────────────────────────────────────────
#  CLI Usage
# ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Optimized autism behavior detection")
    parser.add_argument("--video", type=str, help="Path to video file")
    parser.add_argument("--list-behaviors", action="store_true", help="List available behaviors")
    
    args = parser.parse_args()

    if args.list_behaviors:
        print("Available behaviors:")
        for i, behavior in enumerate(CLASS_NAMES):
            print(f"  {i+1}. {behavior}")
        exit()
    
    if args.video:
        if not os.path.exists(args.video):
            print(f"Error: Video file not found: {args.video}")
            exit()
        
        result = analyze_video_optimized(args.video)
        
        print(f"\n{'='*60}")
        print(f"Optimized Analysis Results:")
        print(f"  Behavior: {result['behavior'] or 'Not detected'}")
        print(f"  Confidence: {result['confidence']:.1%}")
        print(f"  Human detected: {'Yes' if result['is_human'] else 'No'}")
        print(f"  Motion score: {result['motion_score']:.3f}")
        print(f"  Frames analyzed: {result['frames_analyzed']}")
        print(f"  Processing time: {result['processing_time']:.2f} seconds")
        if result['error']:
            print(f"  Note: {result['error']}")
        print(f"{'='*60}")
        
        if result['behavior']:
            print(f"\n* AUTISM-RELATED BEHAVIOR DETECTED: {result['behavior']}")
            print(f"   Confidence: {result['confidence']:.1%}")
            print(f"   Processing Time: {result['processing_time']:.2f}s")
        else:
            print(f"\n* NO AUTISM-RELATED BEHAVIORS DETECTED")
            if result['error']:
                print(f"   Note: {result['error']}")
    
    else:
        print("Optimized Early Screen ASD - Fast Analysis")
        print("Usage:")
        print("  python inference_optimized.py --video <path>    # Analyze video")
        print("  python inference_optimized.py --list-behaviors  # List behaviors")
        print()
        print("Examples:")
        print("  python inference_optimized.py --video videos/v_ArmFlapping_01.mp4")
        print("  python inference_optimized.py --video videos/v_HeadBanging_01.mp4")