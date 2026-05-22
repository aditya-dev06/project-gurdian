import os
import sys
import json
import random
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime, timedelta

# Resolve base directories and import core guardian module
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
import guardian

# ==================== THEME & STYLE CONSTANTS (APPLE PREMIUM DARK MODE) ====================
BG_DARK = "#09090B"          # Pure deep charcoal/black (Midnight)
BG_CARD = "#121214"          # Sleek Space Black card background
BG_INNER = "#1C1C1E"         # Apple premium dark gray inner container
FG_LIGHT = "#F5F5F7"         # Apple primary white text
FG_SECONDARY = "#8E8E93"     # Apple secondary gray text
ACCENT_CYAN = "#0071E3"      # Apple royal signature blue (primary interactive accent)
ACCENT_GREEN = "#30D158"     # Apple vibrant system green (success/completed)
ACCENT_RED = "#FF453A"       # Apple vibrant system red (error/warning)
ACCENT_ORANGE = "#FF9F0A"    # Apple vibrant system orange (stats/countdowns)
ACCENT_PURPLE = "#BF5AF2"    # Apple vibrant system purple (special icons)
HOVER_COLOR = "#222225"      # Minimalist card hover background
BORDER_COLOR = "#2C2C2E"     # Thin clean outline divider

FONT_FAMILY = "Segoe UI" if os.name == "nt" else "Arial"

class HoverTooltip:
    def __init__(self, widget, get_text_func):
        self.widget = widget
        self.get_text_func = get_text_func
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)
        self.widget.bind("<ButtonPress>", self.hide_tip)

    def show_tip(self, event=None):
        text = self.get_text_func()
        if not text:
            return
        
        # Calculate coordinate placement
        x = self.widget.winfo_rootx() + 10
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.attributes("-topmost", True)
        
        # Premium Apple Midnight Tooltip border frame
        frame = tk.Frame(tw, bg=BG_INNER, highlightbackground=BORDER_COLOR, highlightcolor=BORDER_COLOR, highlightthickness=1)
        frame.pack()
        
        label = tk.Label(
            frame,
            text=text,
            justify="left",
            background=BG_INNER,
            foreground=FG_LIGHT,
            font=(FONT_FAMILY, 8, "normal"),
            padx=8,
            pady=4
        )
        label.pack()

    def hide_tip(self, event=None):
        if self.tip_window:
            try:
                self.tip_window.destroy()
            except Exception:
                pass
            self.tip_window = None

class KanjiWidget:
    def __init__(self, root):
        self.root = root
        self.root.title("Kanji Learning Widget")
        self.root.configure(bg=BG_DARK)
        
        # Frameless and Always-on-Top parameters
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.is_pinned = True
        
        # Geometry: compact widget sticking to screen
        self.window_width = 300
        self.window_height = 430
        
        # Sticking position: bottom right above taskbar
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = screen_width - self.window_width - 40
        y = screen_height - self.window_height - 60
        self.root.geometry(f"{self.window_width}x{self.window_height}+{x}+{y}")
        
        # Drag variables
        self.drag_data = {"x": 0, "y": 0}
        
        # Load Kanji database and configurations
        self.config = guardian.load_config()
        self.kanji_db = guardian.load_kanji_data()
        
        # Proactively register/refresh startup shortcut based on config setting
        try:
            startup_enabled = self.config.get("startup_enabled", True)
            guardian.register_startup_shortcut(startup_enabled)
        except Exception:
            pass
        
        # Current active card state
        self.current_card = None
        self.api_in_progress = False
        self.cached_next_card = None
        self.prefetch_in_progress = False
        self.viewed_cards = []
        self.current_view_idx = -1
        
        # Quiz loop variables
        self.quiz_enabled = tk.BooleanVar(value=True)
        self.quiz_interval_min = 10  # default 10 minutes
        self.quiz_timer_id = None
        self.quiz_target_time = None
        
        # Build UI layout
        self.create_title_bar()
        self.create_card_container()
        self.create_options_footer()
        
        # Load initial card (either last reviewed or a fresh one)
        self.load_initial_card()
        
        # Start pop-up quiz scheduler loop
        self.schedule_next_quiz()
        self.update_countdown_ticking()
        self.trigger_background_prefetch()

    # ==================== INTERACTIVE WINDOW DRAGGING ====================

    def create_title_bar(self):
        """Creates a modern title bar for window dragging, unpinning, and closing."""
        title_bar = tk.Frame(self.root, bg=BG_CARD, height=35)
        title_bar.pack(fill="x", side="top")
        title_bar.pack_propagate(False)
        
        # Drag binds
        title_bar.bind("<Button-1>", self.start_drag)
        title_bar.bind("<B1-Motion>", self.drag_window)
        
        # Title text
        self.title_label = tk.Label(
            title_bar,
            text="🎌  KANJI STUDY WIDGET",
            fg=ACCENT_CYAN,
            bg=BG_CARD,
            font=(FONT_FAMILY, 9, "bold")
        )
        self.title_label.pack(side="left", padx=10)
        self.title_label.bind("<Button-1>", self.start_drag)
        self.title_label.bind("<B1-Motion>", self.drag_window)
        
        # Close Button
        close_btn = tk.Button(
            title_bar,
            text="✕",
            fg=FG_LIGHT,
            bg=BG_CARD,
            bd=0,
            activebackground=ACCENT_RED,
            activeforeground=FG_LIGHT,
            font=(FONT_FAMILY, 10, "bold"),
            command=self.root.destroy,
            cursor="hand2"
        )
        close_btn.pack(side="right", fill="y", padx=5)
        self.bind_button_hover(close_btn, BG_CARD, ACCENT_RED)
        
        # Always-on-top Pin Button
        self.pin_btn = tk.Button(
            title_bar,
            text="📌",
            fg=ACCENT_CYAN,
            bg=BG_CARD,
            bd=0,
            activebackground=HOVER_COLOR,
            activeforeground=FG_LIGHT,
            font=(FONT_FAMILY, 9),
            command=self.toggle_pin,
            cursor="hand2"
        )
        self.pin_btn.pack(side="right", fill="y", padx=5)
        self.bind_button_hover(self.pin_btn, BG_CARD, HOVER_COLOR)

    def start_drag(self, event):
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

    def drag_window(self, event):
        x = self.root.winfo_x() + (event.x - self.drag_data["x"])
        y = self.root.winfo_y() + (event.y - self.drag_data["y"])
        self.root.geometry(f"+{x}+{y}")

    def toggle_pin(self):
        """Swaps the widget stay-on-top configuration."""
        self.is_pinned = not self.is_pinned
        self.root.attributes("-topmost", self.is_pinned)
        if self.is_pinned:
            self.pin_btn.config(text="📌", fg=ACCENT_CYAN)
        else:
            self.pin_btn.config(text="📍", fg=FG_LIGHT)

    # ==================== CENTRAL CARD DESIGN ====================

    def create_card_container(self):
        """Creates the main visual frame displaying the active Kanji card."""
        self.card_frame = tk.Frame(
            self.root, 
            bg=BG_INNER,
            pady=10,
            padx=15,
            highlightbackground=BORDER_COLOR,
            highlightcolor=BORDER_COLOR,
            highlightthickness=1
        )
        self.card_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        # LARGE Kanji visual display
        self.kanji_lbl = tk.Label(
            self.card_frame,
            text="漢",
            fg=ACCENT_CYAN,
            bg=BG_INNER,
            font=(FONT_FAMILY, 54, "bold"),
            cursor="hand2"
        )
        self.kanji_lbl.pack(pady=(0, 1))
        self.kanji_lbl.bind("<Button-1>", lambda e: self.hear_kanji_pronunciation())
        
        # Hiragana reading sub-label under the main Kanji title
        self.yomi_lbl = tk.Label(
            self.card_frame,
            text="かん",
            fg="#A0A0B0",
            bg=BG_INNER,
            font=(FONT_FAMILY, 11, "bold")
        )
        self.yomi_lbl.pack(pady=(0, 2))
        
        # Meaning translation
        self.meaning_lbl = tk.Label(
            self.card_frame,
            text="Chinese Character",
            fg=FG_LIGHT,
            bg=BG_INNER,
            font=(FONT_FAMILY, 11, "bold"),
            wraplength=240
        )
        self.meaning_lbl.pack(pady=1)
        
        # Readings panel
        readings_frame = tk.Frame(self.card_frame, bg=BG_INNER)
        readings_frame.pack(fill="x", pady=2)
        
        self.onyomi_lbl = tk.Label(
            readings_frame,
            text="音: カン",
            fg=ACCENT_ORANGE,
            bg=BG_INNER,
            font=(FONT_FAMILY, 8, "bold")
        )
        self.onyomi_lbl.pack(anchor="w")
        
        self.kunyomi_lbl = tk.Label(
            readings_frame,
            text="訓: おとこ",
            fg=ACCENT_GREEN,
            bg=BG_INNER,
            font=(FONT_FAMILY, 8, "bold")
        )
        self.kunyomi_lbl.pack(anchor="w")
        
        # Example sentence frame with horizontal refresher alignment
        example_frame = tk.Frame(self.card_frame, bg=BG_INNER)
        example_frame.pack(fill="x", pady=3)
        
        self.example_lbl = tk.Label(
            example_frame,
            text="漢字はとても面白いです。",
            fg=FG_LIGHT,
            bg=BG_INNER,
            font=(FONT_FAMILY, 9),
            wraplength=210,
            justify="center"
        )
        self.example_lbl.pack(side="left", fill="x", expand=True)
        
        refresh_btn = tk.Button(
            example_frame,
            text="↻",
            bg=BG_INNER,
            fg=ACCENT_CYAN,
            activebackground=HOVER_COLOR,
            activeforeground=FG_LIGHT,
            bd=0,
            font=(FONT_FAMILY, 11, "bold"),
            cursor="hand2",
            command=self.refresh_example_sentence
        )
        refresh_btn.pack(side="right", padx=2)
        self.bind_button_hover(refresh_btn, BG_INNER, HOVER_COLOR)
        
        self.example_en_lbl = tk.Label(
            self.card_frame,
            text="Kanji is very interesting.",
            fg="#A0A0B0",
            bg=BG_INNER,
            font=(FONT_FAMILY, 8, "italic"),
            wraplength=240,
            justify="center"
        )
        self.example_en_lbl.pack(pady=(0, 2))
        
        # Control Buttons inside card
        card_ctrl = tk.Frame(self.card_frame, bg=BG_INNER)
        card_ctrl.pack(fill="x", side="bottom")
        
        # Audio controls row
        audio_ctrl = tk.Frame(self.card_frame, bg=BG_INNER)
        audio_ctrl.pack(fill="x", side="bottom", pady=(4, 0))
        
        # Navigation Buttons: Prev and Next side-by-side
        self.prev_btn = tk.Button(
            card_ctrl,
            text="⬅️ PREV",
            bg=BG_CARD,
            fg=FG_LIGHT,
            activebackground=HOVER_COLOR,
            activeforeground=FG_LIGHT,
            bd=0,
            font=(FONT_FAMILY, 8, "bold"),
            pady=5,
            cursor="hand2",
            command=self.show_previous_card
        )
        self.prev_btn.pack(side="left", fill="x", expand=True, padx=(0, 2), pady=(2, 0))
        self.bind_button_hover(self.prev_btn, BG_CARD, HOVER_COLOR)
        
        self.next_btn = tk.Button(
            card_ctrl,
            text="🧠 NEW CARD",
            bg=ACCENT_CYAN,
            fg=FG_LIGHT,
            activebackground="#147ce5",
            activeforeground=FG_LIGHT,
            bd=0,
            font=(FONT_FAMILY, 8, "bold"),
            pady=5,
            cursor="hand2",
            command=self.fetch_new_card
        )
        self.next_btn.pack(side="right", fill="x", expand=True, padx=(2, 0), pady=(2, 0))
        self.bind_button_hover(self.next_btn, ACCENT_CYAN, "#147ce5")
        
        # Audio controls inside row
        self.slow_var = tk.BooleanVar(value=False)
        
        kanji_audio_btn = tk.Button(
            audio_ctrl,
            text="🔊 KANJI",
            bg=BG_CARD,
            fg=ACCENT_CYAN,
            activebackground=HOVER_COLOR,
            activeforeground=FG_LIGHT,
            bd=0,
            font=(FONT_FAMILY, 8, "bold"),
            pady=5,
            cursor="hand2",
            command=self.hear_kanji_pronunciation
        )
        kanji_audio_btn.pack(side="left", fill="x", expand=True, padx=1)
        self.bind_button_hover(kanji_audio_btn, BG_CARD, HOVER_COLOR)
        
        sentence_audio_btn = tk.Button(
            audio_ctrl,
            text="🔊 SENTENCE",
            bg=BG_CARD,
            fg=ACCENT_CYAN,
            activebackground=HOVER_COLOR,
            activeforeground=FG_LIGHT,
            bd=0,
            font=(FONT_FAMILY, 8, "bold"),
            pady=5,
            cursor="hand2",
            command=self.hear_sentence_pronunciation
        )
        sentence_audio_btn.pack(side="left", fill="x", expand=True, padx=1)
        self.bind_button_hover(sentence_audio_btn, BG_CARD, HOVER_COLOR)
        
        slow_chk = tk.Checkbutton(
            audio_ctrl,
            text="🐢 SLOW",
            variable=self.slow_var,
            bg=BG_INNER,
            fg=ACCENT_ORANGE,
            selectcolor=BG_CARD,
            activebackground=BG_INNER,
            activeforeground=ACCENT_ORANGE,
            font=(FONT_FAMILY, 7, "bold"),
            bd=0,
            highlightthickness=0
        )
        slow_chk.pack(side="right", padx=2)
        
        # Bind Romaji Hover Tooltips
        HoverTooltip(self.kanji_lbl, lambda: self.current_card.get("kanji_romaji", "") if self.current_card else "")
        HoverTooltip(self.yomi_lbl, lambda: self.current_card.get("kanji_romaji", "") if self.current_card else "")
        HoverTooltip(self.example_lbl, lambda: self.current_card.get("example_romaji", "") if self.current_card else "")
        HoverTooltip(self.onyomi_lbl, lambda: self.current_card.get("kanji_romaji", "") if self.current_card else "")
        HoverTooltip(self.kunyomi_lbl, lambda: self.current_card.get("kanji_romaji", "") if self.current_card else "")

    # ==================== OPTIONS FOOTER ====================

    def create_options_footer(self):
        """Creates the bottom settings tray for the popup interval and stats count."""
        footer = tk.Frame(self.root, bg=BG_DARK, pady=8, padx=15)
        footer.pack(fill="x", side="bottom")
        
        # Row 1: Quiz Toggle & Spinbox & Countdown
        ctrl_row = tk.Frame(footer, bg=BG_DARK)
        ctrl_row.pack(fill="x")
        
        quiz_chk = tk.Checkbutton(
            ctrl_row,
            text="Pop Quiz",
            variable=self.quiz_enabled,
            command=self.toggle_quiz_loop,
            bg=BG_DARK,
            fg=FG_LIGHT,
            selectcolor=BG_CARD,
            activebackground=BG_DARK,
            activeforeground=FG_LIGHT,
            font=(FONT_FAMILY, 8),
            bd=0,
            highlightthickness=0
        )
        quiz_chk.pack(side="left")
        
        # Spinbox label
        lbl = tk.Label(ctrl_row, text="every", bg=BG_DARK, fg="#A0A0B0", font=(FONT_FAMILY, 8))
        lbl.pack(side="left", padx=4)
        
        # Custom spinbox values
        self.interval_spin = ttk.Spinbox(
            ctrl_row,
            from_=1,
            to=60,
            width=3,
            font=(FONT_FAMILY, 8),
            command=self.update_interval
        )
        self.interval_spin.pack(side="left", padx=2)
        self.interval_spin.set(str(self.quiz_interval_min))
        
        lbl_min = tk.Label(ctrl_row, text="min", bg=BG_DARK, fg="#A0A0B0", font=(FONT_FAMILY, 8))
        lbl_min.pack(side="left", padx=2)
        
        # Live ticking countdown timer
        self.countdown_lbl = tk.Label(
            ctrl_row,
            text="Quiz in: 10:00",
            bg=BG_DARK,
            fg=ACCENT_GREEN,
            font=(FONT_FAMILY, 8, "bold")
        )
        self.countdown_lbl.pack(side="right", padx=5)
        
        # Row 2: Status Indicator
        self.status_lbl = tk.Label(
            footer,
            text="Studied: 0 Kanji | Accuracy: 0.0%",
            fg=ACCENT_ORANGE,
            bg=BG_DARK,
            font=(FONT_FAMILY, 7, "bold"),
            pady=4
        )
        self.status_lbl.pack(anchor="w")
        self.update_status_display()

    # ==================== DATA RETRIEVAL & PERSISTENCE ====================

    def load_initial_card(self):
        """Loads the first Kanji card on startup from history or fallback pool."""
        vocab = self.kanji_db.get("vocab", {})
        if vocab:
            # Load all previously studied cards in insertion order
            self.viewed_cards = list(vocab.values())
            self.current_view_idx = len(self.viewed_cards) - 1
            self.render_card(self.viewed_cards[self.current_view_idx])
        else:
            # Start with an enriched fallback card
            fallback_first = {
                "kanji": "日",
                "meaning": "day, sun, Japan",
                "onyomi": "ニチ, ジツ",
                "kunyomi": "ひ, び, か",
                "stroke_count": 4,
                "example_ja": "日本にいきたいです。",
                "example_en": "I want to go to Japan.",
                "kanji_yomi": "ひ",
                "kanji_romaji": "hi",
                "example_yomi": "にほん に いきたい です。",
                "example_romaji": "nihon ni ikitai desu."
            }
            self.viewed_cards = [fallback_first]
            self.current_view_idx = 0
            self.render_card(fallback_first)
            
            # Save it to studied list
            self.save_studied_card(fallback_first)

    def render_card(self, card_dict):
        """Pushes structured Kanji card contents directly onto the UI labels."""
        self.current_card = card_dict
        self.kanji_lbl.config(text=card_dict.get("kanji", ""))
        self.meaning_lbl.config(text=card_dict.get("meaning", ""))
        self.yomi_lbl.config(text=card_dict.get("kanji_yomi", ""))
        
        onyomi = card_dict.get("onyomi", "")
        onyomi_text = f"音: {onyomi}" if onyomi else "音: (なし)"
        self.onyomi_lbl.config(text=onyomi_text)
        
        kunyomi = card_dict.get("kunyomi", "")
        kunyomi_text = f"訓: {kunyomi}" if kunyomi else "訓: (なし)"
        self.kunyomi_lbl.config(text=kunyomi_text)
        
        self.example_lbl.config(text=card_dict.get("example_ja", ""))
        self.example_en_lbl.config(text=card_dict.get("example_en", ""))
        
        # Reset card glowing highlight on loaded card
        self.card_frame.config(highlightbackground=BORDER_COLOR, highlightcolor=BORDER_COLOR)
        
        # Update navigation buttons
        self.update_navigation_buttons()

    def fetch_new_card(self):
        """Swaps in the cached card instantly, or triggers a thread-based fetch if the cache is empty."""
        # If we are currently navigating previous cards in history, clicking next simply moves forward in history
        if self.current_view_idx < len(self.viewed_cards) - 1:
            self.current_view_idx += 1
            self.render_card(self.viewed_cards[self.current_view_idx])
            return

        if self.cached_next_card:
            new_card = self.cached_next_card
            self.cached_next_card = None
            self.on_fetch_success(new_card)
            return
            
        if self.api_in_progress:
            return
            
        self.api_in_progress = True
        self.next_btn.config(text="LOADING...", state="disabled")
        
        import threading
        def bg_fetch():
            api_key = self.config.get("gemini_api_key", "").strip()
            excluded = list(self.kanji_db.get("vocab", {}).keys())
            
            # Request card
            new_card = guardian.get_gemini_kanji_card(api_key, jlpt_level="N5", excluded_list=excluded)
            
            # Return to main Tkinter thread to display
            self.root.after(0, lambda: self.on_fetch_success(new_card))
            
        threading.Thread(target=bg_fetch, daemon=True).start()

    def on_fetch_success(self, new_card):
        """Displays and persists the successfully fetched Kanji card."""
        self.api_in_progress = False
        self.next_btn.config(text="🧠 NEW CARD", state="normal")
        
        # Append new card to viewed_cards list if not already present
        if new_card not in self.viewed_cards:
            self.viewed_cards.append(new_card)
        self.current_view_idx = len(self.viewed_cards) - 1
        
        self.render_card(new_card)
        self.save_studied_card(new_card)
        self.update_status_display()
        
        # Play small glowing border flash effect
        self.card_frame.config(highlightbackground=ACCENT_GREEN, highlightcolor=ACCENT_GREEN)
        self.root.after(1000, lambda: self.card_frame.config(highlightbackground=BORDER_COLOR, highlightcolor=BORDER_COLOR))
        
        # Pre-fetch the next card in the background immediately
        self.trigger_background_prefetch()

    def show_previous_card(self):
        """Displays the previously viewed card in this session."""
        if self.current_view_idx > 0:
            self.current_view_idx -= 1
            self.render_card(self.viewed_cards[self.current_view_idx])

    def update_navigation_buttons(self):
        """Updates the state and text of previous/next navigation buttons based on current navigation history."""
        # Enable previous button if we are not at the first card
        if self.current_view_idx > 0:
            self.prev_btn.config(state="normal", bg=BG_CARD)
        else:
            self.prev_btn.config(state="disabled", bg=BG_DARK)
            
        # Toggle next button between forward navigation and fetching a new card
        if self.current_view_idx < len(self.viewed_cards) - 1:
            self.next_btn.config(text="➡️ NEXT", bg=BG_CARD)
            self.bind_button_hover(self.next_btn, BG_CARD, HOVER_COLOR)
        else:
            self.next_btn.config(text="🧠 NEW CARD", bg=ACCENT_CYAN)
            self.bind_button_hover(self.next_btn, ACCENT_CYAN, "#147ce5")

    def trigger_background_prefetch(self):
        """Asynchronously pre-fetches the next Kanji card in the background to avoid user-perceived delays."""
        if self.cached_next_card or self.prefetch_in_progress:
            return
            
        self.prefetch_in_progress = True
        
        import threading
        def bg_prefetch():
            api_key = self.config.get("gemini_api_key", "").strip()
            excluded = list(self.kanji_db.get("vocab", {}).keys())
            if self.current_card and self.current_card.get("kanji") not in excluded:
                excluded.append(self.current_card.get("kanji"))
                
            new_card = guardian.get_gemini_kanji_card(api_key, jlpt_level="N5", excluded_list=excluded)
            self.root.after(0, lambda: self.on_prefetch_success(new_card))
            
        threading.Thread(target=bg_prefetch, daemon=True).start()

    def on_prefetch_success(self, new_card):
        self.cached_next_card = new_card
        self.prefetch_in_progress = False

    def save_studied_card(self, card_dict):
        """Saves or updates a studied card record into kanji_data.json."""
        kanji = card_dict.get("kanji")
        vocab = self.kanji_db.setdefault("vocab", {})
        
        if kanji not in vocab:
            vocab[kanji] = {
                "kanji": kanji,
                "meaning": card_dict.get("meaning"),
                "onyomi": card_dict.get("onyomi"),
                "kunyomi": card_dict.get("kunyomi"),
                "stroke_count": card_dict.get("stroke_count", 0),
                "example_ja": card_dict.get("example_ja"),
                "example_en": card_dict.get("example_en"),
                "kanji_yomi": card_dict.get("kanji_yomi"),
                "kanji_romaji": card_dict.get("kanji_romaji"),
                "example_yomi": card_dict.get("example_yomi"),
                "example_romaji": card_dict.get("example_romaji"),
                "level": "N5",
                "srs_stage": 1,
                "next_review": (datetime.now() + timedelta(days=1)).isoformat(),
                "history": []
            }
            guardian.save_kanji_data(self.kanji_db)

    def update_status_display(self):
        """Recalculates total studied cards and updates metrics in the footer."""
        vocab = self.kanji_db.get("vocab", {})
        stats = self.kanji_db.get("stats", {})
        
        count = len(vocab)
        reviewed = stats.get("total_reviewed", 0)
        correct = stats.get("total_correct", 0)
        
        pct = (correct / reviewed * 100.0) if reviewed > 0 else 0.0
        self.status_lbl.config(text=f"Studied: {count} Kanji  |  Quiz Accuracy: {pct:.1f}%")

    def hear_kanji_pronunciation(self):
        """Pronounces the active Kanji out loud using slow speed control if toggled."""
        kanji = ""
        if self.current_card:
            kanji = self.current_card.get("kanji_yomi", self.current_card.get("kanji", ""))
        if not kanji:
            try:
                kanji = self.kanji_lbl.cget("text").strip()
            except Exception:
                pass
        if kanji:
            guardian.speak_japanese_text(kanji, slow=self.slow_var.get())

    def hear_sentence_pronunciation(self):
        """Pronounces the active Japanese example sentence out loud using slow speed control if toggled."""
        example = ""
        if self.current_card:
            example = self.current_card.get("example_ja", "")
        if not example:
            try:
                example = self.example_lbl.cget("text").strip()
            except Exception:
                pass
        if example:
            guardian.speak_japanese_text(example, slow=self.slow_var.get())

    # ==================== POP-UP QUIZ SYSTEM ====================

    def schedule_next_quiz(self):
        """Registers a recurring .after timer to trigger the random Pop Quiz focus popups."""
        if self.quiz_timer_id is not None:
            self.root.after_cancel(self.quiz_timer_id)
            self.quiz_timer_id = None
            
        if self.quiz_enabled.get():
            interval_ms = self.quiz_interval_min * 60 * 1000
            self.quiz_target_time = datetime.now() + timedelta(minutes=self.quiz_interval_min)
            self.quiz_timer_id = self.root.after(interval_ms, self.trigger_pop_quiz)
        else:
            self.quiz_target_time = None

    def toggle_quiz_loop(self):
        """Enables/disables pop-up quiz scheduled reminders."""
        if self.quiz_enabled.get():
            self.schedule_next_quiz()
        else:
            if self.quiz_timer_id is not None:
                self.root.after_cancel(self.quiz_timer_id)
                self.quiz_timer_id = None
            self.quiz_target_time = None

    def update_interval(self):
        """Triggered when the spinbox value is changed to update the timer duration."""
        try:
            val = int(self.interval_spin.get())
            if 1 <= val <= 60:
                self.quiz_interval_min = val
                self.schedule_next_quiz()
        except ValueError:
            pass

    def update_countdown_ticking(self):
        """Ticking background loop to update the UI countdown indicator in the footer."""
        if self.quiz_enabled.get() and self.quiz_target_time:
            diff = self.quiz_target_time - datetime.now()
            seconds = int(diff.total_seconds())
            if seconds < 0:
                seconds = 0
            mins = seconds // 60
            secs = seconds % 60
            self.countdown_lbl.config(text=f"Quiz in: {mins:02d}:{secs:02d}", fg=ACCENT_GREEN)
        else:
            self.countdown_lbl.config(text="Quiz: Paused", fg=ACCENT_RED)
            
        # Run again in 1 second
        self.root.after(1000, self.update_countdown_ticking)

    def refresh_example_sentence(self):
        """Asynchronously pulls a new, unique Japanese example sentence for the current Kanji."""
        if not self.current_card or self.api_in_progress:
            return
            
        kanji = self.current_card.get("kanji")
        if not kanji:
            return
            
        self.api_in_progress = True
        self.status_lbl.config(text="REFRESHING SENTENCE...", fg=ACCENT_ORANGE)
        
        import threading
        def bg_refresh():
            api_key = self.config.get("gemini_api_key", "").strip()
            new_sentence = guardian.get_gemini_example_sentence(api_key, kanji)
            self.root.after(0, lambda: self.on_refresh_sentence_success(new_sentence))
            
        threading.Thread(target=bg_refresh, daemon=True).start()

    def on_refresh_sentence_success(self, new_sentence):
        """Saves and applies the updated example sentence to the UI and current active card."""
        self.api_in_progress = False
        self.update_status_display()
        
        if not self.current_card or not new_sentence:
            return
            
        # Update current card state
        self.current_card["example_ja"] = new_sentence.get("example_ja", "")
        self.current_card["example_en"] = new_sentence.get("example_en", "")
        self.current_card["example_yomi"] = new_sentence.get("example_yomi", "")
        self.current_card["example_romaji"] = new_sentence.get("example_romaji", "")
        
        # Re-render example sentence labels in UI
        self.example_lbl.config(text=self.current_card.get("example_ja", ""))
        self.example_en_lbl.config(text=self.current_card.get("example_en", ""))
        
        # Save updated card back into kanji_data.json if present in vocab
        vocab = self.kanji_db.get("vocab", {})
        kanji_key = self.current_card.get("kanji")
        if kanji_key in vocab:
            vocab[kanji_key]["example_ja"] = self.current_card["example_ja"]
            vocab[kanji_key]["example_en"] = self.current_card["example_en"]
            vocab[kanji_key]["example_yomi"] = self.current_card["example_yomi"]
            vocab[kanji_key]["example_romaji"] = self.current_card["example_romaji"]
            guardian.save_kanji_data(self.kanji_db)
            
        # Play small glowing border flash effect
        self.card_frame.config(highlightbackground=ACCENT_CYAN, highlightcolor=ACCENT_CYAN)
        self.root.after(1000, lambda: self.card_frame.config(highlightbackground=BORDER_COLOR, highlightcolor=BORDER_COLOR))

    def trigger_pop_quiz(self):
        """Interrupts desktop actions, grabs system focus, and prompts a Kanji review multiple-choice pop-up."""
        # Reschedule next popup first
        self.schedule_next_quiz()
        
        # Ensure we have cards to quiz
        vocab_pool = list(self.kanji_db.get("vocab", {}).values())
        
        # If studied pool is too empty, mix in fallback cards to ensure distractor variety
        fallback_pool = [
            {"kanji": "日", "meaning": "day, sun, Japan", "kanji_romaji": "hi", "kanji_yomi": "ひ"},
            {"kanji": "本", "meaning": "book, origin, main", "kanji_romaji": "hon", "kanji_yomi": "ほん"},
            {"kanji": "人", "meaning": "person, human", "kanji_romaji": "hito", "kanji_yomi": "ひと"},
            {"kanji": "学", "meaning": "study, learning, science", "kanji_romaji": "manabu", "kanji_yomi": "まなぶ"},
            {"kanji": "生", "meaning": "life, birth, genuine", "kanji_romaji": "nama", "kanji_yomi": "なま"},
            {"kanji": "先", "meaning": "ahead, previous, future", "kanji_romaji": "saki", "kanji_yomi": "さき"},
            {"kanji": "国", "meaning": "country", "kanji_romaji": "kuni", "kanji_yomi": "くに"},
            {"kanji": "車", "meaning": "car, vehicle, wheel", "kanji_romaji": "kuruma", "kanji_yomi": "くるま"},
            {"kanji": "水", "meaning": "water", "kanji_romaji": "mizu", "kanji_yomi": "みず"},
            {"kanji": "金", "meaning": "gold, money", "kanji_romaji": "kane", "kanji_yomi": "かね"},
            {"kanji": "子", "meaning": "child, young", "kanji_romaji": "ko", "kanji_yomi": "こ"},
            {"kanji": "大", "meaning": "large, big, grand", "kanji_romaji": "ookii", "kanji_yomi": "おおきい"},
            {"kanji": "中", "meaning": "in, inside, middle", "kanji_romaji": "naka", "kanji_yomi": "なか"},
            {"kanji": "小", "meaning": "small, little", "kanji_romaji": "chiisai", "kanji_yomi": "ちいさい"},
            {"kanji": "何", "meaning": "what", "kanji_romaji": "nani", "kanji_yomi": "なに"}
        ]
        
        # Pick target question
        if vocab_pool:
            target = random.choice(vocab_pool)
        else:
            target = random.choice(fallback_pool)
            
        # Select distractor pools
        all_others = [c for c in fallback_pool if c["kanji"] != target["kanji"]]
        if vocab_pool:
            all_others += [c for c in vocab_pool if c["kanji"] != target["kanji"]]
            
        random.shuffle(all_others)
        distractors = all_others[:3]
        
        # Multiple choices (distractors + target)
        choices = [target] + distractors
        random.shuffle(choices)
        
        # Spawn Topmost Modal Question grab window
        quiz_win = tk.Toplevel(self.root)
        quiz_win.title("⚡ KANJI POP QUIZ!")
        quiz_win.configure(bg=BG_DARK)
        quiz_win.geometry("320x360")
        quiz_win.resizable(False, False)
        quiz_win.attributes("-topmost", True)
        
        # Steal and force desktop active focus
        quiz_win.focus_force()
        
        # Center popup on screen
        sw = quiz_win.winfo_screenwidth()
        sh = quiz_win.winfo_screenheight()
        qx = (sw - 320) // 2
        qy = (sh - 360) // 2
        quiz_win.geometry(f"+{qx}+{qy}")
        
        # Question Header
        tk.Label(
            quiz_win,
            text="⚡  RAPID POP QUIZ  ⚡",
            fg=ACCENT_ORANGE,
            bg=BG_DARK,
            font=(FONT_FAMILY, 10, "bold"),
            pady=12
        ).pack()
        
        # Big Kanji question
        q_kanji_lbl = tk.Label(
            quiz_win,
            text=target["kanji"],
            fg=ACCENT_CYAN,
            bg=BG_DARK,
            font=(FONT_FAMILY, 48, "bold")
        )
        q_kanji_lbl.pack(pady=2)
        
        # Bind hover tooltip to the pop-up quiz Kanji label
        HoverTooltip(q_kanji_lbl, lambda: target.get("kanji_romaji", ""))
        
        tk.Label(
            quiz_win,
            text="What is the correct meaning of this Kanji?",
            fg=FG_LIGHT,
            bg=BG_DARK,
            font=(FONT_FAMILY, 9),
            pady=8
        ).pack()
        
        # Pronounce target voice helper in background
        guardian.speak_japanese_text(target.get("kanji_yomi", target.get("kanji", "")) if target else "")
        
        def select_option(selected_card):
            # Evaluate answer
            correct = (selected_card["kanji"] == target["kanji"])
            
            # Save history & statistics
            stats = self.kanji_db.setdefault("stats", {"total_reviewed": 0, "total_correct": 0})
            stats["total_reviewed"] += 1
            if correct:
                stats["total_correct"] += 1
                
            # If target belongs to studied database, update SRS stage
            kanji_key = target["kanji"]
            vocab = self.kanji_db.get("vocab", {})
            if kanji_key in vocab:
                vocab[kanji_key]["history"].append({
                    "date": datetime.now().isoformat(),
                    "correct": correct
                })
                if correct:
                    vocab[kanji_key]["srs_stage"] = min(5, vocab[kanji_key].get("srs_stage", 1) + 1)
                    # Next review scheduled further
                    days_delay = [1, 2, 4, 7, 14, 30][vocab[kanji_key]["srs_stage"]]
                    vocab[kanji_key]["next_review"] = (datetime.now() + timedelta(days=days_delay)).isoformat()
                else:
                    vocab[kanji_key]["srs_stage"] = 1 # reset SRS
                    vocab[kanji_key]["next_review"] = (datetime.now() + timedelta(days=1)).isoformat()
                    
            guardian.save_kanji_data(self.kanji_db)
            self.update_status_display()
            
            # Audio response + popup feedback alert
            if correct:
                guardian.speak_japanese_text("せいかい！ 正解") # Speak "Correct!"
                messagebox.showinfo("🎉 CORRECT!", f"Excellent work!\n\n'{target['kanji']}' indeed means '{target['meaning']}'!", parent=quiz_win)
            else:
                guardian.speak_japanese_text("まちがい！ 間違い") # Speak "Mistake!"
                messagebox.showerror("❌ INCORRECT", f"Ah, not quite!\n\n'{target['kanji']}' means '{target['meaning']}'!", parent=quiz_win)
                
            # Destroy question frame
            quiz_win.destroy()
            
        # Draw choices as large clickable cards
        for idx, card in enumerate(choices):
            btn = tk.Button(
                quiz_win,
                text=card["meaning"],
                bg=BG_CARD,
                fg=FG_LIGHT,
                activebackground=ACCENT_CYAN,
                activeforeground=FG_LIGHT,
                bd=0,
                relief="flat",
                font=(FONT_FAMILY, 9, "bold"),
                pady=6,
                cursor="hand2",
                command=lambda c=card: select_option(c)
            )
            btn.pack(fill="x", padx=25, pady=4)
            self.bind_button_hover(btn, BG_CARD, HOVER_COLOR)
            
            # Bind tooltip to the option choice button to show Romaji
            HoverTooltip(btn, lambda c=card: f"{c.get('kanji_romaji', '')} ({c.get('kanji_yomi', '')})" if c.get('kanji_romaji') else "")

    # ==================== GUI HOVER BIND HELPMATES ====================

    def bind_button_hover(self, button, bg_normal, bg_hover):
        def enter(e):
            if button.cget('state') != 'disabled':
                button.config(bg=bg_hover)
        def leave(e):
            if button.cget('state') != 'disabled':
                button.config(bg=bg_normal)
        button.bind("<Enter>", enter)
        button.bind("<Leave>", leave)

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = KanjiWidget(root)
        root.mainloop()
    except Exception as e:
        # Graceful diagnostic terminal log
        print(f"Kanji widget crash: {e}")
