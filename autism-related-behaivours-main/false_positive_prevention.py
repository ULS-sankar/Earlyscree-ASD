"""
False Positive Prevention System
Prevents detection of non-human videos (screen recordings, animations, etc.)
"""

import cv2
import numpy as np
import os

class FalsePositivePrevention:
    """System to detect and prevent false positives on non-human content"""
    
    def __init__(self):
        """Initialize the false positive prevention system"""
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        
        haarcascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        if os.path.exists(haarcascade_path):
            self.face_cascade = cv2.CascadeClassifier(haarcascade_path)
        else:
            self.face_cascade = None

    def _is_screen_recording(self, frame):
        """Check if the frame is a screen recording or browser window"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape
        
        # 1. Screen recordings often have very low variance in large uniform areas
        std_val = np.std(gray)
        if std_val < 15:
            return True
            
        # 2. Check for text/UI-like patterns using edge detection and line structures
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / (height * width)
        
        # Screen recordings with text/UI elements have high structural edge density
        if edge_density > 0.03:
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25))
            
            horizontal_lines = cv2.morphologyEx(edges, cv2.MORPH_OPEN, horizontal_kernel)
            vertical_lines = cv2.morphologyEx(edges, cv2.MORPH_OPEN, vertical_kernel)
            
            h_density = np.sum(horizontal_lines > 0) / (height * width)
            v_density = np.sum(vertical_lines > 0) / (height * width)
            
            # High orthogonal line density strongly suggests screen/browser content
            if h_density > 0.005 or v_density > 0.005:
                return True
                
            # Extra test: Text-heavy screens have high overall edge density but might not form continuous lines
            if edge_density > 0.08:
                return True
                
        return False

    def _has_human_features(self, frame):
        """Check for human-like features (Face, Body, Skin tone)"""
        # 1. Face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if self.face_cascade is not None:
            faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(30, 30))
            if len(faces) > 0:
                return True
                
        # 2. HOG full-body detection
        h, w = frame.shape[:2]
        # Scale down for faster and more reliable HOG detection
        scale = min(1.0, 400.0 / max(w, 1))
        small_frame = cv2.resize(frame, (int(w * scale), int(h * scale)))
        boxes, _ = self.hog.detectMultiScale(small_frame, winStride=(8,8), padding=(8, 8), scale=1.05)
        if len(boxes) > 0:
            return True
            
        # 3. Fallback: Skin tone detection
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask1 = cv2.inRange(hsv, (0, 20, 70), (20, 255, 255))
        mask2 = cv2.inRange(hsv, (170, 20, 70), (180, 255, 255))
        skin_mask = cv2.bitwise_or(mask1, mask2)
        skin_ratio = np.count_nonzero(skin_mask) / (h * w)
        
        # If we see a significant amount of skin color, might be a human
        if skin_ratio > 0.08:
            return True
            
        return False
        
    def _is_human_content(self, frame):
        """Main method to evaluate a frame"""
        try:
            # Rejection filter goes first
            if self._is_screen_recording(frame):
                return False
                
            # Verification filter goes second
            return self._has_human_features(frame)
        except Exception as e:
            print(f"Error in frame evaluation: {e}")
            return False
    
    def analyze_video_for_human_content(self, video_path, sample_frames=10):
        """Analyze video to determine if it contains human content"""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return False
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames <= 0:
                return False
                
            frame_indices = np.linspace(0, total_frames - 1, sample_frames, dtype=int)
            
            human_detections = 0
            screen_detections = 0
            
            for frame_idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                
                if ret:
                    looks_like_screen = self._is_screen_recording(frame)
                    
                    if looks_like_screen:
                        screen_detections += 1
                    elif self._has_human_features(frame):
                        human_detections += 1
            
            cap.release()
            
            print(f"Human features score:        {human_detections}/{sample_frames} frames")
            print(f"Screen recording structures: {screen_detections}/{sample_frames} frames")
            
            # ── Decision Logic ─────────────────────────────────────────────────
            #
            # PASS  if human detections clearly outnumber screen detections
            #        e.g. 7 human vs 3 screen  → human wins  → process the video
            #
            # REJECT only when:
            #   • Virtually no human evidence (0-1 frames) AND
            #     the majority of frames look like a screen/UI
            #
            # This prevents both false positives (screen recordings wrongly
            # passed) and false negatives (real human videos wrongly rejected).
            # ───────────────────────────────────────────────────────────────────

            # Case 1: humans clearly dominate → always allow
            if human_detections > screen_detections:
                print("ACCEPTED: Human features outnumber screen detections.")
                return True

            # Case 2: zero or very few human hints AND mostly screen → reject
            if human_detections <= 1 and screen_detections >= max(2, sample_frames * 0.4):
                print("REJECTED: Overwhelmingly a screen recording with no human evidence.")
                return False

            # Case 3: tie / borderline → allow if at least 2 human frames found
            if human_detections >= 2:
                print("ACCEPTED: Sufficient human frames detected.")
                return True

            print("REJECTED: Not enough human evidence found.")
            return False
            
        except Exception as e:
            print(f"Error analyzing video: {e}")
            return False
    
    def analyze_image_for_human_content(self, image_path):
        """Analyze image to determine if it contains human content"""
        try:
            frame = cv2.imread(image_path)
            if frame is None:
                return False
            
            return self._is_human_content(frame)
            
        except Exception as e:
            print(f"Error analyzing image: {e}")
            return False
    
    def should_process_video(self, video_path):
        return self.analyze_video_for_human_content(video_path)
    
    def should_process_image(self, image_path):
        return self.analyze_image_for_human_content(image_path)

# Global instance for easy access
fp_prevention = FalsePositivePrevention()

def safe_predict_video(video_path):
    """Safe video prediction with false positive prevention"""
    if not fp_prevention.should_process_video(video_path):
        return "Undetected", 0.0, [], {}, 0
    
    from inference import predict_video
    return predict_video(video_path)

def safe_predict_image(image_path):
    """Safe image prediction with false positive prevention"""
    if not fp_prevention.should_process_image(image_path):
        return "Undetected", 0.0
    
    from inference import predict_image
    return predict_image(image_path)