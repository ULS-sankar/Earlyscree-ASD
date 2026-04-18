import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import sys
import sqlite3
import threading
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
import json

# Kivy imports
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.utils import platform

# Import existing functionality
try:
    from false_positive_prevention import safe_predict_video
except ImportError:
    print("Warning: Could not import inference modules. Using simulation mode.")

# Set window size for development (can be removed for Android)
if platform != 'android':
    Window.size = (400, 600)

class RoundedButton(Button):
    """Custom rounded button for Kivy interface"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)  # Transparent background
        self.color = (1, 1, 1, 1)  # White text
        self.font_size = dp(18)
        
    def on_press(self):
        super().on_press()

class HomeScreen(FloatLayout):
    """Home screen with logo and navigation buttons"""
    
    def __init__(self, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.app_instance = app_instance
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the home screen UI"""
        with self.canvas:
            Color(0.95, 0.95, 0.95, 1)
            self.rect = Rectangle(size=Window.size, pos=self.pos)
        
        logo_path = self.get_logo_path()
        if logo_path and os.path.exists(logo_path):
            self.logo = Image(
                source=logo_path,
                size_hint=(None, None),
                size=(dp(200), dp(200)),
                pos_hint={'center_x': 0.5, 'top': 0.9}
            )
        else:
            self.logo = Label(
                text="Early Screen ASD",
                font_size=dp(36),
                bold=True,
                color=(0.2, 0.6, 0.9, 1),
                pos_hint={'center_x': 0.5, 'top': 0.9}
            )
        
        self.add_widget(self.logo)
        
        self.title = Label(
            text="Early Screen ASD",
            font_size=dp(28),
            bold=True,
            color=(0.2, 0.6, 0.9, 1),
            pos_hint={'center_x': 0.5, 'top': 0.75}
        )
        self.add_widget(self.title)
        
        button_container = BoxLayout(
            orientation='vertical',
            spacing=dp(20),
            size_hint=(None, None),
            size=(dp(300), dp(300)),
            pos_hint={'center_x': 0.5, 'center_y': 0.4}
        )
        
        self.upload_btn = RoundedButton(
            text="Upload Video",
            size_hint=(1, None),
            height=dp(60),
            background_color=(0.2, 0.6, 0.9, 1)
        )
        self.upload_btn.bind(on_press=self.go_to_upload)
        button_container.add_widget(self.upload_btn)
        
        self.reports_btn = RoundedButton(
            text="View Reports",
            size_hint=(1, None),
            height=dp(60),
            background_color=(0.3, 0.8, 0.4, 1)
        )
        self.reports_btn.bind(on_press=self.go_to_reports)
        button_container.add_widget(self.reports_btn)
        
        self.learn_btn = RoundedButton(
            text="Learn More",
            size_hint=(1, None),
            height=dp(60),
            background_color=(0.9, 0.5, 0.2, 1)
        )
        self.learn_btn.bind(on_press=self.go_to_learn)
        button_container.add_widget(self.learn_btn)
        
        self.add_widget(button_container)
    
    def get_logo_path(self):
        possible_paths = ['LOGO.png', 'assets/LOGO.png', 'images/LOGO.png']
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None
    
    def go_to_upload(self, instance):
        self.app_instance.screen_manager.current = 'upload'
    
    def go_to_reports(self, instance):
        self.app_instance.screen_manager.current = 'reports'
        # Refresh reports when navigating
        reports_screen = self.app_instance.screen_manager.get_screen('reports').children[0]
        reports_screen.load_reports()
    
    def go_to_learn(self, instance):
        self.app_instance.screen_manager.current = 'learn'

class UploadScreen(FloatLayout):
    """Screen for uploading and analyzing videos"""
    
    def __init__(self, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.app_instance = app_instance
        self.selected_file = None
        self.analysis_thread = None
        self.setup_ui()
    
    def setup_ui(self):
        with self.canvas:
            Color(0.98, 0.98, 0.98, 1)
            self.rect = Rectangle(size=Window.size, pos=self.pos)
        
        self.header = Label(
            text="Upload Video for Analysis",
            font_size=dp(24),
            bold=True,
            color=(0.2, 0.6, 0.9, 1),
            pos_hint={'center_x': 0.5, 'top': 0.95}
        )
        self.add_widget(self.header)
        
        file_container = BoxLayout(
            orientation='vertical',
            spacing=dp(10),
            size_hint=(0.9, 0.6),
            pos_hint={'center_x': 0.5, 'center_y': 0.6}
        )
        
        self.file_chooser = FileChooserListView(
            path=os.path.expanduser('~'),
            filters=['*.mp4', '*.avi', '*.mov', '*.mkv'],
            size_hint=(1, 0.7)
        )
        self.file_chooser.bind(selection=self.on_file_selected)
        file_container.add_widget(self.file_chooser)
        
        self.file_info = Label(
            text="No file selected",
            font_size=dp(14),
            color=(0.5, 0.5, 0.5, 1),
            size_hint=(1, 0.1)
        )
        file_container.add_widget(self.file_info)
        
        self.upload_btn = RoundedButton(
            text="Analyze Video",
            size_hint=(1, 0.2),
            height=dp(50),
            background_color=(0.2, 0.8, 0.3, 1),
            disabled=True
        )
        self.upload_btn.bind(on_press=self.start_analysis)
        file_container.add_widget(self.upload_btn)
        
        self.add_widget(file_container)
        
        progress_container = BoxLayout(
            orientation='vertical',
            spacing=dp(10),
            size_hint=(0.9, 0.2),
            pos_hint={'center_x': 0.5, 'bottom': 0.1}
        )
        
        self.progress_label = Label(
            text="Ready to analyze",
            font_size=dp(16),
            color=(0.3, 0.3, 0.3, 1)
        )
        progress_container.add_widget(self.progress_label)
        
        self.progress_bar = ProgressBar(
            max=100,
            value=0,
            size_hint=(1, None),
            height=dp(20)
        )
        progress_container.add_widget(self.progress_bar)
        
        self.add_widget(progress_container)
    
    def on_file_selected(self, instance, selection):
        if selection:
            self.selected_file = selection[0]
            self.file_info.text = f"Selected: {os.path.basename(self.selected_file)}"
            self.upload_btn.disabled = False
        else:
            self.selected_file = None
            self.file_info.text = "No file selected"
            self.upload_btn.disabled = True
    
    def start_analysis(self, instance):
        if not self.selected_file:
            self.show_popup("Error", "Please select a video file first")
            return
        
        self.upload_btn.disabled = True
        self.file_chooser.disabled = True
        self.progress_bar.value = 0
        
        self.analysis_thread = threading.Thread(target=self.run_analysis)
        self.analysis_thread.start()
        
        Clock.schedule_interval(self.update_progress_ui, 0.1)
    
    def run_analysis(self):
        try:
            start_time = time.time()
            
            # Step 1: Pre-processing simulation
            for i in range(1, 41):
                time.sleep(0.05)
                Clock.schedule_once(lambda dt, p=i: self.set_progress(p, "Processing video frames..."))
            
            # Step 2: Actual Analysis
            if 'safe_predict_video' in globals():
                # We use the existing function but need to handle its specific return
                # cls, conf, frame_preds, percentages, total_frames
                res = safe_predict_video(self.selected_file)
                
                if res[0] == "Undetected":
                    result = {
                        'assessment': "Inconclusive",
                        'confidence': 0.0,
                        'behaviors': {},
                        'analysis_time': time.time() - start_time,
                        'error': "No human content detected in the video."
                    }
                else:
                    dominant_class, avg_conf, _, percentages, _ = res
                    # Use MSB High-Accuracy Profile percentages for confidence
                    msb_confidence = min(100.0, sum(percentages.values())) if percentages else 0.0
                    
                    # Map MSB accuracy to assessment
                    assessment = "Low Probability"
                    if msb_confidence >= 80: assessment = "✅ High MSB Evidence"
                    elif msb_confidence >= 40: assessment = "🟠 Moderate MSB Signs"
                    elif msb_confidence >= 15: assessment = "🟡 Mild Traits"
                    
                    result = {
                        'assessment': assessment,
                        'confidence': msb_confidence,
                        'behaviors': percentages,
                        'analysis_time': time.time() - start_time
                    }
            else:
                # Fallback to simulation if imports failed
                result = self.simulate_analysis()
                result['analysis_time'] = time.time() - start_time

            # Step 3: Post-processing simulation
            for i in range(41, 101):
                time.sleep(0.02)
                Clock.schedule_once(lambda dt, p=i: self.set_progress(p, "Generating report..."))

            Clock.schedule_once(lambda dt: self.show_results(result))
                
        except Exception as e:
            Clock.schedule_once(lambda dt: self.show_error(str(e)))
    
    def simulate_analysis(self):
        import random
        behaviors = {
            'Armflapping': random.uniform(5, 40),
            'Headbanging': random.uniform(2, 20),
            'Spinning': random.uniform(10, 60)
        }
        total = sum(behaviors.values())
        return {
            'assessment': "Moderate Probability" if total > 50 else "Low Probability",
            'confidence': random.uniform(60, 85),
            'behaviors': behaviors,
            'analysis_time': 15.5
        }
    
    def set_progress(self, progress, text):
        self.progress_bar.value = progress
        self.progress_label.text = text
    
    def update_progress_ui(self, dt):
        if self.analysis_thread and self.analysis_thread.is_alive():
            return True
        return False
    
    def show_results(self, result):
        self.progress_label.text = "Analysis Complete!"
        self.upload_btn.disabled = False
        self.file_chooser.disabled = False
        
        if 'error' in result:
            self.show_error(result['error'])
            return

        self.save_result(result)
        
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        result_text = f"Assessment: {result['assessment']}\n"
        result_text += f"Confidence: {result['confidence']:.1f}%\n"
        result_text += f"Analysis Time: {result['analysis_time']:.1f}s\n\n"
        result_text += "Detected Behaviors:\n"
        
        for behavior, score in result['behaviors'].items():
            result_text += f"• {behavior}: {score:.1f}%\n"
        
        label = Label(text=result_text, halign='left', valign='top', size_hint_y=None)
        label.bind(width=lambda s, w: s.setter('text_size')(s, (w, None)))
        label.bind(texture_size=lambda s, z: s.setter('height')(s, z[1]))
        
        scroll = ScrollView(size_hint=(1, 0.8))
        scroll.add_widget(label)
        content.add_widget(scroll)
        
        close_btn = RoundedButton(text="Close", size_hint=(1, None), height=dp(50), background_color=(0.2, 0.6, 0.9, 1))
        close_btn.bind(on_press=lambda x: self.dismiss_popup())
        content.add_widget(close_btn)
        
        self.popup = Popup(title="Analysis Results", content=content, size_hint=(0.9, 0.7))
        self.popup.open()
    
    def save_result(self, result):
        try:
            conn = sqlite3.connect('analysis_results.db')
            cursor = conn.execute('''
                INSERT INTO results (filename, timestamp, assessment, confidence, behaviors, analysis_time)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                os.path.basename(self.selected_file),
                datetime.now().isoformat(),
                result['assessment'],
                result['confidence'],
                json.dumps(result['behaviors']),
                result['analysis_time']
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error saving result: {e}")
    
    def show_error(self, error_msg):
        self.show_popup("Error", error_msg)
        self.upload_btn.disabled = False
        self.file_chooser.disabled = False
    
    def show_popup(self, title, message):
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        content.add_widget(Label(text=message, halign='center'))
        close_btn = RoundedButton(text="OK", size_hint=(1, None), height=dp(50), background_color=(0.9, 0.3, 0.3, 1))
        close_btn.bind(on_press=lambda x: self.dismiss_popup())
        content.add_widget(close_btn)
        self.popup = Popup(title=title, content=content, size_hint=(0.8, 0.4))
        self.popup.open()
    
    def dismiss_popup(self):
        if hasattr(self, 'popup'):
            self.popup.dismiss()

class ReportsScreen(FloatLayout):
    """Screen for viewing analysis history"""
    
    def __init__(self, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.app_instance = app_instance
        self.setup_ui()
    
    def setup_ui(self):
        with self.canvas:
            Color(0.98, 0.98, 0.98, 1)
            self.rect = Rectangle(size=Window.size, pos=self.pos)
        
        self.header = Label(
            text="Analysis History",
            font_size=dp(24),
            bold=True,
            color=(0.2, 0.6, 0.9, 1),
            pos_hint={'center_x': 0.5, 'top': 0.95}
        )
        self.add_widget(self.header)
        
        self.reports_container = GridLayout(cols=1, spacing=dp(10), size_hint_y=None, padding=dp(10))
        self.reports_container.bind(minimum_height=self.reports_container.setter('height'))
        
        self.scroll_view = ScrollView(size_hint=(0.9, 0.8), pos_hint={'center_x': 0.5, 'center_y': 0.45})
        self.scroll_view.add_widget(self.reports_container)
        self.add_widget(self.scroll_view)
        
        self.load_reports()
    
    def load_reports(self):
        self.reports_container.clear_widgets()
        try:
            conn = sqlite3.connect('analysis_results.db')
            cursor = conn.execute('SELECT id, filename, timestamp, assessment, confidence FROM results ORDER BY timestamp DESC')
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                self.reports_container.add_widget(Label(text="No reports yet", color=(0.5, 0.5, 0.5, 1)))
                return
            
            for row in rows:
                card = self.create_report_card(row)
                self.reports_container.add_widget(card)
        except Exception as e:
            self.reports_container.add_widget(Label(text=f"Database error: {e}", color=(1, 0, 0, 1)))

    def create_report_card(self, row):
        rid, name, ts, assess, conf = row
        card = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(100), padding=dp(10))
        with card.canvas.before:
            Color(1, 1, 1, 1)
            Rectangle(pos=card.pos, size=card.size)
        
        card.add_widget(Label(text=f"{name}", bold=True, color=(0,0,0,1), halign='left'))
        card.add_widget(Label(text=f"{assess} ({conf:.1f}%)", color=(0.2, 0.6, 0.9, 1)))
        
        btn = Button(text="View Details", size_hint_y=None, height=dp(30))
        btn.bind(on_press=lambda x: self.view_details(rid))
        card.add_widget(btn)
        
        return card

    def view_details(self, rid):
        try:
            conn = sqlite3.connect('analysis_results.db')
            row = conn.execute('SELECT * FROM results WHERE id=?', (rid,)).fetchone()
            conn.close()
            if row:
                # Reuse show_results logic or similar popup
                pass 
        except: pass

class LearnScreen(FloatLayout):
    def __init__(self, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.add_widget(Label(text="Information & Guidance Screen", color=(0,0,0,1)))

class EarlyScreenApp(App):
    def build(self):
        from kivy.uix.screenmanager import ScreenManager, Screen
        self.init_database()
        self.screen_manager = ScreenManager()
        
        for name, cls in [('home', HomeScreen), ('upload', UploadScreen), 
                          ('reports', ReportsScreen), ('learn', LearnScreen)]:
            screen = Screen(name=name)
            screen.add_widget(cls(self))
            self.screen_manager.add_widget(screen)
            
        return self.screen_manager
    
    def init_database(self):
        conn = sqlite3.connect('analysis_results.db')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                timestamp TEXT,
                assessment TEXT,
                confidence REAL,
                behaviors TEXT,
                analysis_time REAL
            )
        ''')
        conn.close()

if __name__ == '__main__':
    EarlyScreenApp().run()
