"""
Feature extraction from videos using pre-trained models.
Extracts frames from videos and generates features suitable for temporal models.
"""

import cv2
import numpy as np
import os
import torch
import torch.nn as nn
from torchvision import models, transforms
from pathlib import Path
import re
from collections import defaultdict

# Configuration
VIDEO_DIR = "videos"
OUTPUT_DIR = "data/i3d_feature"
FRAME_SKIP = 10  # Extract every 10th frame (increased for better temporal coverage)
FRAMES_PER_CLIP = 10  # Number of frames per temporal clip (changed to 10 for processing exactly 10 frames)
FEATURE_DIM = 1024
STRIDE = 3  # Stride between clips (increased overlap for better coverage)

# Class mapping based on video filenames
CLASS_MAP = {
    'armflapping': 0,
    'headbanging': 1,
    'spinning': 2
}

# Train/Val/Test split ratios
TRAIN_RATIO = 0.7
VAL_RATIO = 0.15
TEST_RATIO = 0.15

class FeatureExtractor(nn.Module):
    """Feature extractor using pre-trained ResNet50"""
    def __init__(self):
        super().__init__()
        resnet = models.resnet50(pretrained=True)
        # Remove the final classification layer
        self.features = nn.Sequential(*list(resnet.children())[:-1])
        self.eval()
    
    def forward(self, x):
        with torch.no_grad():
            # x shape: (batch, 3, 224, 224)
            features = self.features(x)  # (batch, 2048, 1, 1)
            features = features.view(features.size(0), -1)  # (batch, 2048)
            return features

def extract_frames_from_video(video_path, frame_skip=2):
    """
    Extract frames from a video file.
    
    Args:
        video_path: Path to video file
        frame_skip: Extract every Nth frame
    
    Returns:
        List of frames (numpy arrays)
    """
    frames = []
    cap = cv2.VideoCapture(video_path)
    
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_count % frame_skip == 0:
            # Resize to 224x224 for ResNet input
            frame = cv2.resize(frame, (224, 224))
            frames.append(frame)
        
        frame_count += 1
    
    cap.release()
    return frames

def frames_to_tensor(frames):
    """
    Convert list of frames to tensor suitable for ResNet input.
    
    Args:
        frames: List of CV2 frames (BGR, uint8)
    
    Returns:
        torch.Tensor of shape (N, 3, 224, 224) with normalized values
    """
    # Initialize transformation (ImageNet normalization)
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                           std=[0.229, 0.224, 0.225])
    ])
    
    tensors = []
    for frame in frames:
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Convert to PIL Image, apply transforms, convert back to tensor
        from PIL import Image
        pil_image = Image.fromarray(frame_rgb)
        tensor = transform(pil_image)
        tensors.append(tensor)
    
    return torch.stack(tensors, dim=0)

def extract_temporal_clips(frames, clip_length=15, stride=3):
    """
    Create overlapping temporal clips from frames.
    
    Args:
        frames: List of frames
        clip_length: Number of frames per clip
        stride: stride between clips
    
    Yields:
        Tuple of (clip_frames, start_idx)
    """
    for start_idx in range(0, len(frames) - clip_length + 1, stride):
        clip = frames[start_idx:start_idx + clip_length]
        if len(clip) == clip_length:
            yield clip, start_idx

def extract_features_from_video(video_path, feature_extractor, device):
    """
    Extract temporal features from a video.
    
    Args:
        video_path: Path to video file
        feature_extractor: PyTorch feature extraction model
        device: torch device
    
    Returns:
        Tuple of (features_array, num_frames_extracted) where features_array is numpy array of shape (num_clips, feature_dim)
        or None if insufficient frames
    """
    # Extract frames
    frames = extract_frames_from_video(video_path, frame_skip=FRAME_SKIP)
    
    if len(frames) < FRAMES_PER_CLIP:
        print(f"Warning: {video_path} has only {len(frames)} frames, skipping")
        return None
    
    all_features = []
    
    # Process temporal clips
    for clip_frames, start_idx in extract_temporal_clips(frames, FRAMES_PER_CLIP, STRIDE):
        # Convert clip to tensor
        clip_tensor = frames_to_tensor(clip_frames).to(device)  # (9, 3, 224, 224)
        
        # Extract features for each frame
        frame_features = feature_extractor(clip_tensor)  # (9, 2048)
        
        # Average pool over temporal dimension to get clip feature
        clip_feature = frame_features.mean(dim=0).cpu().numpy()  # (2048,)
        all_features.append(clip_feature)
    
    if len(all_features) == 0:
        return None
    
    return np.array(all_features), len(frames)  # (num_clips, 2048), num_frames_extracted

def atoi(text):
    return int(text) if text.isdigit() else text

def natural_keys(text):
    """Sort filenames naturally (e.g., 01, 02, ... 10)"""
    return [atoi(c) for c in re.split(r'(\d+)', text)]

def main():
    print("Starting feature extraction from videos...")
    
    # Create output directories
    for split in ['train', 'val', 'test']:
        os.makedirs(os.path.join(OUTPUT_DIR, split), exist_ok=True)
    
    # Initialize feature extractor
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    feature_extractor = FeatureExtractor().to(device)
    print("Feature extractor loaded")
    
    # Collect videos by class
    video_files = sorted(os.listdir(VIDEO_DIR), key=natural_keys)
    videos_by_class = defaultdict(list)
    
    for video_file in video_files:
        if not video_file.endswith('.mp4'):
            continue
        
        # Determine class from filename
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
    
    # For testing, process only first 2 videos per class
    print("\n*** TESTING MODE: Processing only first 2 videos per class ***")
    for class_name in videos_by_class:
        videos_by_class[class_name] = videos_by_class[class_name][:2]
        print(f"  {class_name}: reduced to {len(videos_by_class[class_name])} videos")
    
    # Process videos by class
    all_features = {split: {class_name: [] for class_name in CLASS_MAP} 
                    for split in ['train', 'val', 'test']}
    all_labels = {split: [] for split in ['train', 'val', 'test']}
    
    for class_name, class_id in CLASS_MAP.items():
        videos = videos_by_class[class_name]
        
        if len(videos) == 0:
            continue
        
        print(f"\nProcessing {class_name}...")
        
        # For testing, put all videos in train split
        splits = {
            'train': videos,
            'val': [],
            'test': []
        }
        
        for split_name, split_videos in splits.items():
            if len(split_videos) == 0:
                continue
                
            print(f"  {split_name}: {len(split_videos)} videos")
            
            for video_idx, video_path in enumerate(split_videos):
                print(f"    Processing {os.path.basename(video_path)}... ", end='', flush=True)
                
                try:
                    result = extract_features_from_video(video_path, feature_extractor, device)
                    
                    if result is not None:
                        features, num_frames = result
                        # Store features and labels
                        for feature_vec in features:
                            all_features[split_name][class_name].append(feature_vec)
                            all_labels[split_name].append(class_id)
                        print(f"✓ (Detected {num_frames} frames, {features.shape[0]} clips)")
                    else:
                        print("✗ (insufficient frames)")
                except Exception as e:
                    print(f"✗ ({e})")
    
    # Save features and labels for each split
    print("\nSaving features...")
    for split_name in ['train', 'val', 'test']:
        # Concatenate all features and labels for this split
        feature_list = [np.array(all_features[split_name][class_name]) 
                       for class_name in CLASS_MAP 
                       if len(all_features[split_name][class_name]) > 0]
        
        if not feature_list:
            print(f"Warning: No features found for {split_name} split")
            continue
        
        split_features = np.concatenate(feature_list, axis=0)
        
        if len(split_features) == 0:
            print(f"Warning: No features found for {split_name} split")
            continue
        
        # Reduce feature dimension for easier storage (use PCA or simple reduction)
        # For now, we'll keep the 2048-dim features
        # Or we can average adjacent clips
        
        print(f"{split_name}: {split_features.shape}")
        
        # Save by class
        class_idx = 0
        for class_name in CLASS_MAP:
            class_features = np.array(all_features[split_name][class_name])
            if len(class_features) > 0:
                output_file = os.path.join(OUTPUT_DIR, split_name, 
                                          f"{split_name}_{class_name}.npy")
                np.save(output_file, class_features)
                print(f"  Saved: {output_file} - shape {class_features.shape}")
    
    print("\nFeature extraction complete!")
    print(f"Output directory: {OUTPUT_DIR}")

if __name__ == '__main__':
    main()
