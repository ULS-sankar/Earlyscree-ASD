#!/usr/bin/env python3
"""
Fixed Desktop App for Early Screen ASD
This version handles the model architecture mismatch
"""
import sys
import os
import cv2
import numpy as np
import torch
import torch.nn as nn
from datetime import datetime
import sqlite3
from pathlib import Path
import tempfile
import threading
import time

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the fixed inference module
from inference_safe import predict_video_safe, CLASS_NAMES

# Try to import Kivy components
try:
    from kivy.app import App
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.label import Label
    from kivy.uix.button import Button
    from kivy.uix.filechooser import FileChooserListView
    from kivy.uix.popup import Popup
    from kivy.uix.progressbar import ProgressBar
    from kivy.uix.scrollview import ScrollView
    from kivy.uix.gridlayout import GridLayout
    from kivy.uix.image import Image
    from kivy.clock import mainthread
    from kivy.core.window import Window
    from kivy.metrics import dp
    from kivy.graphics import Color, Rectangle
    KIVY_AVAILABLE = True
except ImportError:
    print("Kivy not available. Please install with: pip install kivy")
    KIVY_AVAILABLE = False
    # Define dummy class to prevent NameError
    class App:
        pass

class AnalysisResult:
    """Store analysis results"""
    def __init__(self, video_path, predictions, confidence, behavior_detected, timestamp):
        self.video_path = video_path
        self.predictions = predictions
        self.confidence = confidence
        self.behavior_detected = behavior_detected
        self.timestamp = timestamp

class AnalysisApp(App):
    def build(self):
        self.title = "Early Screen ASD - Desktop Analysis"
        
        # Set window size
        Window.size = (800, 600)
        
        # Main layout
        main_layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        
        # Header
        header = Label(
            text="Early Screen ASD - Desktop Analysis",
            font_size=24,
            size_hint_y=None,
            height=50,
            color=(0.2, 0.6, 0.8, 1)
        )
        main_layout.add_widget(header)
        
        # File selection
        file_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        
        self.file_label = Label(
            text="No video selected",
            size_hint_x=0.7,
            halign='left',
            valign='middle'
        )
        self.file_label.bind(size=self.file_label.setter('text_size'))
        
        select_btn = Button(
            text="Select Video",
            size_hint_x=0.3,
            background_color=(0.2, 0.6, 0.8, 1)
        )
        select_btn.bind(on_press=self.select_video)
        
        file_layout.add_widget(self.file_label)
        file_layout.add_widget(select_btn)
        main_layout.add_widget(file_layout)
        
        # Analysis button
        self.analyze_btn = Button(
            text="Analyze Video",
            size_hint_y=None,
            height=60,
            background_color=(0.1, 0.8, 0.1, 1),
            disabled=True
        )
        self.analyze_btn.bind(on_press=self.start_analysis)
        main_layout.add_widget(self.analyze_btn)
        
        # Progress bar
        self.progress_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=30)
        self.progress_label = Label(text="Ready", size_hint_x=0.7)
        self.progress_bar = ProgressBar(size_hint_x=0.3, max=100)
        self.progress_layout.add_widget(self.progress_label)
        self.progress_layout.add_widget(self.progress_bar)
        main_layout.add_widget(self.progress_layout)
        
        # Results area
        results_label = Label(
            text="Analysis Results:",
            font_size=18,
            size_hint_y=None,
            height=30,
            color=(0.3, 0.3, 0.3, 1)
        )
        main_layout.add_widget(results_label)
        
        # Results display
        self.results_layout = BoxLayout(orientation='vertical', spacing=10)
        scroll_view = ScrollView()
        scroll_view.add_widget(self.results_layout)
        main_layout.add_widget(scroll_view)
        
        return main_layout
    
    def select_video(self, instance):
        """Open file chooser to select video"""
        content = BoxLayout(orientation='vertical')
        
        filechooser = FileChooserListView(
            path=os.path.expanduser("~"),
            filters=['*.mp4', '*.avi', '*.mov', '*.mkv']
        )
        
        btn_layout = BoxLayout(size_hint_y=None, height=50)
        cancel_btn = Button(text='Cancel', size_hint_x=0.5)
        select_btn = Button(text='Select', size_hint_x=0.5)
        
        btn_layout.add_widget(cancel_btn)
        btn_layout.add_widget(select_btn)
        
        content.add_widget(filechooser)
        content.add_widget(btn_layout)
        
        popup = Popup(title='Select Video File', content=content, size_hint=(0.8, 0.8))
        
        def on_select(instance):
            if filechooser.selection:
                self.selected_video = filechooser.selection[0]
                self.file_label.text = f"Selected: {os.path.basename(self.selected_video)}"
                self.analyze_btn.disabled = False
            popup.dismiss()
        
        def on_cancel(instance):
            popup.dismiss()
        
        select_btn.bind(on_press=on_select)
        cancel_btn.bind(on_press=on_cancel)
        
        popup.open()
    
    def start_analysis(self, instance):
        """Start video analysis in background thread"""
        if not hasattr(self, 'selected_video'):
            self.show_popup("Error", "Please select a video file first")
            return
        
        # Disable UI during analysis
        self.analyze_btn.disabled = True
        self.progress_bar.value = 0
        self.progress_label.text = "Analyzing video..."
        
        # Clear previous results
        self.results_layout.clear_widgets()
        
        # Start analysis in background thread
        analysis_thread = threading.Thread(target=self.run_analysis)
        analysis_thread.daemon = True
        analysis_thread.start()
    
    def run_analysis(self):
        """Run the actual analysis"""
        try:
            # Run analysis
            result = predict_video_safe(self.selected_video)
            predictions = [0.0, 0.0, 0.0]  # Initialize predictions
            confidence = result['confidence']
            behavior_detected = result['behavior'] is not None
            
            # Set predictions based on result
            if result['behavior']:
                behavior_idx = CLASS_NAMES.index(result['behavior'])
                predictions[behavior_idx] = confidence
            
            # Update UI with results
            self.update_results(predictions, confidence, behavior_detected)
            
        except Exception as e:
            self.show_error(str(e))
        finally:
            # Re-enable UI
            self.analyze_btn.disabled = False
            self.progress_bar.value = 100
            self.progress_label.text = "Analysis complete"
    
    @mainthread
    def update_results(self, predictions, confidence, behavior_detected):
        """Update the results display"""
        self.results_layout.clear_widgets()
        
        # Add results
        if behavior_detected:
            result_text = f"⚠️ AUTISM-RELATED BEHAVIOR DETECTED\n\n"
            result_text += f"Behavior: {CLASS_NAMES[np.argmax(predictions)]}\n"
            result_text += f"Confidence: {confidence:.2%}\n"
            result_text += f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            result_label = Label(
                text=result_text,
                font_size=16,
                color=(1, 0, 0, 1),
                halign='center',
                valign='middle'
            )
            result_label.bind(size=result_label.setter('text_size'))
        else:
            result_text = f"✅ NO AUTISM-RELATED BEHAVIORS DETECTED\n\n"
            result_text += f"Confidence: {confidence:.2%}\n"
            result_text += f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            result_label = Label(
                text=result_text,
                font_size=16,
                color=(0, 0.5, 0, 1),
                halign='center',
                valign='middle'
            )
            result_label.bind(size=result_label.setter('text_size'))
        
        self.results_layout.add_widget(result_label)
        
        # Add detailed predictions
        detail_label = Label(
            text="Detailed Analysis:",
            font_size=14,
            color=(0.3, 0.3, 0.3, 1),
            size_hint_y=None,
            height=30
        )
        self.results_layout.add_widget(detail_label)
        
        for i, (class_name, prob) in enumerate(zip(CLASS_NAMES, predictions)):
            detail_text = f"{class_name}: {prob:.2%}"
            detail = Label(
                text=detail_text,
                font_size=14,
                color=(0.2, 0.2, 0.2, 1)
            )
            self.results_layout.add_widget(detail)
    
    @mainthread
    def show_popup(self, title, message):
        """Show a popup message"""
        content = BoxLayout(orientation='vertical', padding=20)
        content.add_widget(Label(text=message))
        
        close_btn = Button(text='Close', size_hint_y=None, height=50)
        content.add_widget(close_btn)
        
        popup = Popup(title=title, content=content, size_hint=(0.6, 0.4))
        close_btn.bind(on_press=popup.dismiss)
        popup.open()
    
    @mainthread
    def show_error(self, error_message):
        """Show error message"""
        self.show_popup("Error", f"Analysis failed: {error_message}")
        self.progress_label.text = "Analysis failed"

def main():
    """Main entry point"""
    if not KIVY_AVAILABLE:
        print("Kivy is not available. Please install it with:")
        print("pip install kivy")
        return
    
    print("Starting Early Screen ASD Desktop App...")
    print("Please ensure you have:")
    print("- A video file to analyze")
    print("- The AI models in the models/ directory")
    print("- All dependencies installed")
    print()
    
    try:
        AnalysisApp().run()
    except Exception as e:
        print(f"Error starting app: {e}")
        print("Make sure all dependencies are installed correctly.")

if __name__ == "__main__":
    main()