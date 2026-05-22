import os
import sys

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

# ==================== THEME & COLOR PALETTE ====================
BG_DARK = "#1E1E2E"       # Slate dark background
BG_CARD = "#252538"       # Lighter card container
FG_LIGHT = "#F8F8F2"      # Clean high-contrast text
ACCENT_CYAN = "#8BE9FD"   # Header title cyan
ACCENT_GREEN = "#50FA7B"  # Glowing success neon green
ACCENT_RED = "#FF5555"    # Warning red
ACCENT_ORANGE = "#FFB86C" # Stats orange / flame
ACCENT_PURPLE = "#BD93F9" # Accent buttons purple
HOVER_COLOR = "#34344A"   # Card hover highlight

FONT_FAMILY = "Segoe UI" if os.name == "nt" else "Arial"

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
        
        # Load and synchronize initial today's entries
        self.reload_and_sync_data()

        # Render complete layout
        self.create_title_bar()
        self.create_stats_header()
        
        # Create container for tasks
        self.cards_frame = tk.Frame(self.root, bg=BG_DARK, padx=15)
        self.cards_frame.pack(fill="both", expand=True)
        
        self.render_all_cards()
        self.create_control_footer()
        
        # Initial GitHub live scan in separate thread
        self.trigger_background_github_sync()

    def reload_and_sync_data(self):
        """Loads config and syncs today's records inside database."""
        self.config = guardian.load_config()
        self.data = guardian.load_data()
        self.today = datetime.now().strftime("%Y-%m-%d")
        self.tracked_tasks = self.config.get("tracked_tasks", guardian.DEFAULT_TASKS)
        self.data = guardian.initialize_today(self.data, self.today, self.tracked_tasks)
        guardian.save_data(self.data)
        
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
        title_label = tk.Label(
            self.title_bar,
            text="🛡️  GUARDIAN WIDGET",
            fg=ACCENT_CYAN,
            bg=BG_CARD,
            font=(FONT_FAMILY, 9, "bold")
        )
        title_label.pack(side="left", padx=12)
        title_label.bind("<Button-1>", self.start_drag)
        title_label.bind("<B1-Motion>", self.drag_window)
        
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
        
        # Flame Indicator
        self.flame_label = tk.Label(
            self.stats_frame,
            bg=BG_DARK,
            font=(FONT_FAMILY, 13, "bold")
        )
        self.flame_label.pack(anchor="w")
        
        # Compliance stats
        self.compliance_label = tk.Label(
            self.stats_frame,
            bg=BG_DARK,
            font=(FONT_FAMILY, 8)
        )
        self.compliance_label.pack(anchor="w", pady=2)
        
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
        is_weekend = guardian.get_current_weekend_saturday_date() is not None
        is_active = self.config.get("japan_mnc_prep_active", True)
        if is_weekend and is_active:
            self.create_weekend_prep_card()
            
        # Draw all manual tracked tasks
        idx = 1
        for task in self.tracked_tasks:
            self.create_task_card(task, idx)
            idx += 1
            
        # Draw GitHub commit status card
        self.create_github_card()

    def create_task_card(self, task_name, idx):
        """Creates a custom stylized rounded card row for a manual habit."""
        is_done = self.data[self.today].get(task_name, False)
        
        card = tk.Frame(self.cards_frame, bg=BG_CARD, pady=8, padx=10, highlightthickness=0)
        card.pack(fill="x", pady=6)
        
        # Status Light Canvas (glowing green/red circle)
        canvas = tk.Canvas(card, width=16, height=16, bg=BG_CARD, highlightthickness=0)
        canvas.pack(side="left", padx=5)
        color = ACCENT_GREEN if is_done else ACCENT_RED
        canvas.create_oval(2, 2, 14, 14, fill=color, outline="")
        
        # Label
        label = tk.Label(
            card,
            text=f"{idx}.  {task_name.upper()}",
            fg=FG_LIGHT,
            bg=BG_CARD,
            font=(FONT_FAMILY, 10, "bold")
        )
        label.pack(side="left", padx=10)
        
        # Toggle Button
        btn_text = "UNDO" if is_done else "DONE"
        btn_color = ACCENT_PURPLE if is_done else BG_DARK
        btn_fg = FG_LIGHT
        
        toggle_btn = tk.Button(
            card,
            text=btn_text,
            bg=btn_color,
            fg=btn_fg,
            activebackground=HOVER_COLOR,
            activeforeground=FG_LIGHT,
            bd=1,
            highlightthickness=0,
            relief="flat",
            font=(FONT_FAMILY, 8, "bold"),
            width=8,
            cursor="hand2",
            command=lambda t=task_name: self.toggle_task_state(t)
        )
        toggle_btn.pack(side="right", padx=5)

    def create_github_card(self):
        """Creates the card row representing public commit synchronization."""
        # Check cached state
        is_done = self.data[self.today].get("github-commit", False)
        if self.github_live_status is not None:
            is_done = self.github_live_status
            
        card = tk.Frame(self.cards_frame, bg=BG_CARD, pady=8, padx=10)
        card.pack(fill="x", pady=6)
        
        # Status Canvas
        self.git_canvas = tk.Canvas(card, width=16, height=16, bg=BG_CARD, highlightthickness=0)
        self.git_canvas.pack(side="left", padx=5)
        color = ACCENT_GREEN if is_done else ACCENT_RED
        self.git_canvas.create_oval(2, 2, 14, 14, fill=color, outline="")
        
        # Label
        self.git_label = tk.Label(
            card,
            text="🐙  GITHUB COMMIT",
            fg=FG_LIGHT,
            bg=BG_CARD,
            font=(FONT_FAMILY, 10, "bold")
        )
        self.git_label.pack(side="left", padx=10)
        
        # Sync Button
        sync_text = "SYNCING..." if self.is_syncing_github else "🔄 SYNC"
        self.sync_btn = tk.Button(
            card,
            text=sync_text,
            bg=BG_DARK,
            fg=ACCENT_CYAN,
            activebackground=HOVER_COLOR,
            activeforeground=FG_LIGHT,
            bd=1,
            relief="flat",
            font=(FONT_FAMILY, 8, "bold"),
            width=9,
            cursor="hand2",
            command=self.trigger_background_github_sync,
            state="disabled" if self.is_syncing_github else "normal"
        )
        self.sync_btn.pack(side="right", padx=5)

    def create_weekend_prep_card(self):
        """Creates the premium Weekend Japan MNC Prep card at the top of the habit board."""
        # Get or create current weekend task
        task_entry = guardian.get_or_create_weekend_task()
        if not task_entry:
            return
            
        is_done = task_entry.get("completed", False)
        
        # Glowing premium card frame with purple border highlight
        card = tk.Frame(
            self.cards_frame, 
            bg="#2B2B42", # Distinct darker indigo-slate background
            pady=10, 
            padx=12,
            highlightbackground=ACCENT_PURPLE,
            highlightcolor=ACCENT_PURPLE,
            highlightthickness=1
        )
        card.pack(fill="x", pady=6)
        
        # Header Row
        header_frame = tk.Frame(card, bg="#2B2B42")
        header_frame.pack(fill="x")
        
        # Header Label with Emoji
        header_lbl = tk.Label(
            header_frame,
            text="🎌  TOKYO MNC PREP",
            fg=ACCENT_CYAN,
            bg="#2B2B42",
            font=(FONT_FAMILY, 9, "bold")
        )
        header_lbl.pack(side="left")
        
        # Source tag (e.g. Gemini AI or Curated)
        source_lbl = tk.Label(
            header_frame,
            text=f"[{task_entry.get('source', 'Roadmap')}]",
            fg=ACCENT_ORANGE,
            bg="#2B2B42",
            font=(FONT_FAMILY, 7, "bold")
        )
        source_lbl.pack(side="right")
        
        # Task Description (Wrapped)
        task_lbl = tk.Label(
            card,
            text=task_entry.get("task_title", ""),
            fg=FG_LIGHT,
            bg="#2B2B42",
            font=(FONT_FAMILY, 9),
            justify="left",
            wraplength=310,
            pady=6
        )
        task_lbl.pack(anchor="w")
        
        # Controls Frame (Complete, Notes, History)
        ctrl_frame = tk.Frame(card, bg="#2B2B42")
        ctrl_frame.pack(fill="x", pady=4)
        
        # Toggle Button
        btn_text = "UNDO" if is_done else "✓ COMPLETE"
        btn_bg = ACCENT_GREEN if not is_done else ACCENT_PURPLE
        btn_fg = BG_DARK if not is_done else FG_LIGHT
        
        toggle_btn = tk.Button(
            ctrl_frame,
            text=btn_text,
            bg=btn_bg,
            fg=btn_fg,
            activebackground=HOVER_COLOR,
            activeforeground=FG_LIGHT,
            bd=0,
            relief="flat",
            font=(FONT_FAMILY, 8, "bold"),
            padx=10,
            cursor="hand2",
            command=self.toggle_weekend_task_state
        )
        toggle_btn.pack(side="left", padx=2)
        
        # Notes Button
        notes_btn = tk.Button(
            ctrl_frame,
            text="📝 NOTES",
            bg=BG_CARD,
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
        
        # History Button
        history_btn = tk.Button(
            ctrl_frame,
            text="📚 HISTORY",
            bg=BG_CARD,
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

    def toggle_weekend_task_state(self):
        """Toggles the completed state of the current weekend task in the database."""
        sat_date_str = guardian.get_current_weekend_saturday_date()
        if not sat_date_str:
            return
            
        data = guardian.load_data()
        if "weekend_history" not in data:
            data["weekend_history"] = []
            
        for entry in data["weekend_history"]:
            if entry.get("date") == sat_date_str:
                entry["completed"] = not entry.get("completed", False)
                break
                
        guardian.save_data(data)
        self.reload_and_sync_data()
        self.render_all_cards()

    def open_weekend_notes_dialog(self):
        """Opens a Tkinter Toplevel modal dialog to log/edit study notes for the weekend task."""
        sat_date_str = guardian.get_current_weekend_saturday_date()
        if not sat_date_str:
            return
            
        task_entry = guardian.get_or_create_weekend_task()
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
            bg=ACCENT_PURPLE,
            fg=FG_LIGHT,
            activebackground=HOVER_COLOR,
            activeforeground=FG_LIGHT,
            bd=0,
            pady=10,
            font=(FONT_FAMILY, 9, "bold"),
            command=save_notes,
            cursor="hand2"
        )
        save_btn.pack(fill="x", padx=15, pady=15)

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
        
        # Enable mousewheel scrolling on scrollable frame
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _unbind_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
            
        modal.bind("<Destroy>", _unbind_mousewheel)
        
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
                    highlightbackground="#34344A",
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
            bg=BG_CARD,
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

    # ==================== CONTROLLER FUNCTIONS ====================

    def toggle_task_state(self, task_name):
        """Flips a manual task's state in database and updates GUI."""
        current_state = self.data[self.today].get(task_name, False)
        self.data[self.today][task_name] = not current_state
        guardian.save_data(self.data)
        
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
        modal.geometry("340x550")
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
        mnc_chk.pack(anchor="w", pady=6)

        def save_and_close():
            user = git_ent.get().strip()
            topic = topic_ent.get().strip()
            tasks_str = tasks_ent.get().strip()
            start_val = start_ent.get().strip()
            end_val = end_ent.get().strip()
            gemini_val = gemini_ent.get().strip()
            mnc_val = mnc_var.get()
            
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
            guardian.save_config(self.config)
            
            modal.destroy()
            
            # Refresh main app
            self.reload_and_sync_data()
            self.update_stats_header()
            self.render_all_cards()
            
        save_btn = tk.Button(
            modal, 
            text="SAVE CONFIG", 
            bg=ACCENT_PURPLE, 
            fg=FG_LIGHT, 
            activebackground=HOVER_COLOR,
            activeforeground=FG_LIGHT,
            bd=0, 
            pady=8,
            font=(FONT_FAMILY, 9, "bold"),
            command=save_and_close,
            cursor="hand2"
        )
        save_btn.pack(fill="x", padx=20, pady=15)

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
