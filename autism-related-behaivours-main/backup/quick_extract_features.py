"""
Quick feature extraction from videos - simplified version
"""

import cv2
import numpy as np
import os
import torch
import torch.nn as nn
from torchvision import models, transforms
import re
from collections import defaultdict

# Configuration
VIDEO_DIR = "videos"
OUTPUT_DIR = "data/i3d_feature"
FRAME_SKIP = 5  # Extract every 5th frame (better temporal coverage)
FRAMES_PER_CLIP = 9  # More frames per clip for better temporal modeling
MAX_FRAMES = 100  # Extract up to 100 frames per video
STRIDE = 3  # Overlap clips for more data

# Class mapping
CLASS_MAP = {
    'armflapping': 0,
    'headbanging': 1,
    'spinning': 2
}

class SimpleFeatureExtractor(nn.Module):
    """Simple feature extractor using ResNet18"""
    def __init__(self):
        super().__init__()
        resnet = models.resnet18(pretrained=True)
        self.features = nn.Sequential(*list(resnet.children())[:-2])  # Keep spatial dims
        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        self.eval()

    def forward(self, x):
        with torch.no_grad():
            features = self.features(x)  # (batch, 512, 7, 7)
            features = self.avgpool(features)  # (batch, 512, 1, 1)
            features = features.view(features.size(0), -1)  # (batch, 512)
            return features

def extract_frames_from_video(video_path, max_frames=100):
    """Extract frames from video with better temporal sampling"""
    frames = []
    cap = cv2.VideoCapture(video_path)

    frame_count = 0
    extracted_count = 0

    while extracted_count < max_frames:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % FRAME_SKIP == 0:
            frame = cv2.resize(frame, (224, 224))
            frames.append(frame)
            extracted_count += 1

        frame_count += 1

    cap.release()
    return frames

def create_temporal_clips(frames, clip_length=9, stride=3):
    """Create overlapping temporal clips from frames"""
    clips = []
    for start_idx in range(0, len(frames) - clip_length + 1, stride):
        clip = frames[start_idx:start_idx + clip_length]
        if len(clip) == clip_length:
            clips.append(clip)
    return clips

def frames_to_tensor(frames):
    """Convert frames to tensor"""
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    tensors = []
    for frame in frames:
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        from PIL import Image
        pil_image = Image.fromarray(frame_rgb)
        tensor = transform(pil_image)
        tensors.append(tensor)

    return torch.stack(tensors, dim=0)

def extract_features_from_video(video_path, feature_extractor, device):
    """Extract multiple temporal clips from video"""
    frames = extract_frames_from_video(video_path)

    if len(frames) < FRAMES_PER_CLIP:
        return None

    # Create multiple overlapping clips
    clips = create_temporal_clips(frames, FRAMES_PER_CLIP, STRIDE)

    if len(clips) == 0:
        return None

    all_clip_features = []

    for clip_frames in clips:
        clip_tensor = frames_to_tensor(clip_frames).to(device)
        clip_features = feature_extractor(clip_tensor)  # (9, 512)
        all_clip_features.append(clip_features.numpy())  # (9, 512)

    # Return as (num_clips, 9, 512)
    return np.array(all_clip_features)

def atoi(text):
    return int(text) if text.isdigit() else text

def natural_keys(text):
    return [atoi(c) for c in re.split(r'(\d+)', text)]

def main():
    print("Starting QUICK feature extraction from videos...")

    # Create output directories
    for split in ['train', 'val', 'test']:
        os.makedirs(os.path.join(OUTPUT_DIR, split), exist_ok=True)

    # Initialize feature extractor
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")

    feature_extractor = SimpleFeatureExtractor().to(device)
    print("Feature extractor loaded")

    # Collect videos by class
    video_files = sorted(os.listdir(VIDEO_DIR), key=natural_keys)
    videos_by_class = defaultdict(list)

    for video_file in video_files:
        if not video_file.endswith('.mp4'):
            continue

        found_class = False
        for class_name, class_id in CLASS_MAP.items():
            if class_name in video_file.lower():
                videos_by_class[class_name].append(os.path.join(VIDEO_DIR, video_file))
                found_class = True
                break

        if not found_class:
            print(f"Warning: Could not determine class for {video_file}")

    print(f"\nFound videos:")
    for class_name, videos in videos_by_class.items():
        print(f"  {class_name}: {len(videos)} videos")

    # Process ALL videos (remove the limit)
    print("\n*** PROCESSING ALL VIDEOS ***")
    # Comment out the limiting code:
    # for class_name in videos_by_class:
    #     videos_by_class[class_name] = videos_by_class[class_name][:3]
    #     print(f"  {class_name}: reduced to {len(videos_by_class[class_name])} videos")

    # Process videos
    all_features = {class_name: [] for class_name in CLASS_MAP}
    all_labels = []

    for class_name, class_id in CLASS_MAP.items():
        videos = videos_by_class[class_name]

        if len(videos) == 0:
            continue

        print(f"\nProcessing {class_name}...")

        for video_path in videos:
            print(f"  Processing {os.path.basename(video_path)}... ", end='', flush=True)

            try:
                features = extract_features_from_video(video_path, feature_extractor, device)

                if features is not None:
                    # features is (num_clips, 9, 512), add each clip
                    for clip_features in features:
                        all_features[class_name].append(clip_features)  # Add (9, 512) array
                        all_labels.append(class_id)
                    print(f"✓ ({len(features)} clips)")
                else:
                    print("✗ (insufficient frames)")
            except Exception as e:
                print(f"✗ ({e})")

    # Save features
    print("\nSaving features...")
    for class_name in CLASS_MAP:
        if len(all_features[class_name]) > 0:
            features_array = np.array(all_features[class_name])
            output_file = os.path.join(OUTPUT_DIR, 'train', f'train_{class_name}.npy')
            np.save(output_file, features_array)
            print(f"  Saved: {output_file} - shape {features_array.shape}")

    # Create dummy val and test files (copy train data)
    for class_name in CLASS_MAP:
        train_file = os.path.join(OUTPUT_DIR, 'train', f'train_{class_name}.npy')
        if os.path.exists(train_file):
            features = np.load(train_file)
            # Use subset for val/test
            val_size = max(1, len(features) // 3)
            test_size = max(1, len(features) // 3)

            np.save(os.path.join(OUTPUT_DIR, 'val', f'val_{class_name}.npy'), features[:val_size])
            np.save(os.path.join(OUTPUT_DIR, 'test', f'test_{class_name}.npy'), features[val_size:val_size+test_size])

    print("\nFeature extraction complete!")
    print(f"Output directory: {OUTPUT_DIR}")

if __name__ == '__main__':
    main()