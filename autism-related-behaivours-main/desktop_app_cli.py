#!/usr/bin/env python3
"""
Command Line Interface for Early Screen ASD
This version works without Kivy for testing and analysis
"""
import sys
import os
import argparse
from inference_safe import predict_video_safe, predict_image_safe, CLASS_NAMES

def analyze_video_cli(video_path):
    """Analyze a video file via command line"""
    print(f"Analyzing video: {video_path}")
    print("=" * 60)
    
    result = predict_video_safe(video_path)
    
    print(f"Behavior: {result['behavior'] or 'Not detected'}")
    print(f"Confidence: {result['confidence']:.1%}")
    print(f"Human detected: {'Yes' if result['is_human'] else 'No'}")
    print(f"Motion score: {result['motion_score']:.3f}")
    print(f"Frames analyzed: {result['frames_analyzed']}")
    
    if result['error']:
        print(f"Note: {result['error']}")
    
    print("=" * 60)
    
    return result

def analyze_image_cli(image_path):
    """Analyze a single image via command line"""
    print(f"Analyzing image: {image_path}")
    print("=" * 60)
    
    cls, conf, valid = predict_image_safe(image_path)
    
    print(f"Behavior: {cls}")
    print(f"Confidence: {conf:.1%}")
    print(f"Valid: {'Yes' if valid else 'No (low confidence)'}")
    
    print("=" * 60)
    
    return cls, conf, valid

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Early Screen ASD - Command Line Analysis")
    parser.add_argument("--video", type=str, help="Path to video file")
    parser.add_argument("--image", type=str, help="Path to image file")
    parser.add_argument("--list-behaviors", action="store_true", help="List available behaviors")
    
    args = parser.parse_args()
    
    if args.list_behaviors:
        print("Available behaviors:")
        for i, behavior in enumerate(CLASS_NAMES):
            print(f"  {i+1}. {behavior}")
        return
    
    if args.video:
        if not os.path.exists(args.video):
            print(f"Error: Video file not found: {args.video}")
            return
        
        result = analyze_video_cli(args.video)
        
        if result['behavior']:
            print(f"\n✅ AUTISM-RELATED BEHAVIOR DETECTED: {result['behavior']}")
            print(f"   Confidence: {result['confidence']:.1%}")
        else:
            print(f"\n✅ NO AUTISM-RELATED BEHAVIORS DETECTED")
            if result['error']:
                print(f"   Note: {result['error']}")
    
    elif args.image:
        if not os.path.exists(args.image):
            print(f"Error: Image file not found: {args.image}")
            return
        
        cls, conf, valid = analyze_image_cli(args.image)
        
        if valid and cls != "Unconfident":
            print(f"\n✅ BEHAVIOR DETECTED: {cls}")
            print(f"   Confidence: {conf:.1%}")
        else:
            print(f"\n✅ NO BEHAVIOR DETECTED (or low confidence)")
    
    else:
        print("Early Screen ASD - Command Line Analysis")
        print("Usage:")
        print("  python desktop_app_cli.py --video <path>    # Analyze video")
        print("  python desktop_app_cli.py --image <path>    # Analyze image")
        print("  python desktop_app_cli.py --list-behaviors  # List behaviors")
        print()
        print("Examples:")
        print("  python desktop_app_cli.py --video videos/v_ArmFlapping_01.mp4")
        print("  python desktop_app_cli.py --image data/command.png")

if __name__ == "__main__":
    main()