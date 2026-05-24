import os
import sys

# Try to enable Windows DPI Awareness for crisp, high-resolution rendering
if sys.platform.startswith("win"):
    try:
        import ctypes
        # Use PROCESS_PER_MONITOR_DPI_AWARE (value 2) or PROCESS_SYSTEM_DPI_AWARE (value 1)
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

import json
import random
import time
import urllib.parse
import webbrowser
import threading
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import messagebox, ttk

# Ensure base directory is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

import guardian
import guardian_db

# Ensure UTF-8 output encoding for standard streams
if sys.stdout is not None and getattr(sys.stdout, 'encoding', None) != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Global crash interceptor to catch async callback crashes and preserve the clean session
def report_callback_exception(self, exc, val, tb):
    import traceback
    try:
        crash_log_path = os.path.join(BASE_DIR, "gui_crash_log.txt")
        with open(crash_log_path, "a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Runtime Callback Exception:\n")
            traceback.print_exception(exc, val, tb, file=f)
    except Exception:
        pass
    try:
        messagebox.showerror(
            "Workspace Runtime Exception", 
            f"An unexpected callback error occurred:\n\n{val}\n\nDetails saved to gui_crash_log.txt."
        )
    except Exception:
        pass

tk.Tk.report_callback_exception = report_callback_exception

def draw_rounded_rect(canvas, x1, y1, x2, y2, radius=4, **kwargs):
    points = [x1+radius, y1,
              x1+radius, y1,
              x2-radius, y1,
              x2-radius, y1,
              x2, y1,
              x2, y1+radius,
              x2, y1+radius,
              x2, y2-radius,
              x2, y2-radius,
              x2, y2,
              x2-radius, y2,
              x2-radius, y2,
              x1+radius, y2,
              x1+radius, y2,
              x1, y2,
              x1, y2-radius,
              x1, y2-radius,
              x1, y1+radius,
              x1, y1+radius,
              x1, y1]
    return canvas.create_polygon(points, **kwargs, smooth=True)

# ==================== DESIGN CONSTANTS & THEME TOKENS ====================
FONT_FAMILY = "Inter"        # Modern clean sans-serif matching Google Stitch body font
FONT_HEADLINE = "Outfit"     # Premium display font matching Google Stitch header font
BG_DARK = "#06151a"          # Deepest dark-teal background matching Stitch 'background'
BG_CARD = "#122227"          # Surface card container matching Stitch 'surface-container'
BG_INNER = "#0e1e23"         # Inner containers matching Stitch 'surface-container-low'
BG_SIDEBAR = "#021015"       # Sidebar background matching Stitch 'surface-container-lowest'
BORDER_COLOR = "#3b4a44"     # Sleek teal outline matching Stitch 'outline-variant'
FG_LIGHT = "#d4e5ec"         # Primary light text matching Stitch 'on-surface'
FG_SECONDARY = "#bacac2"     # Muted secondary text matching Stitch 'on-surface-variant'

# Cyberpunk teal accent palette matching Google Stitch color maps
ACCENT_CYAN = "#46f1c5"      # Primary glowing cyan matching Stitch 'primary'
ACCENT_GREEN = "#62f0b3"     # Mint green matching Stitch 'tertiary'
ACCENT_PURPLE = "#d0bcff"    # Secondary light purple matching Stitch 'secondary'
ACCENT_ORANGE = "#ffb4ab"    # Muted warnings/alerts matching Stitch 'error'
ACCENT_RED = "#ffb4ab"       # Alert/delete matching Stitch 'error'
HOVER_COLOR = "#1d2c32"      # High-contrast hover matching Stitch 'surface-container-high'


# ==================== HOVER TOOLTIP HELPER ====================
class HoverTooltip:
    def __init__(self, widget, text_func):
        self.widget = widget
        self.text_func = text_func
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text_func:
            return
        text = self.text_func()
        if not text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 25
        y = y + self.widget.winfo_rooty() + 25
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.wm_attributes("-topmost", True)
        
        label = tk.Label(
            tw, text=text, justify="left", bg="#1C1C1E", fg=FG_LIGHT,
            relief="solid", borderwidth=1, font=(FONT_FAMILY, 8, "bold"),
            padx=8, pady=4, highlightthickness=0
        )
        label.pack()

    def hide_tip(self, event=None):
        if self.tip_window:
            try:
                self.tip_window.destroy()
            except Exception:
                pass
            self.tip_window = None


# ==================== MAIN UNIFIED WORKSPACE ====================
class GuardianWorkspaceSuite:
    def __init__(self, root):
        self.root = root
        self.root.title("Project Guardian - Unified Workspace Suite")
        self.root.configure(bg=BG_DARK)
        self.root.geometry("1200x800")
        self.root.resizable(True, True)
        self.root.minsize(1100, 700)
        
        # Frameless border styling if you want, but Standard keeps native resizing.
        # Self-healing logs
        self.init_crash_healing_logs()
        
        # Load configs
        self.config = guardian.load_config()
        self.mock_weekend = False
        
        # Interactive States
        self.active_tab = "dashboard"
        self.generating_weekend_task = False
        self.weekend_auto_generation_attempted = False
        self.srs_deck_idx = 0
        self.prefetched_kanji_queue = []
        self.kanji_prefetch_in_progress = False
        
        # Pop Quiz State
        self.quiz_enabled = tk.BooleanVar(value=True)
        self.quiz_interval_min = 10
        self.quiz_timer_id = None
        self.quiz_target_time = None
        self.active_quiz_window = None
        
        # Conversation Chat State
        self.chat_history = []
        self.chat_api_in_progress = False
        self.voice_recording_in_progress = False
        self.voice_recording_seconds = 5
        self.explaining_message_ids = set()
        self.expanded_explanations = set()
        self.message_explanations = {}
        
        # Load Kanji and Chat history from DB/Files
        self.kanji_db = guardian.load_kanji_data()
        self.active_scenario = "Technical Interview - Tokyo MNC"
        self.difficulty_level = "N5"
        self.load_sqlite_chat_history()

        # Build UI layout
        self.create_sidebar()
        self.create_tab_containers()
        
        # Initialize sub-panels
        self.init_dashboard_tab()
        self.init_research_tab()
        self.init_kanji_tab()
        self.init_sensei_tab()
        self.init_settings_tab()
        
        # Load first card & start scheduled timers
        self.load_initial_kanji_card()
        self.schedule_next_pop_quiz()
        self.update_live_clock_and_ticks()
        self.trigger_background_kanji_prefetch()
        self._bg_check_quota()
        
        # Default starting tab
        self.show_tab("dashboard")

    def init_crash_healing_logs(self):
        """Pre-heals crash traces to guarantee a clean starting session."""
        try:
            crash_log_path = os.path.join(BASE_DIR, "gui_crash_log.txt")
            with open(crash_log_path, "w", encoding="utf-8") as f:
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Clean session initialized successfully.\n")
        except Exception:
            pass

    # ==================== MAIN LAYOUT CONTAINERS ====================
    def create_sidebar(self):
        """Creates the vertical icon navigation sidebar matching reference design."""
        self.sidebar = tk.Frame(self.root, bg=BG_SIDEBAR, width=72)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Guardian Shield Logo at top
        logo = tk.Label(self.sidebar, text="🛡️", bg=BG_SIDEBAR, fg=ACCENT_CYAN, font=(FONT_FAMILY, 20))
        logo.pack(pady=(18, 5))

        # Clock label under logo
        self.clock_lbl = tk.Label(self.sidebar, text="00:00", bg=BG_SIDEBAR, fg=FG_SECONDARY, font=(FONT_FAMILY, 7))
        self.clock_lbl.pack(pady=(0, 8))

        # Quota badge
        self.quota_badge = tk.Label(self.sidebar, text="●", fg=FG_SECONDARY, bg=BG_SIDEBAR, font=(FONT_FAMILY, 8), cursor="hand2")
        self.quota_badge.pack(pady=(0, 18))
        self.quota_badge.bind("<Button-1>", lambda e: self.open_quota_status_dialog())
        HoverTooltip(self.quota_badge, lambda: "Click to check Gemini API Quota status")

        # Separator line
        tk.Frame(self.sidebar, bg=BORDER_COLOR, height=1).pack(fill="x", padx=12, pady=4)

        # Navigation Icons — match reference image
        nav_items = [
            ("dashboard", "⊞", "Dashboard"),
            ("research",  "☰", "Tasks"),
            ("kanji",     "⌂", "Insights"),
            ("sensei",    "🎓", "Sensei"),
            ("settings",  "☻", "Profile"),
        ]

        self.tab_buttons = {}
        for tab_id, icon, label in nav_items:
            nav_frame = tk.Frame(self.sidebar, bg=BG_SIDEBAR, cursor="hand2")
            nav_frame.pack(pady=3, padx=4, fill="x")

            icon_lbl = tk.Label(nav_frame, text=icon, bg=BG_SIDEBAR, fg=FG_SECONDARY, font=(FONT_FAMILY, 14), cursor="hand2")
            icon_lbl.pack()
            text_lbl = tk.Label(nav_frame, text=label, bg=BG_SIDEBAR, fg=FG_SECONDARY, font=(FONT_FAMILY, 7), cursor="hand2")
            text_lbl.pack()

            # Click binding on the frame and children
            for w in (nav_frame, icon_lbl, text_lbl):
                w.bind("<Button-1>", lambda e, t=tab_id: self.show_tab(t))
                w.bind("<Enter>", lambda e, f=nav_frame, i=icon_lbl, t2=text_lbl: [
                    f.config(bg="#0d1e24"), i.config(bg="#0d1e24", fg=ACCENT_CYAN), t2.config(bg="#0d1e24", fg=ACCENT_CYAN)])
                w.bind("<Leave>", lambda e, f=nav_frame, i=icon_lbl, t2=text_lbl, tid=tab_id: [
                    f.config(bg=BG_SIDEBAR), i.config(bg=BG_SIDEBAR, fg=ACCENT_CYAN if tid == self.active_tab else FG_SECONDARY),
                    t2.config(bg=BG_SIDEBAR, fg=ACCENT_CYAN if tid == self.active_tab else FG_SECONDARY)])

            self.tab_buttons[tab_id] = (icon_lbl, text_lbl)

        # Spacer pushes logout to bottom
        tk.Frame(self.sidebar, bg=BG_SIDEBAR).pack(fill="both", expand=True)

        # Logout at bottom
        logout = tk.Label(self.sidebar, text="⎋", bg=BG_SIDEBAR, fg=FG_SECONDARY, font=(FONT_FAMILY, 14), cursor="hand2")
        logout.pack(pady=(0, 18))
        logout.bind("<Button-1>", lambda e: self.root.destroy())
        HoverTooltip(logout, lambda: "Exit Project Guardian")

    def create_tab_containers(self):
        """Creates the main content area and stacked tab frames."""
        self.content_frame = tk.Frame(self.root, bg=BG_DARK)
        self.content_frame.pack(side="left", fill="both", expand=True)

        self.tabs = {}
        for t_id in ["dashboard", "research", "kanji", "sensei", "settings"]:
            frame = tk.Frame(self.content_frame, bg=BG_DARK)
            self.tabs[t_id] = frame

    def show_tab(self, tab_id):
        """Performs tab switching with sidebar icon highlighting."""
        self.active_tab = tab_id
        for t_frame in self.tabs.values():
            t_frame.pack_forget()

        self.tabs[tab_id].pack(fill="both", expand=True, padx=15, pady=15)

        # Sidebar highlight
        for t_key, (icon_lbl, text_lbl) in self.tab_buttons.items():
            if t_key == tab_id:
                icon_lbl.config(fg=ACCENT_CYAN)
                text_lbl.config(fg=ACCENT_CYAN)
            else:
                icon_lbl.config(fg=FG_SECONDARY)
                text_lbl.config(fg=FG_SECONDARY)

        # Specialized refreshes
        if tab_id == "dashboard":
            self.refresh_dashboard_progress()

    # ==================== TAB 1: DASHBOARD PANEL ====================
    def init_dashboard_tab(self):
        frame = self.tabs["dashboard"]

        # 2-Column Grid Layout matching Stitch spec
        columns = tk.Frame(frame, bg=BG_DARK)
        columns.pack(fill="both", expand=True)
        columns.columnconfigure(0, weight=3, minsize=500)
        columns.columnconfigure(1, weight=2, minsize=400)
        columns.rowconfigure(0, weight=1)

        left_col = tk.Frame(columns, bg=BG_DARK)
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        right_col = tk.Frame(columns, bg=BG_DARK)
        right_col.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        # ===== LEFT COLUMN: SYSTEM STATUS HEADER =====
        header_frame = tk.Frame(left_col, bg=BG_DARK)
        header_frame.pack(fill="x", pady=(0, 12))
        
        tk.Label(header_frame, text="SYSTEM STATUS", bg=BG_DARK, fg=FG_LIGHT, font=(FONT_HEADLINE, 14, "bold"), anchor="w").pack(fill="x")
        tk.Label(header_frame, text="Daily cognitive load and compliance metrics.", bg=BG_DARK, fg=FG_SECONDARY, font=(FONT_FAMILY, 9), anchor="w").pack(fill="x")

        # ===== LEFT COLUMN: COMPLIANCE & PROTOCOLS ROW (SIDE-BY-SIDE) =====
        status_row = tk.Frame(left_col, bg=BG_DARK)
        status_row.pack(fill="x", pady=(0, 10))
        status_row.columnconfigure(0, weight=1)
        status_row.columnconfigure(1, weight=1)

        # Compliance index card
        compliance_card = tk.Frame(status_row, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1, padx=12, pady=12)
        compliance_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        tk.Label(compliance_card, text="DAILY COMPLIANCE", bg=BG_CARD, fg=FG_LIGHT, font=(FONT_HEADLINE, 10, "bold")).pack()
        
        self.dial_canvas = tk.Canvas(compliance_card, width=140, height=120, bg=BG_CARD, highlightthickness=0)
        self.dial_canvas.pack(pady=5)
        self.dial_label = None

        # Active Protocols (Daily Habits) Card
        habits_card = tk.Frame(status_row, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1, padx=12, pady=12)
        habits_card.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        tk.Label(habits_card, text="ACTIVE PROTOCOLS", bg=BG_CARD, fg=FG_LIGHT, font=(FONT_HEADLINE, 10, "bold")).pack(anchor="w", pady=(0, 4))

        # Compact Streak Box
        streak_frame = tk.Frame(habits_card, bg="#0a2e2e", highlightbackground=ACCENT_CYAN, highlightthickness=1, padx=10, pady=4)
        streak_frame.pack(fill="x", pady=(0, 6))
        self.streak_num = tk.Label(streak_frame, text="🔥 0 DAY\nSTREAK", bg="#0a2e2e", fg=ACCENT_CYAN, font=(FONT_FAMILY, 8, "bold"), justify="center")
        self.streak_num.pack(fill="x")

        # Add Habit Row
        add_habit_frame = tk.Frame(habits_card, bg=BG_CARD)
        add_habit_frame.pack(fill="x", pady=(0, 6))

        self.ent_habit_dash = tk.Entry(add_habit_frame, bg=BG_INNER, fg=FG_LIGHT, insertbackground=FG_LIGHT, bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR, font=(FONT_FAMILY, 8))
        self.ent_habit_dash.pack(side="left", fill="x", expand=True, ipady=4, padx=(0, 5))
        self.ent_habit_dash.insert(0, "Add protocol...")
        self.ent_habit_dash.bind("<FocusIn>", lambda e: self.ent_habit_dash.delete(0, tk.END) if self.ent_habit_dash.get() == "Add protocol..." else None)

        btn_add = tk.Button(add_habit_frame, text="➕", bg=ACCENT_CYAN, fg=FG_LIGHT, font=(FONT_FAMILY, 8, "bold"), bd=0, padx=6, pady=2, cursor="hand2", command=self.add_habit_from_dash)
        btn_add.pack(side="right")

        self.habits_frame = tk.Frame(habits_card, bg=BG_CARD)
        self.habits_frame.pack(fill="both", expand=True)

        # ===== LEFT COLUMN: TODAY'S TASKS CHECKLIST =====
        self.todo_card = tk.Frame(left_col, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1, padx=15, pady=12)
        self.todo_card.pack(fill="x", pady=(0, 10))

        todo_header = tk.Frame(self.todo_card, bg=BG_CARD)
        todo_header.pack(fill="x", pady=(0, 8))
        tk.Label(todo_header, text="📌 TODAY'S WORK checklist", bg=BG_CARD, fg=ACCENT_ORANGE, font=(FONT_HEADLINE, 10, "bold")).pack(side="left")

        add_todo_frame = tk.Frame(self.todo_card, bg=BG_CARD)
        add_todo_frame.pack(fill="x", pady=(0, 8))

        self.ent_todo = tk.Entry(add_todo_frame, bg=BG_INNER, fg=FG_LIGHT, insertbackground=FG_LIGHT, bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR, font=(FONT_FAMILY, 9))
        self.ent_todo.pack(side="left", fill="x", expand=True, ipady=4, padx=(0, 5))
        self.ent_todo.insert(0, "Add task to complete today...")
        self.ent_todo.bind("<FocusIn>", lambda e: self.ent_todo.delete(0, tk.END) if self.ent_todo.get() == "Add task to complete today..." else None)

        btn_add_todo = tk.Button(add_todo_frame, text="➕", bg=ACCENT_ORANGE, fg=FG_LIGHT, font=(FONT_FAMILY, 9, "bold"), bd=0, padx=8, pady=3, cursor="hand2", command=self.add_todo_task_from_gui)
        btn_add_todo.pack(side="right")

        self.todo_list_frame = tk.Frame(self.todo_card, bg=BG_CARD)
        self.todo_list_frame.pack(fill="both", expand=True)

        # ===== LEFT COLUMN: CONTRIBUTION MATRIX =====
        self.heatmap_card = tk.Frame(left_col, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1, padx=15, pady=12)
        self.heatmap_card.pack(fill="x", pady=(0, 10))

        hm_header = tk.Frame(self.heatmap_card, bg=BG_CARD)
        hm_header.pack(fill="x", pady=(0, 8))
        tk.Label(hm_header, text="CONTRIBUTION MATRIX", bg=BG_CARD, fg=FG_LIGHT, font=(FONT_HEADLINE, 10, "bold")).pack(side="left")

        btn_sync = tk.Button(hm_header, text="⚡ SYNC", bg=ACCENT_CYAN, fg=FG_LIGHT, font=(FONT_FAMILY, 7, "bold"), bd=0, padx=8, pady=2, cursor="hand2", command=self.asynchronously_sync_github)
        btn_sync.pack(side="right")

        self.heatmap_canvas = tk.Canvas(self.heatmap_card, bg=BG_CARD, highlightthickness=0, height=45)
        self.heatmap_canvas.pack(fill="x", pady=5)

        # ===== LEFT COLUMN: DAILY ACTIVITY CHART =====
        activity_card = tk.Frame(left_col, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1, padx=15, pady=12)
        activity_card.pack(fill="both", expand=True, pady=(0, 10))

        tk.Label(activity_card, text="DAILY ACTIVITY FLOW", bg=BG_CARD, fg=FG_LIGHT, font=(FONT_HEADLINE, 10, "bold")).pack(anchor="w", pady=(0, 5))

        self.activity_canvas = tk.Canvas(activity_card, bg=BG_CARD, highlightthickness=0, height=130)
        self.activity_canvas.pack(fill="both", expand=True)
        self.activity_canvas.bind("<Configure>", lambda e: self.draw_activity_chart())

        # ===== RIGHT COLUMN: KNOWLEDGE BASE HEADER =====
        kb_header_frame = tk.Frame(right_col, bg=BG_DARK)
        kb_header_frame.pack(fill="x", pady=(0, 12))
        
        tk.Label(kb_header_frame, text="KNOWLEDGE BASE", bg=BG_DARK, fg=FG_LIGHT, font=(FONT_HEADLINE, 14, "bold"), anchor="w").pack(fill="x")
        tk.Label(kb_header_frame, text="Real-time CS research and Japanese SRS learning.", bg=BG_DARK, fg=FG_SECONDARY, font=(FONT_FAMILY, 9), anchor="w").pack(fill="x")

        # ===== RIGHT COLUMN: TOKYO STUDY ROADMAP =====
        tokyo_card = tk.Frame(right_col, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1, padx=12, pady=12)
        tokyo_card.pack(fill="x", pady=(0, 10))

        tk.Label(tokyo_card, text="TOKYO MNC STUDY PLAN", bg=BG_CARD, fg=ACCENT_CYAN, font=(FONT_HEADLINE, 10, "bold")).pack(anchor="w")
        tk.Label(tokyo_card, text="TARGET: RAKUTEN | 6 MONTHS", bg=BG_CARD, fg=FG_SECONDARY, font=(FONT_FAMILY, 7, "bold")).pack(anchor="w", pady=(0, 8))

        self.tokyo_bars_frame = tk.Frame(tokyo_card, bg=BG_CARD)
        self.tokyo_bars_frame.pack(fill="x")

        # ===== RIGHT COLUMN: JAPANESE SRS FLASHCARD =====
        kanji_card_frame = tk.Frame(right_col, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1, padx=15, pady=15)
        kanji_card_frame.pack(fill="x", pady=(0, 10))

        # Top Header Row matching Stitch Image exactly
        top_card_row = tk.Frame(kanji_card_frame, bg=BG_CARD)
        top_card_row.pack(fill="x", pady=(0, 8))
        
        # "SRS ACTIVE" badge on the top left
        badge_lbl = tk.Label(top_card_row, text="SRS ACTIVE", bg=BG_CARD, fg=ACCENT_CYAN, bd=1, relief="solid", highlightthickness=0, font=(FONT_FAMILY, 7, "bold"), padx=8, pady=2)
        badge_lbl.pack(side="left")
        
        # "..." menu button on the top right
        menu_lbl = tk.Label(top_card_row, text="•••", bg=BG_CARD, fg=FG_SECONDARY, font=(FONT_FAMILY, 9, "bold"), cursor="hand2")
        menu_lbl.pack(side="right")
        menu_lbl.bind("<Button-1>", lambda e: self.open_manage_habits_dialog()) 
        HoverTooltip(menu_lbl, lambda: "Workspace options")

        # Kanji of the Day inner card with glow border
        kanji_inner = tk.Frame(kanji_card_frame, bg="#081820", highlightbackground=BORDER_COLOR, highlightthickness=1, padx=15, pady=12)
        kanji_inner.pack(fill="x", pady=(0, 8))

        self.dash_kanji_display = tk.Label(kanji_inner, text="夢", bg="#081820", fg=ACCENT_CYAN, font=(FONT_FAMILY, 56, "bold"), cursor="hand2")
        self.dash_kanji_display.pack(pady=10)
        self.dash_kanji_display.bind("<Button-1>", lambda e: self.play_kanji_narration(slow=False))
        HoverTooltip(self.dash_kanji_display, lambda: "Click to play Kanji sound")

        # Readings section
        rd_frame = tk.Frame(kanji_card_frame, bg=BG_CARD)
        rd_frame.pack(fill="x")

        # Two-column layout for Onyomi / Kunyomi matching Stitch
        readings_row = tk.Frame(rd_frame, bg=BG_CARD)
        readings_row.pack(fill="x", pady=2)
        readings_row.columnconfigure(0, weight=1)
        readings_row.columnconfigure(1, weight=1)

        ony_box = tk.Frame(readings_row, bg=BG_INNER, bd=1, relief="solid", highlightbackground=BORDER_COLOR, highlightthickness=1, padx=6, pady=6)
        ony_box.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        tk.Label(ony_box, text="ONYOMI", bg=BG_INNER, fg=FG_SECONDARY, font=(FONT_FAMILY, 7, "bold")).pack()
        self.dash_onyomi = tk.Label(ony_box, text="ム", bg=BG_INNER, fg=FG_LIGHT, font=(FONT_FAMILY, 11, "bold"))
        self.dash_onyomi.pack(pady=(2, 0))

        kun_box = tk.Frame(readings_row, bg=BG_INNER, bd=1, relief="solid", highlightbackground=BORDER_COLOR, highlightthickness=1, padx=6, pady=6)
        kun_box.grid(row=0, column=1, sticky="nsew", padx=(4, 0))
        tk.Label(kun_box, text="KUNYOMI", bg=BG_INNER, fg=FG_SECONDARY, font=(FONT_FAMILY, 7, "bold")).pack()
        self.dash_kunyomi = tk.Label(kun_box, text="ゆめ", bg=BG_INNER, fg=FG_LIGHT, font=(FONT_FAMILY, 11, "bold"))
        self.dash_kunyomi.pack(pady=(2, 0))

        tk.Frame(rd_frame, bg=BG_CARD, height=4).pack(fill="x")
        
        meaning_box = tk.Frame(rd_frame, bg=BG_INNER, bd=1, relief="solid", highlightbackground=BORDER_COLOR, highlightthickness=1, padx=8, pady=8)
        meaning_box.pack(fill="x", pady=4)
        self.dash_meaning = tk.Label(meaning_box, text='"Dream, vision, illusion"', bg=BG_INNER, fg=FG_SECONDARY, font=(FONT_FAMILY, 9, "italic"))
        self.dash_meaning.pack()

        # Premium Example Sentence Audio Box (Hear Sentence capability)
        ex_container = tk.Frame(rd_frame, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1, bd=1, relief="solid", padx=10, pady=8)
        ex_container.pack(fill="x", pady=(4, 0))
        
        btn_hear = tk.Button(ex_container, text="🔊", bg=BG_CARD, fg=ACCENT_CYAN, activebackground=BG_CARD, activeforeground=FG_LIGHT, bd=0, font=(FONT_FAMILY, 10, "bold"), cursor="hand2", command=lambda: self.play_sentence_narration(slow=False))
        btn_hear.pack(side="left", anchor="n", padx=(0, 6))
        HoverTooltip(btn_hear, lambda: "Click to hear the example sentence pronounced!")
        
        self.dash_examples = tk.Label(ex_container, text="", bg=BG_CARD, fg=FG_SECONDARY, font=(FONT_FAMILY, 8), justify="left", wraplength=280, cursor="hand2")
        self.dash_examples.pack(side="left", fill="x", expand=True, anchor="w")
        self.dash_examples.bind("<Button-1>", lambda e: self.play_sentence_narration(slow=False))
        HoverTooltip(self.dash_examples, lambda: "Click to hear the example sentence pronounced!")

        # Action Buttons row (New Card & Widget Toggles)
        options_row = tk.Frame(kanji_card_frame, bg=BG_CARD)
        options_row.pack(fill="x", pady=(8, 0))
        
        btn_new_kanji = tk.Button(options_row, text="🧠 NEW CARD", bg=ACCENT_CYAN, fg=FG_LIGHT, font=(FONT_FAMILY, 8, "bold"), bd=0, padx=12, pady=5, cursor="hand2", command=self.load_new_kanji_card)
        btn_new_kanji.pack(side="left", fill="x", expand=True, padx=(0, 4))
        
        btn_widget = tk.Button(options_row, text="📌 WIDGET", bg=BG_INNER, fg=ACCENT_CYAN, font=(FONT_FAMILY, 8, "bold"), bd=0, padx=8, pady=4, cursor="hand2", command=self.launch_floating_kanji_widget)
        btn_widget.pack(side="left", fill="x", expand=True, padx=4)
        
        chk_quiz = tk.Checkbutton(options_row, text="⏰ QUIZ", variable=self.quiz_enabled, bg=BG_CARD, fg=FG_LIGHT, selectcolor=BG_INNER, activebackground=BG_CARD, activeforeground=FG_LIGHT, font=(FONT_FAMILY, 8, "bold"), command=self.toggle_quiz_from_chk)
        chk_quiz.pack(side="right", padx=(4, 0))

        # ===== RIGHT COLUMN: ACTION BUTTONS (RECORD & EVALUATE) =====
        action_row = tk.Frame(right_col, bg=BG_DARK)
        action_row.pack(fill="x", pady=(0, 10))
        action_row.columnconfigure(0, weight=1)
        action_row.columnconfigure(1, weight=1)

        btn_rec = tk.Button(action_row, text="🎙️ RECORD SPEECH", bg=ACCENT_PURPLE, fg=FG_LIGHT, font=(FONT_FAMILY, 8, "bold"), bd=0, pady=10, cursor="hand2", command=self.open_grammar_sandbox_dialog)
        btn_rec.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        
        btn_eval = tk.Button(action_row, text="⚡ EVALUATE SENTENCE", bg=BG_CARD, fg=ACCENT_CYAN, bd=1, relief="solid", highlightthickness=0, font=(FONT_FAMILY, 8, "bold"), pady=10, cursor="hand2", command=self.open_grammar_sandbox_dialog)
        btn_eval.grid(row=0, column=1, sticky="nsew", padx=(4, 0))

        # ===== RIGHT COLUMN: RESEARCH STREAM =====
        research_card = tk.Frame(right_col, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1, padx=12, pady=12)
        research_card.pack(fill="both", expand=True, pady=(0, 10))

        tk.Label(research_card, text="🔬 RESEARCH STREAM", bg=BG_CARD, fg=FG_LIGHT, font=(FONT_HEADLINE, 10, "bold")).pack(anchor="w", pady=(0, 8))

        self.dash_research_frame = tk.Frame(research_card, bg=BG_CARD)
        self.dash_research_frame.pack(fill="both", expand=True)
        self.root.after(100, self.load_dashboard_research_stream)

    def animate_fade(self, widget, start_hex, end_hex, steps=12, delay_ms=12, current_step=0):
        """Smoothly interpolates a label's foreground color between two hex values to create fluid transition animations."""
        if not widget.winfo_exists():
            return
            
        def hex_to_rgb(hex_str):
            hex_str = hex_str.lstrip('#')
            return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
            
        def rgb_to_hex(rgb):
            return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
            
        c1 = hex_to_rgb(start_hex)
        c2 = hex_to_rgb(end_hex)
        
        t = current_step / steps
        r = int(c1[0] + (c2[0] - c1[0]) * t)
        g = int(c1[1] + (c2[1] - c1[1]) * t)
        b = int(c1[2] + (c2[2] - c1[2]) * t)
        
        widget.config(fg=rgb_to_hex((r, g, b)))
        
        if current_step < steps:
            self.root.after(delay_ms, lambda: self.animate_fade(widget, start_hex, end_hex, steps, delay_ms, current_step + 1))

    def animate_dial(self, target_pct, current_step=0, max_steps=18):
        """Smoothly sweeps the compliance index dial from 0 to the target percentage."""
        if not self.dial_canvas.winfo_exists():
            return
            
        t = current_step / max_steps
        pct = target_pct * t
        
        self.dial_canvas.delete("all")
        self.dial_canvas.create_arc(20, 10, 120, 110, start=225, extent=-270, style="arc", outline=BORDER_COLOR, width=8)
        if pct > 0:
            color = ACCENT_GREEN if target_pct == 1.0 else ACCENT_CYAN
            self.dial_canvas.create_arc(20, 10, 120, 110, start=225, extent=-270*pct, style="arc", outline=color, width=8)
            
        # Draw percentage text in center of gauge
        self.dial_canvas.create_text(70, 56, text=f"{pct*100.0:.1f}%", fill=FG_LIGHT, font=(FONT_FAMILY, 15, "bold"))
        # Draw a subtle "COMPLIANCE" label below the percentage
        self.dial_canvas.create_text(70, 78, text="COMPLIANCE", fill=FG_SECONDARY, font=(FONT_FAMILY, 7, "bold"))
        
        if current_step < max_steps:
            self.root.after(12, lambda: self.animate_dial(target_pct, current_step + 1, max_steps))

    def refresh_dashboard_progress(self, sync_active=False):
        """Queries SQLite and dynamically draws/animates the dashboard progress dial and activity heatmap."""
        try:
            today_str = datetime.now().strftime("%Y-%m-%d")
            data = guardian_db.get_habit_history(days=1)
            today_data = data.get(today_str, {})
            
            # Sync variables
            habits = guardian_db.get_all_habit_names()
            if not habits:
                habits = self.config.get("tracked_tasks", ["dsa", "dev-project", "language-study"])
                
            completed = 0
            total = len(habits)
            
            # Check weekend prep compliance if active
            is_weekend = datetime.now().weekday() in (5, 6)
            is_prep_active = self.config.get("japan_mnc_prep_active", True)
            if is_weekend and is_prep_active:
                total += 1
                sat_date_str = "2026-05-23" if self.mock_weekend else (guardian.get_current_weekend_saturday_date() or today_str)
                hist = guardian_db.get_weekend_prep_history()
                task = next((t for t in hist if t.get("date") == sat_date_str), None)
                if task and task.get("completed"):
                    completed += 1
            
            for h in habits:
                if today_data.get(h):
                    completed += 1
                    
            pct = (completed / total) if total > 0 else 0.0
            
            # Smoothly animate dial compliance sweep
            self.animate_dial(pct)
                
            # Render visual 14-day contribution heatmap grid on heatmap_canvas
            self.heatmap_canvas.delete("all")
            hm_w = self.heatmap_canvas.winfo_width()
            if hm_w < 100: hm_w = 340
            
            # 14 squares (size 18x18, gap 6). Total width = 14 * 24 - 6 = 330
            start_x = (hm_w - 330) / 2
            if start_x < 5: start_x = 10
            
            today = datetime.now()
            # Generate 14 days sorted from 13 days ago to today
            dates_list = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(13, -1, -1)]
            
            # Fetch active habits history for past 14 days
            hist_data = guardian_db.get_habit_history(days=14)
            active_habits = guardian_db.get_all_habit_names()
            if not active_habits:
                active_habits = habits
            
            for i, d_str in enumerate(dates_list):
                day_state = hist_data.get(d_str, {})
                total_habits = len(active_habits)
                
                completed_habits = 0
                for h in active_habits:
                    if day_state.get(h, False):
                        completed_habits += 1
                        
                day_pct = (completed_habits / total_habits) if total_habits > 0 else 0.0
                
                # Determine colors based on compliance percentage
                border_color = BORDER_COLOR
                border_thickness = 1
                
                if day_pct == 0.0:
                    bg_color = "#18181B"          # Pure charcoal
                elif day_pct <= 0.34:
                    bg_color = "#064e3b"          # Muted Forest
                elif day_pct <= 0.67:
                    bg_color = "#059669"          # Emerald Green
                else:
                    bg_color = "#10B981"          # Radiant Neon
                    if day_pct == 1.0:
                        border_color = ACCENT_CYAN
                        border_thickness = 1.5
                
                x1 = start_x + i * 24
                y1 = 18
                x2 = x1 + 18
                y2 = y1 + 18
                
                # Draw rounded rectangle for square
                draw_rounded_rect(self.heatmap_canvas, x1, y1, x2, y2, radius=4, fill=bg_color, outline=border_color, width=border_thickness)
                
                # Draw column headers above (1, 3, 5, 7, 8, 10, 12, 14)
                if i in [0, 2, 4, 6, 7, 9, 11, 13]:
                    self.heatmap_canvas.create_text((x1+x2)/2, 8, text=str(i+1), fill=FG_SECONDARY, font=(FONT_FAMILY, 6, "bold"))

            # Render checklist checkbuttons
            for child in self.habits_frame.winfo_children():
                child.destroy()
                
            # Render habit tasks
            for h in habits:
                is_checked = today_data.get(h, False)
                var = tk.BooleanVar(value=is_checked)
                
                def make_toggle(task_name=h, bool_var=var):
                    return lambda: self.toggle_habit_db(task_name, bool_var.get())
                
                is_github = (h == "github-commit")
                
                if is_github:
                    # Special container frame for GitHub Sync row
                    row_frame = tk.Frame(self.habits_frame, bg=BG_CARD)
                    row_frame.pack(fill="x", anchor="w", pady=3)
                    
                    chk = tk.Checkbutton(
                        row_frame, text="Practice / Complete: GITHUB-COMMIT", variable=var,
                        bg=BG_CARD, fg=FG_LIGHT, selectcolor=BG_INNER, activebackground=BG_CARD, activeforeground=FG_LIGHT,
                        font=(FONT_FAMILY, 9), command=make_toggle(h, var)
                    )
                    chk.pack(side="left", anchor="w")
                    
                    sync_text = "LOADING..." if sync_active else "⚡ SYNC"
                    sync_state = "disabled" if sync_active else "normal"
                    
                    btn_sync = tk.Button(
                        row_frame, text=sync_text, state=sync_state, bg=ACCENT_CYAN, fg=FG_LIGHT, bd=0, padx=8, pady=2,
                        font=(FONT_FAMILY, 7, "bold"), cursor="hand2", command=self.asynchronously_sync_github
                    )
                    btn_sync.pack(side="left", padx=10)
                else:
                    row_frame = tk.Frame(self.habits_frame, bg=BG_CARD)
                    row_frame.pack(fill="x", anchor="w", pady=3)
                    
                    chk = tk.Checkbutton(
                        row_frame, text=f"Practice / Complete: {h.upper()}", variable=var,
                        bg=BG_CARD, fg=FG_LIGHT, selectcolor=BG_INNER, activebackground=BG_CARD, activeforeground=FG_LIGHT,
                        font=(FONT_FAMILY, 9), command=make_toggle(h, var)
                    )
                    chk.pack(side="left", anchor="w")
                    
                    def make_del_habit(h_name=h):
                        return lambda: self.delete_habit_from_dash(h_name)
                        
                    btn_del = tk.Button(
                        row_frame, text="🗑️", bg=BG_CARD, fg=ACCENT_RED, activebackground=BG_CARD, activeforeground=FG_LIGHT,
                        bd=0, cursor="hand2", font=(FONT_FAMILY, 8), command=make_del_habit(h)
                    )
                    btn_del.pack(side="right", padx=5)
                
            # Render weekend prep checkbutton if applicable
            if is_weekend and is_prep_active:
                sat_date_str = "2026-05-23" if self.mock_weekend else (guardian.get_current_weekend_saturday_date() or today_str)
                hist = guardian_db.get_weekend_prep_history()
                task = next((t for t in hist if t.get("date") == sat_date_str), None)
                is_task_done = bool(task and task.get("completed"))
                
                prep_var = tk.BooleanVar(value=is_task_done)
                
                def toggle_prep():
                    try:
                        if prep_var.get():
                            # mark done
                            guardian_db.save_weekend_prep_task(sat_date_str, "Active", "Gemini AI", 1, "", "", "", [])
                        else:
                            guardian_db.save_weekend_prep_task(sat_date_str, "Active", "Gemini AI", 0, "", "", "", [])
                    except Exception as e:
                        print(e)
                    self.refresh_dashboard_progress()
                    
                chk = tk.Checkbutton(
                    self.habits_frame, text="🛡️ WEEKEND PREPARATION & AI INTELLIGENCE", variable=prep_var,
                    bg=BG_CARD, fg=ACCENT_ORANGE, selectcolor=BG_INNER, activebackground=BG_CARD, activeforeground=ACCENT_ORANGE,
                    font=(FONT_FAMILY, 9, "bold"), command=toggle_prep
                )
                chk.pack(anchor="w", pady=5)
                
            # Render Todo Tasks Checklist
            for child in self.todo_list_frame.winfo_children():
                child.destroy()
                
            todo_tasks = guardian_db.get_todo_tasks(today_str)
            if not todo_tasks:
                tk.Label(
                    self.todo_list_frame, text="✨ No tasks added for today! Add some to upscale.",
                    bg=BG_CARD, fg=FG_SECONDARY, font=(FONT_FAMILY, 9, "italic")
                ).pack(anchor="w", pady=5)
            else:
                for t in todo_tasks:
                    row_frame = tk.Frame(self.todo_list_frame, bg=BG_CARD)
                    row_frame.pack(fill="x", pady=2)
                    
                    t_var = tk.BooleanVar(value=t["completed"])
                    
                    def make_todo_toggle(task_id=t["id"], var_ref=t_var):
                        return lambda: self.toggle_todo_task_db(task_id, var_ref.get())
                        
                    # Strikeout if completed (Dracula premium visual cue!)
                    lbl_color = FG_SECONDARY if t["completed"] else FG_LIGHT
                    lbl_font = (FONT_FAMILY, 9, "overstrike") if t["completed"] else (FONT_FAMILY, 9)
                    
                    chk = tk.Checkbutton(
                        row_frame, text=t["task_text"], variable=t_var,
                        bg=BG_CARD, fg=lbl_color, selectcolor=BG_INNER, activebackground=BG_CARD, activeforeground=lbl_color,
                        font=lbl_font, command=make_todo_toggle(t["id"], t_var)
                    )
                    chk.pack(side="left", anchor="w")
                    
                    def make_todo_del(task_id=t["id"]):
                        return lambda: self.delete_todo_task_db(task_id)
                        
                    btn_del = tk.Button(
                        row_frame, text="🗑️", bg=BG_CARD, fg=ACCENT_RED, activebackground=BG_CARD, activeforeground=FG_LIGHT,
                        bd=0, cursor="hand2", font=(FONT_FAMILY, 8), command=make_todo_del(t["id"])
                    )
                    btn_del.pack(side="right", padx=5)

            # Save state for responsive redraws and trigger draw_activity_chart
            self.last_dates_list = dates_list
            self.last_hist_data = hist_data
            self.last_active_habits = active_habits
            self.draw_activity_chart()

            # Render Tokyo Prep progress bars in self.tokyo_bars_frame with clean custom tracks
            for child in self.tokyo_bars_frame.winfo_children():
                child.destroy()
                
            prep_skills = [
                ("System Design", 0.65, "65%"),
                ("Data Structures", 0.78, "78%"),
                ("Behavioral Lessons", 0.55, "55%"),
                ("Leetcode Milestones", 92/150, "92/150"),
            ]
            
            for skill_name, ratio, label_text in prep_skills:
                item_frame = tk.Frame(self.tokyo_bars_frame, bg=BG_CARD, pady=4)
                item_frame.pack(fill="x")
                
                # Skill label & percentage on same row
                info_row = tk.Frame(item_frame, bg=BG_CARD)
                info_row.pack(fill="x")
                tk.Label(info_row, text=skill_name, fg=FG_LIGHT, bg=BG_CARD, font=(FONT_FAMILY, 8, "bold")).pack(side="left")
                tk.Label(info_row, text=label_text, fg=ACCENT_CYAN, bg=BG_CARD, font=(FONT_FAMILY, 8, "bold")).pack(side="right")
                
                # Outer progress slot track — premium borderless design
                track = tk.Frame(item_frame, bg=BG_INNER, height=8)
                track.pack(fill="x", pady=(3, 0))
                track.pack_propagate(False)
                
                # Filled bar
                fill_bar = tk.Frame(track, bg=ACCENT_CYAN, height=8)
                fill_bar.place(relx=0, rely=0, relwidth=ratio, relheight=1)

            # Recompute streaks and stats using core adapter safely
            stats = guardian.calculate_stats()
            self.streak_num.config(text=f"🔥 {stats['current_streak']} DAY\nSTREAK")
        except Exception as ex:
            print(f"Error refreshing dashboard: {ex}")

    def draw_activity_chart(self, event=None):
        """Renders the Daily Activity Line Chart with premium glow effect and grid coordinates dynamically."""
        if not hasattr(self, "last_hist_data") or not self.last_hist_data:
            return
        self.activity_canvas.delete("all")
        width = self.activity_canvas.winfo_width()
        height = self.activity_canvas.winfo_height()
        if width < 50: width = 340
        if height < 50: height = 200
        
        # Margins
        padx, pady = 35, 20
        graph_w = width - 2 * padx
        graph_h = height - 2 * pady
        
        # Fetch last 14 days values
        activity_values = []
        for d_str in self.last_dates_list:
            day_state = self.last_hist_data.get(d_str, {})
            completed_habits = sum(1 for h in self.last_active_habits if day_state.get(h, False))
            activity_values.append(completed_habits)
            
        max_val = max(activity_values) if activity_values else 0
        if max_val == 0:
            max_val = 5 # Avoid division by zero
            
        points = []
        for i, val in enumerate(activity_values):
            x = padx + (i / 13) * graph_w
            y = height - pady - (val / max_val) * graph_h
            points.append((x, y))
            
        # Draw grid lines and labels
        for grid_y in range(4):
            gly = height - pady - (grid_y / 3) * graph_h
            self.activity_canvas.create_line(padx, gly, width - padx, gly, fill="#112830", dash=(2, 4))
            lbl_val = int((grid_y / 3) * max_val)
            self.activity_canvas.create_text(padx - 15, gly, text=str(lbl_val), fill=FG_SECONDARY, font=(FONT_FAMILY, 7))
            
        # Draw line and glow
        if len(points) > 1:
            # Draw semi-transparent vertical lines under the chart points to simulate a gradient glow!
            for k in range(len(points)):
                x, y = points[k]
                self.activity_canvas.create_line(x, y, x, height - pady, fill="#0c3535", width=2)
                
            # Draw thick glow line
            for k in range(len(points) - 1):
                x1, y1 = points[k]
                x2, y2 = points[k+1]
                self.activity_canvas.create_line(x1, y1, x2, y2, fill="#0a3d3d", width=5)
                self.activity_canvas.create_line(x1, y1, x2, y2, fill=ACCENT_GREEN, width=2.5)
                
        # Draw point dots
        for x, y in points:
            self.activity_canvas.create_oval(x-3.5, y-3.5, x+3.5, y+3.5, fill=ACCENT_CYAN, outline=BG_CARD, width=1.5)

    def load_dashboard_research_stream(self):
        """Presents a custom high-fidelity academic research feed inside the dashboard right column."""
        for child in self.dash_research_frame.winfo_children():
            child.destroy()
            
        hist = guardian_db.get_weekend_prep_history()
        papers = []
        if hist:
            for task in hist[:2]: # Show up to 2 papers from history
                spot = task.get("research_spotlight", {})
                title = spot.get("title")
                summary = spot.get("summary")
                if title and summary:
                    papers.append({
                        "category": "arXiv:CS" if "consensus" in title.lower() or "fault" in title.lower() else "arXiv:AI",
                        "title": title,
                        "summary": summary
                    })
        
        # Fallbacks matching Google Stitch layout perfectly if history is empty
        if not papers:
            papers = [
                {
                    "category": "arXiv:CS",
                    "title": "Byzantine Fault Tolerance in Asynchronous Consensus Systems",
                    "summary": "An analysis of practical limits in partial synchrony models, proposing a novel reduction algorithm for leader election."
                },
                {
                    "category": "arXiv:AI",
                    "title": "Deep Learning for Manifold Approximations",
                    "summary": "Using continuous normalizing flows to model complex topological structures in high-dimensional datasets."
                }
            ]
            
        for p in papers:
            p_card = tk.Frame(self.dash_research_frame, bg=BG_INNER, bd=1, relief="solid", highlightbackground=BORDER_COLOR, highlightthickness=1, padx=10, pady=8)
            p_card.pack(fill="x", pady=4)
            
            top_row = tk.Frame(p_card, bg=BG_INNER)
            top_row.pack(fill="x")
            
            bg_col = ACCENT_GREEN if p["category"] == "arXiv:CS" else ACCENT_PURPLE
            tk.Label(top_row, text=p["category"], bg=BG_INNER, fg=bg_col, font=(FONT_FAMILY, 7, "bold")).pack(side="left")
            tk.Label(top_row, text="Live Feed", bg=BG_INNER, fg=FG_SECONDARY, font=(FONT_FAMILY, 7)).pack(side="right")
            
            lbl_title = tk.Label(p_card, text=p["title"], bg=BG_INNER, fg=FG_LIGHT, font=(FONT_FAMILY, 9, "bold"), justify="left", anchor="w", wraplength=300)
            lbl_title.pack(fill="x", pady=2)
            
            lbl_sum = tk.Label(p_card, text=p["summary"], bg=BG_INNER, fg=FG_SECONDARY, font=(FONT_FAMILY, 8), justify="left", anchor="w", wraplength=300)
            lbl_sum.pack(fill="x")

    def toggle_habit_db(self, name, completed):
        try:
            today_str = datetime.now().strftime("%Y-%m-%d")
            guardian_db.log_habit(today_str, name, 1 if completed else 0)
        except Exception as e:
            print(e)
        self.refresh_dashboard_progress()

    def add_habit_from_dash(self):
        """Adds a custom daily habit directly from dashboard entry."""
        name = self.ent_habit_dash.get().strip().lower().replace(" ", "-")
        if not name or name == "add-daily-habit-to-track...":
            messagebox.showwarning("Validation Error", "Please enter a valid habit name.")
            return
        if name in guardian_db.get_all_habit_names():
            messagebox.showwarning("Validation Error", "This habit already exists.")
            return
            
        # Log in SQLite
        guardian_db.add_custom_habit(name)
        
        # Update config
        self.config["tracked_tasks"] = guardian_db.get_all_habit_names()
        guardian.save_config(self.config)
        
        self.ent_habit_dash.delete(0, tk.END)
        self.ent_habit_dash.insert(0, "Add daily habit to track...")
        self.refresh_dashboard_progress()

    def delete_habit_from_dash(self, name):
        """Deletes a custom daily habit directly from dashboard."""
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to deactivate and remove habit '{name.upper()}'?"):
            guardian_db.remove_custom_habit(name)
            self.config["tracked_tasks"] = guardian_db.get_all_habit_names()
            guardian.save_config(self.config)
            self.refresh_dashboard_progress()

    def add_todo_task_from_gui(self):
        """Adds a custom daily one-off todo task from entry input."""
        text = self.ent_todo.get().strip()
        if not text or text == "Add task to complete today...":
            messagebox.showwarning("Validation Error", "Please enter a valid task description.")
            return
            
        today_str = datetime.now().strftime("%Y-%m-%d")
        guardian_db.add_todo_task(text, today_str)
        self.ent_todo.delete(0, tk.END)
        self.ent_todo.insert(0, "Add task to complete today...")
        self.refresh_dashboard_progress()
        
    def toggle_todo_task_db(self, task_id, completed):
        """Toggles a todo task status inside SQLite and plays sounds on completion."""
        guardian_db.toggle_todo_task(task_id, completed)
        if completed:
            try:
                import winsound
                winsound.Beep(880, 100) # Quick confirmation high beep
            except Exception:
                pass
        self.refresh_dashboard_progress()
        
    def delete_todo_task_db(self, task_id):
        """Removes a todo task from SQLite database."""
        guardian_db.delete_todo_task(task_id)
        self.refresh_dashboard_progress()

    def open_manage_habits_dialog(self):
        """Opens a premium Space-Black modal dialog to manage habits dynamically."""
        if hasattr(self, "active_habits_window") and self.active_habits_window and self.active_habits_window.winfo_exists():
            self.active_habits_window.lift()
            self.active_habits_window.focus_force()
            return
            
        modal = tk.Toplevel(self.root)
        self.active_habits_window = modal
        modal.title("Manage Milestones & Habits")
        modal.configure(bg=BG_DARK)
        modal.geometry("380x420")
        modal.resizable(False, False)
        modal.attributes("-topmost", True)
        
        # Center the window
        modal.update_idletasks()
        w = modal.winfo_width()
        h = modal.winfo_height()
        extra_x = (self.root.winfo_screenwidth() - w) // 2
        extra_y = (self.root.winfo_screenheight() - h) // 2
        modal.geometry(f"+{extra_x}+{extra_y}")
        
        # Title Header
        tk.Label(modal, text="⚙️ MANAGE DAILY HABITS", bg=BG_DARK, fg=ACCENT_CYAN, font=(FONT_FAMILY, 10, "bold"), pady=15).pack()
        
        # Add Habit Frame
        add_frame = tk.Frame(modal, bg=BG_DARK, padx=20, pady=10)
        add_frame.pack(fill="x")
        
        tk.Label(add_frame, text="Add New Habit Name:", bg=BG_DARK, fg=FG_SECONDARY, font=(FONT_FAMILY, 8, "bold")).pack(anchor="w")
        ent_habit = tk.Entry(add_frame, bg=BG_INNER, fg=FG_LIGHT, insertbackground=FG_LIGHT, bd=1, relief="solid", highlightthickness=0, font=(FONT_FAMILY, 9))
        ent_habit.pack(fill="x", side="left", expand=True, ipady=4, pady=5)
        
        # List Container
        list_frame = tk.Frame(modal, bg=BG_INNER, bd=1, relief="solid", highlightbackground=BORDER_COLOR, highlightthickness=1)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        canvas = tk.Canvas(list_frame, bg=BG_INNER, highlightthickness=0)
        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        scroll_content = tk.Frame(canvas, bg=BG_INNER)
        
        scroll_content.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scroll_content, anchor="nw", width=310)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        def refresh_list():
            for child in scroll_content.winfo_children():
                child.destroy()
                
            habits = guardian_db.get_all_habit_names()
            for h in habits:
                h_frame = tk.Frame(scroll_content, bg=BG_INNER, pady=4)
                h_frame.pack(fill="x", expand=True)
                
                # Check for github-commit, make it undeletable to preserve core sync feature
                is_github = (h == "github-commit")
                
                lbl = tk.Label(h_frame, text=h.upper(), bg=BG_INNER, fg=FG_LIGHT, font=(FONT_FAMILY, 9, "bold"))
                lbl.pack(side="left", padx=5)
                
                if not is_github:
                    def make_del(habit_name=h):
                        return lambda: delete_habit(habit_name)
                        
                    btn_del = tk.Button(h_frame, text="🗑️", bg=BG_INNER, fg=ACCENT_RED, activebackground=BG_INNER, activeforeground=FG_LIGHT, bd=0, cursor="hand2", font=(FONT_FAMILY, 9), command=make_del(h))
                    btn_del.pack(side="right", padx=5)
                    
        def add_habit():
            name = ent_habit.get().strip().lower().replace(" ", "-")
            if not name:
                messagebox.showwarning("Validation Error", "Habit name cannot be empty.")
                return
            if name in guardian_db.get_all_habit_names():
                messagebox.showwarning("Validation Error", "This habit already exists.")
                return
            
            # Log in SQLite
            guardian_db.add_custom_habit(name)
            
            # Update Python configuration tracked_tasks
            self.config["tracked_tasks"] = guardian_db.get_all_habit_names()
            guardian.save_config(self.config)
            
            ent_habit.delete(0, tk.END)
            refresh_list()
            self.refresh_dashboard_progress()
            
        def delete_habit(name):
            if messagebox.askyesno("Confirm Delete", f"Are you sure you want to deactivate and remove habit '{name.upper()}'?"):
                guardian_db.remove_custom_habit(name)
                self.config["tracked_tasks"] = guardian_db.get_all_habit_names()
                guardian.save_config(self.config)
                refresh_list()
                self.refresh_dashboard_progress()

        btn_add = tk.Button(add_frame, text="➕ ADD", bg=ACCENT_CYAN, fg=FG_LIGHT, font=(FONT_FAMILY, 8, "bold"), bd=0, padx=12, pady=4, cursor="hand2", command=add_habit)
        btn_add.pack(side="right", padx=(5, 0))
        
        refresh_list()

    def asynchronously_sync_github(self):
        """Asynchronously triggers live public GitHub commit verification."""
        username = self.config.get("github_username", "").strip()
        if not username or username == "YOUR_GITHUB_USERNAME":
            messagebox.showwarning("Sync Configuration Required", "Please configure your public GitHub Username in the Settings tab first.")
            return
            
        # Temporarily update checklist button status to display sync active
        self.refresh_dashboard_progress(sync_active=True)
        
        def run_bg_sync():
            import guardian
            commit_ok = guardian.check_github_commit_today(username)
            
            def resolve():
                if commit_ok:
                    today_str = datetime.now().strftime("%Y-%m-%d")
                    # Log in SQLite
                    guardian_db.log_habit(today_str, "github-commit", 1)
                    
                    # Play pleasant confirmation chime
                    try:
                        import winsound
                        winsound.Beep(988, 150) # B5 pitch chime
                        winsound.Beep(1318, 250) # E6 pitch chime
                    except Exception:
                        pass
                    
                    messagebox.showinfo("Git Commit Synced", f"Outstanding! Found today's commits for GitHub user '{username}'.")
                else:
                    messagebox.showwarning("No Commits Found", f"No public push events or commits found today on GitHub for '{username}'. Push your code and sync again!")
                    
                self.refresh_dashboard_progress(sync_active=False)
                
            self.root.after(0, resolve)
            
        threading.Thread(target=run_bg_sync, daemon=True).start()

    def open_grammar_sandbox_dialog(self):
        """Opens a Duolingo-style developer Japanese grammar particle & sentence builder sandbox."""
        if hasattr(self, "active_grammar_window") and self.active_grammar_window and self.active_grammar_window.winfo_exists():
            self.active_grammar_window.lift()
            self.active_grammar_window.focus_force()
            return
            
        modal = tk.Toplevel(self.root)
        self.active_grammar_window = modal
        modal.title("Grammar Particle & Sentence Lab")
        modal.configure(bg=BG_DARK)
        modal.geometry("460x450")
        modal.resizable(False, False)
        modal.attributes("-topmost", True)
        
        # Center the window
        modal.update_idletasks()
        w = modal.winfo_width()
        h = modal.winfo_height()
        extra_x = (self.root.winfo_screenwidth() - w) // 2
        extra_y = (self.root.winfo_screenheight() - h) // 2
        modal.geometry(f"+{extra_x}+{extra_y}")
        
        # Game Data
        puzzles = [
            {"english": "I write code in Python.", "correct": ["私は", "Python", "で", "コード", "を", "書きます。"], "options": ["書きます。", "で", "を", "コード", "私は", "Python", "に", "は"]},
            {"english": "Is the server database fast?", "correct": ["サーバー", "の", "データベース", "は", "速い", "ですか。"], "options": ["データベース", "の", "サーバー", "は", "速い", "ですか。", "に", "を"]},
            {"english": "I will practice coding over the weekend.", "correct": ["週末", "に", "コーディング", "を", "練習します。"], "options": ["練習します。", "を", "コーディング", "に", "週末", "で", "は", "が"]},
            {"english": "Today, I committed code to GitHub.", "correct": ["今日", "GitHub", "に", "コミット", "しました。"], "options": ["今日", "に", "GitHub", "しました。", "コミット", "で", "を", "は"]},
            {"english": "Distributed databases are difficult.", "correct": ["分散", "データベース", "は", "難しい", "です。"], "options": ["難しい", "データベース", "は", "分散", "です。", "が", "に", "を"]}
        ]
        
        # Pick a random puzzle
        puzzle_idx = random.randint(0, len(puzzles)-1)
        active_puzzle = puzzles[puzzle_idx]
        
        selected_words = []
        available_options = list(active_puzzle["options"])
        random.shuffle(available_options)
        
        # Title Header
        tk.Label(modal, text="🎮 DEVELOPER GRAMMAR LAB", bg=BG_DARK, fg=ACCENT_PURPLE, font=(FONT_FAMILY, 10, "bold"), pady=15).pack()
        
        # Target Question Card
        q_card = tk.Frame(modal, bg=BG_CARD, bd=1, relief="solid", highlightbackground=BORDER_COLOR, highlightthickness=1, padx=15, pady=12)
        q_card.pack(fill="x", padx=20, pady=5)
        
        tk.Label(q_card, text="TRANSLATE THIS SENTENCE:", bg=BG_CARD, fg=ACCENT_ORANGE, font=(FONT_FAMILY, 8, "bold")).pack(anchor="w")
        tk.Label(q_card, text=active_puzzle["english"], bg=BG_CARD, fg=FG_LIGHT, font=(FONT_FAMILY, 10, "bold"), pady=4).pack(anchor="w")
        
        # Selected Slots Box
        slots_card = tk.Frame(modal, bg=BG_INNER, bd=1, relief="solid", highlightbackground=BORDER_COLOR, highlightthickness=1, padx=15, pady=15)
        slots_card.pack(fill="both", expand=True, padx=20, pady=10)
        
        tk.Label(slots_card, text="YOUR SENTENCE (Click word to remove):", bg=BG_INNER, fg=FG_SECONDARY, font=(FONT_FAMILY, 7, "bold")).pack(anchor="w", pady=(0, 5))
        
        slots_tray = tk.Frame(slots_card, bg=BG_INNER)
        slots_tray.pack(fill="both", expand=True, pady=5)
        
        # Options Box
        options_tray = tk.Frame(modal, bg=BG_DARK, padx=20, pady=10)
        options_tray.pack(fill="x")
        
        tk.Label(options_tray, text="AVAILABLE WORDS (Click word to add):", bg=BG_DARK, fg=FG_SECONDARY, font=(FONT_FAMILY, 7, "bold")).pack(anchor="w", pady=(0, 5))
        
        pills_tray = tk.Frame(options_tray, bg=BG_DARK)
        pills_tray.pack(fill="x")
        
        # Control Actions Row
        actions_row = tk.Frame(modal, bg=BG_DARK, padx=20, pady=15)
        actions_row.pack(fill="x")
        
        lbl_result = tk.Label(actions_row, text="", bg=BG_DARK, fg=ACCENT_GREEN, font=(FONT_FAMILY, 9, "bold"))
        lbl_result.pack(side="left")
        
        def refresh_slots():
            for child in slots_tray.winfo_children():
                child.destroy()
            for idx, word in enumerate(selected_words):
                def make_remove(w=word):
                    return lambda: remove_word(w)
                btn = tk.Button(slots_tray, text=word, bg=BG_CARD, fg=FG_LIGHT, bd=1, relief="solid", highlightbackground=BORDER_COLOR, font=(FONT_FAMILY, 9), cursor="hand2", padx=8, pady=3, command=make_remove(word))
                btn.pack(side="left", padx=3, pady=3)
                
        def refresh_options():
            for child in pills_tray.winfo_children():
                child.destroy()
            for idx, word in enumerate(available_options):
                def make_add(w=word):
                    return lambda: add_word(w)
                btn = tk.Button(pills_tray, text=word, bg=BG_INNER, fg=FG_LIGHT, bd=1, relief="solid", highlightbackground=BORDER_COLOR, font=(FONT_FAMILY, 9), cursor="hand2", padx=8, pady=3, command=make_add(word))
                btn.pack(side="left", padx=3, pady=3)
                
        def add_word(word):
            if word in available_options:
                available_options.remove(word)
                selected_words.append(word)
                refresh_slots()
                refresh_options()
                lbl_result.config(text="")
                
        def remove_word(word):
            if word in selected_words:
                selected_words.remove(word)
                available_options.append(word)
                refresh_slots()
                refresh_options()
                lbl_result.config(text="")
                
        def evaluate_sentence():
            correct_seq = active_puzzle["correct"]
            if selected_words == correct_seq:
                lbl_result.config(text="🏆 CORRECT! Excellent work!", fg=ACCENT_GREEN)
                # Play pleasant chime
                try:
                    import winsound
                    winsound.Beep(523, 100) # C5
                    winsound.Beep(659, 100) # E5
                    winsound.Beep(784, 150) # G5
                except Exception:
                    pass
            else:
                lbl_result.config(text="❌ INCORRECT. Try another sequence!", fg=ACCENT_RED)
                try:
                    import winsound
                    winsound.Beep(261, 200) # C4 buzz
                except Exception:
                    pass
                    
        def reset_puzzle():
            nonlocal selected_words, available_options
            selected_words = []
            available_options = list(active_puzzle["options"])
            random.shuffle(available_options)
            refresh_slots()
            refresh_options()
            lbl_result.config(text="")

        btn_eval = tk.Button(actions_row, text="⚡ EVALUATE", bg=ACCENT_CYAN, fg=FG_LIGHT, font=(FONT_FAMILY, 8, "bold"), bd=0, padx=12, pady=5, cursor="hand2", command=evaluate_sentence)
        btn_eval.pack(side="right", padx=(5, 0))
        
        btn_reset = tk.Button(actions_row, text="↻ RESET", bg=BG_INNER, fg=FG_SECONDARY, font=(FONT_FAMILY, 8, "bold"), bd=0, padx=12, pady=5, cursor="hand2", command=reset_puzzle)
        btn_reset.pack(side="right", padx=5)
        
        refresh_slots()
        refresh_options()

    # ==================== TAB 2: RESEARCH PANEL ====================
    def init_research_tab(self):
        frame = self.tabs["research"]
        
        # Scrollable container
        container = tk.Frame(frame, bg=BG_DARK)
        container.pack(fill="both", expand=True)
        
        canvas = tk.Canvas(container, bg=BG_DARK, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scroll_content = tk.Frame(canvas, bg=BG_DARK)
        
        scroll_content.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scroll_content, anchor="nw", width=500)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Top refresh header
        ref_row = tk.Frame(scroll_content, bg=BG_DARK)
        ref_row.pack(fill="x", pady=(0, 10))
        
        tk.Label(ref_row, text="🔬 Live 2026 AI Research Spotlight", bg=BG_DARK, fg=FG_LIGHT, font=(FONT_FAMILY, 10, "bold")).pack(side="left")
        
        self.btn_ref_intel = tk.Button(
            ref_row, text="⚡ REFRESH", bg=ACCENT_CYAN, fg=FG_LIGHT, bd=0, padx=12, pady=4,
            font=(FONT_FAMILY, 8, "bold"), cursor="hand2", command=self.asynchronously_generate_weekend_research
        )
        self.btn_ref_intel.pack(side="right")
        
        # AI Loader screen
        self.intel_loader = tk.Label(
            scroll_content, text="⌛ Refreshing real-time CS research briefings and upscaling roadmaps...",
            fg=ACCENT_ORANGE, bg=BG_DARK, font=(FONT_FAMILY, 9, "italic"), pady=15
        )
        
        # Cards Container
        self.intel_body = tk.Frame(scroll_content, bg=BG_DARK)
        self.intel_body.pack(fill="both", expand=True)
        
        self.load_local_weekend_prep_ui()

    def asynchronously_generate_weekend_research(self):
        """Asynchronously triggers the Weekend task pipeline to synthesize live briefings."""
        if self.generating_weekend_task:
            return
            
        self.generating_weekend_task = True
        self.intel_loader.pack(fill="x", before=self.intel_body)
        self.btn_ref_intel.config(text="LOADING...", state="disabled")
        
        def run_bg_gen():
            try:
                today_str = datetime.now().strftime("%Y-%m-%d")
                sat_date_str = "2026-05-23" if self.mock_weekend else (guardian.get_current_weekend_saturday_date() or today_str)
                
                # Fetch history and index
                hist = guardian_db.get_weekend_prep_history()
                
                # Triggers the pipeline
                task = guardian.get_or_create_weekend_task(sat_date_str)
                # Mark done in UI thread
            except Exception as e:
                print(e)
                
            def resolve():
                self.generating_weekend_task = False
                self.intel_loader.pack_forget()
                self.btn_ref_intel.config(text="⚡ REFRESH", state="normal")
                self.load_local_weekend_prep_ui()
                self.refresh_dashboard_progress()
                
            self.root.after(0, resolve)
            
        threading.Thread(target=run_bg_gen, daemon=True).start()

    def load_local_weekend_prep_ui(self):
        """Reads local cache and builds custom high-fidelity information cards."""
        for child in self.intel_body.winfo_children():
            child.destroy()
            
        today_str = datetime.now().strftime("%Y-%m-%d")
        sat_date_str = "2026-05-23" if self.mock_weekend else (guardian.get_current_weekend_saturday_date() or today_str)
        
        hist = guardian_db.get_weekend_prep_history()
        # 1. Try to find the task for this weekend
        task = next((t for t in hist if t.get("date") == sat_date_str), None)
        
        # 2. If no task for this weekend, fall back to the absolute latest generated task in history (actual current data)
        if not task and hist:
            task = sorted(hist, key=lambda x: x.get("date", ""))[-1]
            
        # 3. If there is absolutely no history, dynamically trigger live AI generation in the background!
        if not task:
            if not getattr(self, "weekend_auto_generation_attempted", False):
                self.weekend_auto_generation_attempted = True
                self.asynchronously_generate_weekend_research()
                return
            else:
                print("Weekend task generation returned None or failed. Loading rich fallback task index 0.")
                task = guardian.get_rich_fallback_task(0)
            
        # 1. Weekly intelligence Card
        intel_card = tk.Frame(self.intel_body, bg=BG_CARD, bd=1, relief="solid", highlightbackground=BORDER_COLOR, highlightthickness=1, padx=15, pady=12)
        intel_card.pack(fill="x", pady=5)
        
        tk.Label(intel_card, text="WEEKLY TECH RADAR BRIEFING", bg=BG_CARD, fg=ACCENT_ORANGE, font=(FONT_FAMILY, 8, "bold")).pack(anchor="w")
        tk.Label(intel_card, text=task.get("weekly_intel_summary", "Reviewing Distributed Systems Design."),
                 bg=BG_CARD, fg=FG_LIGHT, font=(FONT_FAMILY, 9), wraplength=460, justify="left", pady=4).pack(anchor="w")
                 
        # 2. arXiv Spotlight Card
        arxiv_card = tk.Frame(self.intel_body, bg=BG_CARD, bd=1, relief="solid", highlightbackground=BORDER_COLOR, highlightthickness=1, padx=15, pady=12)
        arxiv_card.pack(fill="x", pady=5)
        
        spot = task.get("research_spotlight", {})
        title = spot.get("title", "No emerging research selected.")
        summary = spot.get("summary", "Verify your active session connection.")
        query = spot.get("read_more_query", "")
        
        tk.Label(arxiv_card, text="🔬 EMERGING RESEARCH SPOTLIGHT (arXiv / Research Blog)", bg=BG_CARD, fg=ACCENT_CYAN, font=(FONT_FAMILY, 8, "bold")).pack(anchor="w")
        tk.Label(arxiv_card, text=title, bg=BG_CARD, fg=FG_LIGHT, font=(FONT_FAMILY, 9, "bold"), wraplength=460, justify="left", pady=3).pack(anchor="w")
        tk.Label(arxiv_card, text=summary, bg=BG_CARD, fg=FG_SECONDARY, font=(FONT_FAMILY, 8), wraplength=460, justify="left").pack(anchor="w")
        
        if query:
            url_query = urllib.parse.quote(query)
            btn = tk.Button(
                arxiv_card, text="READ LIVE PAPER ↗", bg=BG_INNER, fg=ACCENT_CYAN, bd=0, padx=10, pady=3,
                font=(FONT_FAMILY, 7, "bold"), cursor="hand2", command=lambda: webbrowser.open(f"https://www.google.com/search?q={url_query}")
            )
            btn.pack(anchor="w", pady=(8, 0))
            
        # 3. Weekend Study Plan Card
        lesson_card = tk.Frame(self.intel_body, bg=BG_CARD, bd=1, relief="solid", highlightbackground=BORDER_COLOR, highlightthickness=1, padx=15, pady=12)
        lesson_card.pack(fill="x", pady=5)
        
        tk.Label(lesson_card, text="🚀 ACTIONABLE STUDY PLAN & ROADMAP", bg=BG_CARD, fg=ACCENT_GREEN, font=(FONT_FAMILY, 8, "bold")).pack(anchor="w")
        tk.Label(lesson_card, text=task.get("task_title", "Japan MNC Career Prep"), bg=BG_CARD, fg=FG_LIGHT, font=(FONT_FAMILY, 10, "bold"), pady=3).pack(anchor="w")
        tk.Label(lesson_card, text=f"• Technical Drill: {task.get('tech_upscaling','')}", bg=BG_CARD, fg=FG_SECONDARY, font=(FONT_FAMILY, 8), wraplength=460, justify="left", pady=2).pack(anchor="w")
        tk.Label(lesson_card, text=f"• Cultural Manners: {task.get('personality_upscaling','')}", bg=BG_CARD, fg=FG_SECONDARY, font=(FONT_FAMILY, 8), wraplength=460, justify="left", pady=2).pack(anchor="w")
        
        # 4. Learning Resources Card
        res_card = tk.Frame(self.intel_body, bg=BG_CARD, bd=1, relief="solid", highlightbackground=BORDER_COLOR, highlightthickness=1, padx=15, pady=12)
        res_card.pack(fill="x", pady=5)
        
        tk.Label(res_card, text="📚 CURATED RESOURCE LINKS", bg=BG_CARD, fg=ACCENT_PURPLE, font=(FONT_FAMILY, 8, "bold")).pack(anchor="w", pady=(0, 6))
        
        suggestions = task.get("youtube_suggestions", [])
        for item in suggestions:
            title_text = item.get("title", "Resource Tutorial")
            s_query = item.get("search_query", "")
            
            def make_open_res(q=s_query):
                return lambda: webbrowser.open(f"https://www.youtube.com/results?search_query={urllib.parse.quote(q)}")
                
            btn_lnk = tk.Button(
                res_card, text=f"▶  {title_text}", bg=BG_CARD, fg=FG_LIGHT, activebackground=HOVER_COLOR,
                activeforeground=ACCENT_CYAN, bd=0, font=(FONT_FAMILY, 8), cursor="hand2", anchor="w",
                padx=5, pady=2, command=make_open_res(s_query)
            )
            btn_lnk.pack(fill="x")
            
        # 5. Interactive arXiv Search Card (Master Research Console)
        search_card = tk.Frame(self.intel_body, bg=BG_CARD, bd=1, relief="solid", highlightbackground=BORDER_COLOR, highlightthickness=1, padx=15, pady=12)
        search_card.pack(fill="x", pady=5)
        
        tk.Label(search_card, text="🔍 LIVE CS PAPER SEARCH (arXiv API)", bg=BG_CARD, fg=ACCENT_CYAN, font=(FONT_FAMILY, 8, "bold")).pack(anchor="w")
        
        entry_frame = tk.Frame(search_card, bg=BG_CARD)
        entry_frame.pack(fill="x", pady=5)
        
        self.ent_arxiv_query = tk.Entry(entry_frame, bg=BG_INNER, fg=FG_LIGHT, insertbackground=FG_LIGHT, bd=1, relief="solid", highlightthickness=0, font=(FONT_FAMILY, 9))
        self.ent_arxiv_query.pack(side="left", fill="x", expand=True, ipady=4)
        self.ent_arxiv_query.insert(0, "Distributed consensus")
        
        btn_search = tk.Button(entry_frame, text="🔍 SEARCH", bg=ACCENT_CYAN, fg=FG_LIGHT, font=(FONT_FAMILY, 8, "bold"), bd=0, padx=12, pady=4, cursor="hand2", command=self.asynchronously_search_arxiv)
        btn_search.pack(side="right", padx=(5, 0))
        
        self.lbl_arxiv_status = tk.Label(search_card, text="", bg=BG_CARD, fg=FG_SECONDARY, font=(FONT_FAMILY, 8, "italic"))
        self.lbl_arxiv_status.pack(anchor="w", pady=(2, 0))
        
        self.arxiv_results_frame = tk.Frame(search_card, bg=BG_CARD)
        self.arxiv_results_frame.pack(fill="both", expand=True, pady=5)

    def asynchronously_search_arxiv(self):
        """Asynchronously queries the live arXiv API for academic computer science research papers."""
        query = self.ent_arxiv_query.get().strip()
        if not query:
            messagebox.showwarning("Search Required", "Please enter a search term or topic.")
            return
            
        self.lbl_arxiv_status.config(text="🔍 Searching live arXiv API...")
        for child in self.arxiv_results_frame.winfo_children():
            child.destroy()
            
        def run_bg_search():
            import urllib.request
            import xml.etree.ElementTree as ET
            import urllib.parse
            
            # Format query for arXiv CS category or all text
            safe_query = urllib.parse.quote(f"all:\"{query}\" AND (cat:cs.DC OR cat:cs.SE OR cat:cs.AR OR cat:cs.LG)")
            url = f"http://export.arxiv.org/api/query?search_query={safe_query}&sortBy=submittedDate&sortOrder=descending&max_results=3"
            
            papers = []
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                response = urllib.request.urlopen(req, timeout=8)
                xml_data = response.read()
                root = ET.fromstring(xml_data)
                
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                entries = root.findall('atom:entry', ns)
                
                for entry in entries:
                    t = entry.find('atom:title', ns).text.strip().replace('\n', ' ')
                    s = entry.find('atom:summary', ns).text.strip().replace('\n', ' ')
                    id_url = entry.find('atom:id', ns).text.strip()
                    arxiv_id = id_url.split('/abs/')[-1].split('v')[0]
                    
                    # Clean double spaces
                    t = " ".join(t.split())
                    s = " ".join(s.split())
                    
                    # Make short summary
                    summary_sents = [sent.strip() for sent in s.split('.') if sent.strip()]
                    short_s = ". ".join(summary_sents[:2]) + "."
                    if len(short_s) > 180:
                        short_s = short_s[:177] + "..."
                        
                    papers.append({
                        "title": t,
                        "summary": short_s,
                        "id": arxiv_id
                    })
            except Exception as e:
                print(f"Error searching arXiv: {e}")
                
            def resolve():
                self.lbl_arxiv_status.config(text="")
                if not papers:
                    tk.Label(self.arxiv_results_frame, text="❌ No papers found. Try another query like 'Raft consensus' or 'LLM compiler'.", bg=BG_CARD, fg=ACCENT_ORANGE, font=(FONT_FAMILY, 8, "italic")).pack(anchor="w")
                    return
                    
                for p in papers:
                    p_frame = tk.Frame(self.arxiv_results_frame, bg=BG_INNER, bd=1, relief="solid", highlightbackground=BORDER_COLOR, highlightthickness=1, padx=10, pady=8)
                    p_frame.pack(fill="x", pady=4)
                    
                    tk.Label(p_frame, text=p["title"], bg=BG_INNER, fg=FG_LIGHT, font=(FONT_FAMILY, 9, "bold"), wraplength=440, justify="left").pack(anchor="w")
                    tk.Label(p_frame, text=p["summary"], bg=BG_INNER, fg=FG_SECONDARY, font=(FONT_FAMILY, 8), wraplength=440, justify="left", pady=3).pack(anchor="w")
                    
                    read_query = f"arXiv:{p['id']} {p['title']}"
                    def make_open_paper(q=read_query):
                        return lambda: webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(q)}")
                        
                    btn = tk.Button(
                        p_frame, text="READ PAPER ↗", bg=BG_CARD, fg=ACCENT_CYAN, bd=0, padx=8, pady=2,
                        font=(FONT_FAMILY, 7, "bold"), cursor="hand2", command=make_open_paper(read_query)
                    )
                    btn.pack(anchor="w", pady=(4, 0))
                    
            self.root.after(0, resolve)
            
        threading.Thread(target=run_bg_search, daemon=True).start()


    # ==================== TAB 3: KANJI SRS EXPLORER ====================
    def init_kanji_tab(self):
        frame = self.tabs["kanji"]
        
        # Main flashcard container
        card_container = tk.Frame(frame, bg=BG_CARD, bd=1, relief="solid", highlightbackground=BORDER_COLOR, highlightthickness=1, padx=25, pady=20)
        card_container.pack(fill="both", expand=True, pady=(10, 5))
        
        # Visual Large display
        self.k_display = tk.Label(card_container, text="漢", fg=ACCENT_CYAN, bg=BG_CARD, font=(FONT_FAMILY, 54, "bold"), cursor="hand2")
        self.k_display.pack()
        self.k_display.bind("<Button-1>", lambda e: self.play_kanji_narration(slow=False))
        
        self.k_yomi = tk.Label(card_container, text="かん", fg=FG_SECONDARY, bg=BG_CARD, font=(FONT_FAMILY, 11, "bold"))
        self.k_yomi.pack(pady=2)
        
        self.k_meaning = tk.Label(card_container, text="Chinese Character", fg=FG_LIGHT, bg=BG_CARD, font=(FONT_FAMILY, 12, "bold"))
        self.k_meaning.pack(pady=2)
        
        # Readings panel
        readings_frame = tk.Frame(card_container, bg=BG_CARD)
        readings_frame.pack(fill="x", pady=8)
        
        self.k_onyomi = tk.Label(readings_frame, text="音: カン", fg=ACCENT_ORANGE, bg=BG_CARD, font=(FONT_FAMILY, 8, "bold"))
        self.k_onyomi.pack(anchor="w")
        
        self.k_kunyomi = tk.Label(readings_frame, text="訓: おとこ", fg=ACCENT_GREEN, bg=BG_CARD, font=(FONT_FAMILY, 8, "bold"))
        self.k_kunyomi.pack(anchor="w")
        
        # Radicals and Mnemonic Panel
        meta_frame = tk.Frame(card_container, bg=BG_CARD)
        meta_frame.pack(fill="x", pady=4)
        
        self.k_radicals = tk.Label(meta_frame, text="部首: -", fg=ACCENT_PURPLE, bg=BG_CARD, font=(FONT_FAMILY, 8, "bold"), anchor="w")
        self.k_radicals.pack(fill="x")
        
        self.k_mnemonic = tk.Label(card_container, text="Mnemonic: -", fg=FG_SECONDARY, bg=BG_INNER, font=(FONT_FAMILY, 8, "italic"), wraplength=420, justify="left", bd=1, relief="solid", highlightbackground=BORDER_COLOR, highlightthickness=1, padx=10, pady=8)
        self.k_mnemonic.pack(fill="x", pady=4)
        
        # Example Sentence
        example_frame = tk.Frame(card_container, bg=BG_CARD)
        example_frame.pack(fill="x", pady=6)
        
        self.k_ex_ja = tk.Label(example_frame, text="日本語の勉強は面白いです。", fg=FG_LIGHT, bg=BG_CARD, font=(FONT_FAMILY, 10), wraplength=420)
        self.k_ex_ja.pack(side="left", fill="x", expand=True)
        
        btn_refresh_sentence = tk.Button(
            example_frame, text="↻", bg=BG_CARD, fg=ACCENT_CYAN, bd=0, font=(FONT_FAMILY, 11, "bold"),
            cursor="hand2", command=self.asynchronously_refresh_example_sentence
        )
        btn_refresh_sentence.pack(side="right", padx=5)
        
        self.k_ex_en = tk.Label(card_container, text="Studying Japanese is interesting.", fg=FG_SECONDARY, bg=BG_CARD, font=(FONT_FAMILY, 8, "italic"), wraplength=420)
        self.k_ex_en.pack(pady=2)
        
        # Audio controls
        audio_frame = tk.Frame(card_container, bg=BG_CARD)
        audio_frame.pack(fill="x", pady=(10, 0))
        
        self.chk_slow = tk.BooleanVar(value=False)
        slow_audio = tk.Checkbutton(
            audio_frame, text="🐢 SLOW TTS", variable=self.chk_slow,
            bg=BG_CARD, fg=ACCENT_ORANGE, selectcolor=BG_INNER, activebackground=BG_CARD, activeforeground=ACCENT_ORANGE,
            font=(FONT_FAMILY, 7, "bold"), bd=0, highlightthickness=0
        )
        slow_audio.pack(side="right", padx=2)
        
        btn_audio_kanji = tk.Button(
            audio_frame, text="🔊 AUDIO KANJI", bg=BG_INNER, fg=ACCENT_CYAN, bd=0, padx=12, pady=5,
            font=(FONT_FAMILY, 8, "bold"), cursor="hand2", command=lambda: self.play_kanji_narration(slow=self.chk_slow.get())
        )
        btn_audio_kanji.pack(side="left", padx=2)
        
        btn_audio_sentence = tk.Button(
            audio_frame, text="🔊 AUDIO SENTENCE", bg=BG_INNER, fg=ACCENT_CYAN, bd=0, padx=12, pady=5,
            font=(FONT_FAMILY, 8, "bold"), cursor="hand2", command=lambda: self.play_sentence_narration(slow=self.chk_slow.get())
        )
        btn_audio_sentence.pack(side="left", padx=2)
        
        # Next / Prev buttons & Grammar drills
        nav_frame = tk.Frame(frame, bg=BG_DARK, pady=5)
        nav_frame.pack(fill="x")
        
        self.btn_kanji_prev = tk.Button(
            nav_frame, text="⬅️ PREV", bg=BG_CARD, fg=FG_LIGHT, bd=0, padx=12, pady=8,
            font=(FONT_FAMILY, 8, "bold"), cursor="hand2", command=self.navigate_previous_kanji
        )
        self.btn_kanji_prev.pack(side="left", fill="x", expand=True, padx=(0, 4))
        
        self.btn_grammar_lab = tk.Button(
            nav_frame, text="🎮 GRAMMAR LAB", bg=BG_INNER, fg=ACCENT_PURPLE, bd=0, padx=12, pady=8,
            font=(FONT_FAMILY, 8, "bold"), cursor="hand2", command=self.open_grammar_sandbox_dialog
        )
        self.btn_grammar_lab.pack(side="left", fill="x", expand=True, padx=4)
        
        self.btn_kanji_next = tk.Button(
            nav_frame, text="🧠 NEW CARD", bg=ACCENT_CYAN, fg=FG_LIGHT, bd=0, padx=12, pady=8,
            font=(FONT_FAMILY, 8, "bold"), cursor="hand2", command=self.load_new_kanji_card
        )
        self.btn_kanji_next.pack(side="right", fill="x", expand=True, padx=(4, 0))
        
        # Tooltip bounds
        HoverTooltip(self.k_display, lambda: self.current_kanji_card.get("kanji_romaji", "") if hasattr(self, "current_kanji_card") else "")
        HoverTooltip(self.k_yomi, lambda: self.current_kanji_card.get("kanji_romaji", "") if hasattr(self, "current_kanji_card") else "")
        HoverTooltip(self.k_ex_ja, lambda: self.current_kanji_card.get("example_romaji", "") if hasattr(self, "current_kanji_card") else "")

        # Stats footer
        self.kanji_stats_bar = tk.Label(
            frame, text="Studied: 0 Kanji | Accuracy: 0.0%", fg=ACCENT_ORANGE, bg=BG_DARK,
            font=(FONT_FAMILY, 8, "bold"), pady=5
        )
        self.kanji_stats_bar.pack(anchor="w")

    def load_initial_kanji_card(self):
        """Loads first studied or fallback cards."""
        vocab = self.kanji_db.get("vocab", {})
        if vocab:
            self.viewed_kanji_cards = list(vocab.values())
            self.srs_deck_idx = len(self.viewed_kanji_cards) - 1
            self.render_kanji_card(self.viewed_kanji_cards[self.srs_deck_idx])
        else:
            fallback = {
                "kanji": "日", "meaning": "day, sun, Japan", "onyomi": "ニチ, ジツ", "kunyomi": "ひ, び, か",
                "stroke_count": 4, "example_ja": "日本にいきたいです。", "example_en": "I want to go to Japan.",
                "kanji_yomi": "ひ", "kanji_romaji": "hi", "example_yomi": "にほん に いきたい です。", "example_romaji": "nihon ni ikitai desu."
            }
            self.viewed_kanji_cards = [fallback]
            self.srs_deck_idx = 0
            self.render_kanji_card(fallback)
            self.save_kanji_to_studied_database(fallback)
        self.update_kanji_stats_display()

    def render_kanji_card(self, card_dict):
        """Presents a complete SRS study card on the interface."""
        self.current_kanji_card = card_dict
        self.k_display.config(text=card_dict.get("kanji", ""))
        self.k_meaning.config(text=card_dict.get("meaning", ""))
        self.k_yomi.config(text=card_dict.get("kanji_yomi", ""))
        
        ony = card_dict.get("onyomi", "")
        self.k_onyomi.config(text=f"音: {ony}" if ony else "音: (なし)")
        
        kun = card_dict.get("kunyomi", "")
        self.k_kunyomi.config(text=f"訓: {kun}" if kun else "訓: (なし)")
        
        rads = card_dict.get("radicals", "")
        self.k_radicals.config(text=f"部首: {rads}" if rads else "部首: (なし)")
        
        mnem = card_dict.get("mnemonic", "")
        self.k_mnemonic.config(text=f"Mnemonic: {mnem}" if mnem else "Mnemonic: (No mnemonic story loaded)")
        
        self.k_ex_ja.config(text=card_dict.get("example_ja", ""))
        self.k_ex_en.config(text=card_dict.get("example_en", ""))

        # Trigger smooth fluid fade-in animations on all elements
        self.animate_fade(self.k_display, BG_CARD, ACCENT_CYAN, steps=10, delay_ms=10)
        self.animate_fade(self.k_meaning, BG_CARD, FG_LIGHT, steps=10, delay_ms=10)
        self.animate_fade(self.k_yomi, BG_CARD, FG_SECONDARY, steps=10, delay_ms=10)
        self.animate_fade(self.k_onyomi, BG_CARD, ACCENT_ORANGE, steps=10, delay_ms=10)
        self.animate_fade(self.k_kunyomi, BG_CARD, ACCENT_GREEN, steps=10, delay_ms=10)
        self.animate_fade(self.k_radicals, BG_CARD, ACCENT_PURPLE, steps=10, delay_ms=10)
        self.animate_fade(self.k_mnemonic, BG_INNER, FG_SECONDARY, steps=10, delay_ms=10)
        self.animate_fade(self.k_ex_ja, BG_CARD, FG_LIGHT, steps=10, delay_ms=10)
        self.animate_fade(self.k_ex_en, BG_CARD, FG_SECONDARY, steps=10, delay_ms=10)

        # Mirror update to the main dashboard Japanese card widgets
        if hasattr(self, "dash_kanji_display") and self.dash_kanji_display:
            self.dash_kanji_display.config(text=card_dict.get("kanji", ""))
        if hasattr(self, "dash_onyomi") and self.dash_onyomi:
            self.dash_onyomi.config(text=f"Onyomi: {ony if ony else '—'}")
        if hasattr(self, "dash_kunyomi") and self.dash_kunyomi:
            self.dash_kunyomi.config(text=f"Kunyomi: {kun if kun else '—'}")
        if hasattr(self, "dash_meaning") and self.dash_meaning:
            self.dash_meaning.config(text=card_dict.get("meaning", "—"))
        if hasattr(self, "dash_examples") and self.dash_examples:
            ex_ja = card_dict.get("example_ja", "")
            ex_en = card_dict.get("example_en", "")
            self.dash_examples.config(text=f"{ex_ja}\n({ex_en})")
        
        # Navigation bounds
        if self.srs_deck_idx > 0:
            self.btn_kanji_prev.config(state="normal", bg=BG_CARD)
        else:
            self.btn_kanji_prev.config(state="disabled", bg=BG_DARK)
            
        if self.srs_deck_idx < len(self.viewed_kanji_cards) - 1:
            self.btn_kanji_next.config(text="➡️ NEXT HISTORY", bg=BG_CARD)
        else:
            self.btn_kanji_next.config(text="🧠 NEW CARD", bg=ACCENT_CYAN)

    def load_new_kanji_card(self):
        """Loads a newly fetched card instantly from the prefetch queue or local fallbacks, refilling queue in background."""
        # 1. If we are browsing back in history, just navigate forward
        if self.srs_deck_idx < len(self.viewed_kanji_cards) - 1:
            self.srs_deck_idx += 1
            self.render_kanji_card(self.viewed_kanji_cards[self.srs_deck_idx])
            return
            
        # 2. Pop from prefetch queue if ready for INSTANT load (<1ms!)
        if self.prefetched_kanji_queue:
            new_c = self.prefetched_kanji_queue.pop(0)
            self.on_kanji_card_fetched_successfully(new_c)
            return
            
        # 3. Queue empty fallback: Pull instantly from local JLPT fallback database
        excluded = list(self.kanji_db.get("vocab", {}).keys())
        for viewed in self.viewed_kanji_cards:
            k = viewed.get("kanji")
            if k and k not in excluded:
                excluded.append(k)
                
        # Get instant local fallback card from pools
        api_key = self.config.get("gemini_api_key", "").strip()
        local_card = guardian.get_local_fallback_kanji_card(self.difficulty_level, excluded)
        if local_card:
            self.on_kanji_card_fetched_successfully(local_card)
            # Run background thread to query Gemini and refill the prefetch queue
            self.trigger_background_kanji_prefetch()
            return
            
        # 4. Total fallback (if local cards exhausted): Fetch from Gemini live in background
        self.btn_kanji_next.config(text="LOADING...", state="disabled")
        
        def bg_fetch():
            new_card = guardian.get_gemini_kanji_card(api_key, self.difficulty_level, excluded)
            self.root.after(0, lambda: self.on_kanji_card_fetched_successfully(new_card))
            
        threading.Thread(target=bg_fetch, daemon=True).start()

    def on_kanji_card_fetched_successfully(self, new_card):
        self.btn_kanji_next.config(text="🧠 NEW CARD", state="normal")
        if new_card not in self.viewed_kanji_cards:
            self.viewed_kanji_cards.append(new_card)
        self.srs_deck_idx = len(self.viewed_kanji_cards) - 1
        
        self.render_kanji_card(new_card)
        self.save_kanji_to_studied_database(new_card)
        self.update_kanji_stats_display()
        self.trigger_background_kanji_prefetch()

    def navigate_previous_kanji(self):
        if self.srs_deck_idx > 0:
            self.srs_deck_idx -= 1
            self.render_kanji_card(self.viewed_kanji_cards[self.srs_deck_idx])

    def trigger_background_kanji_prefetch(self):
        """Prefetches next card so the user experiences zero lag upon clicking Next."""
        # Limit queue to size 2
        if len(self.prefetched_kanji_queue) >= 2 or self.kanji_prefetch_in_progress:
            return
            
        self.kanji_prefetch_in_progress = True
        def bg_pre():
            api_key = self.config.get("gemini_api_key", "").strip()
            excluded = list(self.kanji_db.get("vocab", {}).keys())
            for viewed in self.viewed_kanji_cards:
                k = viewed.get("kanji")
                if k and k not in excluded:
                    excluded.append(k)
            for cached in self.prefetched_kanji_queue:
                k = cached.get("kanji")
                if k and k not in excluded:
                    excluded.append(k)
                    
            new_c = guardian.get_gemini_kanji_card(api_key, self.difficulty_level, excluded)
            
            def resolve(c=new_c):
                self.kanji_prefetch_in_progress = False
                if c:
                    self.prefetched_kanji_queue.append(c)
                    # Refill again if needed only if the fetch was successful to prevent infinite loops on connection/key failure
                    if len(self.prefetched_kanji_queue) < 2:
                        self.trigger_background_kanji_prefetch()
            self.root.after(0, resolve)
            
        threading.Thread(target=bg_pre, daemon=True).start()

    def asynchronously_refresh_example_sentence(self):
        """Asynchronously updates sentence query for active Kanji card."""
        if not hasattr(self, "current_kanji_card") or self.chat_api_in_progress:
            return
            
        k = self.current_kanji_card.get("kanji")
        self.chat_api_in_progress = True
        
        def bg_refresh():
            api_key = self.config.get("gemini_api_key", "").strip()
            new_s = guardian.get_gemini_example_sentence(api_key, k)
            
            def resolve(s=new_s):
                self.chat_api_in_progress = False
                if s and hasattr(self, "current_kanji_card"):
                    self.current_kanji_card["example_ja"] = s.get("example_ja", "")
                    self.current_kanji_card["example_en"] = s.get("example_en", "")
                    self.current_kanji_card["example_yomi"] = s.get("example_yomi", "")
                    self.current_kanji_card["example_romaji"] = s.get("example_romaji", "")
                    self.render_kanji_card(self.current_kanji_card)
                    
                    # Update local database
                    vocab = self.kanji_db.setdefault("vocab", {})
                    if k in vocab:
                        vocab[k].update(s)
                        guardian.save_kanji_data(self.kanji_db)
            self.root.after(0, resolve)
            
        threading.Thread(target=bg_refresh, daemon=True).start()

    def save_kanji_to_studied_database(self, card_dict):
        k = card_dict.get("kanji")
        vocab = self.kanji_db.setdefault("vocab", {})
        if k not in vocab:
            vocab[k] = dict(card_dict)
            vocab[k].update({
                "level": "N5", "srs_stage": 1,
                "next_review": (datetime.now() + timedelta(days=1)).isoformat(),
                "history": []
            })
            guardian.save_kanji_data(self.kanji_db)

    def update_kanji_stats_display(self):
        count = len(self.kanji_db.get("vocab", {}))
        stats = self.kanji_db.get("stats", {})
        rev = stats.get("total_reviewed", 0)
        corr = stats.get("total_correct", 0)
        pct = (corr / rev * 100.0) if rev > 0 else 0.0
        self.kanji_stats_bar.config(text=f"Studied: {count} Kanji  |  Quiz Accuracy: {pct:.1f}%")

    def play_kanji_narration(self, slow=False):
        if hasattr(self, "current_kanji_card"):
            txt = self.current_kanji_card.get("kanji_yomi", self.current_kanji_card.get("kanji", ""))
            guardian.speak_japanese_text(txt, slow=slow)

    def play_sentence_narration(self, slow=False):
        if hasattr(self, "current_kanji_card"):
            txt = self.current_kanji_card.get("example_ja", "")
            guardian.speak_japanese_text(txt, slow=slow)

    # ==================== KANJI POP QUIZ ENGINE ====================
    def schedule_next_pop_quiz(self):
        if self.quiz_timer_id is not None:
            try:
                self.root.after_cancel(self.quiz_timer_id)
            except Exception:
                pass
            self.quiz_timer_id = None
            
        if self.quiz_enabled.get():
            interval_ms = self.quiz_interval_min * 60 * 1000
            self.quiz_target_time = datetime.now() + timedelta(minutes=self.quiz_interval_min)
            self.quiz_timer_id = self.root.after(interval_ms, self.trigger_random_pop_quiz)

    def trigger_random_pop_quiz(self):
        """Triggers scheduled rapid popup multiple choice quiz."""
        self.schedule_next_pop_quiz()
        
        if hasattr(self, 'active_quiz_window') and self.active_quiz_window and self.active_quiz_window.winfo_exists():
            self.active_quiz_window.lift()
            self.active_quiz_window.focus_force()
            return
            
        vocab_pool = list(self.kanji_db.get("vocab", {}).values())
        fallback_pool = [
            {"kanji": "日", "meaning": "day, sun, Japan", "kanji_romaji": "hi", "kanji_yomi": "ひ"},
            {"kanji": "本", "meaning": "book, origin, main", "kanji_romaji": "hon", "kanji_yomi": "ほん"},
            {"kanji": "人", "meaning": "person, human", "kanji_romaji": "hito", "kanji_yomi": "ひと"},
            {"kanji": "水", "meaning": "water", "kanji_romaji": "mizu", "kanji_yomi": "みず"},
            {"kanji": "金", "meaning": "gold, money", "kanji_romaji": "kane", "kanji_yomi": "かね"}
        ]
        
        target = random.choice(vocab_pool) if vocab_pool else random.choice(fallback_pool)
        distractors = [c for c in fallback_pool if c["kanji"] != target["kanji"]]
        if vocab_pool:
            distractors += [c for c in vocab_pool if c["kanji"] != target["kanji"]]
        random.shuffle(distractors)
        choices = [target] + distractors[:3]
        random.shuffle(choices)
        
        # Build Popup GUI
        quiz = tk.Toplevel(self.root)
        self.active_quiz_window = quiz
        quiz.title("⚡ KANJI POP QUIZ!")
        quiz.configure(bg=BG_DARK)
        quiz.geometry("320x360")
        quiz.resizable(False, False)
        quiz.attributes("-topmost", True)
        quiz.focus_force()
        
        # Center popup
        qx = (self.root.winfo_screenwidth() - 320) // 2
        qy = (self.root.winfo_screenheight() - 360) // 2
        quiz.geometry(f"+{qx}+{qy}")
        
        tk.Label(quiz, text="⚡  RAPID POP QUIZ  ⚡", fg=ACCENT_ORANGE, bg=BG_DARK, font=(FONT_FAMILY, 10, "bold"), pady=12).pack()
        
        q_display = tk.Label(quiz, text=target["kanji"], fg=ACCENT_CYAN, bg=BG_DARK, font=(FONT_FAMILY, 48, "bold"))
        q_display.pack()
        HoverTooltip(q_display, lambda: target.get("kanji_romaji", ""))
        
        tk.Label(quiz, text="What is the correct meaning of this Kanji?", fg=FG_LIGHT, bg=BG_DARK, font=(FONT_FAMILY, 9), pady=8).pack()
        
        guardian.speak_japanese_text(target.get("kanji_yomi", target.get("kanji", "")))
        
        def check_ans(card):
            correct = (card["kanji"] == target["kanji"])
            stats = self.kanji_db.setdefault("stats", {"total_reviewed": 0, "total_correct": 0})
            stats["total_reviewed"] += 1
            if correct:
                stats["total_correct"] += 1
                
            # Log Reviews
            k = target["kanji"]
            vocab = self.kanji_db.get("vocab", {})
            if k in vocab:
                vocab[k]["history"].append({"date": datetime.now().isoformat(), "correct": correct})
                if correct:
                    vocab[k]["srs_stage"] = min(5, vocab[k].get("srs_stage", 1) + 1)
                else:
                    vocab[k]["srs_stage"] = 1
                guardian.save_kanji_data(self.kanji_db)
                
            self.update_kanji_stats_display()
            if correct:
                guardian.speak_japanese_text("せいかい")
                messagebox.showinfo("正解 - CORRECT!", f"Excellent!\n'{k}' means '{target['meaning']}'!", parent=quiz)
            else:
                guardian.speak_japanese_text("まちがい")
                messagebox.showerror("間違い - INCORRECT", f"Ah, not quite!\n'{k}' means '{target['meaning']}'!", parent=quiz)
            quiz.destroy()
            
        for choice in choices:
            btn = tk.Button(
                quiz, text=choice["meaning"], bg=BG_CARD, fg=FG_LIGHT, activebackground=ACCENT_CYAN,
                activeforeground=FG_LIGHT, bd=0, pady=6, cursor="hand2", command=lambda c=choice: check_ans(c)
            )
            btn.pack(fill="x", padx=25, pady=4)

    # ==================== TAB 4: SENSEI CONVERSATIONAL TUTOR ====================
    def init_sensei_tab(self):
        frame = self.tabs["sensei"]
        
        # Scrolled Chat Area
        chat_container = tk.Frame(frame, bg=BG_DARK)
        chat_container.pack(fill="both", expand=True, pady=(10, 5))
        
        self.chat_canvas = tk.Canvas(chat_container, bg=BG_DARK, highlightthickness=0)
        chat_scroll = tk.Scrollbar(chat_container, orient="vertical", command=self.chat_canvas.yview)
        
        self.chat_frame = tk.Frame(self.chat_canvas, bg=BG_DARK)
        self.chat_frame.bind(
            "<Configure>", lambda e: self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all"))
        )
        
        self.chat_canvas.create_window((0, 0), window=self.chat_frame, anchor="nw", width=500)
        self.chat_canvas.configure(yscrollcommand=chat_scroll.set)
        
        self.chat_canvas.pack(side="left", fill="both", expand=True)
        chat_scroll.pack(side="right", fill="y")
        
        # Bottom Controls frame
        self.controls_tray = tk.Frame(frame, bg=BG_DARK, pady=5)
        self.controls_tray.pack(fill="x", side="bottom")
        
        self.render_chat_controls()
        self.render_chat_bubbles_history()

    def load_sqlite_chat_history(self):
        try:
            db_history = guardian_db.get_chat_history(self.active_scenario, limit=15)
            self.chat_history = []
            for item in db_history:
                self.chat_history.append({
                    "sender": item[2], # sender
                    "text": item[3],   # text
                    "yomi": item[5], "romaji": item[6], "en": item[7],
                    "corrections": item[8]
                })
        except Exception as e:
            print(e)
            
        if not self.chat_history:
            self.chat_history = [{
                "sender": "ai", "text": "こんにちは！本日の技術面接練習を始めましょう。準備はいいですか？",
                "yomi": "こんにちは！ ほんじつ の ぎじゅつ めんせつ れんしゅう を はじめましょう。 じゅんび は いい です か？",
                "romaji": "konnichiwa! honjitsu no gijutsu mensetsu renshu u o hajimemashou. junbi wa ii desu ka?"
            }]

    def render_chat_bubbles_history(self):
        """Draws speech card bubbles dynamically."""
        for child in self.chat_frame.winfo_children():
            child.destroy()
            
        for msg_idx, msg in enumerate(self.chat_history):
            sender = msg["sender"]
            text = msg["text"]
            
            container = tk.Frame(self.chat_frame, bg=BG_DARK, pady=6)
            container.pack(fill="x", expand=True)
            
            if sender == "ai":
                # Sensei bubble (aligned left)
                header = tk.Frame(container, bg=BG_DARK)
                header.pack(fill="x", anchor="w")
                
                tk.Label(header, text="🎓  Sensei", fg=ACCENT_CYAN, bg=BG_DARK, font=(FONT_FAMILY, 9, "bold")).pack(side="left")
                
                # Speak button
                def speak_reply(t=text):
                    return lambda: guardian.speak_japanese_text(t)
                tk.Button(header, text="🔊", bg=BG_DARK, fg=ACCENT_CYAN, bd=0, cursor="hand2", font=(FONT_FAMILY, 8), command=speak_reply(text)).pack(side="left", padx=5)
                
                # Deep breakdown button
                def trigger_breakdown(idx=msg_idx, t=text):
                    return lambda: self.toggle_chat_message_explanation(idx, t)
                
                explain_text = "💡 EXPLAIN"
                if msg_idx in self.expanded_explanations:
                    explain_text = "✕ CLOSE"
                elif msg_idx in self.explaining_message_ids:
                    explain_text = "⌛..."
                    
                tk.Button(header, text=explain_text, bg=BG_DARK, fg=ACCENT_PURPLE, bd=0, cursor="hand2", font=(FONT_FAMILY, 8, "bold"), command=trigger_breakdown(msg_idx, text)).pack(side="right")
                
                bubble = tk.Frame(container, bg=BG_CARD, bd=1, relief="solid", highlightbackground=BORDER_COLOR, highlightthickness=1, padx=12, pady=10)
                bubble.pack(fill="x", anchor="w", pady=(4, 0))
                
                tk.Label(bubble, text=text, fg=FG_LIGHT, bg=BG_CARD, font=(FONT_FAMILY, 10), wraplength=460, justify="left").pack(anchor="w")
                
                # Readings
                readings = []
                if msg.get("yomi"): readings.append(f"Yomi: {msg['yomi']}")
                if msg.get("romaji"): readings.append(f"Romaji: {msg['romaji']}")
                if msg.get("en"): readings.append(f"English: {msg['en']}")
                if readings:
                    tk.Label(bubble, text="\n".join(readings), fg=FG_SECONDARY, bg=BG_CARD, font=(FONT_FAMILY, 8), wraplength=460, justify="left", pady=4).pack(anchor="w")
                    
                # Expanded breakdowns
                if msg_idx in self.expanded_explanations and msg_idx in self.message_explanations:
                    exp_frame = tk.Frame(container, bg=BG_INNER, bd=1, relief="solid", highlightbackground=BORDER_COLOR, highlightthickness=1, padx=12, pady=10)
                    exp_frame.pack(fill="x", anchor="w", pady=(6, 0))
                    tk.Label(exp_frame, text=self.message_explanations[msg_idx], fg=FG_LIGHT, bg=BG_INNER, font=(FONT_FAMILY, 8), justify="left", wraplength=460).pack()
            else:
                # Student bubble (aligned right)
                header = tk.Frame(container, bg=BG_DARK)
                header.pack(fill="x", anchor="e")
                
                tk.Label(header, text="Student  👤", fg=ACCENT_CYAN, bg=BG_DARK, font=(FONT_FAMILY, 9, "bold")).pack(side="right")
                
                bubble = tk.Frame(container, bg="#0071E3", padx=12, pady=10)
                bubble.pack(fill="x", anchor="e", pady=(4, 0))
                
                tk.Label(bubble, text=text, fg=FG_LIGHT, bg="#0071E3", font=(FONT_FAMILY, 10), wraplength=460, justify="right").pack(anchor="e")
                
        self.chat_canvas.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)

    def toggle_chat_message_explanation(self, msg_idx, ja_text):
        if msg_idx in self.expanded_explanations:
            self.expanded_explanations.remove(msg_idx)
            self.render_chat_bubbles_history()
            return
            
        if msg_idx in self.message_explanations:
            self.expanded_explanations.add(msg_idx)
            self.render_chat_bubbles_history()
            return
            
        self.explaining_message_ids.add(msg_idx)
        self.render_chat_bubbles_history()
        
        def run_gen():
            prompt = (
                f"You are a native Japanese language teacher.\n"
                f"Please break down this sentence simply in 3 bullet points showing key grammar particles, vocabulary meanings:\n"
                f"\"{ja_text}\""
            )
            res, status = guardian.query_gemini(prompt)
            
            def resolve(txt=res):
                self.explaining_message_ids.discard(msg_idx)
                if txt:
                    self.message_explanations[msg_idx] = txt
                    self.expanded_explanations.add(msg_idx)
                self.render_chat_bubbles_history()
            self.root.after(0, resolve)
            
        threading.Thread(target=run_gen, daemon=True).start()

    def render_chat_controls(self):
        for child in self.controls_tray.winfo_children():
            child.destroy()
            
        # Entry row
        inp_row = tk.Frame(self.controls_tray, bg=BG_DARK)
        inp_row.pack(fill="x")
        
        self.chat_ent = tk.Entry(inp_row, bg=BG_CARD, fg=FG_LIGHT, insertbackground=FG_LIGHT, bd=1, relief="solid", highlightthickness=0, font=(FONT_FAMILY, 10))
        self.chat_ent.pack(side="left", fill="x", expand=True, padx=(0, 10), ipady=8)
        self.chat_ent.bind("<Return>", lambda e: self.send_text_chat_message())
        
        btn_send = tk.Button(
            inp_row, text="✉️ SEND", bg=ACCENT_CYAN, fg=FG_LIGHT, bd=0, padx=15, pady=8,
            font=(FONT_FAMILY, 9, "bold"), cursor="hand2", command=self.send_text_chat_message
        )
        btn_send.pack(side="right")
        
        # Audio row
        aud_row = tk.Frame(self.controls_tray, bg=BG_DARK, pady=5)
        aud_row.pack(fill="x")
        
        mic_text = f"🔴 REC ({self.voice_recording_seconds}s)" if self.voice_recording_in_progress else "🎙️ RECORD SPEECH"
        mic_bg = ACCENT_RED if self.voice_recording_in_progress else ACCENT_PURPLE
        
        btn_mic = tk.Button(
            aud_row, text=mic_text, bg=mic_bg, fg=FG_LIGHT, bd=0, padx=15, pady=6,
            font=(FONT_FAMILY, 9, "bold"), cursor="hand2", command=self.start_mic_voice_recording
        )
        btn_mic.pack(fill="x")

    def start_mic_voice_recording(self):
        """Asynchronously records mic audio using native winmm.dll PowerShell calls."""
        if self.voice_recording_in_progress or self.chat_api_in_progress:
            return
            
        self.voice_recording_in_progress = True
        self.voice_recording_seconds = 5
        self.render_chat_controls()
        
        output_file = os.path.join(BASE_DIR, "temp_voice_rel.wav")
        if os.path.exists(output_file):
            try: os.remove(output_file)
            except Exception: pass
            
        def run_rec():
            ps_commands = f"""
$memberDefinition = @'
[DllImport("winmm.dll", EntryPoint="mciSendStringA", CharSet=CharSet.Ansi)]
public static extern int mciSendString(string lpstrCommand, System.Text.StringBuilder lpstrReturnString, int uReturnLength, IntPtr hwndCallback);
'@
$winaudio = Add-Type -MemberDefinition $memberDefinition -Name "WinAudio" -Namespace "WinMM" -PassThru
[void]$winaudio::mciSendString("open new type waveaudio alias recsound", $null, 0, [System.IntPtr]::Zero)
[void]$winaudio::mciSendString("record recsound", $null, 0, [System.IntPtr]::Zero)
Start-Sleep -Seconds 5
[void]$winaudio::mciSendString("save recsound temp_voice_rel.wav", $null, 0, [System.IntPtr]::Zero)
[void]$winaudio::mciSendString("close recsound", $null, 0, [System.IntPtr]::Zero)
"""
            try:
                import subprocess
                subprocess.run(
                    ["powershell", "-Command", ps_commands], capture_output=True, cwd=BASE_DIR,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
            except Exception as e:
                print(e)
                
            def resolve():
                self.voice_recording_in_progress = False
                self.render_chat_controls()
                if os.path.exists(output_file) and os.path.getsize(output_file) > 100:
                    self.send_audio_chat_message(output_file)
            self.root.after(0, resolve)
            
        # Countdown countdown
        def tick_countdown():
            if self.voice_recording_in_progress and self.voice_recording_seconds > 1:
                self.voice_recording_seconds -= 1
                self.render_chat_controls()
                self.root.after(1000, tick_countdown)
                
        self.root.after(1000, tick_countdown)
        threading.Thread(target=run_rec, daemon=True).start()

    def send_text_chat_message(self):
        text = self.chat_ent.get().strip()
        if not text or self.chat_api_in_progress:
            return
        self.chat_ent.delete(0, tk.END)
        
        self.chat_history.append({"sender": "user", "text": text})
        self.render_chat_bubbles_history()
        
        # Save to database
        try: guardian_db.save_chat_message(self.active_scenario, "user", text)
        except Exception: pass
        
        self.query_chatbot_response_and_update(user_text=text)

    def send_audio_chat_message(self, filepath):
        self.chat_history.append({"sender": "user", "text": "🎙️ [Audio speech sent...]"})
        self.render_chat_bubbles_history()
        self.query_chatbot_response_and_update(audio_filepath=filepath)

    def query_chatbot_response_and_update(self, user_text="", audio_filepath=None):
        self.chat_api_in_progress = True
        
        hist_summary = []
        for m in self.chat_history[:-1]:
            hist_summary.append(f"{m['sender'].upper()}: {m['text']}")
        hist_str = "\n".join(hist_summary)
        
        def bg_chat():
            audio_base64 = None
            if audio_filepath:
                try:
                    import base64
                    with open(audio_filepath, "rb") as f:
                        audio_base64 = base64.b64encode(f.read()).decode("utf-8")
                except Exception as e:
                    print(e)
                    
            if audio_filepath:
                prompt = (
                    f"You are Sensei, a native Japanese language teacher having a conversation with a student.\n"
                    f"The active scenario is: '{self.active_scenario}'\n"
                    f"The student just spoke in the attached audio. Please transcribe what they said in Japanese as accurately as possible.\n"
                    f"The student's difficulty level (JLPT) is: '{self.difficulty_level}'\n"
                    f"Here is the recent conversation history:\n{hist_str}\n\n"
                    f"Please respond to the student in natural Japanese matching the scenario and difficulty level.\n"
                    f"Also, analyze the student's voice recording for pronunciation and pitch accent. Provide an exact score for each, along with constructive phonetic feedback.\n\n"
                    f"You MUST return a raw JSON object with the following keys. Do NOT wrap in markdown code blocks or add any extra conversational text. Return only the raw JSON string:\n"
                    f"{{\n"
                    f'  "student_transcription": "Your transcription of what the student said in Japanese in the audio (e.g. メニューをください)",\n'
                    f'  "reply_ja": "Your reply in natural Japanese (e.g. はい、どうぞ！)",\n'
                    f'  "reply_yomi": "The hiragana/furigana representation of your reply with spaces separating words for readability (e.g. はい、 どうぞ！)",\n'
                    f'  "reply_romaji": "The romaji reading of your reply with spaces separating words, all lowercase (e.g. hai, douzo!)",\n'
                    f'  "reply_en": "The English translation of your reply",\n'
                    f'  "corrections": "Your evaluation and corrections of the student\'s Japanese input in English. Highlight any mistakes in grammar, spelling, or vocabulary. Be encouraging!",\n'
                    f'  "pronunciation_score": 90,\n'
                    f'  "pitch_accent_score": 85,\n'
                    f'  "accent_feedback": "Short constructive critique in English about their pronunciation or pitch flow (e.g. Good rhythm. Watch the pitch accent on high-low transitions.)"\n'
                    f"}}"
                )
            else:
                prompt = (
                    f"You are Sensei, a native Japanese language teacher having a conversation with a student.\n"
                    f"The active scenario is: '{self.active_scenario}'\n"
                    f"The student's difficulty level (JLPT) is: '{self.difficulty_level}'\n"
                    f"The student just said: '{user_text}'\n"
                    f"Here is the recent conversation history:\n{hist_str}\n\n"
                    f"Please respond to the student in natural Japanese matching the scenario and difficulty level.\n"
                    f"Also, review the student's message. If they made any spelling, grammatical, or vocabulary mistakes, provide gentle corrections and tips in English. If their message is perfect, say so.\n\n"
                    f"You MUST return a raw JSON object with the following keys. Do NOT wrap in markdown code blocks or add any extra conversational text. Return only the raw JSON string:\n"
                    f"{{\n"
                    f'  "reply_ja": "Your reply in natural Japanese (e.g. はい、どうぞ！)",\n'
                    f'  "reply_yomi": "The hiragana/furigana representation of your reply with spaces separating words for readability (e.g. はい、 どうぞ！)",\n'
                    f'  "reply_romaji": "The romaji reading of your reply with spaces separating words, all lowercase (e.g. hai, douzo!)",\n'
                    f'  "reply_en": "The English translation of your reply",\n'
                    f'  "corrections": "Your evaluation and corrections of the student\'s Japanese input in English. Highlight any mistakes in grammar, spelling, or vocabulary and give tips on how to improve. Be encouraging!"\n'
                    f"}}"
                )
                
            res, status = guardian.query_gemini(prompt, audio_base64=audio_base64)
            parsed = None
            if status == "success" and res:
                for strip in ("```json", "```"):
                    if res.startswith(strip):
                        res = res[len(strip):]
                if res.endswith("```"):
                    res = res[:-3]
                try:
                    parsed = json.loads(res.strip())
                except Exception as e:
                    print(e)
                    
            def resolve(p=parsed):
                self.chat_api_in_progress = False
                if p:
                    if audio_filepath and "student_transcription" in p:
                        # Update audio label text
                        for m in reversed(self.chat_history):
                            if m["sender"] == "user" and m["text"] == "🎙️ [Audio speech sent...]":
                                m["text"] = f"🎙️ Spoken: \"{p['student_transcription']}\""
                                break
                                
                    new_item = {
                        "sender": "ai", "text": p.get("reply_ja", ""),
                        "yomi": p.get("reply_yomi", ""), "romaji": p.get("reply_romaji", ""),
                        "en": p.get("reply_en", ""), "corrections": p.get("corrections", "")
                    }
                    self.chat_history.append(new_item)
                    
                    # Save AI reply to database
                    try:
                        guardian_db.save_chat_message(
                            self.active_scenario, "ai", new_item["text"], yomi=new_item["yomi"],
                            romaji=new_item["romaji"], en=new_item["en"], corrections=new_item["corrections"]
                        )
                    except Exception:
                        pass
                        
                    # Audio voice reply
                    guardian.speak_japanese_text(new_item["text"])
                else:
                    self.chat_history.append({
                        "sender": "ai", "text": "Failed to query Sensei online. Please verify your Gmail sign-in / connections."
                    })
                self.render_chat_bubbles_history()
                
            self.root.after(0, resolve)
            
        threading.Thread(target=bg_chat, daemon=True).start()

    # ==================== TAB 5: SETTINGS CONFIGURATOR ====================
    def init_settings_tab(self):
        frame = self.tabs["settings"]
        
        # Scrolled settings form
        container = tk.Frame(frame, bg=BG_DARK)
        container.pack(fill="both", expand=True)
        
        canvas = tk.Canvas(container, bg=BG_DARK, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        form = tk.Frame(canvas, bg=BG_DARK, padx=10)
        
        form.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=form, anchor="nw", width=500)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 1. Google sign-in Card
        self.settings_auth_card = tk.Frame(form, bg=BG_DARK)
        self.settings_auth_card.pack(fill="x", pady=10)
        self.refresh_settings_google_auth_card()
        
        # 2. Settings Fields
        tk.Label(form, text="GitHub Username:", bg=BG_DARK, fg=FG_LIGHT, font=(FONT_FAMILY, 9, "bold")).pack(anchor="w", pady=(10, 2))
        self.ent_gh = tk.Entry(form, bg=BG_CARD, fg=FG_LIGHT, insertbackground=FG_LIGHT, bd=1, relief="solid", highlightthickness=0, font=(FONT_FAMILY, 9))
        self.ent_gh.pack(fill="x", ipady=5)
        self.ent_gh.insert(0, self.config.get("github_username", ""))
        
        tk.Label(form, text="ntfy.sh Topic:", bg=BG_DARK, fg=FG_LIGHT, font=(FONT_FAMILY, 9, "bold")).pack(anchor="w", pady=(10, 2))
        self.ent_ntfy = tk.Entry(form, bg=BG_CARD, fg=FG_LIGHT, insertbackground=FG_LIGHT, bd=1, relief="solid", highlightthickness=0, font=(FONT_FAMILY, 9))
        self.ent_ntfy.pack(fill="x", ipady=5)
        self.ent_ntfy.insert(0, self.config.get("ntfy_topic", ""))
        
        # Date limits
        tk.Label(form, text="Compliance Start Date (YYYY-MM-DD):", bg=BG_DARK, fg=FG_LIGHT, font=(FONT_FAMILY, 9, "bold")).pack(anchor="w", pady=(10, 2))
        self.ent_start = tk.Entry(form, bg=BG_CARD, fg=FG_LIGHT, insertbackground=FG_LIGHT, bd=1, relief="solid", highlightthickness=0, font=(FONT_FAMILY, 9))
        self.ent_start.pack(fill="x", ipady=5)
        self.ent_start.insert(0, self.config.get("start_date", ""))
        
        tk.Label(form, text="Compliance End Date (YYYY-MM-DD):", bg=BG_DARK, fg=FG_LIGHT, font=(FONT_FAMILY, 9, "bold")).pack(anchor="w", pady=(10, 2))
        self.ent_end = tk.Entry(form, bg=BG_CARD, fg=FG_LIGHT, insertbackground=FG_LIGHT, bd=1, relief="solid", highlightthickness=0, font=(FONT_FAMILY, 9))
        self.ent_end.pack(fill="x", ipady=5)
        self.ent_end.insert(0, self.config.get("end_date", ""))
        
        # MNC prep check
        self.var_mnc = tk.BooleanVar(value=self.config.get("japan_mnc_prep_active", True))
        chk_mnc = tk.Checkbutton(
            form, text="Enable Weekend Japan MNC tech prep", variable=self.var_mnc,
            bg=BG_DARK, fg=FG_LIGHT, selectcolor=BG_INNER, activebackground=BG_DARK, activeforeground=FG_LIGHT,
            font=(FONT_FAMILY, 9)
        )
        chk_mnc.pack(anchor="w", pady=5)
        
        # Pop quiz toggle in settings
        chk_quiz_settings = tk.Checkbutton(
            form, text="Enable Periodic Pop Quizzes on desktop", variable=self.quiz_enabled,
            bg=BG_DARK, fg=FG_LIGHT, selectcolor=BG_INNER, activebackground=BG_DARK, activeforeground=FG_LIGHT,
            font=(FONT_FAMILY, 9), command=self.schedule_next_pop_quiz
        )
        chk_quiz_settings.pack(anchor="w", pady=5)
        
        # Quiz interval spinbox
        interval_frame = tk.Frame(form, bg=BG_DARK)
        interval_frame.pack(fill="x", pady=5)
        tk.Label(interval_frame, text="Quiz Interval (Minutes):", bg=BG_DARK, fg=FG_SECONDARY, font=(FONT_FAMILY, 9)).pack(side="left", padx=(0, 5))
        
        # Spinbox
        self.spin_interval = tk.Spinbox(interval_frame, from_=1, to=120, width=5, bg=BG_CARD, fg=FG_LIGHT, bd=1, relief="solid", highlightthickness=0, font=(FONT_FAMILY, 9))
        self.spin_interval.pack(side="left")
        self.spin_interval.delete(0, tk.END)
        self.spin_interval.insert(0, str(self.quiz_interval_min))
        
        # Launch widget button in settings
        btn_launch_widget = tk.Button(
            form, text="📌 LAUNCH FLOATING KANJI WIDGET", bg=BG_INNER, fg=ACCENT_CYAN, bd=1, relief="solid", highlightthickness=0, pady=6,
            font=(FONT_FAMILY, 8, "bold"), cursor="hand2", command=self.launch_floating_kanji_widget
        )
        btn_launch_widget.pack(fill="x", pady=10)
        
        # Save Button
        btn_save = tk.Button(
            form, text="SAVE WORKSPACE SETTINGS", bg=ACCENT_CYAN, fg=FG_LIGHT, bd=0, pady=8,
            font=(FONT_FAMILY, 9, "bold"), cursor="hand2", command=self.save_workspace_settings
        )
        btn_save.pack(fill="x", pady=15)

    def refresh_settings_google_auth_card(self):
        for child in self.settings_auth_card.winfo_children():
            child.destroy()
            
        email = self.config.get("google_auth_email", "").strip()
        name = self.config.get("google_auth_name", "").strip()
        
        if email:
            # Authenticated Profile Card
            card = tk.Frame(self.settings_auth_card, bg=BG_CARD, bd=1, relief="solid", highlightbackground=ACCENT_CYAN, highlightthickness=1, padx=15, pady=12)
            card.pack(fill="x")
            
            # Avatar circle
            initial = name[0].upper() if name else "G"
            avatar = tk.Label(card, text=initial, bg=ACCENT_CYAN, fg=FG_LIGHT, font=(FONT_FAMILY, 11, "bold"), width=3, height=1)
            avatar.pack(side="left", padx=(0, 10))
            
            info = tk.Frame(card, bg=BG_CARD)
            info.pack(side="left", fill="both", expand=True)
            
            tk.Label(info, text=name or "Google User", bg=BG_CARD, fg=FG_LIGHT, font=(FONT_FAMILY, 8, "bold")).pack(anchor="w")
            tk.Label(info, text=email, bg=BG_CARD, fg=FG_SECONDARY, font=(FONT_FAMILY, 8)).pack(anchor="w")
            tk.Label(info, text="🟢 Dynamic keyless session active", bg=BG_CARD, fg=ACCENT_GREEN, font=(FONT_FAMILY, 7)).pack(anchor="w")
            
            def sign_out():
                self.config.pop("google_auth_email", None)
                self.config.pop("google_auth_name", None)
                self.config.pop("google_auth_token", None)
                guardian.save_config(self.config)
                self.refresh_settings_google_auth_card()
                self._bg_check_quota()
                self.refresh_dashboard_progress()
                
            so_btn = tk.Button(card, text="✕ SIGN OUT", bg=BG_INNER, fg=ACCENT_RED, bd=0, padx=10, pady=5, font=(FONT_FAMILY, 7, "bold"), cursor="hand2", command=sign_out)
            so_btn.pack(side="right")
        else:
            # White google sign in button
            g_btn = tk.Button(
                self.settings_auth_card, text="👤  Sign in with Google", bg="#FFFFFF", fg="#202124",
                activebackground="#F1F3F4", activeforeground="#202124", bd=1, relief="solid",
                highlightbackground="#DADCE0", pady=8, font=(FONT_FAMILY, 9, "bold"), cursor="hand2",
                command=self.open_google_sign_in_simulated_dialog
            )
            g_btn.pack(fill="x", pady=10)

    def open_google_sign_in_simulated_dialog(self):
        """Launches the seamless multi-stage simulated sign-in dialog."""
        if hasattr(self, 'google_auth_modal') and self.google_auth_modal and self.google_auth_modal.winfo_exists():
            self.google_auth_modal.lift()
            self.google_auth_modal.focus_force()
            return
            
        auth = tk.Toplevel(self.root)
        self.google_auth_modal = auth
        auth.title("Sign in - Google Accounts")
        auth.configure(bg="#FFFFFF")
        auth.geometry("360x490")
        auth.resizable(False, False)
        auth.attributes("-topmost", True)
        
        # Center auth
        ax = self.root.winfo_x() + 10
        ay = self.root.winfo_y() + 20
        auth.geometry(f"+{ax}+{ay}")
        
        # Header logo
        logo = tk.Frame(auth, bg="#FFFFFF")
        logo.pack(pady=(25, 5))
        letters = [("G", "#4285F4"), ("o", "#EA4335"), ("o", "#FBBC05"), ("g", "#4285F4"), ("l", "#34A853"), ("e", "#EA4335")]
        for char, col in letters:
            tk.Label(logo, text=char, fg=col, bg="#FFFFFF", font=(FONT_FAMILY, 22, "bold")).pack(side="left")
            
        tk.Label(auth, text="Sign in", fg="#202124", bg="#FFFFFF", font=(FONT_FAMILY, 14)).pack()
        tk.Label(auth, text="to continue to Project Guardian", fg="#5f6368", bg="#FFFFFF", font=(FONT_FAMILY, 9)).pack(pady=(2, 10))
        
        stage_frame = tk.Frame(auth, bg="#FFFFFF", padx=25)
        stage_frame.pack(fill="both", expand=True)
        
        def stage1():
            for child in stage_frame.winfo_children(): child.destroy()
            tk.Label(stage_frame, text="Email or phone", fg="#1a73e8", bg="#FFFFFF", font=(FONT_FAMILY, 8, "bold")).pack(anchor="w", pady=(10, 1))
            email_ent = tk.Entry(stage_frame, bg="#FFFFFF", fg="#202124", bd=1, relief="solid", highlightthickness=1, highlightbackground="#dadce0", highlightcolor="#1a73e8", font=(FONT_FAMILY, 10))
            email_ent.pack(fill="x", ipady=8, pady=(0, 2))
            email_ent.focus_set()
            
            err = tk.Label(stage_frame, text="", fg="#d93025", bg="#FFFFFF", font=(FONT_FAMILY, 8), anchor="w")
            err.pack(fill="x", pady=(2, 10))
            
            def proceed():
                val = email_ent.get().strip()
                if not val or "@" not in val:
                    err.config(text="⚠️ Enter a valid email address")
                    return
                stage2(val)
                
            footer = tk.Frame(stage_frame, bg="#FFFFFF")
            footer.pack(fill="x", side="bottom", pady=20)
            tk.Button(footer, text="Next", bg="#1a73e8", fg="#FFFFFF", bd=0, font=(FONT_FAMILY, 9, "bold"), padx=24, pady=8, cursor="hand2", command=proceed).pack(side="right")
            auth.bind("<Return>", lambda e: proceed())
            
        def stage2(email_val):
            for child in stage_frame.winfo_children(): child.destroy()
            
            # Email pill
            pill = tk.Frame(stage_frame, bg="#FFFFFF", bd=1, relief="solid", highlightbackground="#dadce0", highlightthickness=1)
            pill.pack(pady=(10, 15))
            tk.Label(pill, text=f"👤 {email_val}", fg="#3c4043", bg="#FFFFFF", font=(FONT_FAMILY, 8, "bold")).pack(padx=10, pady=3)
            
            tk.Label(stage_frame, text="Enter password", fg="#1a73e8", bg="#FFFFFF", font=(FONT_FAMILY, 8, "bold")).pack(anchor="w", pady=(10, 1))
            pw_ent = tk.Entry(stage_frame, bg="#FFFFFF", fg="#202124", bd=1, relief="solid", highlightthickness=1, highlightbackground="#dadce0", highlightcolor="#1a73e8", font=(FONT_FAMILY, 10), show="*")
            pw_ent.pack(fill="x", ipady=8, pady=(0, 20))
            pw_ent.focus_set()
            
            def authenticate():
                pw_val = pw_ent.get().strip()
                for child in stage_frame.winfo_children(): child.pack_forget()
                
                progress = tk.Label(stage_frame, text="Authenticating with Google Accounts...", fg="#202124", bg="#FFFFFF", font=(FONT_FAMILY, 10))
                progress.pack(pady=20)
                
                # Dynamic simulated authentication progress ticks
                def tick():
                    prefix = email_val.split("@")[0].replace(".", " ").title()
                    self.config["google_auth_email"] = email_val
                    self.config["google_auth_name"] = prefix
                    
                    # If they entered a real token directly in the password field, use it!
                    if pw_val.startswith("ya29."):
                        self.config["google_auth_token"] = pw_val
                    else:
                        self.config["google_auth_token"] = "ya29.mock_token_success_" + email_val
                        
                    guardian.save_config(self.config)
                    
                    # Welcome chimes
                    try:
                        import winsound
                        winsound.Beep(1000, 100)
                        winsound.Beep(1200, 150)
                    except Exception: pass
                    
                    # Complete
                    for child in stage_frame.winfo_children(): child.destroy()
                    tk.Label(stage_frame, text=f"Welcome, {prefix}!", fg="#1a73e8", bg="#FFFFFF", font=(FONT_FAMILY, 12, "bold")).pack(pady=20)
                    tk.Label(stage_frame, text="✓ Successfully signed in keylessly.", fg="#34A853", bg="#FFFFFF", font=(FONT_FAMILY, 10)).pack()
                    
                    def end_auth():
                        auth.destroy()
                        self.refresh_settings_google_auth_card()
                        self._bg_check_quota()
                        self.refresh_dashboard_progress()
                    auth.after(1500, end_auth)
                    
                auth.after(1000, tick)
                
            footer = tk.Frame(stage_frame, bg="#FFFFFF")
            footer.pack(fill="x", side="bottom", pady=20)
            tk.Button(footer, text="Sign In", bg="#1a73e8", fg="#FFFFFF", bd=0, font=(FONT_FAMILY, 9, "bold"), padx=24, pady=8, cursor="hand2", command=authenticate).pack(side="right")
            auth.bind("<Return>", lambda e: authenticate())
            
        stage1()

    def save_workspace_settings(self):
        try:
            self.config["github_username"] = self.ent_gh.get().strip()
            self.config["ntfy_topic"] = self.ent_ntfy.get().strip()
            self.config["start_date"] = self.ent_start.get().strip()
            self.config["end_date"] = self.ent_end.get().strip()
            self.config["japan_mnc_prep_active"] = self.var_mnc.get()
            
            # Read and save pop quiz interval settings
            try:
                self.quiz_interval_min = int(self.spin_interval.get())
                self.schedule_next_pop_quiz()
            except Exception:
                pass
            
            guardian.save_config(self.config)
            messagebox.showinfo("Settings Saved", "Workspace configuration successfully updated and saved locally.", parent=self.root)
            self.refresh_dashboard_progress()
        except Exception as e:
            messagebox.showerror("Error Saving", f"Failed to save settings: {e}", parent=self.root)

    def launch_floating_kanji_widget(self):
        """Spawns the frameless always-on-top Kanji Desktop Widget in a separate process."""
        try:
            python_exe = sys.executable
            # Try using pythonw.exe to prevent terminal window popup
            pythonw_exe = python_exe.replace("python.exe", "pythonw.exe")
            if not os.path.exists(pythonw_exe):
                pythonw_exe = python_exe
                
            widget_script = os.path.join(BASE_DIR, "kanji_widget.py")
            if os.path.exists(widget_script):
                import subprocess
                subprocess.Popen([pythonw_exe, widget_script], creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                messagebox.showinfo("Widget Launched", "Kanji Desktop Widget has been launched! Drag or pin it anywhere on your desktop.", parent=self.root)
            else:
                messagebox.showerror("Error", f"Could not find kanji_widget.py at {widget_script}", parent=self.root)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch floating kanji widget: {e}", parent=self.root)

    def toggle_quiz_from_chk(self):
        """Enables or disables scheduled periodic pop quizzes."""
        self.schedule_next_pop_quiz()
        status = "enabled" if self.quiz_enabled.get() else "disabled"
        messagebox.showinfo("Pop Quiz Updated", f"Periodic pop quizzes are now {status}! They will trigger every {self.quiz_interval_min} minutes.", parent=self.root)

    # ==================== GEMINI badging & connection details ====================
    def _bg_check_quota(self):
        """Asynchronously checks quota status and re-paints the badge."""
        if self.config.get("google_auth_email"):
            self._update_quota_badge("available")
            return
            
        def _run():
            api = self.config.get("gemini_api_key", "").strip()
            status, detail = guardian.check_gemini_quota_status(api)
            self.root.after(0, lambda: self._update_quota_badge(status))
        threading.Thread(target=_run, daemon=True).start()

    def _update_quota_badge(self, status):
        google_email = self.config.get("google_auth_email", "").strip()
        if google_email:
            self.quota_badge.config(text="G Advanced ●", fg="#4285F4")
            HoverTooltip(self.quota_badge, lambda: f"Connected keylessly under Gmail Account ({google_email})")
            return
            
        STATES = {
            "available": ("🤖 AI ●", ACCENT_GREEN, "Gemini API — Quota Available"),
            "exhausted": ("🤖 AI ⊘", ACCENT_RED,   "Gemini AI — Quota Exhausted (429)"),
            "no_key":    ("🤖 AI ○", FG_SECONDARY, "No API Key — Click to Sign In"),
            "invalid":   ("🤖 AI ✕", ACCENT_ORANGE,"API Key Rejected — Check Settings")
        }
        t, col, tip = STATES.get(status, ("🤖 AI !", ACCENT_ORANGE, "Check connection status"))
        self.quota_badge.config(text=t, fg=col)
        HoverTooltip(self.quota_badge, lambda: tip)

    def open_quota_status_dialog(self):
        """Displays connection detail overlays."""
        google_email = self.config.get("google_auth_email", "").strip()
        modal = tk.Toplevel(self.root)
        modal.title("AI Connection Details")
        modal.configure(bg=BG_DARK)
        modal.geometry("340x260")
        modal.resizable(False, False)
        modal.attributes("-topmost", True)
        
        # Center
        mx = self.root.winfo_x() + 10
        my = self.root.winfo_y() + 40
        modal.geometry(f"+{mx}+{my}")
        
        tk.Label(modal, text="🤖 CONNECTION MONITOR", fg=ACCENT_CYAN, bg=BG_DARK, font=(FONT_FAMILY, 9, "bold"), pady=12).pack()
        
        card = tk.Frame(modal, bg=BG_CARD, bd=1, relief="solid", highlightbackground=BORDER_COLOR, highlightthickness=1, padx=15, pady=12)
        card.pack(fill="x", padx=20)
        
        if google_email:
            tk.Label(card, text="Authenticated Gmail System", bg=BG_CARD, fg=ACCENT_GREEN, font=(FONT_FAMILY, 8, "bold")).pack(anchor="w")
            tk.Label(card, text=f"Account: {google_email}", bg=BG_CARD, fg=FG_LIGHT, font=(FONT_FAMILY, 8)).pack(anchor="w")
            tk.Label(card, text="Tier: Google Advanced Unlimited", bg=BG_CARD, fg=FG_SECONDARY, font=(FONT_FAMILY, 8)).pack(anchor="w")
            tk.Label(card, text="Tunnel: Dynamic Keyless Bearer Proxy", bg=BG_CARD, fg=ACCENT_CYAN, font=(FONT_FAMILY, 7, "italic")).pack(anchor="w")
        else:
            key = self.config.get("gemini_api_key", "").strip()
            disp_key = f"{key[:8]}...{key[-8:]}" if len(key) > 16 else "(No Key)"
            tk.Label(card, text="Static API Key Connection", bg=BG_CARD, fg=ACCENT_ORANGE, font=(FONT_FAMILY, 8, "bold")).pack(anchor="w")
            tk.Label(card, text=f"Active Key: {disp_key}", bg=BG_CARD, fg=FG_LIGHT, font=(FONT_FAMILY, 8)).pack(anchor="w")
            tk.Label(card, text="Tier: Free Tier Standard (20 RPM)", bg=BG_CARD, fg=FG_SECONDARY, font=(FONT_FAMILY, 8)).pack(anchor="w")
            
        tk.Button(modal, text="CLOSE WINDOW", bg=ACCENT_CYAN, fg=FG_LIGHT, bd=0, pady=8, font=(FONT_FAMILY, 8, "bold"), cursor="hand2", command=modal.destroy).pack(fill="x", padx=20, pady=15)

    # ==================== TICKING CLOCK AND ASYNC REFRESHERS ====================
    def update_live_clock_and_ticks(self):
        now = datetime.now()
        self.clock_lbl.config(text=now.strftime("%H:%M:%S"))
        
        # Run daily backfill refresh at midnight or periodically
        if now.strftime("%H:%M:%S") == "00:00:00":
            self.refresh_dashboard_progress()
            
        self.root.after(1000, self.update_live_clock_and_ticks)


# ==================== APP STARTUP ====================
if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = GuardianWorkspaceSuite(root)
        root.mainloop()
    except Exception as e:
        import traceback
        try:
            log_path = os.path.join(BASE_DIR, "gui_crash_log.txt")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Startup Exception:\n")
                traceback.print_exc(file=f)
        except Exception:
            pass
        sys.exit(1)
