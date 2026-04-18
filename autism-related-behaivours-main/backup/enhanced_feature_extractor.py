"""
Enhanced Feature Extractor for Autism Behavior Recognition
Supports multiple backbone architectures for better feature extraction
"""

import torch
import cv2
import numpy as np
from torchvision import models, transforms
from PIL import Image
import os
import argparse
from pathlib import Path

# Choose feature extractor
EXTRACTORS = {
    'resnet18': lambda: models.resnet18(pretrained=True),
    'resnet50': lambda: models.resnet50(pretrained=True),
    'resnet101': lambda: models.resnet101(pretrained=True),
    'densenet121': lambda: models.densenet121(pretrained=True),
    'densenet169': lambda: models.densenet169(pretrained=True),
    'mobilenet_v3': lambda: models.mobilenet_v3_large(pretrained=True),
}

class FeatureExtractor:
    def __init__(self, model_name='resnet50', device='cuda'):
        """Initialize feature extractor with specified backbone"""
        if model_name not in EXTRACTORS:
            raise ValueError(f"Model {model_name} not supported. Choose from: {list(EXTRACTORS.keys())}")
        
        self.device = device
        self.model_name = model_name
        self.feature_dim = self._get_feature_dim(model_name)
        
        # Load model
        backbone = EXTRACTORS[model_name]()
        self.model = self._create_feature_extractor(backbone)
        self.model.eval()
        self.model.to(device)
        
        # Preprocessing
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225]),
        ])
        
        print(f"✓ Loaded {model_name} feature extractor")
        print(f"  Feature dimension: {self.feature_dim}")
        print(f"  Device: {device}")
    
    def _get_feature_dim(self, model_name):
        """Get output feature dimension for each model"""
        feature_dims = {
            'resnet18': 512,
            'resnet50': 2048,
            'resnet101': 2048,
            'densenet121': 1024,
            'densenet169': 1664,
            'mobilenet_v3': 960,
        }
        return feature_dims.get(model_name, 512)
    
    def _create_feature_extractor(self, model):
        """Create feature extractor from backbone"""
        if 'resnet' in self.model_name:
            # Remove average pooling and FC layer
            return torch.nn.Sequential(
                *list(model.children())[:-2],
                torch.nn.AdaptiveAvgPool2d((1, 1))
            )
        elif 'densenet' in self.model_name:
            features = model.features
            return torch.nn.Sequential(
                features,
                torch.nn.ReLU(inplace=True),
                torch.nn.AdaptiveAvgPool2d((1, 1))
            )
        elif 'mobilenet' in self.model_name:
            return torch.nn.Sequential(
                model.features,
                torch.nn.AdaptiveAvgPool2d((1, 1))
            )
        else:
            return torch.nn.Sequential(*list(model.children())[:-2])
    
    def extract_video_features(self, video_path, frame_skip=10):
        """Extract features from all frames in video"""
        cap = cv2.VideoCapture(video_path)
        features = []
        frame_count = 0
        
        with torch.no_grad():
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_count % frame_skip == 0:
                    # Preprocess frame
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_image = Image.fromarray(frame_rgb)
                    img_tensor = self.transform(pil_image).unsqueeze(0).to(self.device)
                    
                    # Extract features
                    feat = self.model(img_tensor)
                    feat = feat.view(1, -1).cpu().numpy()
                    features.append(feat[0])
                
                frame_count += 1
        
        cap.release()
        return np.array(features) if features else None
    
    def extract_image_features(self, image_path):
        """Extract features from single image"""
        img = Image.open(image_path).convert('RGB')
        img_tensor = self.transform(img).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            feat = self.model(img_tensor)
            feat = feat.view(1, -1).cpu().numpy()
        
        return feat[0]


def extract_features_from_directory(input_dir, output_dir, model_name='resnet50', device='cuda'):
    """Extract features from all videos in directory"""
    extractor = FeatureExtractor(model_name=model_name, device=device)
    
    os.makedirs(output_dir, exist_ok=True)
    
    video_files = list(Path(input_dir).glob('*.mp4')) + list(Path(input_dir).glob('*.avi'))
    
    print(f"\nExtracting features from {len(video_files)} videos...")
    print(f"Input: {input_dir}")
    print(f"Output: {output_dir}")
    
    for idx, video_file in enumerate(video_files):
        print(f"\n[{idx+1}/{len(video_files)}] Processing: {video_file.name}")
        
        try:
            features = extractor.extract_video_features(str(video_file))
            
            if features is not None:
                output_file = os.path.join(
                    output_dir,
                    f"{video_file.stem}_{model_name}.npy"
                )
                np.save(output_file, features)
                print(f"  ✓ Saved: {features.shape} features")
            else:
                print(f"  ✗ Failed to extract features")
        
        except Exception as e:
            print(f"  ✗ Error: {e}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Extract features using different CNN backbones'
    )
    parser.add_argument(
        '--model',
        default='resnet50',
        choices=list(EXTRACTORS.keys()),
        help='Feature extractor model'
    )
    parser.add_argument(
        '--input-dir',
        default='data/videos',
        help='Input directory with videos'
    )
    parser.add_argument(
        '--output-dir',
        default='data/improved_features',
        help='Output directory for features'
    )
    parser.add_argument(
        '--device',
        default='cuda' if torch.cuda.is_available() else 'cpu',
        help='Device to use (cuda/cpu)'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("Enhanced Feature Extractor for Autism Behavior Recognition")
    print("=" * 70)
    
    try:
        extract_features_from_directory(
            input_dir=args.input_dir,
            output_dir=args.output_dir,
            model_name=args.model,
            device=args.device
        )
        print("\n✓ Feature extraction complete!")
    
    except Exception as e:
        print(f"\n✗ Error: {e}")
