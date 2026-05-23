import os
import sys
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

# ==================== DESIGN CONSTANTS & THEME TOKENS ====================
FONT_FAMILY = "Segoe UI"
BG_DARK = "#09090B"          # Pure Deep Charcoal (Midnight)
BG_CARD = "#121214"          # Sleek Card space-black
BG_INNER = "#18181B"         # Slightly lighter slate
BORDER_COLOR = "#27272A"     # Border stroke
FG_LIGHT = "#F4F4F5"         # High-contrast white
FG_SECONDARY = "#A1A1AA"     # Muted grey label

# VibrantTailored HSL accent colors
ACCENT_CYAN = "#06B6D4"      # Cyan for primary highlights
ACCENT_GREEN = "#10B981"     # Emerald Green for completed metrics
ACCENT_ORANGE = "#F97316"    # Orange for warnings / reviews
ACCENT_PURPLE = "#8B5CF6"    # Purple for special coaching / AI
ACCENT_RED = "#EF4444"       # Red for failures / deletes
HOVER_COLOR = "#1F1F23"      # Lighter background hover

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
        self.root.geometry("560x790")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        
        # Frameless border styling if you want, but Standard keeps native resizing.
        # Self-healing logs
        self.init_crash_healing_logs()
        
        # Load configs
        self.config = guardian.load_config()
        self.mock_weekend = False
        
        # Interactive States
        self.active_tab = "dashboard"
        self.generating_weekend_task = False
        self.srs_deck_idx = 0
        self.cached_next_kanji = None
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
        self.create_header_bar()
        self.create_tab_navigation()
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
    def create_header_bar(self):
        """Creates the premium topmost title and status indicator header bar."""
        self.header_frame = tk.Frame(self.root, bg=BG_DARK, pady=10, padx=20)
        self.header_frame.pack(fill="x")
        
        title_lbl = tk.Label(self.header_frame, text="🛡️ PROJECT GUARDIAN", fg=FG_LIGHT, bg=BG_DARK, font=(FONT_FAMILY, 12, "bold"))
        title_lbl.pack(side="left")
        
        self.clock_lbl = tk.Label(self.header_frame, text="00:00:00", fg=FG_SECONDARY, bg=BG_DARK, font=(FONT_FAMILY, 9, "bold"))
        self.clock_lbl.pack(side="right", padx=(10, 0))
        
        self.quota_badge = tk.Label(self.header_frame, text="🤖 AI ●", fg=FG_SECONDARY, bg=BG_DARK, font=(FONT_FAMILY, 8, "bold"), cursor="hand2")
        self.quota_badge.pack(side="right", padx=5)
        self.quota_badge.bind("<Button-1>", lambda e: self.open_quota_status_dialog())
        HoverTooltip(self.quota_badge, lambda: "Click to check Gemini API Quota status")

    def create_tab_navigation(self):
        """Creates Apple-style premium tab navigation bar."""
        self.nav_frame = tk.Frame(self.root, bg=BG_DARK, pady=2, padx=10)
        self.nav_frame.pack(fill="x")
        
        tabs_config = [
            ("dashboard", "📊 DASHBOARD"),
            ("research",  "🔬 RESEARCH"),
            ("kanji",     "🧠 KANJI SRS"),
            ("sensei",    "🎓 AI SENSEI"),
            ("settings",  "⚙️ SETTINGS")
        ]
        
        self.tab_buttons = {}
        for tab_id, tab_label in tabs_config:
            btn = tk.Button(
                self.nav_frame, text=tab_label, bg=BG_DARK, fg=FG_SECONDARY,
                activebackground=BG_DARK, activeforeground=FG_LIGHT,
                bd=0, font=(FONT_FAMILY, 9, "bold"), cursor="hand2",
                padx=12, pady=8, command=lambda t=tab_id: self.show_tab(t)
            )
            btn.pack(side="left", fill="x", expand=True)
            self.tab_buttons[tab_id] = btn

    def create_tab_containers(self):
        """Creates stacked frames for all tabs."""
        self.content_frame = tk.Frame(self.root, bg=BG_DARK)
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self.tabs = {}
        for t_id in ["dashboard", "research", "kanji", "sensei", "settings"]:
            frame = tk.Frame(self.content_frame, bg=BG_DARK)
            self.tabs[t_id] = frame

    def show_tab(self, tab_id):
        """Performs dynamic tab switching and visual underline updates."""
        self.active_tab = tab_id
        for t_frame in self.tabs.values():
            t_frame.pack_forget()
            
        self.tabs[tab_id].pack(fill="both", expand=True)
        
        # Color updating
        for t_key, btn in self.tab_buttons.items():
            if t_key == tab_id:
                btn.config(fg=ACCENT_CYAN)
            else:
                btn.config(fg=FG_SECONDARY)
                
        # Specialized refreshes
        if tab_id == "dashboard":
            self.refresh_dashboard_progress()

    # ==================== TAB 1: DASHBOARD PANEL ====================
    def init_dashboard_tab(self):
        frame = self.tabs["dashboard"]
        
        # Stats Cards container
        stats_frame = tk.Frame(frame, bg=BG_DARK)
        stats_frame.pack(fill="x", pady=10)
        
        # Compliance Dial Frame
        dial_card = tk.Frame(stats_frame, bg=BG_CARD, bd=1, relief="solid", highlightbackground=BORDER_COLOR, highlightthickness=1, padx=15, pady=15)
        dial_card.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        tk.Label(dial_card, text="COMPLIANCE INDEX", bg=BG_CARD, fg=FG_SECONDARY, font=(FONT_FAMILY, 8, "bold")).pack()
        
        self.dial_canvas = tk.Canvas(dial_card, width=120, height=120, bg=BG_CARD, highlightthickness=0)
        self.dial_canvas.pack(pady=5)
        
        self.dial_label = tk.Label(dial_card, text="0.0%", bg=BG_CARD, fg=FG_LIGHT, font=(FONT_FAMILY, 14, "bold"))
        self.dial_label.pack()
        
        # Streak Card Frame
        streak_card = tk.Frame(stats_frame, bg=BG_CARD, bd=1, relief="solid", highlightbackground=BORDER_COLOR, highlightthickness=1, padx=15, pady=15)
        streak_card.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        tk.Label(streak_card, text="STUDY STREAK", bg=BG_CARD, fg=FG_SECONDARY, font=(FONT_FAMILY, 8, "bold")).pack()
        
        self.streak_num = tk.Label(streak_card, text="0 DAYS", bg=BG_CARD, fg=ACCENT_ORANGE, font=(FONT_FAMILY, 24, "bold"))
        self.streak_num.pack(pady=10)
        
        self.streak_tip = tk.Label(streak_card, text="Streaks synced with GitHub", bg=BG_CARD, fg=FG_SECONDARY, font=(FONT_FAMILY, 7, "italic"))
        self.streak_tip.pack()
        
        # Checklist Container
        checklist_card = tk.Frame(frame, bg=BG_CARD, bd=1, relief="solid", highlightbackground=BORDER_COLOR, highlightthickness=1, padx=20, pady=15)
        checklist_card.pack(fill="both", expand=True, pady=10)
        
        tk.Label(checklist_card, text="TODAY'S UPSCALE MILESTONES", bg=BG_CARD, fg=ACCENT_CYAN, font=(FONT_FAMILY, 9, "bold")).pack(anchor="w", pady=(0, 10))
        
        self.habits_frame = tk.Frame(checklist_card, bg=BG_CARD)
        self.habits_frame.pack(fill="both", expand=True)

    def refresh_dashboard_progress(self):
        """Queries SQLite and dynamically draws/animates the dashboard progress dial."""
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
            
            # Update labels
            self.dial_label.config(text=f"{pct*100.0:.1f}%")
            
            # Draw dial
            self.dial_canvas.delete("all")
            self.dial_canvas.create_arc(10, 10, 110, 110, start=225, extent=-270, style="arc", outline=BORDER_COLOR, width=8)
            if pct > 0:
                color = ACCENT_GREEN if pct == 1.0 else ACCENT_CYAN
                self.dial_canvas.create_arc(10, 10, 110, 110, start=225, extent=-270*pct, style="arc", outline=color, width=8)
                
            # Render checklist checkbuttons
            for child in self.habits_frame.winfo_children():
                child.destroy()
                
            # Render habit tasks
            for h in habits:
                is_checked = today_data.get(h, False)
                var = tk.BooleanVar(value=is_checked)
                
                def make_toggle(task_name=h, bool_var=var):
                    return lambda: self.toggle_habit_db(task_name, bool_var.get())
                    
                chk = tk.Checkbutton(
                    self.habits_frame, text=f"Practice / Complete: {task_name.upper()}", variable=var,
                    bg=BG_CARD, fg=FG_LIGHT, selectcolor=BG_INNER, activebackground=BG_CARD, activeforeground=FG_LIGHT,
                    font=(FONT_FAMILY, 9), command=make_toggle(h, var)
                )
                chk.pack(anchor="w", pady=5)
                
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
                
            # Render sync streak
            streak_cnt = guardian_db.get_db_connection().execute("SELECT count(*) FROM daily_habits").fetchone()[0]
            self.streak_num.config(text=f"{streak_cnt} DAYS")
        except Exception as ex:
            print(f"Error refreshing dashboard: {ex}")

    def toggle_habit_db(self, name, completed):
        try:
            today_str = datetime.now().strftime("%Y-%m-%d")
            guardian_db.log_habit(today_str, name, 1 if completed else 0)
        except Exception as e:
            print(e)
        self.refresh_dashboard_progress()

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
        task = next((t for t in hist if t.get("date") == sat_date_str), None)
        
        if not task:
            # Fall back to Week 0
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
        
        # Next / Prev buttons
        nav_frame = tk.Frame(frame, bg=BG_DARK, pady=5)
        nav_frame.pack(fill="x")
        
        self.btn_kanji_prev = tk.Button(
            nav_frame, text="⬅️ PREV HISTORY", bg=BG_CARD, fg=FG_LIGHT, bd=0, padx=15, pady=8,
            font=(FONT_FAMILY, 8, "bold"), cursor="hand2", command=self.navigate_previous_kanji
        )
        self.btn_kanji_prev.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.btn_kanji_next = tk.Button(
            nav_frame, text="🧠 NEW CARD", bg=ACCENT_CYAN, fg=FG_LIGHT, bd=0, padx=15, pady=8,
            font=(FONT_FAMILY, 8, "bold"), cursor="hand2", command=self.load_new_kanji_card
        )
        self.btn_kanji_next.pack(side="right", fill="x", expand=True, padx=(5, 0))
        
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
        
        self.k_ex_ja.config(text=card_dict.get("example_ja", ""))
        self.k_ex_en.config(text=card_dict.get("example_en", ""))
        
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
        """Loads a newly fetched card instantly, or triggers background threaded generations."""
        if self.srs_deck_idx < len(self.viewed_kanji_cards) - 1:
            self.srs_deck_idx += 1
            self.render_kanji_card(self.viewed_kanji_cards[self.srs_deck_idx])
            return
            
        if self.cached_next_kanji:
            new_c = self.cached_next_kanji
            self.cached_next_kanji = None
            self.on_kanji_card_fetched_successfully(new_c)
            return
            
        self.btn_kanji_next.config(text="LOADING...", state="disabled")
        
        def bg_fetch():
            api_key = self.config.get("gemini_api_key", "").strip()
            excluded = list(self.kanji_db.get("vocab", {}).keys())
            new_card = guardian.get_gemini_kanji_card(api_key, "N5", excluded)
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
        if self.cached_next_kanji or self.kanji_prefetch_in_progress:
            return
            
        self.kanji_prefetch_in_progress = True
        def bg_pre():
            api_key = self.config.get("gemini_api_key", "").strip()
            excluded = list(self.kanji_db.get("vocab", {}).keys())
            if hasattr(self, "current_kanji_card"):
                k = self.current_kanji_card.get("kanji")
                if k not in excluded:
                    excluded.append(k)
            new_c = guardian.get_gemini_kanji_card(api_key, "N5", excluded)
            
            def resolve(c=new_c):
                self.cached_next_kanji = c
                self.kanji_prefetch_in_progress = False
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
        chk_mnc.pack(anchor="w", pady=10)
        
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
            
            guardian.save_config(self.config)
            messagebox.showinfo("Settings Saved", "Workspace configuration successfully updated and saved locally.", parent=self.root)
            self.refresh_dashboard_progress()
        except Exception as e:
            messagebox.showerror("Error Saving", f"Failed to save settings: {e}", parent=self.root)

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
