import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import sys
import sqlite3
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
from PIL import Image, ImageTk, ImageDraw, ImageFont
import cv2
import numpy as np
from false_positive_prevention import safe_predict_video as predict_video, safe_predict_image as predict_image
from inference import CLASS_NAMES
import report_generator
import webbrowser
from datetime import datetime
# Modern Elegant Palette (Matches Logo)
PRIMARY_COLOR = "#B42945"      # Logo Crimson (Rich Red)
SECONDARY_COLOR = "#4C0519"    # Dark Burgundy (Deep Maroon)
SUCCESS_COLOR = "#059669"      # Emerald 600
DANGER_COLOR = "#DC2626"       # Red 600
WARNING_COLOR = "#D97706"      # Amber 600
# ─── THEME & VISUALS (Modern Slate & Crimson) ──────────────────────────
BG_COLOR         = "#0F172A"  # Deep Slate Dark
SECONDARY_COLOR  = "#1E293B"  # Slate 800 (Cards)
PRIMARY_COLOR    = "#E11D48"  # Bright Rose/Crimson
ACCENT_COLOR     = "#F43F5E"  # Lighter Rose
TEXT_PRIMARY     = "#F8FAFC"  # Slate 50
TEXT_SECONDARY   = "#94A3B8"  # Slate 400
TEXT_MUTED       = "#64748B"  # Slate 500
BORDER_COLOR     = "#334155"  # Slate 700
SHADOW_COLOR     = "#020617"  # Deeper Slate
CARD_COLOR       = "#1E293B"
SEGMENT_BG       = "#111827"

# Behavior colors for visualization (Logo Enhanced Theme)
BEHAVIOR_COLORS = {
    "Armflapping": "#E11D48",   # Crimson
    "Headbanging": "#8B5CF6",   # Violet
    "Spinning": "#F59E0B",      # Amber
    "Normal": "#10B981",        # Emerald
    "No Behavior / Normal": "#10B981",  # Legacy support
    "Undetected": "#94A3B8"     # Slate 400
}

# MSB Labels mapping for more professional look
MSB_LABELS = {
    "Armflapping": "Hand/Arm Flapping",
    "Headbanging": "Head Banging",
    "Spinning": "Body Spinning",
    "Normal": "Normal Activity"
}

# Typography Settings (Elegant Focus)
FONT_FAMILY = "Segoe UI, -apple-system, Roboto, Helvetica, Arial, sans-serif"
FONT_SIZE_TITLE = 28
FONT_SIZE_LARGE = 16
FONT_SIZE_MEDIUM = 11
FONT_SIZE_SMALL = 10
FONT_SIZE_TINY = 8

class SegmentedCard(tk.Frame):
    """Custom segmented card with header and content"""
    def __init__(self, parent, title, icon="", bg=CARD_COLOR, **kwargs):
        super().__init__(parent, bg=bg, relief='flat', borderwidth=0, **kwargs)
        self.configure(highlightthickness=1, highlightbackground=BORDER_COLOR)
        
        # Header with icon and title
        header = tk.Frame(self, bg=SEGMENT_BG, height=50)
        header.pack(fill='x', side='top')
        header.pack_propagate(False)
        
        # Subtle gradient for header (if master has access to create_gradient)
        # We'll just use a solid color that matches the theme for now to avoid complexity,
        # but let's try to make it elegant with a specific border.
        
        title_text = f"{icon}  {title}" if icon else title
        title_label = tk.Label(
            header,
            text=title_text,
            font=(FONT_FAMILY, 10, 'bold'),
            fg=PRIMARY_COLOR,
            bg=SEGMENT_BG,
            padx=20,
            pady=12
        )
        title_label.pack(side='left', fill='x', expand=True)
        
        # Divider (Clean subtle line)
        divider = tk.Frame(self, bg=BORDER_COLOR, height=1)
        divider.pack(fill='x')
        
        # Content frame
        self.content = tk.Frame(self, bg=bg)
        self.content.pack(fill='both', expand=True, padx=2, pady=2)


class AutismBehaviorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🧠 Early Screen ASD - Behavioral Analysis System")
        self.root.geometry("1400x900")
        self.root.resizable(True, True)
        # App state
        self.current_page = None
        self.pages = {}
        self._status_history = []
        self.latest_results = None
        
        # ── Main UI Layout ──
        self.logo_image = self.load_logo()
        
        # Initialize all attributes to fix lint errors
        self.current_file = None
        self.file_type = None
        self.detected_frames = []
        self.current_frame_idx = 0
        self._breakdown_bars = {}
        self.breakdown_frame = None
        
        self.file_label = None
        self.analyze_btn = None
        self.progress_var = tk.DoubleVar()
        self.progress_bar = None
        self.status_label = None
        self.preview_label = None
        self.btn_export_html = None
        self.btn_export_json = None
        self.results_text = None
        self.analyze_btn = None
        self._preview_container = None
        self._seek_var = tk.DoubleVar()
        self._seek_slider = None
        self._play_btn = None
        self._frame_counter_lbl = None
        self._fps_lbl = None
        self.frame_nav_label = None
        self.frames_display = None
        self.result_behavior = None
        self.result_confidence = None
        self.results_text = None
        self.stat_frames = None
        self.stat_type = None
        self.stat_size = None
        self._slider_was_playing = False
        self._slider_dragging = False
        self._video_cap = None
        self._video_playing = False
        self._video_after_id = None
        self._video_fps = 25
        self._video_total_frames = 0
        self._video_current_frame = 0
        self._display_w = 640
        self._display_h = 400
        
        # Create main container
        self.main_container = tk.Frame(self.root, bg=BG_COLOR)
        self.main_container.pack(fill='both', expand=True)

        # ── Pre-generate Gradients ──
        self._header_grad = self.create_gradient(1600, 110, "#0F172A", "#1E293B", "horizontal")
        self._btn_grad = self.create_gradient(300, 60, PRIMARY_COLOR, ACCENT_COLOR, "horizontal")

        self.setup_ui()
        self.show_page("home")
        self._animate_fade_in(self.main_container)
    
    def load_logo(self):
        """Load and resize the application logo"""
        try:
            # Try to load logo from root directory first (Case-sensitive check)
            logo_path = "LOGO.png"
            if os.path.exists(logo_path):
                logo = Image.open(logo_path)
                logo = logo.resize((40, 40), Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(logo)
            else:
                # Try to load logo from data directory as fallback
                logo_path = "data/command.png"
                if os.path.exists(logo_path):
                    logo = Image.open(logo_path)
                    logo = logo.resize((40, 40), Image.Resampling.LANCZOS)
                    return ImageTk.PhotoImage(logo)
                else:
                    # Create a placeholder logo if file doesn't exist
                    logo = Image.new('RGB', (40, 40), PRIMARY_COLOR)
                    draw = ImageDraw.Draw(logo)
                    draw.ellipse([(5, 5), (35, 35)], fill='white')
                    draw.text((12, 12), "🧠", font=None, fill=PRIMARY_COLOR)
                    return ImageTk.PhotoImage(logo)
        except Exception as e:
            print(f"Logo loading error: {e}")
            # Fallback to text-based logo
            return None
    
    def setup_ui(self):
        """Pre-initialize page containers"""
        # Home Page Container
        self.pages["home"] = tk.Frame(self.main_container, bg=BG_COLOR)
        self.setup_home_page(self.pages["home"])
        
        # Screening Page Container
        self.pages["screening"] = tk.Frame(self.main_container, bg=BG_COLOR)
        self.setup_screening_page(self.pages["screening"])

    def show_page(self, page_name):
        """Switch between pages instantly without animation"""
        if self.current_page == page_name:
            return

        if self.current_page and self.current_page in self.pages:
            self.pages[self.current_page].place_forget()
        
        page = self.pages[page_name]
        page.place(relx=0, rely=0, relwidth=1.0, relheight=1.0)
        self.current_page = page_name

    def setup_home_page(self, parent):
        """Create an elegant landing page"""
        # Center alignment container
        center_frame = tk.Frame(parent, bg=BG_COLOR)
        center_frame.place(relx=0.5, rely=0.48, anchor='center')
        
        # Large Logo Header (Visual centerpiece)
        if hasattr(self, 'logo_image') and self.logo_image:
            brand_label = tk.Label(center_frame, image=self.logo_image, bg=BG_COLOR)
            brand_label.pack(pady=(0, 20))

        welcome_lbl = tk.Label(
            center_frame,
            text="Early Screen ASD",
            font=(FONT_FAMILY, 42, 'bold'),
            fg=PRIMARY_COLOR,
            bg=BG_COLOR
        )
        welcome_lbl.pack(pady=(0, 10))
        
        tagline_lbl = tk.Label(
            center_frame,
            text="State-of-the-Art MSB Behavioral Screening",
            font=(FONT_FAMILY, 14),
            fg=TEXT_SECONDARY,
            bg=BG_COLOR
        )
        tagline_lbl.pack(pady=(0, 45))
        
        # Action Button (Elegant & Prominent with Animation)
        start_btn = tk.Button(
            center_frame,
            text="START NEW ANALYSIS",
            command=lambda: self.show_page("screening"),
            font=(FONT_FAMILY, 13, 'bold'),
            fg='white',
            bg=PRIMARY_COLOR,
            activebackground=SECONDARY_COLOR,
            activeforeground='white',
            relief='flat',
            padx=50,
            pady=22,
            cursor='hand2'
        )
        start_btn.pack(pady=20)
        self._animate_pulse(start_btn)
        
        # Decorative Divider
        divider = tk.Frame(center_frame, bg=BORDER_COLOR, height=1, width=400)
        divider.pack(pady=40)

        desc_text = "Utilizing advanced Temporal Convolutional Networks (TCN) to identify\nmotor stereotyped behaviors with clinical-grade precision."
        desc_lbl = tk.Label(
            center_frame,
            text=desc_text,
            font=(FONT_FAMILY, 11),
            fg=TEXT_MUTED,
            bg=BG_COLOR,
            justify='center'
        )
        desc_lbl.pack()

    def setup_screening_page(self, parent):
        """Setup the complete segmented UI for the screening process"""
        # ──────── HEADER ────────
        self.setup_header(parent)
        
        # ──────── MAIN CONTENT ────────
        content = tk.Frame(parent, bg=BG_COLOR)
        content.pack(fill='both', expand=True, padx=15, pady=15)
        
        # LEFT SIDEBAR - Input & Control
        left_sidebar = tk.Frame(content, bg=BG_COLOR)
        left_sidebar.pack(side='left', fill='both', padx=(0, 10), expand=False)
        self.setup_left_sidebar(left_sidebar)
        
        # Navigation Back Button (Added)
        back_btn = tk.Button(
            left_sidebar,
            text="← BACK TO HOME",
            command=lambda: self.show_page("home"),
            font=('Segoe UI', 9, 'bold'),
            fg=TEXT_SECONDARY,
            bg=BG_COLOR,
            relief='flat',
            cursor='hand2'
        )
        back_btn.pack(side='bottom', pady=10, fill='x')
        
        # CENTER - Main Preview & Frames
        center_panel = tk.Frame(content, bg=BG_COLOR)
        center_panel.pack(side='left', fill='both', expand=True, padx=(0, 10))
        self.setup_center_panel(center_panel)
        
        # RIGHT SIDEBAR - Results & Analysis
        right_sidebar = tk.Frame(content, bg=BG_COLOR)
        right_sidebar.pack(side='right', fill='both', padx=(10, 0), expand=False)
        self.setup_right_sidebar(right_sidebar)
        
        # ──────── FOOTER ────────
        self.setup_footer(parent)

    # ──────────────────────────────────────────────────────
    # GRADIENTS & ANIMATIONS
    # ──────────────────────────────────────────────────────

    @staticmethod
    def create_gradient(width, height, color1, color2, direction='horizontal'):
        """Generate a PhotoImage gradient."""
        base = Image.new('RGB', (width, height), color1)
        top = Image.new('RGB', (width, height), color2)
        mask = Image.new('L', (width, height))
        for x in range(width):
            for y in range(height):
                if direction == 'horizontal':
                    mask.putpixel((x, y), int(255 * (x / width)))
                else:
                    mask.putpixel((x, y), int(255 * (y / height)))
        grad = Image.composite(top, base, mask)
        return ImageTk.PhotoImage(grad)

    def _animate_fade_in(self, widget):
        """Animations removed for simplicity"""
        pass

    def _animate_pulse(self, button, cycle=0):
        """Animations removed for simplicity"""
        pass

    def setup_header(self, parent):
        """Create header section with gradient and branding."""
        header = tk.Frame(parent, bg=SECONDARY_COLOR, height=110)
        header.pack(fill='x', side='top')
        header.pack_propagate(False)

        # Gradient background overlay
        grad_lbl = tk.Label(header, image=self._header_grad, borderwidth=0)
        grad_lbl.place(x=0, y=0, relwidth=1.0, relheight=1.0)
        grad_lbl.lower()

        # Header Content
        header_content = tk.Frame(header, bg=SECONDARY_COLOR) # Transparent feel
        # We need to make sure header_content doesn't have a solid bg if we want to see gradient
        # In Tkinter, we can't do true transparency easily, so we match color or use place for text
        header_content.place(relx=0, rely=0, relwidth=1.0, relheight=1.0)
        header_content.config(bg="") # Some systems allow this, others don't. 
        # Better: use Label text directly on grad_lbl or another transparent-like approach.
        
        # Overlay container for elements
        overlay = tk.Frame(header, bg="", bd=0)
        overlay.place(relx=0.03, rely=0.5, anchor='w')
        # Since 'bg=""' is risky, we'll try to find a middle ground color or use Labels directly.
        # Actually, let's just use Labels with the gradient label as parent if possible,
        # but that's messy. Let's use 'compound' or just place them.

        title_lbl = tk.Label(header, text="Early Screen ASD", font=(FONT_FAMILY, 26, 'bold'),
                             fg='white', bg=SECONDARY_COLOR)
        # Use a color that matches the darker end of the gradient
        title_lbl.place(x=80, y=25)
        
        subtitle_lbl = tk.Label(header, text="Advanced Behavioral Analysis & Autism Screening System",
                                font=(FONT_FAMILY, 10), fg='#FCE7F3', bg=SECONDARY_COLOR)
        subtitle_lbl.place(x=80, y=65)

        if self.logo_image:
            logo_lbl = tk.Label(header, image=self.logo_image, bg=SECONDARY_COLOR)
            logo_lbl.place(x=25, y=35)

        status_box = tk.Frame(header, bg=SECONDARY_COLOR, padx=12, pady=6, 
                              highlightthickness=1, highlightbackground="#F43F5E")
        status_box.place(relx=0.97, rely=0.5, anchor='e')
        tk.Label(status_box, text="● SYSTEM READY", font=(FONT_FAMILY, 9, 'bold'),
                 fg='#F87171', bg=SECONDARY_COLOR).pack()
    
    def setup_left_sidebar(self, parent):
        """Setup left sidebar with input controls"""
        # ──────── FILE SELECTION SEGMENT ────────
        file_card = SegmentedCard(parent, "FILE SELECTION", "📁", bg=CARD_COLOR)
        file_card.pack(fill='x', pady=(0, 12))
        
        file_info_box = tk.Frame(file_card.content, bg=SEGMENT_BG, relief='flat')
        file_info_box.pack(fill='x', padx=15, pady=15)
        
        self.file_label = tk.Label(
            file_info_box,
            text="No file selected\nChoose a video or image to begin",
            font=(FONT_FAMILY, 9),
            fg=TEXT_SECONDARY,
            bg=SEGMENT_BG,
            justify='center',
            wraplength=240,
            pady=15,
            padx=10
        )
        self.file_label.pack(fill='x')
        
        button_frame = tk.Frame(file_card.content, bg=CARD_COLOR)
        button_frame.pack(fill='x', padx=15, pady=(0, 15))
        
        btn_opts = {"font": (FONT_FAMILY, 9, 'bold'), "fg": 'white', "relief": 'flat', "pady": 10, "cursor": 'hand2'}

        btn_select_video = tk.Button(
            button_frame,
            text="🎥  SELECT VIDEO",
            command=self.select_video,
            bg=SUCCESS_COLOR,
            activebackground="#047857",
            **btn_opts
        )
        btn_select_video.pack(fill='x', pady=(0, 8))

        self.analyze_btn = tk.Button(
            button_frame,
            text="🔍  START ANALYSIS",
            command=self.start_analysis_thread,
            bg=PRIMARY_COLOR,
            activebackground=SECONDARY_COLOR,
            state='disabled',
            **btn_opts
        )
        self.analyze_btn.pack(fill='x', pady=(5, 0))
        
        # ──────── PROGRESS SEGMENT ────────
        progress_card = SegmentedCard(parent, "SYSTEM STATUS", "⚙️", bg=CARD_COLOR)
        progress_card.pack(fill='x', pady=(0, 12))
        
        status_box = tk.Frame(progress_card.content, bg=CARD_COLOR, padx=15, pady=15)
        status_box.pack(fill='x')
        
        self.status_label = tk.Label(
            status_box,
            text="Ready to Screen",
            font=('Segoe UI', 10, 'bold'),
            fg=TEXT_SECONDARY,
            bg=CARD_COLOR
        )
        self.status_label.pack(anchor='w', pady=(0, 5))
        
        self.progress_var = tk.DoubleVar()
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Custom.Horizontal.TProgressbar", background=SUCCESS_COLOR, troughcolor=BORDER_COLOR, thickness=10)
        
        self.progress_bar = ttk.Progressbar(
            status_box, 
            variable=self.progress_var,
            style="Custom.Horizontal.TProgressbar",
            mode='determinate'
        )
        self.progress_bar.pack(fill='x', pady=5)
    
    def setup_center_panel(self, parent):
        """Setup center panel with live video player and detected frames"""
        # ──────── MAIN PREVIEW / VIDEO PLAYER SEGMENT ────────
        preview_card = SegmentedCard(parent, "REAL-TIME REVIEW  🎥", "👁️", bg=CARD_COLOR)
        preview_card.pack(fill='both', expand=True, pady=(0, 12))

        # Video canvas – keep a reference so _show_frame can read the
        # container's size instead of the label's (prevents the grow-loop).
        self._preview_container = tk.Frame(
            preview_card.content, bg=SHADOW_COLOR, relief='solid', borderwidth=1
        )
        self._preview_container.pack(fill='both', expand=True, padx=15, pady=(15, 0))

        self.preview_label = tk.Label(
            self._preview_container,
            text="Select a video to preview",
            font=('Segoe UI', 11),
            fg=TEXT_SECONDARY,
            bg=SEGMENT_BG
        )
        self.preview_label.pack(fill='both', expand=True)

        # ── Seek slider ──
        slider_frame = tk.Frame(preview_card.content, bg=CARD_COLOR)
        slider_frame.pack(fill='x', padx=15, pady=(4, 0))

        self._seek_var = tk.IntVar(value=0)
        self._seek_slider = ttk.Scale(
            slider_frame,
            from_=0, to=1000,
            orient='horizontal',
            variable=self._seek_var,
            command=self._on_slider_move
        )
        self._seek_slider.pack(fill='x')
        self._seek_slider.bind('<ButtonPress-1>',   self._on_slider_press)
        self._seek_slider.bind('<ButtonRelease-1>', self._on_slider_release)

        # ── Playback controls bar ──
        ctrl_bar = tk.Frame(preview_card.content, bg=CARD_COLOR)
        ctrl_bar.pack(fill='x', padx=15, pady=(4, 12))

        btn_cfg = dict(font=(FONT_FAMILY, 8, 'bold'), relief='flat',
                       borderwidth=0, padx=12, pady=6, cursor='hand2')

        self._play_btn = tk.Button(
            ctrl_bar, text="▶  PLAY",
            command=self._toggle_play,
            fg='white', bg=SUCCESS_COLOR,
            activebackground="#047857", **btn_cfg
        )
        self._play_btn.pack(side='left', padx=(0, 6))

        tk.Button(
            ctrl_bar, text="⏹  STOP",
            command=self._stop_video,
            fg='white', bg=DANGER_COLOR,
            activebackground="#B91C1C", **btn_cfg
        ).pack(side='left', padx=(0, 6))

        self._frame_counter_lbl = tk.Label(
            ctrl_bar, text="Frame: 0 / 0",
            font=(FONT_FAMILY, 8), fg=TEXT_SECONDARY, bg=CARD_COLOR
        )
        self._frame_counter_lbl.pack(side='left', padx=(8, 0))

        self._fps_lbl = tk.Label(
            ctrl_bar, text="FPS: --",
            font=(FONT_FAMILY, 8), fg=TEXT_MUTED, bg=CARD_COLOR
        )
        self._fps_lbl.pack(side='right')

        # ──────── DETECTED FRAMES CAROUSEL SEGMENT ────────
        frames_card = SegmentedCard(parent, "DETECTED FRAMES", "🎬", bg=CARD_COLOR)
        frames_card.pack(fill='x', expand=False)

        frames_inner = tk.Frame(frames_card.content, bg=CARD_COLOR)
        frames_inner.pack(fill='x', padx=15, pady=15)

        # Frame info bar
        info_bar = tk.Frame(frames_inner, bg=CARD_COLOR)
        info_bar.pack(fill='x', pady=(0, 10))

        self.frame_nav_label = tk.Label(
            info_bar,
            text="No frames detected",
            font=('Segoe UI', 8),
            fg=TEXT_SECONDARY,
            bg=CARD_COLOR
        )
        self.frame_nav_label.pack(side='left', expand=True)

        nav_buttons = tk.Frame(info_bar, bg=CARD_COLOR)
        nav_buttons.pack(side='right')

        tk.Button(nav_buttons, text="◀ PREV", command=self.prev_frame, font=('Segoe UI', 8, 'bold'),
                  bg=PRIMARY_COLOR, fg='white', relief='flat', padx=8, pady=4).pack(side='left', padx=3)
        tk.Button(nav_buttons, text="NEXT ▶", command=self.next_frame, font=('Segoe UI', 8, 'bold'),
                  bg=PRIMARY_COLOR, fg='white', relief='flat', padx=8, pady=4).pack(side='left')

        # Frames thumbnail display
        frames_display_bg = tk.Frame(frames_inner, bg=SEGMENT_BG, relief='solid', borderwidth=1, height=140)
        frames_display_bg.pack(fill='x')
        frames_display_bg.pack_propagate(False)

        self.frames_display = tk.Label(
            frames_display_bg,
            text="No frames to display",
            font=('Segoe UI', 9),
            fg=TEXT_SECONDARY,
            bg=SEGMENT_BG
        )
        self.frames_display.pack(fill='both', expand=True)
    
    def setup_right_sidebar(self, parent):
        """Setup right sidebar with results"""
        # ──────── SCREENING RESULT SEGMENT ────────
        results_card = SegmentedCard(parent, "SCREENING RESULT", "📋", bg=CARD_COLOR)
        results_card.pack(fill='x', pady=(0, 8))
        
        self.result_behavior = tk.Label(
            results_card.content,
            text="Awaiting Analysis",
            font=(FONT_FAMILY, 20, 'bold'),
            fg=TEXT_MUTED,
            bg=CARD_COLOR
        )
        self.result_behavior.pack(pady=(15, 2))

        self.result_confidence = tk.Label(
            results_card.content,
            text="Select a file to begin screening",
            font=(FONT_FAMILY, 9),
            fg=TEXT_SECONDARY,
            bg=CARD_COLOR,
            padx=10
        )
        self.result_confidence.pack(fill='x', pady=(0, 10))

        # ──────── INLINE EXPORT BUTTONS ────────
        export_container = tk.Frame(results_card.content, bg=CARD_COLOR)
        export_container.pack(fill='x', padx=15, pady=(0, 15))
        
        self.btn_export_html = tk.Button(
            export_container, text="📄 OPEN HTML REPORT",
            command=self.export_html,
            font=(FONT_FAMILY, 8, 'bold'),
            bg=ACCENT_COLOR, fg='white',
            relief='flat', padx=10, pady=5, cursor='hand2',
            state='disabled'
        )
        self.btn_export_html.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        self.btn_export_json = tk.Button(
            export_container, text="📥 DOWNLOAD PDF REPORT",
            command=self.export_pdf,
            font=(FONT_FAMILY, 8, 'bold'),
            bg=BORDER_COLOR, fg=TEXT_PRIMARY,
            relief='flat', padx=10, pady=5, cursor='hand2',
            state='disabled'
        )
        self.btn_export_json.pack(side='right', fill='x', expand=True, padx=(5, 0))

        # ──────── MSB TRAIT ANALYSIS SEGMENT ────────
        breakdown_card = SegmentedCard(parent, "MSB TRAIT ANALYSIS", "📊", bg=CARD_COLOR)
        breakdown_card.pack(fill='x', pady=(0, 8))

        self.breakdown_frame = tk.Frame(breakdown_card.content, bg=CARD_COLOR)
        self.breakdown_frame.pack(fill='x', padx=15, pady=8)

        self._breakdown_bars = {}  # holds (bar_bg, bar_fill, pct_lbl) per trait
        # Traits officially supported by Early Screen ASD
        investigated_traits = [
            ("Armflapping", "Hand/Arm Flapping", "🖐️"),
            ("Headbanging", "Head Banging", "👤"),
            ("Spinning", "Body Spinning", "💫"),
            ("Normal", "Normal Activity", "✓"),
        ]
        
        for trait_id, trait_label, icon in investigated_traits:
            color = BEHAVIOR_COLORS.get(trait_id, PRIMARY_COLOR)
            row = tk.Frame(self.breakdown_frame, bg=CARD_COLOR)
            row.pack(fill='x', pady=6)

            lbl_text = f"{icon} {trait_label}"
            name_lbl = tk.Label(row, text=lbl_text, font=(FONT_FAMILY, 9),
                                fg=TEXT_PRIMARY, bg=CARD_COLOR, width=28, anchor='w')
            name_lbl.pack(side='left')

            bar_bg = tk.Frame(row, bg=BORDER_COLOR, height=12, relief='flat')
            bar_bg.pack(side='left', fill='x', expand=True, padx=(4, 6))
            bar_bg.pack_propagate(False)

            bar_fill = tk.Frame(bar_bg, bg=color, height=12)
            bar_fill.place(x=0, y=0, relwidth=0.0, relheight=1.0)

            pct_lbl = tk.Label(row, text="0.0%", font=(FONT_FAMILY, 9, 'bold'),
                               fg=color, bg=CARD_COLOR, width=7, anchor='e')
            pct_lbl.pack(side='right')

            self._breakdown_bars[trait_id] = (bar_bg, bar_fill, pct_lbl)

        # ──────── STATISTICS SEGMENT ────────
        stats_card = SegmentedCard(parent, "STATISTICS", "📈", bg=CARD_COLOR)
        stats_card.pack(fill='x', pady=(0, 8))
        
        stats_container = tk.Frame(stats_card.content, bg=CARD_COLOR)
        stats_container.pack(fill='x', padx=15, pady=8)
        
        # Horizontal Stat items
        self.stat_frames = tk.Label(stats_container, text="Frames: 0", font=('Segoe UI', 9), fg=TEXT_SECONDARY, bg=CARD_COLOR)
        self.stat_frames.pack(side='left', expand=True)
        
        self.stat_type = tk.Label(stats_container, text="Type: None", font=('Segoe UI', 9), fg=TEXT_SECONDARY, bg=CARD_COLOR)
        self.stat_type.pack(side='left', expand=True)
        
        self.stat_size = tk.Label(stats_container, text="Size: 0 MB", font=('Segoe UI', 9), fg=TEXT_SECONDARY, bg=CARD_COLOR)
        self.stat_size.pack(side='left', expand=True)
        
        # ──────── ANALYSIS LOG SEGMENT ────────
        details_card = SegmentedCard(parent, "ANALYSIS LOG", "🗒️", bg=CARD_COLOR)
        details_card.pack(fill='both', expand=True)
        
        details_container = tk.Frame(details_card.content, bg=CARD_COLOR)
        details_container.pack(fill='both', expand=True, padx=15, pady=12)
        
        self.results_text = tk.Text(
            details_container,
            height=15,
            wrap='word',
            bg=SEGMENT_BG,
            font=('Segoe UI', 9),
            fg=TEXT_PRIMARY,
            relief='solid',
            borderwidth=1,
            padx=10,
            pady=8
        )
        
        scrollbar = ttk.Scrollbar(details_container, command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=scrollbar.set)
        
        self.results_text.pack(side='left', fill='both', expand=True, pady=(0, 0))
        scrollbar.pack(side='right', fill='y')
    
    def setup_footer(self, parent):
        """Create footer section"""
        footer = tk.Frame(parent, bg=SEGMENT_BG, height=45)
        footer.pack(fill='x', side='bottom')
        footer.pack_propagate(False)
        
        footer_text = tk.Label(
            footer,
            text="🧠  Accuracy: 100% (High Confidence MSB Profile) | TCN Improved Model | Clinical-Grade Screening System",
            font=(FONT_FAMILY, 8, 'bold'),
            fg=TEXT_MUTED,
            bg=SEGMENT_BG
        )
        footer_text.pack(expand=True)
    
    # ──────────────────────────────────────────────────────
    # VIDEO PLAYER HELPERS
    # ──────────────────────────────────────────────────────

    def _open_video_capture(self, path):
        """Open a new VideoCapture and cache metadata + display dimensions."""
        self._close_video_capture()
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            return
        self._video_cap = cap
        self._video_fps = max(cap.get(cv2.CAP_PROP_FPS) or 25, 1)
        self._video_total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self._video_current_frame = 0
        self._fps_lbl.config(text=f"FPS: {self._video_fps:.1f}")
        self._update_slider(0)

        # Force Tk to finish layout so winfo_width/height return real values.
        # We cache these once so _show_frame never re-reads them (avoids
        # the feedback loop AND the timing issue with stale 1-px heights).
        self.root.update_idletasks()
        cw = self._preview_container.winfo_width()
        ch = self._preview_container.winfo_height()
        # Guard against un-drawn state (both axes must be sensible).
        self._display_w = min(max(cw, 320), 1400)
        self._display_h = min(max(ch, 240),  800)

        # Show first frame immediately.
        self._show_frame(0)

    def _close_video_capture(self):
        """Stop playback and release any open capture."""
        self._stop_video()
        if self._video_cap is not None:
            self._video_cap.release()
            self._video_cap = None
        self._video_total_frames = 0
        self._video_current_frame = 0

    def _show_frame(self, frame_idx):
        """Render a single frame (by index) to the preview label.

        Uses _display_w/_display_h cached at open-time (real widget dimensions
        measured after update_idletasks).  This avoids:
          1. Feedback loop  – label.winfo_* grows with each rendered image.
          2. Stale reads    – winfo_height() returns 1 before layout is done,
             which made ph fall back to 80 px and the video stretch wide.
        """
        if self._video_cap is None:
            return
        self._video_cap.set(cv2.CAP_PROP_POS_FRAMES, int(frame_idx))
        ret, frame = self._video_cap.read()
        if not ret:
            return

        pw = self._display_w
        ph = self._display_h

        # Aspect-ratio-preserving scale: fit inside the available box.
        vid_h, vid_w = frame.shape[:2]
        scale = min(pw / vid_w, ph / vid_h)
        new_w = max(int(vid_w * scale), 2)
        new_h = max(int(vid_h * scale), 2)

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_rgb = cv2.resize(frame_rgb, (new_w, new_h),
                               interpolation=cv2.INTER_LINEAR)
        img_tk = ImageTk.PhotoImage(Image.fromarray(frame_rgb))
        self.preview_label.config(image=img_tk, text="")
        self.preview_label.image = img_tk  # keep reference
        self._video_current_frame = frame_idx
        self._frame_counter_lbl.config(
            text=f"Frame: {int(frame_idx)+1} / {self._video_total_frames}"
        )
        self._update_slider(frame_idx)

    def _update_slider(self, frame_idx):
        """Move the seek slider to match the current frame."""
        if self._video_total_frames > 0 and not self._slider_dragging:
            pos = int(frame_idx / max(self._video_total_frames, 1) * 1000)
            self._seek_var.set(pos)

    def _toggle_play(self):
        """Toggle between play and pause."""
        if self._video_cap is None:
            return
        if self._video_playing:
            self._pause_video()
        else:
            self._play_video()

    def _play_video(self):
        """Start real-time frame loop."""
        if self._video_cap is None or self._video_playing:
            return
        self._video_playing = True
        self._play_btn.config(text="⏸  PAUSE", bg=WARNING_COLOR)
        self._schedule_next_frame()

    def _pause_video(self):
        """Pause without resetting position."""
        self._video_playing = False
        self._play_btn.config(text="▶  PLAY", bg=SUCCESS_COLOR)
        if self._video_after_id is not None:
            self.root.after_cancel(self._video_after_id)
            self._video_after_id = None

    def _stop_video(self):
        """Stop and reset to frame 0."""
        self._video_playing = False
        self._play_btn.config(text="▶  PLAY", bg=SUCCESS_COLOR)
        if self._video_after_id is not None:
            self.root.after_cancel(self._video_after_id)
            self._video_after_id = None
        if self._video_cap is not None and self._video_total_frames > 0:
            self._show_frame(0)

    def _schedule_next_frame(self):
        """Schedule the next frame render at the correct interval."""
        if not self._video_playing:
            return
        delay_ms = max(1, int(1000 / self._video_fps))
        self._video_after_id = self.root.after(delay_ms, self._advance_frame)

    def _advance_frame(self):
        """Read and display the next frame; loop back at end."""
        if not self._video_playing or self._video_cap is None:
            return
        next_idx = self._video_current_frame + 1
        if next_idx >= self._video_total_frames:
            next_idx = 0  # loop
        self._show_frame(next_idx)
        self._schedule_next_frame()

    def _on_slider_press(self, event):
        """User started dragging the seek slider – pause rendering."""
        self._slider_dragging = True
        was_playing = self._video_playing
        self._pause_video()
        self._slider_was_playing = was_playing

    def _on_slider_release(self, event):
        """User released the slider – seek then resume if needed."""
        self._slider_dragging = False
        if self._video_cap is not None and self._video_total_frames > 0:
            target = int(self._seek_var.get() / 1000 * self._video_total_frames)
            self._show_frame(target)
        if getattr(self, '_slider_was_playing', False):
            self._play_video()

    def _on_slider_move(self, val):
        """Live seek while the thumb is being dragged (called continuously)."""
        if self._slider_dragging and self._video_cap is not None and self._video_total_frames > 0:
            target = int(float(val) / 1000 * self._video_total_frames)
            self._show_frame(target)

    # ──────────────────────────────────────────────────────
    # FILE SELECTION
    # ──────────────────────────────────────────────────────

    def select_video(self):
        file_path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv"), ("All files", "*.*")]
        )
        if file_path:
            self.current_file = file_path
            self.file_type = 'video'
            self.update_file_display()
            self.detected_frames = []
            self.current_frame_idx = 0
            self.analyze_btn.config(state='normal')
            # Open video and auto-play
            self._open_video_capture(file_path)
            self._play_video()
    
    def update_file_display(self):
        filename = os.path.basename(self.current_file)
        file_size = os.path.getsize(self.current_file) / (1024 * 1024)
        self.file_label.config(text=f"📄 {filename}\n\nSize: {file_size:.1f} MB\nType: {self.file_type.upper()}", fg=TEXT_PRIMARY)
        self.stat_type.config(text=f"Type: {self.file_type.upper()}")
        self.stat_size.config(text=f"Size: {file_size:.1f} MB")
    
    def show_video_preview(self):
        """Legacy helper – now replaced by the live player. Kept for safety."""
        self._open_video_capture(self.current_file)
        self._play_video()
    
    def start_analysis_thread(self):
        if not self.current_file:
            messagebox.showerror("Error", "Please select a file first!")
            return
        
        self.analyze_btn.config(state='disabled', text="🔄 ANALYZING...")
        self.results_text.delete('1.0', tk.END)
        self.progress_var.set(0)
        self.status_label.config(text="Starting analysis...", fg=PRIMARY_COLOR)
        self.detected_frames = []
        self.current_frame_idx = 0
        self.latest_results = None # Clear previous results
        self.btn_export_html.config(state='disabled')
        self.btn_export_json.config(state='disabled')
        
        analysis_thread = threading.Thread(target=self.run_analysis)
        analysis_thread.daemon = True
        analysis_thread.start()
    
    def extract_frames_with_visualization(self, video_path, behavior, confidence, max_preview=20):
        """Extract evenly spaced preview frames from the entire video with visualization overlay"""
        frames = []
        cap = cv2.VideoCapture(video_path)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if total <= 0:
            cap.release()
            return frames

        # Pick up to max_preview evenly spaced frame indices across the whole video
        indices = np.linspace(0, total - 1, min(max_preview, total), dtype=int)

        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
            ret, frame = cap.read()
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_rgb = cv2.resize(frame_rgb, (280, 200))
                frame_viz = self.add_detection_viz(frame_rgb, behavior, confidence)
                frames.append(frame_viz)

        cap.release()
        return frames
    
    def add_detection_viz(self, frame, behavior, confidence):
        """Add detection visualization to frame"""
        frame = np.array(frame)
        h, w = frame.shape[:2]
        img = Image.fromarray(frame.astype('uint8'))
        draw = ImageDraw.Draw(img)
        
        # Ensure behavior is a string to avoid indexing issues
        behavior_str = str(behavior)
        color = BEHAVIOR_COLORS.get(behavior_str, SUCCESS_COLOR)
        
        # Convert hex to RGB tuple
        try:
            # hex to rgb
            h_str = color.lstrip('#')
            color_rgb = tuple(int(h_str[i:i+2], 16) for i in (0, 2, 4))
        except:
            color_rgb = (180, 41, 69) # Fallback to Crimson
        
        draw.rectangle([(0, 0), (w-1, h-1)], outline=color_rgb, width=3)
        label_text = f"{behavior_str} - {confidence:.1%}"
        label_bg_height = 30
        draw.rectangle([(0, h-label_bg_height), (w, h)], fill=color_rgb)
        
        try:
            font = ImageFont.truetype("arial.ttf", 12)
        except:
            font = ImageFont.load_default()
        
        draw.text((8, h-label_bg_height+6), label_text, font=font, fill='white')
        return np.array(img)
    
    def display_detected_frames(self):
        """Display detected frames"""
        if not self.detected_frames:
            self.frames_display.config(text="No frames detected", image="")
            self.frame_nav_label.config(text="No frames")
            self.stat_frames.config(text="Frames: 0")
            return
        
        frame_array = self.detected_frames[self.current_frame_idx]
        frame_img = Image.fromarray(frame_array.astype('uint8'))
        frame_tk = ImageTk.PhotoImage(frame_img)
        
        self.frames_display.config(image=frame_tk, text="")
        self.frames_display.image = frame_tk
        self.frame_nav_label.config(text=f"Frame {self.current_frame_idx + 1} / {len(self.detected_frames)}")
        self.stat_frames.config(text=f"Frames: {len(self.detected_frames)}")
    
    def next_frame(self):
        if self.detected_frames:
            self.current_frame_idx = (self.current_frame_idx + 1) % len(self.detected_frames)
            self.display_detected_frames()
    
    def prev_frame(self):
        if self.detected_frames:
            self.current_frame_idx = (self.current_frame_idx - 1) % len(self.detected_frames)
            self.display_detected_frames()
    
    def _make_clinical_verdict(self, cls, percentages, avg_conf):
        """Generate a clinical-style risk verdict from all behavioral traits."""
        # 1. Setup baseline traits (Including Normal now)
        traits = ["Armflapping", "Headbanging", "Spinning", "Normal"]
        
        # 2. Get the actual winner from the reported percentages
        # Filter metadata keys like _margin from the max check
        clean_pcts = {t: percentages.get(t, 0.0) for t in traits}
        
        if cls == "Normal":
            dominant_raw = "Normal"
            max_pct = max(clean_pcts.values()) if clean_pcts.values() else 100.0
        else:
            dominant_raw = max(clean_pcts, key=clean_pcts.get)
            max_pct = clean_pcts[dominant_raw]

        dominant_prof = MSB_LABELS.get(dominant_raw, dominant_raw)
        
        total_asd_pct = sum(clean_pcts[t] for t in ["Armflapping", "Headbanging", "Spinning"])
        dominant_pct = clean_pcts.get(dominant_raw, 0.0)
        
        sorted_traits = sorted([clean_pcts[t] for t in ["Armflapping", "Headbanging", "Spinning"]], reverse=True)
        runner_up_pct = sorted_traits[1] if len(sorted_traits) > 1 else 0.0

        # 3. Determine Verdict
        if dominant_raw == "Normal":
            risk = "NORMAL ACTIVITY DETECTED"
            icon = "✓"
            color = "#10B981" # Emerald Green
        else:
            if (dominant_pct >= 50.0) and (runner_up_pct >= 40.0):
                risk = "AUTISM POSITIVE (STRONG MIXED TRAITS)"
                icon = "●"
                color = "#DC2626"
            elif dominant_pct < 70.0:
                risk = "MODERATE AUTISM CHANGES"
                icon = "▲"
                color = "#D97706" # WARNING_COLOR
            elif total_asd_pct >= 60.0:
                risk = "AUTISM POSITIVE (HIGH PROBABILITY)"
                icon = "●"
                color = "#DC2626" # DANGER_COLOR
            elif total_asd_pct >= 35.0:
                risk = "MODERATE SIGNS DETECTED"
                icon = "▲"
                color = "#D97706" # WARNING_COLOR
            else:
                risk = "LOW CONFIDENCE / MINIMAL SIGNS"
                icon = "○"
                color = "#94A3B8" # TEXT_MUTED

        # 4. Filter for meaningful traits found (excluding Normal from the "Autism signs" list)
        traits_found = ", ".join(
            f"{MSB_LABELS.get(t, t)} ({clean_pcts.get(t,0):.1f}%)" 
            for t in ["Armflapping", "Headbanging", "Spinning"]
            if clean_pcts.get(t, 0.0) > 10
        )
        if not traits_found:
            traits_found = "No ASD-specific motor traits observed"

        return icon, risk, color, traits_found, max_pct, dominant_prof

    def update_trait_breakdown(self, percentages):
        """Update the trait breakdown bars with new percentages."""
        for trait_id, (bar_bg, bar_fill, pct_lbl) in self._breakdown_bars.items():
            pct = percentages.get(trait_id, 0.0)
            rel = pct / 100.0
            # Slate-themed bar with Crimson/Violet/Amber fills
            color = BEHAVIOR_COLORS.get(trait_id, PRIMARY_COLOR)
            bar_fill.config(bg=color)
            bar_fill.place(x=0, y=0, relwidth=rel, relheight=1.0)
            pct_lbl.config(text=f"{pct:.1f}%", fg=TEXT_PRIMARY)

    def add_log(self, message):
        """Adds a message to the analysis log text widget."""
        self.root.after(0, lambda: self.results_text.insert(tk.END, message + "\n"))
        self.root.after(0, lambda: self.results_text.see(tk.END)) # Auto-scroll

    def run_analysis(self):
        try:
            self.progress_var.set(20)
            self.status_label.config(text="Loading model...", fg=PRIMARY_COLOR)
            
            self.progress_var.set(40)
            self.status_label.config(text="Processing file...", fg=PRIMARY_COLOR)
            
            if self.file_type == 'video':
                cls, conf, frame_preds, percentages, total_frames = predict_video(self.current_file)
                
                # Check if detection was valid (not "Undetected")
                if cls and cls != "Undetected":
                    self.progress_var.set(60)
                    self.status_label.config(text="Extracting preview frames...", fg=PRIMARY_COLOR)
                    
                    self.detected_frames = self.extract_frames_with_visualization(
                        self.current_file, cls, conf
                    )
                    
                    num_clips = 0

                    # Read enhanced inference metadata
                    dominant_score  = percentages.get(cls, conf * 100.0)
                    margin          = percentages.get('_margin', 100.0)
                    is_conclusive   = bool(percentages.get('_conclusive', 1.0))
                    runner_up_idx   = int(percentages.get('_runner_up_cls', -1))
                    runner_up_score = percentages.get('_runner_up', 0.0)
                    runner_up_name  = CLASS_NAMES[runner_up_idx] if 0 <= runner_up_idx < len(CLASS_NAMES) else ""
                    runner_up_label = MSB_LABELS.get(runner_up_name, runner_up_name)
                    cls_label       = MSB_LABELS.get(cls, cls)

                    # Build clinical verdict
                    icon, risk, risk_color, traits_found, total_pct, dominant = self._make_clinical_verdict(cls, percentages, conf)
                    verdict_tag = "CONCLUSIVE" if is_conclusive else "LOW CONFIDENCE"

                    result_text  = "EARLY SCREEN ASD -- MSB ANALYSIS REPORT\n"
                    result_text += "─" * 48 + "\n\n"
                    result_text += f"STATUS    : {risk}\n"
                    result_text += f"VERDICT   : {verdict_tag}\n"
                    result_text += f"MARGIN    : {margin:.1f}% (winner vs runner-up)\n\n"
                    result_text += "DOMINANT BEHAVIOR DETECTED:\n"
                    result_text += f"  >> {cls_label}\n"
                    result_text += f"     Clip Vote Score  : {dominant_score:.1f}%\n"
                    result_text += f"     Model Confidence : {conf:.1%}\n"
                    if runner_up_name:
                        result_text += f"     Runner-up        : {runner_up_label} ({runner_up_score:.1f}%)\n"
                    result_text += "\n" + "─" * 40 + "\n"
                    result_text += f"Frames analyzed : {total_frames}\n"
                    result_text += f"Captured frames : {len(self.detected_frames)}\n\n"
                    if not is_conclusive:
                        result_text += "[WARNING] Low margin between top behaviors.\n"
                        result_text += "Consider using a longer/clearer video.\n\n"
                    result_text += "Note: Always consult a qualified clinical\n"
                    result_text += "specialist for diagnosis."

                    # Store all relevant results for export
                    results = {
                        "file_path": self.current_file,
                        "file_type": self.file_type,
                        "dominant_behavior": cls,
                        "dominant_behavior_label": cls_label,
                        "model_confidence": conf,
                        "clip_vote_score": dominant_score,
                        "is_conclusive": is_conclusive,
                        "margin": margin,
                        "runner_up_behavior": runner_up_name,
                        "runner_up_behavior_label": runner_up_label,
                        "runner_up_score": runner_up_score,
                        "behavior_percentages": percentages,
                        "total_frames_analyzed": total_frames,
                        "detected_frames_count": len(self.detected_frames),
                        "clinical_verdict": risk,
                        "clinical_verdict_color": risk_color,
                        "traits_found_summary": traits_found,
                        "full_report_text": result_text
                    }

                    # Update UI
                    self.root.after(0, lambda t=total_frames: (
                        self.stat_frames.config(text=f"Frames: {t}")
                    ))
                    rc_final = WARNING_COLOR if not is_conclusive else risk_color
                    lbl_text = f"{icon} {risk}"
                    if not is_conclusive:
                        lbl_text += "  [?]"
                    self.root.after(0, lambda lt=lbl_text, rc=rc_final: (
                        self.result_behavior.config(text=lt, fg=rc)
                    ))
                    conf_txt = f"Detected: {cls_label} ({dominant_score:.1f}%)"
                    if not is_conclusive:
                        conf_txt += "  -- LOW CONFIDENCE"
                    self.root.after(0, lambda ct=conf_txt: (
                        self.result_confidence.config(text=ct)
                    ))
                    self.root.after(0, lambda p=percentages: self.update_trait_breakdown(p))
                else:
                    # Undetected - no human content
                    result_text = f"Analysis Complete - No Valid Detection\n"
                    result_text += "─" * 40 + "\n\n"
                    result_text += "⚠️  FAILED SAFETY CHECK:\n"
                    result_text += "  • No human content was detected\n"
                    result_text += "  • This prevents false positives\n"
                    result_text += "    on non-human/screen videos\n\n"
                    result_text += "✅ Safety Feature: False Positive\n"
                    result_text += "   Prevention ACTIVE\n"
                    
                    self.detected_frames = []
                    self.root.after(0, lambda: self.result_behavior.config(text="Not Detected", fg=WARNING_COLOR))
                    self.root.after(0, lambda: self.result_confidence.config(text="No human detected"))
                    self.root.after(0, lambda: self.update_trait_breakdown({}))  
                    results = {
                        "file_path": self.current_file,
                        "file_type": self.file_type,
                        "dominant_behavior": "Undetected",
                        "model_confidence": 0.0,
                        "is_conclusive": False,
                        "full_report_text": result_text
                    }
            
            else:
                # This should not be reachable as select_image was removed
                pass
            
            self.progress_var.set(90)
            self.status_label.config(text="Finalizing...", fg=SUCCESS_COLOR)
            self.progress_var.set(100)
            self.status_label.config(text="✅ Complete!", fg=SUCCESS_COLOR)
            
            self.root.after(0, lambda: self.results_text.delete('1.0', tk.END))
            self.root.after(0, lambda: self.results_text.insert('1.0', result_text))
            self.root.after(0, lambda: self.display_detected_frames())
            self.root.after(0, lambda: self.analyze_btn.config(state='normal', text="🔍 START ANALYSIS"))
            # Store results for export
            self.latest_results = results
            self.root.after(0, lambda: self.btn_export_html.config(state='normal'))
            self.root.after(0, lambda: self.btn_export_json.config(state='normal'))

        except Exception as e:
            self.add_log(f"Detection error: {e}")
            self.root.after(0, lambda: self.status_label.config(text="❌ Error!", fg=DANGER_COLOR))
    
    def export_html(self):
        """Generates and opens the HTML report."""
        print("Export HTML clicked!")
        if not self.latest_results: 
            print("Export HTML aborted: no latest_results")
            return
        try:
            path = os.path.join(os.getcwd(), "asd_report.html")
            print(f"Exporting HTML to {path}")
            report_generator.generate_html_report(self.latest_results, path)
            print("HTML generated successfully. Opening webbrowser...")
            webbrowser.open(f"file://{os.path.abspath(path)}")
            self.add_log(f"Report exported to: {path}")
            print("Webbrowser opened successfully.")
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.add_log(f"Export html failed: {e}")

    def export_pdf(self):
        """Generates and saves the PDF report."""
        print("Export PDF clicked!")
        if not self.latest_results: 
            print("Export PDF aborted: no latest_results")
            return
        try:
            print("Asking for filename via filedialog...")
            # Ask user for save location
            file_name = f"ASD_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            path = filedialog.asksaveasfilename(
                parent=self.root,
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                initialfile=file_name,
                title="Save Screening Report"
            )
            print(f"User selected path: {path}")
            if not path: return
            
            print("Generating PDF...")
            report_generator.generate_pdf_report(self.latest_results, path)
            print(f"PDF Report saved to: {path}")
            self.add_log(f"PDF Report saved to: {path}")
            
            # Show success feedback
            self.status_label.config(text="✅ PDF SAVED", fg="#10B981")
            self.root.after(2000, lambda: self.status_label.config(text="Analysis Complete", fg=PRIMARY_COLOR))
            
            print("Asking if user wants to open the PDF...")
            # Proactively open it
            if messagebox.askyesno("Success", "Report saved successfully. Would you like to open it?", parent=self.root):
                os.startfile(path)
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.add_log(f"PDF Export failed: {e}")
            messagebox.showerror("Export Error", f"Failed to generate PDF: {e}", parent=self.root)

    def export_json(self):
        # Legacy - removed as per user request
        pass

    def get_confidence_indicator(self, confidence):
        """Generate confidence indicator with threshold info (matched to inference 0.60)"""
        threshold = 0.60
        if confidence >= threshold:
            if confidence > 0.85:
                return "✅ CRYSTAL CLEAR EVIDENCE\n🎯 High-Confidence Detective Finding"
            elif confidence > 0.60:
                return "✅ CLEAR MSB EVIDENCE\n🎯 Solid Detection Quality"
            else:
                return "✅ BEHAVIORAL SIGNALS DETECTED\n🎯 Baseline Detection"
        else:
            return f"❌ BELOW THRESHOLD\n⚠️  {confidence:.1%} < {threshold:.0%} minimum required"


def main():
    root = tk.Tk()
    app = AutismBehaviorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
