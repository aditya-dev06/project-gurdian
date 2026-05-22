import os
import sys
import webbrowser
import urllib.parse

try:
    import winsound
except ImportError:
    winsound = None

# Define crash log path in the same directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CRASH_LOG = os.path.join(BASE_DIR, "gui_crash_log.txt")

try:
    if os.path.exists(CRASH_LOG):
        os.remove(CRASH_LOG)
except Exception:
    pass

try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    import threading
    from datetime import datetime

    # Add current folder to path to import core guardian logic
    sys.path.append(BASE_DIR)

    import guardian
    import random
except Exception as e:
    import traceback
    try:
        with open(CRASH_LOG, "w") as f:
            f.write(f"Startup Crash Error:\n{str(e)}\n\nTraceback:\n")
            traceback.print_exc(file=f)
    except Exception:
        pass
    # Try to show a GUI popup if tkinter loaded
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Guardian GUI Startup Error", f"Failed to start Guardian Widget:\n\n{e}\n\nCheck gui_crash_log.txt for details.")
    except Exception:
        pass
    sys.exit(1)

# ==================== THEME & COLOR PALETTE (APPLE PREMIUM DARK MODE) ====================
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

class GuardianWidget:
    def __init__(self, root):
        self.root = root
        self.root.title("Guardian Widget")
        self.root.configure(bg=BG_DARK)
        
        # Frameless window configuration
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)  # Always on top by default
        self.is_pinned = True
        
        # Set Window geometry (width x height + X_offset + Y_offset)
        self.window_width = 360
        self.window_height = 490
        
        # Center on screen
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = screen_width - self.window_width - 40
        y = 80
        self.root.geometry(f"{self.window_width}x{self.window_height}+{x}+{y}")
        
        # Setup custom drag variables
        self.drag_data = {"x": 0, "y": 0}
        
        # Live state caching
        self.github_live_status = None
        self.is_syncing_github = False
        self.mock_weekend = False
        self.current_drawn_pct = 0.0
        
        # Load and synchronize initial today's entries
        self.reload_and_sync_data()

        # Render complete layout
        self.create_title_bar()
        self.create_stats_header()
        
        # Create scrollable container for tasks
        self.main_scroll_container = tk.Frame(self.root, bg=BG_DARK, padx=15)
        self.main_scroll_container.pack(fill="both", expand=True)
        
        self.main_canvas = tk.Canvas(self.main_scroll_container, bg=BG_DARK, highlightthickness=0)
        self.main_scrollbar = tk.Scrollbar(self.main_scroll_container, orient="vertical", command=self.main_canvas.yview)
        
        self.cards_frame = tk.Frame(self.main_canvas, bg=BG_DARK)
        
        self.cards_frame.bind(
            "<Configure>",
            lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
        )
        
        self.main_canvas.create_window((0, 0), window=self.cards_frame, anchor="nw", width=310)
        self.main_canvas.configure(yscrollcommand=self.main_scrollbar.set)
        
        self.main_canvas.pack(side="left", fill="both", expand=True)
        self.main_scrollbar.pack(side="right", fill="y")
        
        # Enable mousewheel scrolling on main window
        def _on_main_mousewheel(event):
            try:
                if event.delta:
                    units = -1 * (event.delta / 120)
                    if units > 0:
                        units = int(units) if units >= 1 else 1
                    else:
                        units = int(units) if units <= -1 else -1
                    self.main_canvas.yview_scroll(units, "units")
            except Exception:
                pass
                
        self.root.bind("<MouseWheel>", _on_main_mousewheel)
        
        self.render_all_cards()
        self.create_control_footer()
        
        # Initial GitHub live scan in separate thread
        self.trigger_background_github_sync()
        
        # Kick off dynamic clock in the title bar
        self.update_live_clock()
        
        # Proactively register/refresh startup shortcut based on config setting
        try:
            startup_enabled = self.config.get("startup_enabled", True)
            guardian.register_startup_shortcut(startup_enabled)
        except Exception:
            pass

    def reload_and_sync_data(self):
        """Loads config and syncs today's records inside database."""
        self.config = guardian.load_config()
        self.data = guardian.load_data()
        self.today = datetime.now().strftime("%Y-%m-%d")
        self.tracked_tasks = self.config.get("tracked_tasks", guardian.DEFAULT_TASKS)
        self.data = guardian.initialize_today(self.data, self.today, self.tracked_tasks)
        guardian.save_data(self.data)
        
        # Load Kanji study statistics
        self.kanji_db = guardian.load_kanji_data()
        
    # ==================== INTERACTIVE WINDOW DRAGGING ====================

    def create_title_bar(self):
        """Creates a sleek title bar with drag capability, pin toggle, and close."""
        self.title_bar = tk.Frame(self.root, bg=BG_CARD, height=35)
        self.title_bar.pack(fill="x", side="top")
        self.title_bar.pack_propagate(False)
        
        # Drag binds
        self.title_bar.bind("<Button-1>", self.start_drag)
        self.title_bar.bind("<B1-Motion>", self.drag_window)
        
        # Title text
        self.title_label = tk.Label(
            self.title_bar,
            text="🛡️  GUARDIAN WIDGET",
            fg=ACCENT_CYAN,
            bg=BG_CARD,
            font=(FONT_FAMILY, 9, "bold")
        )
        self.title_label.pack(side="left", padx=12)
        self.title_label.bind("<Button-1>", self.start_drag)
        self.title_label.bind("<B1-Motion>", self.drag_window)
        
        # Close Button
        close_btn = tk.Button(
            self.title_bar,
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
        
        # Pin Button
        self.pin_btn = tk.Button(
            self.title_bar,
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
        """Toggles the 'Always on Top' parameter of the frameless window."""
        self.is_pinned = not self.is_pinned
        self.root.attributes("-topmost", self.is_pinned)
        if self.is_pinned:
            self.pin_btn.config(text="📌", fg=ACCENT_CYAN)
        else:
            self.pin_btn.config(text="📍", fg=FG_LIGHT)

    # ==================== RENDER WIDGET SECTIONS ====================

    def create_stats_header(self):
        """Renders the top statistics panel summarizing streak performance."""
        self.stats_frame = tk.Frame(self.root, bg=BG_DARK, pady=12)
        self.stats_frame.pack(fill="x", padx=15)
        
        # Streak Row container
        streak_row = tk.Frame(self.stats_frame, bg=BG_DARK)
        streak_row.pack(fill="x")
        
        # Flame Indicator
        self.flame_label = tk.Label(
            streak_row,
            bg=BG_DARK,
            font=(FONT_FAMILY, 13, "bold")
        )
        self.flame_label.pack(side="left")
        
        # Weekend Preview Toggle
        self.weekend_preview_btn = tk.Button(
            streak_row,
            text="🗓️ TEST WEEKEND",
            bg=BG_CARD,
            fg=ACCENT_CYAN,
            activebackground=HOVER_COLOR,
            activeforeground=FG_LIGHT,
            bd=0,
            padx=8,
            pady=2,
            font=(FONT_FAMILY, 7, "bold"),
            relief="flat",
            cursor="hand2",
            command=self.toggle_mock_weekend
        )
        self.weekend_preview_btn.pack(side="right")
        
        def wp_enter(e):
            self.weekend_preview_btn.config(bg=HOVER_COLOR)
        def wp_leave(e):
            if self.mock_weekend:
                self.weekend_preview_btn.config(bg=ACCENT_PURPLE)
            else:
                self.weekend_preview_btn.config(bg=BG_CARD)
        self.weekend_preview_btn.bind("<Enter>", wp_enter)
        self.weekend_preview_btn.bind("<Leave>", wp_leave)
        
        # Compliance stats
        self.compliance_label = tk.Label(
            self.stats_frame,
            bg=BG_DARK,
            font=(FONT_FAMILY, 8)
        )
        self.compliance_label.pack(anchor="w", pady=2)
        
        # Visual Progress Bar
        self.progress_canvas = tk.Canvas(self.stats_frame, height=6, bg="#252538", highlightthickness=0)
        self.progress_canvas.pack(fill="x", pady=6)
        self.progress_canvas.bind("<Configure>", lambda e: self.redraw_progress_bar())
        
        # Set text based on state
        self.update_stats_header()
        
        # Divider line
        divider = tk.Frame(self.root, bg=BG_CARD, height=1)
        divider.pack(fill="x", padx=15, pady=2)

    def render_all_cards(self):
        """Destroys and recreates the card list for manual tasks, weekend prep, and github."""
        # Clear existing cards
        for widget in self.cards_frame.winfo_children():
            widget.destroy()
            
        # Draw Weekend Japan MNC Prep card if today is weekend and it is active
        is_weekend = (guardian.get_current_weekend_saturday_date() is not None) or self.mock_weekend
        is_active = self.config.get("japan_mnc_prep_active", True)
        if is_weekend and is_active:
            self.create_weekend_prep_card()
            
        # Draw Kanji Study Dashboard Card
        self.create_kanji_dashboard_card()
            
        # Draw all manual tracked tasks
        idx = 1
        for task in self.tracked_tasks:
            self.create_task_card(task, idx)
            idx += 1
            
        # Draw GitHub commit status card
        self.create_github_card()

        # Force geometry calculation and set correct scrollregion after card redraws
        if hasattr(self, "main_canvas") and hasattr(self, "cards_frame"):
            self.cards_frame.update_idletasks()
            self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))

    def create_task_card(self, task_name, idx):
        """Creates a custom stylized rounded card row for a manual habit with glowing borders."""
        is_done = self.data[self.today].get(task_name, False)
        
        border_color = ACCENT_GREEN if is_done else BORDER_COLOR
        card = tk.Frame(
            self.cards_frame, 
            bg=BG_CARD, 
            pady=12, 
            padx=15, 
            highlightbackground=border_color,
            highlightcolor=border_color,
            highlightthickness=1
        )
        card.pack(fill="x", pady=6)
        
        # Status Light Canvas (glowing green/red circle)
        canvas = tk.Canvas(card, width=16, height=16, bg=BG_CARD, highlightthickness=0)
        canvas.pack(side="left", padx=5)
        color = ACCENT_GREEN if is_done else ACCENT_RED
        canvas.create_oval(2, 2, 14, 14, fill=color, outline="")
        
        # Label
        text_val = f"✓ {idx}.  {task_name.upper()}" if is_done else f"{idx}.  {task_name.upper()}"
        fg_val = ACCENT_GREEN if is_done else FG_LIGHT
        label = tk.Label(
            card,
            text=text_val,
            fg=fg_val,
            bg=BG_CARD,
            font=(FONT_FAMILY, 10, "bold")
        )
        label.pack(side="left", padx=10)
        
        # Toggle Button
        btn_text = "UNDO" if is_done else "✓ DONE"
        btn_color = BG_INNER if is_done else ACCENT_CYAN
        btn_fg = FG_LIGHT
        
        toggle_btn = tk.Button(
            card,
            text=btn_text,
            bg=btn_color,
            fg=btn_fg,
            activebackground=HOVER_COLOR if is_done else "#147ce5",
            activeforeground=FG_LIGHT,
            bd=0,
            highlightthickness=0,
            relief="flat",
            font=(FONT_FAMILY, 8, "bold"),
            width=8,
            cursor="hand2",
            command=lambda t=task_name: self.toggle_task_state(t)
        )
        toggle_btn.pack(side="right", padx=5)
        self.bind_button_hover(toggle_btn, btn_color, HOVER_COLOR if is_done else "#147ce5")
        
        # Bind tactile hover highlights
        self.bind_hover_highlight(card, BG_CARD, HOVER_COLOR)

    def create_github_card(self):
        """Creates the card row representing public commit synchronization with glowing borders."""
        # Check cached state
        is_done = self.data[self.today].get("github-commit", False)
        if self.github_live_status is not None:
            is_done = self.github_live_status
            
        border_color = ACCENT_GREEN if is_done else BORDER_COLOR
        card = tk.Frame(
            self.cards_frame, 
            bg=BG_CARD, 
            pady=12, 
            padx=15,
            highlightbackground=border_color,
            highlightcolor=border_color,
            highlightthickness=1
        )
        card.pack(fill="x", pady=6)
        
        # Status Canvas
        self.git_canvas = tk.Canvas(card, width=16, height=16, bg=BG_CARD, highlightthickness=0)
        self.git_canvas.pack(side="left", padx=5)
        color = ACCENT_GREEN if is_done else ACCENT_RED
        self.git_canvas.create_oval(2, 2, 14, 14, fill=color, outline="")
        
        # Label
        text_val = "✓ 🐙  GITHUB COMMIT" if is_done else "🐙  GITHUB COMMIT"
        fg_val = ACCENT_GREEN if is_done else FG_LIGHT
        self.git_label = tk.Label(
            card,
            text=text_val,
            fg=fg_val,
            bg=BG_CARD,
            font=(FONT_FAMILY, 10, "bold")
        )
        self.git_label.pack(side="left", padx=10)
        
        # Sync Button
        sync_text = "SYNCING..." if self.is_syncing_github else "🔄 SYNC"
        self.sync_btn = tk.Button(
            card,
            text=sync_text,
            bg=BG_INNER,
            fg=FG_LIGHT,
            activebackground=HOVER_COLOR,
            activeforeground=FG_LIGHT,
            bd=0,
            relief="flat",
            font=(FONT_FAMILY, 8, "bold"),
            width=9,
            cursor="hand2",
            command=self.trigger_background_github_sync,
            state="disabled" if self.is_syncing_github else "normal"
        )
        self.sync_btn.pack(side="right", padx=5)
        self.bind_button_hover(self.sync_btn, BG_INNER, HOVER_COLOR)
        
        # Bind tactile hover highlights
        self.bind_hover_highlight(card, BG_CARD, HOVER_COLOR)

    def create_weekend_prep_card(self):
        """Creates the premium Weekend Japan MNC Prep card at the top of the habit board."""
        # Get or create current weekend task
        sat_date_str = "2026-05-23" if self.mock_weekend else guardian.get_current_weekend_saturday_date()
        task_entry = guardian.get_or_create_weekend_task(sat_date_str)
        if not task_entry:
            return
            
        is_done = task_entry.get("completed", False)
        
        # Glowing premium card frame with green/gray border highlight
        border_color = ACCENT_GREEN if is_done else BORDER_COLOR
        card = tk.Frame(
            self.cards_frame, 
            bg=BG_CARD, 
            pady=12, 
            padx=15,
            highlightbackground=border_color,
            highlightcolor=border_color,
            highlightthickness=1
        )
        card.pack(fill="x", pady=6)
        
        # Header Row
        header_frame = tk.Frame(card, bg=BG_CARD)
        header_frame.pack(fill="x")
        
        # Header Label with Emoji
        header_text = "✓ 🎌  TOKYO MNC PREP" if is_done else "🎌  TOKYO MNC PREP"
        header_color = ACCENT_GREEN if is_done else ACCENT_CYAN
        header_lbl = tk.Label(
            header_frame,
            text=header_text,
            fg=header_color,
            bg=BG_CARD,
            font=(FONT_FAMILY, 9, "bold")
        )
        header_lbl.pack(side="left")
        
        # Source tag (e.g. Gemini AI or Curated)
        source_lbl = tk.Label(
            header_frame,
            text=f"[{task_entry.get('source', 'Roadmap')}]",
            fg=ACCENT_ORANGE,
            bg=BG_CARD,
            font=(FONT_FAMILY, 7, "bold")
        )
        source_lbl.pack(side="right")
        
        # Task Description (Wrapped)
        task_lbl = tk.Label(
            card,
            text=task_entry.get("task_title", ""),
            fg=FG_LIGHT,
            bg=BG_CARD,
            font=(FONT_FAMILY, 9),
            justify="left",
            wraplength=310,
            pady=6
        )
        task_lbl.pack(anchor="w")
        
        # Controls Frame (Complete, Notes, History)
        ctrl_frame = tk.Frame(card, bg=BG_CARD)
        ctrl_frame.pack(fill="x", pady=4)
        
        # Toggle Button
        btn_text = "UNDO" if is_done else "✓ COMPLETE"
        btn_bg = BG_INNER if is_done else ACCENT_CYAN
        btn_fg = FG_LIGHT
        
        toggle_btn = tk.Button(
            ctrl_frame,
            text=btn_text,
            bg=btn_bg,
            fg=btn_fg,
            activebackground=HOVER_COLOR if is_done else "#147ce5",
            activeforeground=FG_LIGHT,
            bd=0,
            relief="flat",
            font=(FONT_FAMILY, 8, "bold"),
            padx=10,
            cursor="hand2",
            command=self.toggle_weekend_task_state
        )
        toggle_btn.pack(side="left", padx=2)
        self.bind_button_hover(toggle_btn, btn_bg, HOVER_COLOR if is_done else "#147ce5")
        
        # Notes Button
        notes_btn = tk.Button(
            ctrl_frame,
            text="📝 NOTES",
            bg=BG_INNER,
            fg=FG_LIGHT,
            activebackground=HOVER_COLOR,
            activeforeground=FG_LIGHT,
            bd=0,
            relief="flat",
            font=(FONT_FAMILY, 8, "bold"),
            padx=8,
            cursor="hand2",
            command=self.open_weekend_notes_dialog
        )
        notes_btn.pack(side="left", padx=2)
        self.bind_button_hover(notes_btn, BG_INNER, HOVER_COLOR)
        
        # History Button
        history_btn = tk.Button(
            ctrl_frame,
            text="📚 HISTORY",
            bg=BG_INNER,
            fg=FG_LIGHT,
            activebackground=HOVER_COLOR,
            activeforeground=FG_LIGHT,
            bd=0,
            relief="flat",
            font=(FONT_FAMILY, 8, "bold"),
            padx=8,
            cursor="hand2",
            command=self.open_weekend_history_dialog
        )
        history_btn.pack(side="left", padx=2)
        self.bind_button_hover(history_btn, BG_INNER, HOVER_COLOR)

        # Research Button
        research_btn = tk.Button(
            ctrl_frame,
            text="🔬 RESEARCH",
            bg=BG_INNER,
            fg=FG_LIGHT,
            activebackground=HOVER_COLOR,
            activeforeground=FG_LIGHT,
            bd=0,
            relief="flat",
            font=(FONT_FAMILY, 8, "bold"),
            padx=8,
            cursor="hand2",
            command=self.open_weekend_research_dialog
        )
        research_btn.pack(side="left", padx=2)
        self.bind_button_hover(research_btn, BG_INNER, HOVER_COLOR)
 
        # Bind tactile hover highlight (distinct minimal dark theme)
        self.bind_hover_highlight(card, BG_CARD, HOVER_COLOR)

    def toggle_weekend_task_state(self):
        """Toggles the completed state of the current weekend task in the database."""
        sat_date_str = "2026-05-23" if self.mock_weekend else guardian.get_current_weekend_saturday_date()
        if not sat_date_str:
            return
            
        data = guardian.load_data()
        if "weekend_history" not in data:
            data["weekend_history"] = []
            
        new_state = False
        for entry in data["weekend_history"]:
            if entry.get("date") == sat_date_str:
                entry["completed"] = not entry.get("completed", False)
                new_state = entry["completed"]
                break
                
        guardian.save_data(data)
        
        # Play completion sound if task transitioned to DONE and winsound is available
        if winsound and new_state:
            try:
                winsound.PlaySound("SystemAsterisk", winsound.SND_ASYNC)
            except Exception:
                pass
                
        self.reload_and_sync_data()
        self.render_all_cards()

    def open_weekend_notes_dialog(self):
        """Opens a Tkinter Toplevel modal dialog to log/edit study notes for the weekend task."""
        sat_date_str = "2026-05-23" if self.mock_weekend else guardian.get_current_weekend_saturday_date()
        if not sat_date_str:
            return
            
        task_entry = guardian.get_or_create_weekend_task(sat_date_str)
        current_notes = task_entry.get("notes", "")
        
        modal = tk.Toplevel(self.root)
        modal.title("Log Weekend Notes")
        modal.configure(bg=BG_DARK)
        modal.geometry("340x380")
        modal.resizable(False, False)
        modal.attributes("-topmost", True)
        
        # Center modal relative to main widget
        mx = self.root.winfo_x() + 10
        my = self.root.winfo_y() + 40
        modal.geometry(f"+{mx}+{my}")
        
        # Modal Header
        lbl = tk.Label(
            modal, 
            text="📝  WEEKEND STUDY JOURNAL", 
            bg=BG_DARK, 
            fg=ACCENT_CYAN, 
            font=(FONT_FAMILY, 10, "bold"), 
            pady=10
        )
        lbl.pack()
        
        # Task sub-header
        sub_lbl = tk.Label(
            modal,
            text=f"Task: {task_entry.get('task_title')[:45]}...",
            bg=BG_DARK,
            fg=ACCENT_ORANGE,
            font=(FONT_FAMILY, 8, "italic"),
            wraplength=300
        )
        sub_lbl.pack(pady=2)
        
        # Text input area
        text_frame = tk.Frame(modal, bg=BG_DARK, padx=15, pady=5)
        text_frame.pack(fill="both", expand=True)
        
        # Text widget
        notes_text = tk.Text(
            text_frame,
            bg=BG_CARD,
            fg=FG_LIGHT,
            bd=0,
            insertbackground=FG_LIGHT,
            font=(FONT_FAMILY, 9),
            padx=8,
            pady=8,
            wrap="word"
        )
        notes_text.pack(fill="both", expand=True)
        notes_text.insert("1.0", current_notes)
        
        def save_notes():
            notes_content = notes_text.get("1.0", "end-1c").strip()
            data = guardian.load_data()
            for entry in data.get("weekend_history", []):
                if entry.get("date") == sat_date_str:
                    entry["notes"] = notes_content
                    break
            guardian.save_data(data)
            modal.destroy()
            messagebox.showinfo("Notes Saved", "Your research notes have been saved successfully!", parent=self.root)
            self.reload_and_sync_data()
            self.render_all_cards()
            
        save_btn = tk.Button(
            modal,
            text="SAVE JOURNAL ENTRY",
            bg=ACCENT_CYAN,
            fg=FG_LIGHT,
            activebackground="#147ce5",
            activeforeground=FG_LIGHT,
            bd=0,
            pady=10,
            font=(FONT_FAMILY, 9, "bold"),
            command=save_notes,
            cursor="hand2"
        )
        save_btn.pack(fill="x", padx=15, pady=15)
        self.bind_button_hover(save_btn, ACCENT_CYAN, "#147ce5")

    def open_weekend_history_dialog(self):
        """Opens a Toplevel modal dialog displaying all historical weekend prep logs in a scrollable view."""
        data = guardian.load_data()
        history = data.get("weekend_history", [])
        
        modal = tk.Toplevel(self.root)
        modal.title("Japan MNC Prep History")
        modal.configure(bg=BG_DARK)
        modal.geometry("350x420")
        modal.resizable(False, False)
        modal.attributes("-topmost", True)
        
        mx = self.root.winfo_x() + 5
        my = self.root.winfo_y() + 30
        modal.geometry(f"+{mx}+{my}")
        
        # Header
        lbl = tk.Label(
            modal, 
            text="📚  MNC PREP HISTORY LOG", 
            bg=BG_DARK, 
            fg=ACCENT_CYAN, 
            font=(FONT_FAMILY, 10, "bold"), 
            pady=10
        )
        lbl.pack()
        
        # Scrollable Frame Container
        container = tk.Frame(modal, bg=BG_DARK, padx=10, pady=5)
        container.pack(fill="both", expand=True)
        
        canvas = tk.Canvas(container, bg=BG_DARK, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        
        scrollable_frame = tk.Frame(canvas, bg=BG_DARK)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=310)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Enable mousewheel scrolling locally with smooth trackpad support
        def _on_mousewheel(event):
            try:
                if event.delta:
                    units = -1 * (event.delta / 120)
                    if units > 0:
                        units = int(units) if units >= 1 else 1
                    else:
                        units = int(units) if units <= -1 else -1
                    canvas.yview_scroll(units, "units")
            except Exception:
                pass
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        if not history:
            no_data_lbl = tk.Label(
                scrollable_frame,
                text="No history logs found.\nYour progress will start recording this weekend!",
                bg=BG_DARK,
                fg=FG_LIGHT,
                font=(FONT_FAMILY, 9, "italic"),
                pady=50
            )
            no_data_lbl.pack(fill="x")
        else:
            for entry in reversed(history):
                # Individual History Item Card
                status_color = ACCENT_GREEN if entry.get("completed") else ACCENT_RED
                status_text = "COMPLETED" if entry.get("completed") else "PENDING"
                
                item_card = tk.Frame(
                    scrollable_frame, 
                    bg=BG_CARD, 
                    pady=8, 
                    padx=10,
                    highlightbackground=BORDER_COLOR,
                    highlightthickness=1
                )
                item_card.pack(fill="x", pady=5)
                
                # Header row: date & status
                meta_frame = tk.Frame(item_card, bg=BG_CARD)
                meta_frame.pack(fill="x")
                
                date_lbl = tk.Label(
                    meta_frame,
                    text=entry.get("date", ""),
                    fg=ACCENT_CYAN,
                    bg=BG_CARD,
                    font=(FONT_FAMILY, 8, "bold")
                )
                date_lbl.pack(side="left")
                
                status_lbl = tk.Label(
                    meta_frame,
                    text=status_text,
                    fg=status_color,
                    bg=BG_CARD,
                    font=(FONT_FAMILY, 7, "bold")
                )
                status_lbl.pack(side="right")
                
                # Task Title
                task_lbl = tk.Label(
                    item_card,
                    text=entry.get("task_title", ""),
                    fg=FG_LIGHT,
                    bg=BG_CARD,
                    font=(FONT_FAMILY, 8, "bold"),
                    justify="left",
                    wraplength=280
                )
                task_lbl.pack(anchor="w", pady=4)
                
                # Notes section if any
                notes_content = entry.get("notes", "").strip()
                if notes_content:
                    notes_lbl = tk.Label(
                        item_card,
                        text=f"📝 {notes_content}",
                        fg="#A0A0B0",
                        bg=BG_CARD,
                        font=(FONT_FAMILY, 8),
                        justify="left",
                        wraplength=280
                    )
                    notes_lbl.pack(anchor="w", pady=2)
                else:
                    notes_lbl = tk.Label(
                        item_card,
                        text="📝 (No notes recorded)",
                        fg="#5F5F7A",
                        bg=BG_CARD,
                        font=(FONT_FAMILY, 8, "italic")
                    )
                    notes_lbl.pack(anchor="w", pady=2)
        
        # Close button at the bottom of modal
        close_btn = tk.Button(
            modal,
            text="CLOSE WINDOW",
            bg=BG_INNER,
            fg=FG_LIGHT,
            activebackground=HOVER_COLOR,
            activeforeground=FG_LIGHT,
            bd=0,
            pady=8,
            font=(FONT_FAMILY, 9, "bold"),
            command=modal.destroy,
            cursor="hand2"
        )
        close_btn.pack(fill="x", side="bottom")
        self.bind_button_hover(close_btn, BG_INNER, HOVER_COLOR)

        # Bind MouseWheel to Toplevel modal to capture bubbling events
        modal.bind("<MouseWheel>", _on_mousewheel)
        
        # Set focus to modal so it receives keyboard and mouse events immediately
        modal.focus_set()

        # Recursively bind mousewheel scrolling to all widgets inside the scrollable container
        def bind_wheel_recursive(w):
            try:
                w.bind("<MouseWheel>", _on_mousewheel)
            except Exception:
                pass
            for child in w.winfo_children():
                bind_wheel_recursive(child)
                
        bind_wheel_recursive(container)

        # Force geometry update and set correct scrollregion on startup
        scrollable_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

    def open_weekend_research_dialog(self):
        """Opens a Toplevel modal dialog to explore deep research upscaling roadmap and trending YouTube videos."""
        sat_date_str = "2026-05-23" if self.mock_weekend else guardian.get_current_weekend_saturday_date()
        if not sat_date_str:
            messagebox.showinfo("Weekend Only", "Weekend Japan MNC Prep is only active on weekends (Saturdays & Sundays). Check back then!", parent=self.root)
            return
            
        task_entry = guardian.get_or_create_weekend_task(sat_date_str)
        if not task_entry:
            messagebox.showwarning("Prep Inactive", "Weekend Japan MNC Prep is currently disabled in your settings.", parent=self.root)
            return

        modal = tk.Toplevel(self.root)
        modal.title("Deep Research Roadmap")
        modal.configure(bg=BG_DARK)
        modal.geometry("350x450")
        modal.resizable(False, False)
        modal.attributes("-topmost", True)
        
        # Center modal relative to main widget
        mx = self.root.winfo_x() + 5
        my = self.root.winfo_y() + 30
        modal.geometry(f"+{mx}+{my}")
        
        # Header
        lbl = tk.Label(
            modal, 
            text="🔬  MNC PREP DEEP RESEARCH", 
            bg=BG_DARK, 
            fg=ACCENT_CYAN, 
            font=(FONT_FAMILY, 10, "bold"), 
            pady=10
        )
        lbl.pack()
        
        # Scrollable Frame Container
        container = tk.Frame(modal, bg=BG_DARK, padx=10, pady=5)
        container.pack(fill="both", expand=True)
        
        canvas = tk.Canvas(container, bg=BG_DARK, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        
        scrollable_frame = tk.Frame(canvas, bg=BG_DARK)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=310)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Enable mousewheel scrolling locally with smooth trackpad support
        def _on_mousewheel(event):
            try:
                if event.delta:
                    units = -1 * (event.delta / 120)
                    if units > 0:
                        units = int(units) if units >= 1 else 1
                    else:
                        units = int(units) if units <= -1 else -1
                    canvas.yview_scroll(units, "units")
            except Exception:
                pass
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Task Overview Card
        task_card = tk.Frame(
            scrollable_frame,
            bg=BG_CARD,
            pady=8,
            padx=10,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1
        )
        task_card.pack(fill="x", pady=4)
        
        tk.Label(
            task_card,
            text=f"🎯 WEEKEND TASK: {sat_date_str}",
            fg=ACCENT_CYAN,
            bg=BG_CARD,
            font=(FONT_FAMILY, 8, "bold")
        ).pack(anchor="w")
        
        tk.Label(
            task_card,
            text=task_entry.get("task_title", ""),
            fg=FG_LIGHT,
            bg=BG_CARD,
            font=(FONT_FAMILY, 9, "bold"),
            justify="left",
            wraplength=280
        ).pack(anchor="w", pady=4)
        
        # Technical Upscaling Card
        tech_card = tk.Frame(
            scrollable_frame,
            bg=BG_CARD,
            pady=8,
            padx=10,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1
        )
        tech_card.pack(fill="x", pady=6)
        
        tk.Label(
            tech_card,
            text="💻 TECHNICAL SKILL DEEP-DIVE",
            fg=ACCENT_GREEN,
            bg=BG_CARD,
            font=(FONT_FAMILY, 8, "bold")
        ).pack(anchor="w")
        
        tk.Label(
            tech_card,
            text=task_entry.get("tech_upscaling", "No technical guidelines defined."),
            fg=FG_LIGHT,
            bg=BG_CARD,
            font=(FONT_FAMILY, 9),
            justify="left",
            wraplength=280,
            pady=4
        ).pack(anchor="w")
        
        # Personality Upscaling Card
        personality_card = tk.Frame(
            scrollable_frame,
            bg=BG_CARD,
            pady=8,
            padx=10,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1
        )
        personality_card.pack(fill="x", pady=6)
        
        tk.Label(
            personality_card,
            text="🧠 CULTURAL & JAPAN INTERVIEW PREP",
            fg=ACCENT_PURPLE,
            bg=BG_CARD,
            font=(FONT_FAMILY, 8, "bold")
        ).pack(anchor="w")
        
        tk.Label(
            personality_card,
            text=task_entry.get("personality_upscaling", "No cultural guidelines defined."),
            fg=FG_LIGHT,
            bg=BG_CARD,
            font=(FONT_FAMILY, 9),
            justify="left",
            wraplength=280,
            pady=4
        ).pack(anchor="w")
        
        # YouTube Recommendations Card
        youtube_card = tk.Frame(
            scrollable_frame,
            bg=BG_CARD,
            pady=8,
            padx=10,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1
        )
        youtube_card.pack(fill="x", pady=6)
        
        tk.Label(
            youtube_card,
            text="🎥 TRENDING YOUTUBE ROADMAP VIDEOS",
            fg=ACCENT_ORANGE,
            bg=BG_CARD,
            font=(FONT_FAMILY, 8, "bold")
        ).pack(anchor="w")
        
        yt_suggestions = task_entry.get("youtube_suggestions", [])
        if not yt_suggestions:
            tk.Label(
                youtube_card,
                text="No YouTube recommendations for this weekend's topic.",
                fg="#A0A0B0",
                bg=BG_CARD,
                font=(FONT_FAMILY, 8, "italic"),
                pady=4
            ).pack(anchor="w")
        else:
            for idx, item in enumerate(yt_suggestions, 1):
                # Suggestion row
                sug_lbl = tk.Label(
                    youtube_card,
                    text=f"{idx}. {item.get('title', '')}",
                    fg=FG_LIGHT,
                    bg=BG_CARD,
                    font=(FONT_FAMILY, 8, "bold"),
                    justify="left",
                    wraplength=280,
                    anchor="w"
                )
                sug_lbl.pack(anchor="w", pady=(4, 2))
                
                # Dynamic clickable Search Pill Button
                query = item.get("search_query", "")
                
                # We need lambda capture for query to prevent closure cell lookup issue!
                def make_search_cmd(q=query):
                    return lambda: webbrowser.open(f"https://www.youtube.com/results?search_query={urllib.parse.quote(q)}")
                
                search_btn = tk.Button(
                    youtube_card,
                    text="🔍 SEARCH ON YOUTUBE",
                    bg=BG_DARK,
                    fg=ACCENT_CYAN,
                    activebackground=HOVER_COLOR,
                    activeforeground=FG_LIGHT,
                    bd=1,
                    relief="flat",
                    font=(FONT_FAMILY, 7, "bold"),
                    padx=6,
                    pady=2,
                    cursor="hand2",
                    command=make_search_cmd(query)
                )
                search_btn.pack(anchor="w", padx=10, pady=(0, 6))
                self.bind_button_hover(search_btn, BG_DARK, HOVER_COLOR)
                
        # Close button at the bottom of modal
        close_btn = tk.Button(
            modal,
            text="CLOSE RESEARCH",
            bg=BG_INNER,
            fg=FG_LIGHT,
            activebackground=HOVER_COLOR,
            activeforeground=FG_LIGHT,
            bd=0,
            pady=8,
            font=(FONT_FAMILY, 9, "bold"),
            command=modal.destroy,
            cursor="hand2"
        )
        close_btn.pack(fill="x", side="bottom")
        self.bind_button_hover(close_btn, BG_INNER, HOVER_COLOR)

        # Bind MouseWheel to Toplevel modal to capture bubbling events
        modal.bind("<MouseWheel>", _on_mousewheel)
        
        # Set focus to modal so it receives keyboard and mouse events immediately
        modal.focus_set()

        # Recursively bind mousewheel scrolling to all widgets inside the scrollable container
        def bind_wheel_recursive(w):
            try:
                w.bind("<MouseWheel>", _on_mousewheel)
            except Exception:
                pass
            for child in w.winfo_children():
                bind_wheel_recursive(child)
                
        bind_wheel_recursive(container)

        # Force geometry update and set correct scrollregion on startup
        scrollable_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

    def create_control_footer(self):
        """Creates the bottom action control footer for Auditing & Settings."""
        footer_frame = tk.Frame(self.root, bg=BG_DARK, pady=15, padx=15)
        footer_frame.pack(fill="x", side="bottom")
        
        # Settings Button
        settings_btn = tk.Button(
            footer_frame,
            text="⚙️ SETTINGS",
            bg=BG_CARD,
            fg=FG_LIGHT,
            activebackground=HOVER_COLOR,
            activeforeground=FG_LIGHT,
            bd=0,
            pady=6,
            font=(FONT_FAMILY, 8, "bold"),
            command=self.open_settings_modal,
            cursor="hand2"
        )
        settings_btn.pack(side="left", fill="x", expand=True, padx=4)
        self.bind_button_hover(settings_btn, BG_CARD, HOVER_COLOR)
        
        # Test Warn Button
        warn_btn = tk.Button(
            footer_frame,
            text="🔔 TEST WARN",
            bg=BG_CARD,
            fg=ACCENT_ORANGE,
            activebackground=HOVER_COLOR,
            activeforeground=FG_LIGHT,
            bd=0,
            pady=6,
            font=(FONT_FAMILY, 8, "bold"),
            command=self.trigger_manual_warning_test,
            cursor="hand2"
        )
        warn_btn.pack(side="left", fill="x", expand=True, padx=4)
        self.bind_button_hover(warn_btn, BG_CARD, HOVER_COLOR)
        
        # Audit Test Button
        audit_btn = tk.Button(
            footer_frame,
            text="🚨 TEST AUDIT",
            bg=BG_CARD,
            fg=ACCENT_RED,
            activebackground=HOVER_COLOR,
            activeforeground=FG_LIGHT,
            bd=0,
            pady=6,
            font=(FONT_FAMILY, 8, "bold"),
            command=self.trigger_manual_audit_test,
            cursor="hand2"
        )
        audit_btn.pack(side="left", fill="x", expand=True, padx=4)
        self.bind_button_hover(audit_btn, BG_CARD, HOVER_COLOR)

    # ==================== CONTROLLER FUNCTIONS ====================

    def toggle_task_state(self, task_name):
        """Flips a manual task's state in database and updates GUI."""
        current_state = self.data[self.today].get(task_name, False)
        self.data[self.today][task_name] = not current_state
        guardian.save_data(self.data)
        
        # Play completion sound if task transitioned to DONE and winsound is available
        if winsound and not current_state:
            try:
                winsound.PlaySound("SystemAsterisk", winsound.SND_ASYNC)
            except Exception:
                pass
                
        # Redraw GUI panels
        self.reload_and_sync_data()
        self.update_stats_header()
        self.render_all_cards()

    def trigger_background_github_sync(self):
        """Launches a non-blocking background thread to check GitHub commits."""
        if self.is_syncing_github:
            return
            
        self.is_syncing_github = True
        if hasattr(self, 'sync_btn'):
            self.sync_btn.config(text="SYNCING...", state="disabled")
            
        thread = threading.Thread(target=self.perform_github_api_check, daemon=True)
        thread.start()

    def perform_github_api_check(self):
        """Runs the network check for GitHub commits today."""
        github_user = self.config.get("github_username", "")
        live_result = guardian.check_github_commit_today(github_user)
        
        self.github_live_status = live_result
        
        # Save to database
        self.data[self.today]["github-commit"] = live_result
        guardian.save_data(self.data)
        
        # Return to main thread to update UI safely
        self.root.after(0, self.on_github_sync_complete)

    def on_github_sync_complete(self):
        """Updates GUI when GitHub checking thread resolves."""
        self.is_syncing_github = False
        self.reload_and_sync_data()
        self.update_stats_header()
        self.render_all_cards()

    def update_stats_header(self):
        """Updates the text statistics labels without resetting frame."""
        if not guardian.is_within_timeline():
            self.flame_label.config(text="⏱️  TIMELINE IDLE", fg=ACCENT_CYAN)
            self.compliance_label.config(
                text="Widget is in standby mode (outside active timeline)", fg="#A0A0B0"
            )
        else:
            stats = guardian.calculate_stats()
            self.flame_label.config(text=f"🔥  {stats['current_streak']} DAY STREAK", fg=ACCENT_ORANGE)
            self.compliance_label.config(
                text=f"📊  7d Compliance: {stats['compliance_7d']:.1f}%   |   30d: {stats['compliance_30d']:.1f}%",
                fg=FG_LIGHT
            )
        self.redraw_progress_bar()

    def trigger_manual_audit_test(self):
        """Simulates audit and triggers alerts to phone."""
        # Quick non-blocking alert trigger
        threading.Thread(
            target=lambda: guardian.run_nightly_audit(force_test=True),
            daemon=True
        ).start()
        messagebox.showinfo(
            "Audit Triggered", 
            "Nightly audit run simulated!\nNotification sent successfully to your phone if ntfy is set."
        )
        self.reload_and_sync_data()
        self.update_stats_header()
        self.render_all_cards()

    def trigger_manual_warning_test(self):
        """Simulates warning and triggers high-priority alarm alert to phone."""
        # Quick non-blocking alert trigger
        threading.Thread(
            target=lambda: guardian.run_test_warning(),
            daemon=True
        ).start()
        messagebox.showinfo(
            "Warning Alarm Test Sent", 
            "Max-priority sound alarm test dispatched!\nCheck your phone now for a loud alarm sound.",
            parent=self.root
        )

    # ==================== SETTINGS EDITOR DIALOG ====================

    def open_settings_modal(self):
        """Launches a modal window inside Tkinter to update settings."""
        modal = tk.Toplevel(self.root)
        modal.title("Settings Editor")
        modal.configure(bg=BG_DARK)
        modal.geometry("340x590")
        modal.resizable(False, False)
        modal.attributes("-topmost", True)
        
        # Center modal relative to main widget
        mx = self.root.winfo_x() + 10
        my = self.root.winfo_y() - 30
        modal.geometry(f"+{mx}+{my}")
        
        # Modal Header
        lbl = tk.Label(modal, text="⚙️  SETTINGS CONFIGURATOR", bg=BG_DARK, fg=ACCENT_CYAN, font=(FONT_FAMILY, 10, "bold"), pady=10)
        lbl.pack()
        
        # Form Container
        form = tk.Frame(modal, bg=BG_DARK, padx=20)
        form.pack(fill="both", expand=True)
        
        # Field 1: GitHub Username
        tk.Label(form, text="GitHub Username:", bg=BG_DARK, fg=FG_LIGHT, font=(FONT_FAMILY, 9)).pack(anchor="w", pady=2)
        git_ent = tk.Entry(form, bg=BG_CARD, fg=FG_LIGHT, bd=1, relief="flat", insertbackground=FG_LIGHT, font=(FONT_FAMILY, 9))
        git_ent.pack(fill="x", pady=2)
        git_ent.insert(0, self.config.get("github_username", ""))
        
        # Field 2: ntfy Topic
        tk.Label(form, text="ntfy.sh Notification Topic:", bg=BG_DARK, fg=FG_LIGHT, font=(FONT_FAMILY, 9)).pack(anchor="w", pady=2)
        topic_ent = tk.Entry(form, bg=BG_CARD, fg=FG_LIGHT, bd=1, relief="flat", insertbackground=FG_LIGHT, font=(FONT_FAMILY, 9))
        topic_ent.pack(fill="x", pady=2)
        topic_ent.insert(0, self.config.get("ntfy_topic", ""))
        
        # Field 3: Custom Tasks list
        tk.Label(form, text="Habit Tasks (separated by commas):", bg=BG_DARK, fg=FG_LIGHT, font=(FONT_FAMILY, 9)).pack(anchor="w", pady=2)
        tasks_ent = tk.Entry(form, bg=BG_CARD, fg=FG_LIGHT, bd=1, relief="flat", insertbackground=FG_LIGHT, font=(FONT_FAMILY, 9))
        tasks_ent.pack(fill="x", pady=2)
        tasks_ent.insert(0, ", ".join(self.config.get("tracked_tasks", guardian.DEFAULT_TASKS)))

        # Field 4: Start Date
        tk.Label(form, text="Timeline Start Date (YYYY-MM-DD):", bg=BG_DARK, fg=FG_LIGHT, font=(FONT_FAMILY, 9)).pack(anchor="w", pady=2)
        start_ent = tk.Entry(form, bg=BG_CARD, fg=FG_LIGHT, bd=1, relief="flat", insertbackground=FG_LIGHT, font=(FONT_FAMILY, 9))
        start_ent.pack(fill="x", pady=2)
        start_ent.insert(0, self.config.get("start_date", ""))

        # Field 5: End Date
        tk.Label(form, text="Timeline End Date (YYYY-MM-DD):", bg=BG_DARK, fg=FG_LIGHT, font=(FONT_FAMILY, 9)).pack(anchor="w", pady=2)
        end_ent = tk.Entry(form, bg=BG_CARD, fg=FG_LIGHT, bd=1, relief="flat", insertbackground=FG_LIGHT, font=(FONT_FAMILY, 9))
        end_ent.pack(fill="x", pady=2)
        end_ent.insert(0, self.config.get("end_date", ""))

        # Field 6: Gemini API Key
        tk.Label(form, text="Gemini API Key (Optional):", bg=BG_DARK, fg=FG_LIGHT, font=(FONT_FAMILY, 9)).pack(anchor="w", pady=2)
        gemini_ent = tk.Entry(form, bg=BG_CARD, fg=FG_LIGHT, bd=1, relief="flat", insertbackground=FG_LIGHT, font=(FONT_FAMILY, 9), show="*")
        gemini_ent.pack(fill="x", pady=2)
        gemini_ent.insert(0, self.config.get("gemini_api_key", ""))

        # Field 7: Checkbutton for active weekend prep
        mnc_var = tk.BooleanVar(value=self.config.get("japan_mnc_prep_active", True))
        mnc_chk = tk.Checkbutton(
            form,
            text="Enable Weekend Japan MNC Tech Prep",
            variable=mnc_var,
            bg=BG_DARK,
            fg=FG_LIGHT,
            selectcolor=BG_CARD,
            activebackground=BG_DARK,
            activeforeground=FG_LIGHT,
            font=(FONT_FAMILY, 9),
            bd=0,
            highlightthickness=0
        )
        mnc_chk.pack(anchor="w", pady=4)

        # Field 8: Checkbutton for active boot auto-startup
        startup_var = tk.BooleanVar(value=self.config.get("startup_enabled", True))
        startup_chk = tk.Checkbutton(
            form,
            text="Start Kanji Widget on System Boot",
            variable=startup_var,
            bg=BG_DARK,
            fg=FG_LIGHT,
            selectcolor=BG_CARD,
            activebackground=BG_DARK,
            activeforeground=FG_LIGHT,
            font=(FONT_FAMILY, 9),
            bd=0,
            highlightthickness=0
        )
        startup_chk.pack(anchor="w", pady=4)

        def save_and_close():
            user = git_ent.get().strip()
            topic = topic_ent.get().strip()
            tasks_str = tasks_ent.get().strip()
            start_val = start_ent.get().strip()
            end_val = end_ent.get().strip()
            gemini_val = gemini_ent.get().strip()
            mnc_val = mnc_var.get()
            startup_val = startup_var.get()
            
            if not user or not topic:
                messagebox.showerror("Error", "Fields cannot be blank!", parent=modal)
                return
                
            # Validate dates
            if start_val:
                try:
                    datetime.strptime(start_val, "%Y-%m-%d")
                except ValueError:
                    messagebox.showerror("Invalid Date", "Start Date must be in YYYY-MM-DD format!", parent=modal)
                    return
            if end_val:
                try:
                    datetime.strptime(end_val, "%Y-%m-%d")
                except ValueError:
                    messagebox.showerror("Invalid Date", "End Date must be in YYYY-MM-DD format!", parent=modal)
                    return
            if start_val and end_val:
                try:
                    start_dt = datetime.strptime(start_val, "%Y-%m-%d")
                    end_dt = datetime.strptime(end_val, "%Y-%m-%d")
                    if start_dt > end_dt:
                        messagebox.showerror("Invalid Range", "Start Date cannot be after End Date!", parent=modal)
                        return
                except ValueError:
                    pass

            tasks = [t.strip().lower() for t in tasks_str.split(",") if t.strip()]
            if not tasks:
                tasks = guardian.DEFAULT_TASKS
                
            self.config["github_username"] = user
            self.config["ntfy_topic"] = topic
            self.config["tracked_tasks"] = tasks
            self.config["start_date"] = start_val
            self.config["end_date"] = end_val
            self.config["gemini_api_key"] = gemini_val
            self.config["japan_mnc_prep_active"] = mnc_val
            self.config["startup_enabled"] = startup_val
            guardian.save_config(self.config)
            
            # Programmatically add/remove shortcut in Windows Startup Folder
            guardian.register_startup_shortcut(startup_val)
            
            modal.destroy()
            
            # Refresh main app
            self.reload_and_sync_data()
            self.update_stats_header()
            self.render_all_cards()

        save_btn = tk.Button(
            modal, 
            text="SAVE CONFIG", 
            bg=ACCENT_CYAN, 
            fg=FG_LIGHT, 
            activebackground="#147ce5",
            activeforeground=FG_LIGHT,
            bd=0, 
            pady=8,
            font=(FONT_FAMILY, 9, "bold"),
            command=save_and_close,
            cursor="hand2"
        )
        save_btn.pack(fill="x", padx=20, pady=15)
        self.bind_button_hover(save_btn, ACCENT_CYAN, "#147ce5")

    def bind_button_hover(self, button, bg_normal, bg_hover):
        """Binds mouse enter and leave events to a button to change its background color smoothly."""
        def enter(e):
            button.config(bg=bg_hover)
        def leave(e):
            button.config(bg=bg_normal)
        button.bind("<Enter>", enter)
        button.bind("<Leave>", leave)

    def bind_hover_highlight(self, widget, bg_normal, bg_hover):
        """Binds recursive hover highlighting to a container widget and all its children."""
        def enter(e):
            widget.config(bg=bg_hover)
            for child in widget.winfo_children():
                # Avoid changing buttons or status lights to prevent disrupting their custom colors
                if not isinstance(child, (tk.Button, tk.Canvas)):
                    try:
                        child.config(bg=bg_hover)
                    except tk.TclError:
                        pass
        def leave(e):
            widget.config(bg=bg_normal)
            for child in widget.winfo_children():
                if not isinstance(child, (tk.Button, tk.Canvas)):
                    try:
                        child.config(bg=bg_normal)
                    except tk.TclError:
                        pass
                        
        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)
        for child in widget.winfo_children():
            if not isinstance(child, (tk.Button, tk.Canvas)):
                child.bind("<Enter>", enter)
                child.bind("<Leave>", leave)

    def toggle_mock_weekend(self):
        """Toggles weekend simulation mode on/off to interactively test weekend features."""
        self.mock_weekend = not self.mock_weekend
        if self.mock_weekend:
            self.weekend_preview_btn.config(text="🗓️ LIVE MODE", bg=ACCENT_PURPLE, fg=FG_LIGHT)
        else:
            self.weekend_preview_btn.config(text="🗓️ TEST WEEKEND", bg=BG_CARD, fg=ACCENT_CYAN)
        
        # Refresh main app layout immediately
        self.reload_and_sync_data()
        self.update_stats_header()
        self.render_all_cards()

    # ==================== KANJI SUB-APP GUI INTEGRATIONS ====================

    def create_kanji_dashboard_card(self):
        """Creates the premium Kanji Study stats card on the main widget habit board."""
        vocab = self.kanji_db.get("vocab", {})
        stats = self.kanji_db.get("stats", {})
        
        count = len(vocab)
        reviewed = stats.get("total_reviewed", 0)
        correct = stats.get("total_correct", 0)
        accuracy = (correct / reviewed * 100.0) if reviewed > 0 else 0.0
        
        # Glowing premium card frame with clean accent border highlight
        card = tk.Frame(
            self.cards_frame, 
            bg=BG_CARD, 
            pady=12, 
            padx=15,
            highlightbackground=BORDER_COLOR,
            highlightcolor=BORDER_COLOR,
            highlightthickness=1
        )
        card.pack(fill="x", pady=6)
        
        # Header Row
        header_frame = tk.Frame(card, bg=BG_CARD)
        header_frame.pack(fill="x")
        
        # Header Label with Emoji
        header_lbl = tk.Label(
            header_frame,
            text="🎌  KANJI STUDY CORE",
            fg=ACCENT_CYAN,
            bg=BG_CARD,
            font=(FONT_FAMILY, 9, "bold")
        )
        header_lbl.pack(side="left")
        
        # Study progress stats
        stats_lbl = tk.Label(
            card,
            text=f"Vocabulary: {count} Kanji Studied\nQuiz Accuracy: {accuracy:.1f}% ({correct}/{reviewed})",
            fg=FG_LIGHT,
            bg=BG_CARD,
            font=(FONT_FAMILY, 8, "bold"),
            justify="left"
        )
        stats_lbl.pack(anchor="w", pady=(6, 4))
        
        # Action row
        ctrl_frame = tk.Frame(card, bg=BG_CARD)
        ctrl_frame.pack(fill="x", pady=(4, 0))
        
        # Launch Widget button
        launch_btn = tk.Button(
            ctrl_frame,
            text="🧠 LAUNCH",
            bg=ACCENT_CYAN,
            fg=FG_LIGHT,
            activebackground="#147ce5",
            activeforeground=FG_LIGHT,
            bd=0,
            relief="flat",
            font=(FONT_FAMILY, 8, "bold"),
            padx=6,
            pady=3,
            cursor="hand2",
            command=self.launch_kanji_widget_subapp
        )
        launch_btn.pack(side="left", padx=2, fill="x", expand=True)
        self.bind_button_hover(launch_btn, ACCENT_CYAN, "#147ce5")
        
        # Kanji Test button
        test_btn = tk.Button(
            ctrl_frame,
            text="📝 CHALLENGE",
            bg=BG_INNER,
            fg=FG_LIGHT,
            activebackground=HOVER_COLOR,
            activeforeground=FG_LIGHT,
            bd=0,
            relief="flat",
            font=(FONT_FAMILY, 8, "bold"),
            padx=6,
            pady=3,
            cursor="hand2",
            command=self.open_weekend_kanji_test_modal
        )
        test_btn.pack(side="right", padx=2, fill="x", expand=True)
        self.bind_button_hover(test_btn, BG_INNER, HOVER_COLOR)
        
        self.bind_hover_highlight(card, BG_CARD, HOVER_COLOR)

    def launch_kanji_widget_subapp(self):
        """Launches the Kanji flashcard widget as an independent concurrent subprocess."""
        try:
            import subprocess
            python_exe = sys.executable
            script_path = os.path.join(BASE_DIR, "kanji_widget.py")
            subprocess.Popen([python_exe, script_path], creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        except Exception as e:
            messagebox.showerror("Execution Error", f"Failed to launch Kanji Widget:\n\n{e}", parent=self.root)

    def open_weekend_kanji_test_modal(self):
        """Launches the interactive Kanji weekend verification test in a beautiful modal dialog."""
        vocab_pool = list(self.kanji_db.get("vocab", {}).values())
        
        # Standard default pool of N5 Kanji to fall back/supplement if studied pool is small
        fallback_pool = [
            {
                "kanji": "日", "meaning": "day, sun, Japan", "onyomi": "ニチ", "kunyomi": "ひ", "example_ja": "日本にいきたいです。",
                "kanji_yomi": "ひ", "kanji_romaji": "hi", "example_yomi": "にほん に いきたい です。", "example_romaji": "nihon ni ikitai desu."
            },
            {
                "kanji": "本", "meaning": "book, origin, main", "onyomi": "ホン", "kunyomi": "もと", "example_ja": "日本語をべんきょうします。",
                "kanji_yomi": "ほん", "kanji_romaji": "hon", "example_yomi": "にほんご を べんきょう します。", "example_romaji": "nihongo o benkyou shimasu."
            },
            {
                "kanji": "人", "meaning": "person, human", "onyomi": "ジン", "kunyomi": "ひと", "example_ja": "あの人はだれですか。",
                "kanji_yomi": "ひと", "kanji_romaji": "hito", "example_yomi": "あの ひと は だれ です か。", "example_romaji": "ano hito wa dare desu ka."
            },
            {
                "kanji": "学", "meaning": "study, learning, science", "onyomi": "ガク", "kunyomi": "まな-ぶ", "example_ja": "学生ですか。",
                "kanji_yomi": "まなぶ", "kanji_romaji": "manabu", "example_yomi": "がくせい です か。", "example_romaji": "gakusei desu ka."
            },
            {
                "kanji": "生", "meaning": "life, birth, genuine", "onyomi": "セイ", "kunyomi": "い-きる", "example_ja": "先生、こんにちは。",
                "kanji_yomi": "なま", "kanji_romaji": "nama", "example_yomi": "せんせい、こんにちは。", "example_romaji": "sensei, konnichiwa."
            },
            {
                "kanji": "先", "meaning": "ahead, previous, future", "onyomi": "セン", "kunyomi": "さき", "example_ja": "先月、日本にいきました。",
                "kanji_yomi": "さき", "kanji_romaji": "saki", "example_yomi": "せんげつ、にほん に いきました。", "example_romaji": "sengetsu, nihon ni ikimashita."
            },
            {
                "kanji": "国", "meaning": "country", "onyomi": "コク", "kunyomi": "くに", "example_ja": "お国はどちらですか。",
                "kanji_yomi": "くに", "kanji_romaji": "kuni", "example_yomi": "おくに は どちら です か。", "example_romaji": "okuni wa dochira desu ka."
            },
            {
                "kanji": "車", "meaning": "car, vehicle, wheel", "onyomi": "シャ", "kunyomi": "くるま", "example_ja": "新しい車を買いました。",
                "kanji_yomi": "くるま", "kanji_romaji": "kuruma", "example_yomi": "あたらしい くるま を かいました。", "example_romaji": "atarashii kuruma o kaimashita."
            },
            {
                "kanji": "水", "meaning": "water", "onyomi": "スイ", "kunyomi": "みず", "example_ja": "お水をください。",
                "kanji_yomi": "みず", "kanji_romaji": "mizu", "example_yomi": "おみず を ください。", "example_romaji": "omizu o kudasai."
            },
            {
                "kanji": "金", "meaning": "gold, money", "onyomi": "キン", "kunyomi": "かね", "example_ja": "お金がありません。",
                "kanji_yomi": "かね", "kanji_romaji": "kane", "example_yomi": "おかね が ありません。", "example_romaji": "okane ga arimasen."
            }
        ]
        
        # Merge studied pool with fallback pool to ensure we have at least 10 items for distractor pool
        distractor_pool = fallback_pool + vocab_pool
        # Unique list by Kanji
        seen = set()
        unique_pool = []
        for c in distractor_pool:
            if c["kanji"] not in seen:
                seen.add(c["kanji"])
                unique_pool.append(c)
        
        # Pick 5 questions: prioritize studied vocab_pool, fallback to unique_pool
        test_questions = []
        if vocab_pool:
            shuffled_vocab = list(vocab_pool)
            random.shuffle(shuffled_vocab)
            test_questions = shuffled_vocab[:5]
            
        # Supplement if less than 5
        if len(test_questions) < 5:
            remaining_needed = 5 - len(test_questions)
            shuffled_unique = [c for c in unique_pool if c not in test_questions]
            random.shuffle(shuffled_unique)
            test_questions += shuffled_unique[:remaining_needed]
            
        # Set up variables for tracking test state
        self.test_score = 0
        self.current_q_idx = 0
        self.questions_list = test_questions
        
        # Build modal Toplevel
        modal = tk.Toplevel(self.root)
        modal.title("Kanji Weekend Test")
        modal.configure(bg=BG_DARK)
        modal.geometry("350x460")
        modal.resizable(False, False)
        modal.attributes("-topmost", True)
        
        # Center modal relative to main widget
        mx = self.root.winfo_x() + 5
        my = self.root.winfo_y() + 10
        modal.geometry(f"+{mx}+{my}")
        
        # Sleek Title Bar with Drag Binds
        title_bar = tk.Frame(modal, bg=BG_CARD, height=35)
        title_bar.pack(fill="x", side="top")
        
        # Drag binds
        self.test_drag_data = {"x": 0, "y": 0}
        def start_test_drag(event):
            self.test_drag_data["x"] = event.x
            self.test_drag_data["y"] = event.y
        def drag_test_window(event):
            x = modal.winfo_x() + (event.x - self.test_drag_data["x"])
            y = modal.winfo_y() + (event.y - self.test_drag_data["y"])
            modal.geometry(f"+{x}+{y}")
            
        title_bar.bind("<Button-1>", start_test_drag)
        title_bar.bind("<B1-Motion>", drag_test_window)
        
        title_lbl = tk.Label(
            title_bar,
            text="📝  WEEKEND KANJI CHALLENGE",
            fg=ACCENT_CYAN,
            bg=BG_CARD,
            font=(FONT_FAMILY, 9, "bold")
        )
        title_lbl.pack(side="left", padx=12)
        title_lbl.bind("<Button-1>", start_test_drag)
        title_lbl.bind("<B1-Motion>", drag_test_window)
        
        close_btn = tk.Button(
            title_bar,
            text="✕",
            fg=FG_LIGHT,
            bg=BG_CARD,
            bd=0,
            activebackground=ACCENT_RED,
            activeforeground=FG_LIGHT,
            font=(FONT_FAMILY, 10, "bold"),
            command=modal.destroy,
            cursor="hand2"
        )
        close_btn.pack(side="right", fill="y", padx=5)
        self.bind_button_hover(close_btn, BG_CARD, ACCENT_RED)
        
        # Main content area
        content_frame = tk.Frame(modal, bg=BG_DARK, padx=20, pady=10)
        content_frame.pack(fill="both", expand=True)
        
        # Steal and force active focus
        modal.focus_set()
        
        def render_question():
            # Clear existing widgets in content_frame
            for widget in content_frame.winfo_children():
                widget.destroy()
                
            if self.current_q_idx >= 5:
                render_scorecard()
                return
                
            q_card = self.questions_list[self.current_q_idx]
            
            # Progress label
            progress_lbl = tk.Label(
                content_frame,
                text=f"QUESTION {self.current_q_idx + 1} OF 5",
                fg=ACCENT_ORANGE,
                bg=BG_DARK,
                font=(FONT_FAMILY, 8, "bold")
            )
            progress_lbl.pack(anchor="w", pady=(0, 10))
            
            # Question Card Frame
            card = tk.Frame(
                content_frame,
                bg=BG_CARD,
                pady=15,
                padx=10,
                highlightbackground="#34344A",
                highlightthickness=1
            )
            card.pack(fill="x", pady=5)
            
            # Kanji text
            kanji_lbl = tk.Label(
                card,
                text=q_card["kanji"],
                fg=ACCENT_CYAN,
                bg=BG_CARD,
                font=(FONT_FAMILY, 44, "bold")
            )
            kanji_lbl.pack()
            HoverTooltip(kanji_lbl, lambda: q_card.get("kanji_romaji", ""))
            
            # Audio Pronounce Row
            audio_btn = tk.Button(
                card,
                text="🔊 HEAR PRONUNCIATION",
                bg=BG_DARK,
                fg=ACCENT_CYAN,
                activebackground=HOVER_COLOR,
                activeforeground=FG_LIGHT,
                bd=0,
                relief="flat",
                font=(FONT_FAMILY, 7, "bold"),
                padx=8,
                pady=3,
                cursor="hand2",
                command=lambda: guardian.speak_japanese_text(q_card.get("kanji_yomi", q_card.get("kanji", "")) if q_card else "")
            )
            audio_btn.pack(pady=4)
            self.bind_button_hover(audio_btn, BG_DARK, HOVER_COLOR)
            
            # Prompt instructions
            prompt_lbl = tk.Label(
                content_frame,
                text="What is the correct meaning/translation of this Kanji?",
                fg=FG_LIGHT,
                bg=BG_DARK,
                font=(FONT_FAMILY, 8, "bold")
            )
            prompt_lbl.pack(pady=8)
            
            # Select distractors from unique_pool
            others = [c for c in unique_pool if c["kanji"] != q_card["kanji"]]
            random.shuffle(others)
            distractors = others[:3]
            
            choices = [q_card] + distractors
            random.shuffle(choices)
            
            # Handle user selection
            def select_answer(selected_item, btn_clicked, all_btns):
                correct = (selected_item["kanji"] == q_card["kanji"])
                
                # Disable all buttons to prevent double clicks
                for b in all_btns:
                    b.config(state="disabled")
                    
                if correct:
                    self.test_score += 1
                    btn_clicked.config(bg=ACCENT_GREEN, fg=BG_DARK)
                    guardian.speak_japanese_text("せいかい！ 正解")
                else:
                    btn_clicked.config(bg=ACCENT_RED, fg=FG_LIGHT)
                    # Find correct button and flash it green
                    for b, item in zip(all_btns, choices):
                        if item["kanji"] == q_card["kanji"]:
                            b.config(bg=ACCENT_GREEN, fg=BG_DARK)
                    guardian.speak_japanese_text("まちがい！ 間違い")
                    
                # Schedule transition to next question after 1.5 seconds
                self.current_q_idx += 1
                modal.after(1500, render_question)
                
            # Render option buttons
            buttons_list = []
            for choice in choices:
                opt_btn = tk.Button(
                    content_frame,
                    text=choice["meaning"],
                    bg=BG_CARD,
                    fg=FG_LIGHT,
                    activebackground=ACCENT_PURPLE,
                    activeforeground=FG_LIGHT,
                    bd=1,
                    relief="flat",
                    font=(FONT_FAMILY, 9, "bold"),
                    pady=6,
                    cursor="hand2"
                )
                opt_btn.pack(fill="x", pady=4)
                self.bind_button_hover(opt_btn, BG_CARD, HOVER_COLOR)
                HoverTooltip(opt_btn, lambda c=choice: f"{c.get('kanji_romaji', '')} ({c.get('kanji_yomi', '')})" if c.get('kanji_romaji') else "")
                buttons_list.append(opt_btn)
                
            # Wire command to choices
            for btn, choice in zip(buttons_list, choices):
                btn.config(command=lambda c=choice, b=btn, l=buttons_list: select_answer(c, b, l))
                
        def render_scorecard():
            # Clear content_frame
            for widget in content_frame.winfo_children():
                widget.destroy()
                
            percentage = (self.test_score / 5.0) * 100.0
            
            # Header
            tk.Label(
                content_frame,
                text="📝  WEEKEND CHALLENGE COMPLETE",
                fg=ACCENT_CYAN,
                bg=BG_DARK,
                font=(FONT_FAMILY, 10, "bold")
            ).pack(pady=10)
            
            # Glowing stats card
            card = tk.Frame(
                content_frame,
                bg=BG_CARD,
                pady=20,
                padx=15,
                highlightbackground=ACCENT_GREEN if self.test_score >= 4 else ACCENT_ORANGE,
                highlightthickness=1
            )
            card.pack(fill="x", pady=10)
            
            # Score
            score_lbl = tk.Label(
                card,
                text=f"{self.test_score} / 5",
                fg=ACCENT_GREEN if self.test_score >= 4 else ACCENT_ORANGE,
                bg=BG_CARD,
                font=(FONT_FAMILY, 36, "bold")
            )
            score_lbl.pack()
            
            pct_lbl = tk.Label(
                card,
                text=f"Accuracy: {percentage:.1f}%",
                fg=FG_LIGHT,
                bg=BG_CARD,
                font=(FONT_FAMILY, 12, "bold")
            )
            pct_lbl.pack(pady=4)
            
            # Motivational text based on score
            if self.test_score == 5:
                msg = "Perfect Score! あなたは天才です！ Excellent command over your vocabulary."
            elif self.test_score >= 4:
                msg = "Great Job! Almost perfect. You are well on your way to upscaling your Japanese!"
            elif self.test_score >= 3:
                msg = "Passed! Good progress, but make sure to review incorrect ones in the Kanji App."
            else:
                msg = "Keep Studying! More practice makes perfect. Use the pop quizzes to secure your memory."
                
            msg_lbl = tk.Label(
                card,
                text=msg,
                fg="#A0A0B0",
                bg=BG_CARD,
                font=(FONT_FAMILY, 8, "italic"),
                wraplength=240,
                justify="center"
            )
            msg_lbl.pack(pady=8)
            
            # Persist test scorecard in database history
            test_history = self.kanji_db.setdefault("test_history", [])
            test_history.append({
                "date": datetime.now().isoformat(),
                "score": f"{self.test_score}/5",
                "percentage": percentage
            })
            
            # Update stats as well
            stats = self.kanji_db.setdefault("stats", {"total_reviewed": 0, "total_correct": 0})
            stats["total_reviewed"] += 5
            stats["total_correct"] += self.test_score
            
            guardian.save_kanji_data(self.kanji_db)
            
            # Refresh statistics inside main GUI thread
            self.reload_and_sync_data()
            self.update_stats_header()
            self.render_all_cards()
            
            # OK/Done Button
            done_btn = tk.Button(
                content_frame,
                text="FINISH CHALLENGE",
                bg=ACCENT_PURPLE,
                fg=FG_LIGHT,
                activebackground="#9d6ef7",
                activeforeground=FG_LIGHT,
                bd=0,
                pady=10,
                font=(FONT_FAMILY, 9, "bold"),
                command=modal.destroy,
                cursor="hand2"
            )
            done_btn.pack(fill="x", pady=15)
            self.bind_button_hover(done_btn, ACCENT_PURPLE, "#9d6ef7")
            
        # Draw first question
        render_question()

        
    def redraw_progress_bar(self):
        """Redraws the horizontal glowing compliance progress bar inside stats header with smooth animation."""
        if not hasattr(self, "progress_canvas"):
            return
            
        total = len(self.tracked_tasks) + 1
        completed = sum(1 for t in self.tracked_tasks if self.data[self.today].get(t, False))
        
        # Check GitHub completed state
        git_done = self.data[self.today].get("github-commit", False)
        if self.github_live_status is not None:
            git_done = self.github_live_status
        if git_done:
            completed += 1
            
        # Add weekend prep task to progress if today is weekend and it is active
        is_weekend = (guardian.get_current_weekend_saturday_date() is not None) or self.mock_weekend
        is_active = self.config.get("japan_mnc_prep_active", True)
        if is_weekend and is_active:
            total += 1
            sat_date_str = "2026-05-23" if self.mock_weekend else guardian.get_current_weekend_saturday_date()
            task_entry = guardian.get_or_create_weekend_task(sat_date_str)
            if task_entry and task_entry.get("completed", False):
                completed += 1
                
        target_pct = completed / total
        
        if not hasattr(self, "current_drawn_pct"):
            self.current_drawn_pct = 0.0
            
        # Cancel any active animation loops
        if hasattr(self, "progress_anim_id") and self.progress_anim_id is not None:
            self.root.after_cancel(self.progress_anim_id)
            self.progress_anim_id = None
            
        self.animate_progress_bar(target_pct)

    def animate_progress_bar(self, target_pct):
        """Recursively updates the progress bar to animate it smoothly at 60fps."""
        diff = target_pct - self.current_drawn_pct
        step = 0.05
        
        if abs(diff) < step:
            self.current_drawn_pct = target_pct
        else:
            self.current_drawn_pct += step if diff > 0 else -step
            
        width = self.progress_canvas.winfo_width()
        if width <= 1:
            width = 330 # Fallback width
            
        self.progress_canvas.delete("bar")
        # Draw sleek progress bar
        self.progress_canvas.create_rectangle(0, 0, int(width * self.current_drawn_pct), 6, fill=ACCENT_GREEN, outline="", tags="bar")
        
        if self.current_drawn_pct != target_pct:
            self.progress_anim_id = self.root.after(15, lambda: self.animate_progress_bar(target_pct))
        else:
            self.progress_anim_id = None

    def update_live_clock(self):
        """Updates a ticking clock inside the widget title bar to bring it to life with dynamic progress badges."""
        try:
            now = datetime.now()
            time_str = now.strftime("%I:%M %p")
            # Blinking colon effect
            if now.second % 2 == 0:
                time_str = time_str.replace(":", " ")
                
            # Calculate dynamic task fraction
            total = len(self.tracked_tasks) + 1
            completed = sum(1 for t in self.tracked_tasks if self.data[self.today].get(t, False))
            
            git_done = self.data[self.today].get("github-commit", False)
            if self.github_live_status is not None:
                git_done = self.github_live_status
            if git_done:
                completed += 1
                
            is_weekend = (guardian.get_current_weekend_saturday_date() is not None) or self.mock_weekend
            is_active = self.config.get("japan_mnc_prep_active", True)
            if is_weekend and is_active:
                total += 1
                sat_date_str = "2026-05-23" if self.mock_weekend else guardian.get_current_weekend_saturday_date()
                task_entry = guardian.get_or_create_weekend_task(sat_date_str)
                if task_entry and task_entry.get("completed", False):
                    completed += 1
            
            badge = f"🏆 {completed}/{total}" if completed == total else f"🎯 {completed}/{total}"
            
            if hasattr(self, "title_label") and self.title_label.winfo_exists():
                self.title_label.config(text=f"🛡️  GUARDIAN  |  {badge}  |  ⏰ {time_str}")
        except Exception:
            pass
        self.root.after(1000, self.update_live_clock)

if __name__ == "__main__":
    try:
        # Create Tkinter root and run main application loop
        root = tk.Tk()
        app = GuardianWidget(root)
        root.mainloop()
    except Exception as e:
        import traceback
        try:
            with open(CRASH_LOG, "a") as f:
                f.write(f"\nRuntime GUI Execution Crash Error:\n{str(e)}\n\nTraceback:\n")
                traceback.print_exc(file=f)
        except Exception:
            pass
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Guardian GUI Runtime Error", f"Guardian Widget crashed:\n\n{e}\n\nCheck gui_crash_log.txt for details.")
        except Exception:
            pass
        sys.exit(1)
