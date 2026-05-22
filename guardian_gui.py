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
        
        # Load stats
        stats = guardian.calculate_stats()
        
        # Flame Indicator
        self.flame_label = tk.Label(
            self.stats_frame,
            text=f"🔥  {stats['current_streak']} DAY STREAK",
            fg=ACCENT_ORANGE,
            bg=BG_DARK,
            font=(FONT_FAMILY, 13, "bold")
        )
        self.flame_label.pack(anchor="w")
        
        # Compliance stats
        self.compliance_label = tk.Label(
            self.stats_frame,
            text=f"📊  7d Compliance: {stats['compliance_7d']:.1f}%   |   30d: {stats['compliance_30d']:.1f}%",
            fg=FG_LIGHT,
            bg=BG_DARK,
            font=(FONT_FAMILY, 8)
        )
        self.compliance_label.pack(anchor="w", pady=2)
        
        # Divider line
        divider = tk.Frame(self.root, bg=BG_CARD, height=1)
        divider.pack(fill="x", padx=15, pady=2)

    def render_all_cards(self):
        """Destroys and recreates the card list for manual tasks and github."""
        # Clear existing cards
        for widget in self.cards_frame.winfo_children():
            widget.destroy()
            
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
        audit_btn.pack(side="right", fill="x", expand=True, padx=4)

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
        stats = guardian.calculate_stats()
        self.flame_label.config(text=f"🔥  {stats['current_streak']} DAY STREAK")
        self.compliance_label.config(
            text=f"📊  7d Compliance: {stats['compliance_7d']:.1f}%   |   30d: {stats['compliance_30d']:.1f}%"
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

    # ==================== SETTINGS EDITOR DIALOG ====================

    def open_settings_modal(self):
        """Launches a modal window inside Tkinter to update settings."""
        modal = tk.Toplevel(self.root)
        modal.title("Settings Editor")
        modal.configure(bg=BG_DARK)
        modal.geometry("320x350")
        modal.resizable(False, False)
        modal.attributes("-topmost", True)
        
        # Center modal relative to main widget
        mx = self.root.winfo_x() + 20
        my = self.root.winfo_y() + 50
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

        def save_and_close():
            user = git_ent.get().strip()
            topic = topic_ent.get().strip()
            tasks_str = tasks_ent.get().strip()
            
            if not user or not topic:
                messagebox.showerror("Error", "Fields cannot be blank!", parent=modal)
                return
                
            tasks = [t.strip().lower() for t in tasks_str.split(",") if t.strip()]
            if not tasks:
                tasks = guardian.DEFAULT_TASKS
                
            self.config["github_username"] = user
            self.config["ntfy_topic"] = topic
            self.config["tracked_tasks"] = tasks
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
