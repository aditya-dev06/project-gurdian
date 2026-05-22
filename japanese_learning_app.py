import os
import sys
import json
import random
import threading
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import messagebox, ttk

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

# ==================== PRE-DEFINED GRAMMAR CURRICULUM ====================
GRAMMAR_LESSONS = [
    {
        "id": "wa_particle",
        "title": "Lesson 1: Topic Marker (は - wa)",
        "desc": "The particle は (pronounced 'wa') is the topic marker. It establishes the main topic of your sentence, which is then described.",
        "concept": "Topic [Noun] + は + Description [Noun/Adjective] + です\nExample: 私は学生です (As for me, I am a student).",
        "examples": [
            {"ja": "私は学生です。", "romaji": "watashi wa gakusei desu.", "en": "I am a student.", "pron": "わたしはがくせいです。"},
            {"ja": "これは本です。", "romaji": "kore wa hon desu.", "en": "This is a book.", "pron": "これはほんです。"}
        ],
        "builder": {
            "english": "I am a student.",
            "correct_order": ["私", "は", "学生", "です"],
            "options": ["学生", "は", "に", "私", "です", "猫"]
        }
    },
    {
        "id": "ga_particle",
        "title": "Lesson 2: Subject Marker (が - ga)",
        "desc": "The particle が marks the specific subject that performs an action or exists. While は emphasizes the description, が emphasizes the subject itself.",
        "concept": "Subject [Noun] + が + います (living objects) / あります (inanimate objects)\nExample: 猫がいます (There is a cat).",
        "examples": [
            {"ja": "猫がいます。", "romaji": "neko ga imasu.", "en": "There is a cat.", "pron": "ねこがいます。"},
            {"ja": "水があります。", "romaji": "mizu ga arimasu.", "en": "There is water.", "pron": "みずがあります。"}
        ],
        "builder": {
            "english": "There is a cat.",
            "correct_order": ["猫", "が", "います"],
            "options": ["猫", "は", "が", "います", "あります", "犬"]
        }
    },
    {
        "id": "o_particle",
        "title": "Lesson 3: Direct Object (を - o)",
        "desc": "The particle を (pronounced 'o') marks the direct object of a transitive verb. It indicates what is being acted upon.",
        "concept": "Object [Noun] + を + Verb [Action]\nExample: 本を読みます (I read a book).",
        "examples": [
            {"ja": "本を読みます。", "romaji": "hon o yomimasu.", "en": "I read a book.", "pron": "ほんをよみます。"},
            {"ja": "水を飲みます。", "romaji": "mizu o nomimasu.", "en": "I drink water.", "pron": "みずをのみます。"}
        ],
        "builder": {
            "english": "I read a book.",
            "correct_order": ["本", "を", "読みます"],
            "options": ["本", "に", "を", "読みます", "飲みます", "水"]
        }
    },
    {
        "id": "ni_particle",
        "title": "Lesson 4: Direction/Time (に - ni)",
        "desc": "The particle に has multiple uses, but its most core are marking: 1) a specific point in time, and 2) the destination of motion verbs.",
        "concept": "Destination [Noun] + に + 行きます (go) / 来ます (come)\nExample: 日本に行きます (I go to Japan).",
        "examples": [
            {"ja": "日本に行きます。", "romaji": "nihon ni ikimasu.", "en": "I go to Japan.", "pron": "にほん に いきます。"},
            {"ja": "駅に行きます。", "romaji": "eki ni ikimasu.", "en": "I go to the station.", "pron": "えき に いきます。"}
        ],
        "builder": {
            "english": "I go to Japan.",
            "correct_order": ["日本", "に", "行きます"],
            "options": ["日本", "を", "に", "行きます", "来ます", "駅"]
        }
    },
    {
        "id": "polite_verbs",
        "title": "Lesson 5: Polite Conjugation (~ます)",
        "desc": "Verbs in Japanese end in a dictionary form (plain). To speak politely, we conjugate them into the '~masu' form for present, and '~mashita' for past.",
        "concept": "行く (iku / go) ➔ 行きます (ikimasu / polite present)\n行く ➔ 行きました (ikimashitai / polite past)\n行く ➔ 行きません (ikimasen / polite present negative)",
        "examples": [
            {"ja": "行きました。", "romaji": "ikimashia.", "en": "I went.", "pron": "いきました。"},
            {"ja": "食べません。", "romaji": "tabemasen.", "en": "I do not eat.", "pron": "たべません。"}
        ],
        "builder": {
            "english": "I went to the school (学校).",
            "correct_order": ["学校", "に", "行きました"],
            "options": ["学校", "に", "を", "行きます", "行きました", "日本"]
        }
    },
    {
        "id": "adjectives",
        "title": "Lesson 6: Adjectives (い vs な)",
        "desc": "Japanese adjectives fall into two classes: i-adjectives (end in 'i' natively) and na-adjectives (require 'na' to connect to nouns).",
        "concept": "i-adj: 新しい車 (atarashii kuruma / new car) ➔ Connects directly.\nna-adj: 有名な人 (yuumei na hito / famous person) ➔ Requires 'na'.",
        "examples": [
            {"ja": "新しい車です。", "romaji": "atarashii kuruma desu.", "en": "It is a new car.", "pron": "あたらしいくるまです。"},
            {"ja": "有名な人です。", "romaji": "yuumei na hito desu.", "en": "He/she is a famous person.", "pron": "ゆうめいなひとです。"}
        ],
        "builder": {
            "english": "It is a new car.",
            "correct_order": ["新しい", "車", "です"],
            "options": ["新しい", "車", "な", "有名", "です", "猫"]
        }
    }
]

# ==================== TOOLTIP COMPONENT ====================
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
            font=(FONT_FAMILY, 9, "normal"),
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


# ==================== MAIN APPLICATION CLASS ====================
class JapaneseLearningApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Nihongo Study Core - Standalone Japanese Academy")
        self.root.geometry("1100x700")
        self.root.configure(bg=BG_DARK)
        
        # Set minimum window dimensions
        self.root.minsize(1000, 650)
        
        # State & Database variables
        self.kanji_db = guardian.load_kanji_data()
        self.config = guardian.load_config()
        self.tracker_data = guardian.load_data()
        
        # Active states
        self.active_kanji = None
        self.api_in_progress = False
        
        # Sentence builder active selection
        self.selected_builder_words = []
        self.current_lesson_idx = 0
        
        # SRS Review Active state
        self.srs_queue = []
        self.srs_current_idx = 0
        self.srs_show_details = False
        
        # Main Layout Partitioning
        self.create_layouts()
        self.draw_sidebar()
        
        # Start at Dashboard
        self.switch_view("dashboard")

    # ==================== WINDOW LAYOUT INITIALIZER ====================
    def create_layouts(self):
        """Partitions the window into a left sidebar and right content frame."""
        # Main window container
        self.main_container = tk.Frame(self.root, bg=BG_DARK)
        self.main_container.pack(fill="both", expand=True)
        
        # Sidebar Frame
        self.sidebar_frame = tk.Frame(
            self.main_container,
            bg=BG_CARD,
            width=230,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1
        )
        self.sidebar_frame.pack(side="left", fill="y")
        self.sidebar_frame.pack_propagate(False)
        
        # Main Area Content Frame
        self.content_frame = tk.Frame(self.main_container, bg=BG_DARK, padx=25, pady=20)
        self.content_frame.pack(side="right", fill="both", expand=True)

    # ==================== LEFT SIDEBAR NAVIGATION ====================
    def draw_sidebar(self):
        """Renders the sidebar with dynamic status metrics and navigation buttons."""
        # Top Logo Banner
        logo_lbl = tk.Label(
            self.sidebar_frame,
            text="🎌  NIHONGO CLASSIC",
            fg=ACCENT_CYAN,
            bg=BG_CARD,
            font=(FONT_FAMILY, 11, "bold"),
            pady=25
        )
        logo_lbl.pack()
        
        # Navigation Items list
        self.nav_buttons = {}
        nav_items = [
            ("dashboard", "📊  Dashboard"),
            ("kanji_explorer", "🎋  Kanji Explorer"),
            ("grammar_hub", "📖  Grammar Hub"),
            ("srs_review", "⚡  SRS Review Center")
        ]
        
        for view_key, label_text in nav_items:
            btn = tk.Button(
                self.sidebar_frame,
                text=label_text,
                bg=BG_CARD,
                fg=FG_SECONDARY,
                activebackground=HOVER_COLOR,
                activeforeground=FG_LIGHT,
                bd=0,
                anchor="w",
                padx=20,
                pady=12,
                font=(FONT_FAMILY, 9, "bold"),
                cursor="hand2",
                command=lambda k=view_key: self.switch_view(k)
            )
            btn.pack(fill="x", pady=2)
            self.bind_button_hover(btn, BG_CARD, HOVER_COLOR)
            self.nav_buttons[view_key] = btn
            
        # Add visual divider
        divider = tk.Frame(self.sidebar_frame, bg=BORDER_COLOR, height=1)
        divider.pack(fill="x", padx=15, pady=20)
        
        # Bottom Sidebar stats tracker container
        self.sidebar_stats_frame = tk.Frame(self.sidebar_frame, bg=BG_CARD, padx=20)
        self.sidebar_stats_frame.pack(fill="x", side="bottom", pady=20)
        
        self.lbl_streak_sb = tk.Label(
            self.sidebar_stats_frame,
            text="🔥 0 Day Streak",
            fg=ACCENT_ORANGE,
            bg=BG_CARD,
            font=(FONT_FAMILY, 10, "bold"),
            anchor="w"
        )
        self.lbl_streak_sb.pack(fill="x", pady=2)
        
        self.lbl_reviewed_sb = tk.Label(
            self.sidebar_stats_frame,
            text="🧠 0 Kanji Studied",
            fg=ACCENT_GREEN,
            bg=BG_CARD,
            font=(FONT_FAMILY, 8, "bold"),
            anchor="w"
        )
        self.lbl_reviewed_sb.pack(fill="x", pady=2)
        
        self.lbl_due_sb = tk.Label(
            self.sidebar_stats_frame,
            text="⚡ Reviews Due: 0",
            fg=ACCENT_CYAN,
            bg=BG_CARD,
            font=(FONT_FAMILY, 8, "bold"),
            anchor="w"
        )
        self.lbl_due_sb.pack(fill="x", pady=2)
        
        self.update_sidebar_stats()

    def update_sidebar_stats(self):
        """Calculates and refreshes the live data badges inside the sidebar."""
        # Calculate studied Kanji
        vocab = self.kanji_db.get("vocab", {})
        studied_count = len(vocab)
        
        # Calculate active streak from tracker
        streak = 0
        try:
            stats = guardian.calculate_stats()
            streak = stats.get("current_streak", 0)
        except Exception:
            pass
            
        # Calculate active due reviews
        due_count = 0
        now = datetime.now()
        for c in vocab.values():
            nxt = c.get("next_review")
            if nxt:
                try:
                    if datetime.fromisoformat(nxt) <= now:
                        due_count += 1
                except Exception:
                    pass
                    
        # Apply labels
        self.lbl_streak_sb.config(text=f"🔥  {streak} DAY STREAK")
        self.lbl_reviewed_sb.config(text=f"🧠  {studied_count} Kanji Studied")
        self.lbl_due_sb.config(text=f"⚡  Reviews Due: {due_count}")
        
        # Add dynamic countdown badge value to sidebar reviews item
        if due_count > 0:
            self.nav_buttons["srs_review"].config(text=f"⚡  SRS Review ({due_count})", fg=ACCENT_CYAN)
        else:
            self.nav_buttons["srs_review"].config(text="⚡  SRS Review Center", fg=FG_SECONDARY)

    # ==================== NAVIGATION CONTROLLER ====================
    def switch_view(self, view_key):
        """Cleans current views and swaps in the targeted modular panel."""
        # Reset navigation highlights
        for key, btn in self.nav_buttons.items():
            btn.config(bg=BG_CARD, fg=FG_SECONDARY)
            
        # Highlight active navigation
        self.nav_buttons[view_key].config(bg=HOVER_COLOR, fg=FG_LIGHT)
        
        # Clear main content children
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        # Reload databases for real-time consistency
        self.kanji_db = guardian.load_kanji_data()
        self.tracker_data = guardian.load_data()
        self.update_sidebar_stats()
        
        # Launch corresponding view constructor
        if view_key == "dashboard":
            self.draw_dashboard()
        elif view_key == "kanji_explorer":
            self.draw_kanji_explorer()
        elif view_key == "grammar_hub":
            self.draw_grammar_hub()
        elif view_key == "srs_review":
            self.draw_srs_review()

    # ==================== VIEW 1: DASHBOARD HUB ====================
    def draw_dashboard(self):
        """Renders a beautiful greetings dashboard showing overview stats and studied metrics."""
        # Top Header Greeting
        header = tk.Frame(self.content_frame, bg=BG_DARK)
        header.pack(fill="x", pady=(0, 20))
        
        tk.Label(
            header,
            text="こんにちは, 学習者!",
            fg=ACCENT_CYAN,
            bg=BG_DARK,
            font=(FONT_FAMILY, 20, "bold"),
            anchor="w"
        ).pack(anchor="w")
        
        tk.Label(
            header,
            text="Welcome to your Nihongo Study Core. Monitor stats, explore kanji, and review lessons.",
            fg=FG_SECONDARY,
            bg=BG_DARK,
            font=(FONT_FAMILY, 10),
            anchor="w"
        ).pack(anchor="w", pady=(4, 0))
        
        # Grid Container for Action Tiles
        grid_frame = tk.Frame(self.content_frame, bg=BG_DARK)
        grid_frame.pack(fill="both", expand=True)
        
        # Row 1 Frame
        row1 = tk.Frame(grid_frame, bg=BG_DARK)
        row1.pack(fill="x", pady=8)
        
        # Streak Card (Left Column)
        streak = 0
        try:
            stats = guardian.calculate_stats()
            streak = stats.get("current_streak", 0)
        except Exception:
            pass
            
        card_streak = tk.Frame(
            row1,
            bg=BG_CARD,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1,
            padx=20,
            pady=20
        )
        card_streak.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        tk.Label(
            card_streak,
            text="🔥  CURRENT STREAK",
            fg=ACCENT_ORANGE,
            bg=BG_CARD,
            font=(FONT_FAMILY, 9, "bold")
        ).pack(anchor="w")
        
        tk.Label(
            card_streak,
            text=f"{streak} Days Active",
            fg=FG_LIGHT,
            bg=BG_CARD,
            font=(FONT_FAMILY, 18, "bold")
        ).pack(anchor="w", pady=6)
        
        tk.Label(
            card_streak,
            text="Commit code, study kanji, and complete habits daily to protect your flame!",
            fg=FG_SECONDARY,
            bg=BG_CARD,
            font=(FONT_FAMILY, 8),
            wraplength=350,
            justify="left"
        ).pack(anchor="w")
        
        # SRS Queue Status Card (Right Column)
        vocab = self.kanji_db.get("vocab", {})
        due_count = 0
        now = datetime.now()
        for c in vocab.values():
            nxt = c.get("next_review")
            if nxt:
                try:
                    if datetime.fromisoformat(nxt) <= now:
                        due_count += 1
                except Exception:
                    pass
                    
        card_srs = tk.Frame(
            row1,
            bg=BG_CARD,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1,
            padx=20,
            pady=20
        )
        card_srs.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        tk.Label(
            card_srs,
            text="⚡  SRS REVIEW QUEUE",
            fg=ACCENT_CYAN,
            bg=BG_CARD,
            font=(FONT_FAMILY, 9, "bold")
        ).pack(anchor="w")
        
        tk.Label(
            card_srs,
            text=f"{due_count} Vocabulary Due",
            fg=FG_LIGHT,
            bg=BG_CARD,
            font=(FONT_FAMILY, 18, "bold")
        ).pack(anchor="w", pady=6)
        
        btn_start = tk.Button(
            card_srs,
            text="START REVIEW SESSION",
            bg=ACCENT_CYAN if due_count > 0 else BG_INNER,
            fg=FG_LIGHT,
            activebackground="#147ce5",
            bd=0,
            font=(FONT_FAMILY, 8, "bold"),
            padx=12,
            pady=6,
            cursor="hand2",
            command=lambda: self.switch_view("srs_review"),
            state="normal" if due_count > 0 else "disabled"
        )
        btn_start.pack(anchor="w", pady=4)
        if due_count > 0:
            self.bind_button_hover(btn_start, ACCENT_CYAN, "#147ce5")
            
        # Row 2 Frame
        row2 = tk.Frame(grid_frame, bg=BG_DARK)
        row2.pack(fill="both", expand=True, pady=10)
        
        # Daily Vocabulary Inspiration (Left Column)
        card_inspire = tk.Frame(
            row2,
            bg=BG_CARD,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1,
            padx=20,
            pady=20
        )
        card_inspire.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        tk.Label(
            card_inspire,
            text="💡  DAILY INSPIRATION",
            fg=ACCENT_PURPLE,
            bg=BG_CARD,
            font=(FONT_FAMILY, 9, "bold")
        ).pack(anchor="w")
        
        # Pick a random studied kanji or fallback
        items = list(vocab.values())
        if items:
            inspire_kanji = random.choice(items)
        else:
            inspire_kanji = {
                "kanji": "日",
                "meaning": "day, sun, Japan",
                "onyomi": "ニチ",
                "kunyomi": "ひ",
                "example_ja": "日本にいきたいです。",
                "example_en": "I want to go to Japan."
            }
            
        lbl_k = tk.Label(
            card_inspire,
            text=inspire_kanji.get("kanji"),
            fg=ACCENT_CYAN,
            bg=BG_CARD,
            font=(FONT_FAMILY, 36, "bold")
        )
        lbl_k.pack(anchor="w", pady=4)
        
        tk.Label(
            card_inspire,
            text=f"Meaning: {inspire_kanji.get('meaning')}",
            fg=FG_LIGHT,
            bg=BG_CARD,
            font=(FONT_FAMILY, 10, "bold")
        ).pack(anchor="w")
        
        tk.Label(
            card_inspire,
            text=f"On: {inspire_kanji.get('onyomi', '(none)')}   |   Kun: {inspire_kanji.get('kunyomi', '(none)')}",
            fg=FG_SECONDARY,
            bg=BG_CARD,
            font=(FONT_FAMILY, 8, "bold")
        ).pack(anchor="w", pady=2)
        
        tk.Label(
            card_inspire,
            text=f"例句: {inspire_kanji.get('example_ja')}",
            fg=FG_LIGHT,
            bg=BG_CARD,
            font=(FONT_FAMILY, 9),
            wraplength=350,
            justify="left"
        ).pack(anchor="w", pady=(8, 2))
        
        # Audio Pronounce
        btn_speak = tk.Button(
            card_inspire,
            text="🔊 PRONOUNCE",
            bg=BG_INNER,
            fg=ACCENT_CYAN,
            activebackground=HOVER_COLOR,
            bd=0,
            font=(FONT_FAMILY, 8, "bold"),
            padx=10,
            pady=4,
            cursor="hand2",
            command=lambda: guardian.speak_japanese_text(inspire_kanji.get("example_ja", inspire_kanji.get("kanji")))
        )
        btn_speak.pack(anchor="w", pady=(6, 0))
        self.bind_button_hover(btn_speak, BG_INNER, HOVER_COLOR)
        
        # Fast Dictionary Quick Lookup Widget (Right Column)
        card_lookup = tk.Frame(
            row2,
            bg=BG_CARD,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1,
            padx=20,
            pady=20
        )
        card_lookup.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        tk.Label(
            card_lookup,
            text="🔍  DICTIONARY SEARCH",
            fg=ACCENT_GREEN,
            bg=BG_CARD,
            font=(FONT_FAMILY, 9, "bold")
        ).pack(anchor="w")
        
        tk.Label(
            card_lookup,
            text="Quickly search studied vocabulary by character or English meaning:",
            fg=FG_SECONDARY,
            bg=BG_CARD,
            font=(FONT_FAMILY, 8),
            wraplength=350,
            justify="left"
        ).pack(anchor="w", pady=(4, 8))
        
        search_entry = tk.Entry(
            card_lookup,
            bg=BG_INNER,
            fg=FG_LIGHT,
            insertbackground=FG_LIGHT,
            bd=1,
            relief="flat",
            font=(FONT_FAMILY, 9)
        )
        search_entry.pack(fill="x", pady=4)
        
        result_lbl = tk.Label(
            card_lookup,
            text="",
            fg=ACCENT_ORANGE,
            bg=BG_CARD,
            font=(FONT_FAMILY, 9, "bold"),
            justify="left",
            wraplength=350
        )
        result_lbl.pack(anchor="w", fill="both", expand=True, pady=8)
        
        def run_search(e=None):
            q = search_entry.get().strip().lower()
            if not q:
                result_lbl.config(text="")
                return
            for key, val in vocab.items():
                if q in key or q in val.get("meaning", "").lower():
                    result_lbl.config(
                        text=f"Matched: {key} ({val.get('meaning')})\n"
                             f"On: {val.get('onyomi')} | Kun: {val.get('kunyomi')}\n"
                             f"Example: {val.get('example_ja')}"
                    )
                    return
            result_lbl.config(text="No studied Kanji matching query.")
            
        search_entry.bind("<KeyRelease>", run_search)

    # ==================== VIEW 2: KANJI EXPLORER ====================
    def draw_kanji_explorer(self):
        """Displays a dual-panel list/grid layout of Kanji with dynamic Gemini example generator and manual input additions."""
        # Top Header
        header = tk.Frame(self.content_frame, bg=BG_DARK)
        header.pack(fill="x", pady=(0, 15))
        
        tk.Label(
            header,
            text="🎋  KANJI EXPLORER CORE",
            fg=ACCENT_CYAN,
            bg=BG_DARK,
            font=(FONT_FAMILY, 16, "bold")
        ).pack(side="left")
        
        # Dual main columns partition
        explorer_body = tk.Frame(self.content_frame, bg=BG_DARK)
        explorer_body.pack(fill="both", expand=True)
        
        # 1. Left List panel
        list_panel = tk.Frame(explorer_body, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1, width=340)
        list_panel.pack(side="left", fill="both")
        list_panel.pack_propagate(False)
        
        # List Panel Search Filter
        search_frame = tk.Frame(list_panel, bg=BG_CARD, padx=10, pady=10)
        search_frame.pack(fill="x")
        
        search_input = tk.Entry(
            search_frame,
            bg=BG_INNER,
            fg=FG_LIGHT,
            insertbackground=FG_LIGHT,
            bd=0,
            font=(FONT_FAMILY, 9)
        )
        search_input.pack(fill="x", pady=(0, 8))
        
        # Filter Buttons frame
        filter_frame = tk.Frame(search_frame, bg=BG_CARD)
        filter_frame.pack(fill="x")
        
        filter_state = tk.StringVar(value="all")
        
        # Kanji Scrollable Container list
        scroll_container = tk.Frame(list_panel, bg=BG_CARD)
        scroll_container.pack(fill="both", expand=True, padx=5, pady=(0, 10))
        
        list_canvas = tk.Canvas(scroll_container, bg=BG_CARD, highlightthickness=0)
        scrollbar = tk.Scrollbar(scroll_container, orient="vertical", command=list_canvas.yview)
        list_frame = tk.Frame(list_canvas, bg=BG_CARD)
        
        list_frame.bind(
            "<Configure>",
            lambda e: list_canvas.configure(scrollregion=list_canvas.bbox("all"))
        )
        list_canvas.create_window((0, 0), window=list_frame, anchor="nw", width=310)
        list_canvas.configure(yscrollcommand=scrollbar.set)
        
        list_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Capture mouse scroll recursively
        def _on_list_scroll(event):
            if event.delta:
                list_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        list_canvas.bind("<MouseWheel>", _on_list_scroll)
        
        # 2. Right Detail panel
        detail_panel = tk.Frame(explorer_body, bg=BG_DARK, padx=15)
        detail_panel.pack(side="right", fill="both", expand=True)
        
        # Constructor for detail sub-elements inside right panel
        self.detail_body_frame = tk.Frame(detail_panel, bg=BG_DARK)
        self.detail_body_frame.pack(fill="both", expand=True)
        
        def render_explorer_list(e=None):
            # Clear old items
            for child in list_frame.winfo_children():
                child.destroy()
                
            query = search_input.get().strip().lower()
            vocab = self.kanji_db.get("vocab", {})
            
            # Sort items alphabetically by Kanji
            sorted_items = sorted(vocab.values(), key=lambda x: x.get("kanji", ""))
            
            idx = 0
            for item in sorted_items:
                kanji = item.get("kanji")
                meaning = item.get("meaning", "")
                
                # Apply filter
                if query and (query not in kanji and query not in meaning.lower()):
                    continue
                    
                # Highlight if selected
                active_kanji = self.active_kanji.get("kanji") if self.active_kanji else None
                bg_c = HOVER_COLOR if active_kanji == kanji else BG_CARD
                border_c = ACCENT_CYAN if active_kanji == kanji else BORDER_COLOR
                
                row_card = tk.Frame(
                    list_frame,
                    bg=bg_c,
                    pady=8,
                    padx=12,
                    highlightbackground=border_c,
                    highlightthickness=1,
                    cursor="hand2"
                )
                row_card.pack(fill="x", pady=3)
                
                k_lbl = tk.Label(row_card, text=kanji, fg=ACCENT_CYAN, bg=bg_c, font=(FONT_FAMILY, 14, "bold"))
                k_lbl.pack(side="left", padx=5)
                
                m_lbl = tk.Label(row_card, text=meaning[:20] + ("..." if len(meaning) > 20 else ""), fg=FG_LIGHT, bg=bg_c, font=(FONT_FAMILY, 8, "bold"))
                m_lbl.pack(side="left", padx=10)
                
                srs = item.get("srs_stage", 1)
                srs_lbl = tk.Label(row_card, text=f"SRS: {srs}", fg=ACCENT_ORANGE, bg=bg_c, font=(FONT_FAMILY, 7, "bold"))
                srs_lbl.pack(side="right", padx=5)
                
                # Bind select commands
                def bind_select_card(w, target_item=item):
                    def action(e):
                        self.active_kanji = target_item
                        self.render_kanji_details_pane()
                        render_explorer_list()
                    w.bind("<Button-1>", action)
                    for c in w.winfo_children():
                        c.bind("<Button-1>", action)
                        
                bind_select_card(row_card)
                self.bind_hover_highlight(row_card, bg_c, HOVER_COLOR)
                
                # Capture scroll
                row_card.bind("<MouseWheel>", _on_list_scroll)
                for child in row_card.winfo_children():
                    child.bind("<MouseWheel>", _on_list_scroll)
                    
            # Draw standard Manual Custom creation button at bottom of list
            btn_add_kanji = tk.Button(
                list_frame,
                text="➕  ADD CUSTOM KANJI",
                bg=BG_INNER,
                fg=ACCENT_CYAN,
                activebackground=HOVER_COLOR,
                activeforeground=FG_LIGHT,
                bd=0,
                font=(FONT_FAMILY, 8, "bold"),
                pady=10,
                cursor="hand2",
                command=self.open_custom_kanji_form
            )
            btn_add_kanji.pack(fill="x", pady=10)
            self.bind_button_hover(btn_add_kanji, BG_INNER, HOVER_COLOR)
            
        search_input.bind("<KeyRelease>", render_explorer_list)
        
        # Load first studied card as active card if available
        vocab_pool = list(self.kanji_db.get("vocab", {}).values())
        if vocab_pool and not self.active_kanji:
            self.active_kanji = sorted(vocab_pool, key=lambda x: x.get("kanji", ""))[0]
            
        render_explorer_list()
        self.render_kanji_details_pane()

    def render_kanji_details_pane(self):
        """Builds the rich detailed visualization for the active Kanji card in the right Explorer panel."""
        # Clear right main detail container
        for child in self.detail_body_frame.winfo_children():
            child.destroy()
            
        if not self.active_kanji:
            no_card = tk.Frame(self.detail_body_frame, bg=BG_DARK, pady=100)
            no_card.pack(fill="both", expand=True)
            tk.Label(
                no_card,
                text="🎋 No Kanji Selected",
                fg=FG_SECONDARY,
                bg=BG_DARK,
                font=(FONT_FAMILY, 14, "bold")
            ).pack()
            tk.Label(
                no_card,
                text="Select a studied Kanji from the left list or add a custom card to view details.",
                fg=FG_SECONDARY,
                bg=BG_DARK,
                font=(FONT_FAMILY, 9)
            ).pack(pady=4)
            return
            
        item = self.active_kanji
        
        # Header Row Details card
        card_frame = tk.Frame(
            self.detail_body_frame,
            bg=BG_CARD,
            padx=25,
            pady=25,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1
        )
        card_frame.pack(fill="both", expand=True)
        
        # Big Kanji character display
        left_header = tk.Frame(card_frame, bg=BG_CARD)
        left_header.pack(fill="x")
        
        kanji_lbl = tk.Label(
            left_header,
            text=item.get("kanji"),
            fg=ACCENT_CYAN,
            bg=BG_CARD,
            font=(FONT_FAMILY, 64, "bold"),
            cursor="hand2"
        )
        kanji_lbl.pack(side="left", padx=(0, 20))
        HoverTooltip(kanji_lbl, lambda: item.get("kanji_romaji", ""))
        
        details_col = tk.Frame(left_header, bg=BG_CARD)
        details_col.pack(side="left", fill="y", pady=10)
        
        meaning_lbl = tk.Label(
            details_col,
            text=item.get("meaning", "").upper(),
            fg=FG_LIGHT,
            bg=BG_CARD,
            font=(FONT_FAMILY, 16, "bold"),
            justify="left"
        )
        meaning_lbl.pack(anchor="w")
        
        yomi_lbl = tk.Label(
            details_col,
            text=f"読み: {item.get('kanji_yomi', '')}",
            fg=FG_SECONDARY,
            bg=BG_CARD,
            font=(FONT_FAMILY, 11, "bold")
        )
        yomi_lbl.pack(anchor="w", pady=2)
        HoverTooltip(yomi_lbl, lambda: item.get("kanji_romaji", ""))
        
        # Row 2: Readings Details
        readings_frame = tk.Frame(card_frame, bg=BG_INNER, padx=15, pady=12, highlightbackground=BORDER_COLOR, highlightthickness=1)
        readings_frame.pack(fill="x", pady=15)
        
        onyomi = item.get("onyomi", "")
        onyomi_txt = f"音読み (Onyomi): {onyomi}" if onyomi else "音読み (Onyomi): (none)"
        lbl_on = tk.Label(readings_frame, text=onyomi_txt, fg=ACCENT_ORANGE, bg=BG_INNER, font=(FONT_FAMILY, 9, "bold"))
        lbl_on.pack(anchor="w")
        HoverTooltip(lbl_on, lambda: item.get("kanji_romaji", ""))
        
        kunyomi = item.get("kunyomi", "")
        kunyomi_txt = f"訓読み (Kunyomi): {kunyomi}" if kunyomi else "訓読み (Kunyomi): (none)"
        lbl_kun = tk.Label(readings_frame, text=kunyomi_txt, fg=ACCENT_GREEN, bg=BG_INNER, font=(FONT_FAMILY, 9, "bold"))
        lbl_kun.pack(anchor="w", pady=(4, 0))
        HoverTooltip(lbl_kun, lambda: item.get("kanji_romaji", ""))
        
        # Row 3: Example Sentence Details
        example_frame = tk.Frame(card_frame, bg=BG_CARD)
        example_frame.pack(fill="x", pady=10)
        
        tk.Label(
            example_frame,
            text="例句 (EXAMPLE SENTENCE)",
            fg=ACCENT_PURPLE,
            bg=BG_CARD,
            font=(FONT_FAMILY, 9, "bold")
        ).pack(anchor="w")
        
        # The sentence content card
        sentence_box = tk.Frame(example_frame, bg=BG_INNER, padx=15, pady=15, highlightbackground=BORDER_COLOR, highlightthickness=1)
        sentence_box.pack(fill="x", pady=6)
        
        lbl_sentence_ja = tk.Label(
            sentence_box,
            text=item.get("example_ja"),
            fg=FG_LIGHT,
            bg=BG_INNER,
            font=(FONT_FAMILY, 12),
            wraplength=450,
            justify="left"
        )
        lbl_sentence_ja.pack(anchor="w")
        HoverTooltip(lbl_sentence_ja, lambda: item.get("example_romaji", ""))
        
        lbl_sentence_en = tk.Label(
            sentence_box,
            text=item.get("example_en"),
            fg=FG_SECONDARY,
            bg=BG_INNER,
            font=(FONT_FAMILY, 9, "italic"),
            wraplength=450,
            justify="left"
        )
        lbl_sentence_en.pack(anchor="w", pady=(4, 0))
        
        # Action Row Buttons inside Details card
        action_row = tk.Frame(card_frame, bg=BG_CARD)
        action_row.pack(fill="x", side="bottom", pady=(10, 0))
        
        # 1. Sound plays text pronunciation natively
        btn_pron_k = tk.Button(
            action_row,
            text="🔊 PRONOUNCE KANJI",
            bg=BG_INNER,
            fg=ACCENT_CYAN,
            activebackground=HOVER_COLOR,
            activeforeground=FG_LIGHT,
            bd=0,
            font=(FONT_FAMILY, 8, "bold"),
            padx=12,
            pady=8,
            cursor="hand2",
            command=lambda: guardian.speak_japanese_text(item.get("kanji_yomi", item.get("kanji")))
        )
        btn_pron_k.pack(side="left", padx=2)
        self.bind_button_hover(btn_pron_k, BG_INNER, HOVER_COLOR)
        
        btn_pron_s = tk.Button(
            action_row,
            text="🔊 PRONOUNCE SENTENCE",
            bg=BG_INNER,
            fg=ACCENT_CYAN,
            activebackground=HOVER_COLOR,
            activeforeground=FG_LIGHT,
            bd=0,
            font=(FONT_FAMILY, 8, "bold"),
            padx=12,
            pady=8,
            cursor="hand2",
            command=lambda: guardian.speak_japanese_text(item.get("example_ja"))
        )
        btn_pron_s.pack(side="left", padx=2)
        self.bind_button_hover(btn_pron_s, BG_INNER, HOVER_COLOR)
        
        # 2. Gemini sentence refresher helper
        btn_refresh = tk.Button(
            action_row,
            text="↻  REFRESH SENTENCE",
            bg=BG_INNER,
            fg=ACCENT_ORANGE,
            activebackground=HOVER_COLOR,
            activeforeground=FG_LIGHT,
            bd=0,
            font=(FONT_FAMILY, 8, "bold"),
            padx=12,
            pady=8,
            cursor="hand2",
            command=self.refresh_explorer_example_sentence
        )
        btn_refresh.pack(side="right", padx=2)
        self.bind_button_hover(btn_refresh, BG_INNER, HOVER_COLOR)

    def refresh_explorer_example_sentence(self):
        """Async triggers Gemini API call to generate a fresh, new Japanese sentence for current Kanji."""
        if not self.active_kanji or self.api_in_progress:
            return
            
        kanji = self.active_kanji.get("kanji")
        self.api_in_progress = True
        
        def run_refresh():
            api_key = self.config.get("gemini_api_key", "").strip()
            new_res = guardian.get_gemini_example_sentence(api_key, kanji)
            self.root.after(0, lambda: self.on_refresh_sentence_resolved(new_res))
            
        threading.Thread(target=run_refresh, daemon=True).start()

    def on_refresh_sentence_resolved(self, new_sentence):
        self.api_in_progress = False
        if not new_sentence or not self.active_kanji:
            return
            
        kanji_key = self.active_kanji.get("kanji")
        vocab = self.kanji_db.get("vocab", {})
        
        if kanji_key in vocab:
            vocab[kanji_key]["example_ja"] = new_sentence.get("example_ja", "")
            vocab[kanji_key]["example_en"] = new_sentence.get("example_en", "")
            vocab[kanji_key]["example_yomi"] = new_sentence.get("example_yomi", "")
            vocab[kanji_key]["example_romaji"] = new_sentence.get("example_romaji", "")
            
            # Save and update active card frame
            self.active_kanji = vocab[kanji_key]
            guardian.save_kanji_data(self.kanji_db)
            self.render_kanji_details_pane()

    def open_custom_kanji_form(self):
        """Launches a modal top dialog form allowing manual input/creation of custom Kanji cards."""
        modal = tk.Toplevel(self.root)
        modal.title("➕ Create Custom Kanji Vocabulary")
        modal.configure(bg=BG_DARK)
        modal.geometry("380x560")
        modal.resizable(False, False)
        modal.attributes("-topmost", True)
        
        # Center relative to root window
        mx = self.root.winfo_x() + 300
        my = self.root.winfo_y() + 80
        modal.geometry(f"+{mx}+{my}")
        
        # Title Header
        tk.Label(
            modal,
            text="➕  ADD CUSTOM KANJI NODE",
            fg=ACCENT_CYAN,
            bg=BG_DARK,
            font=(FONT_FAMILY, 11, "bold"),
            pady=15
        ).pack()
        
        form_frame = tk.Frame(modal, bg=BG_DARK, padx=20)
        form_frame.pack(fill="both", expand=True)
        
        # Custom Form Entries
        fields = [
            ("kanji", "Kanji Character (e.g. 木):"),
            ("meaning", "English Meaning (e.g. tree, wood):"),
            ("yomi", "Hiragana Reading (e.g. き):"),
            ("romaji", "Romaji Reading (e.g. ki):"),
            ("onyomi", "Onyomi (Chinese reading - e.g. モク):"),
            ("kunyomi", "Kunyomi (Japanese reading - e.g. き):"),
            ("ex_ja", "Example Japanese Sentence:"),
            ("ex_en", "Example English Translation:")
        ]
        
        entries = {}
        for key, prompt in fields:
            tk.Label(form_frame, text=prompt, fg=FG_LIGHT, bg=BG_DARK, font=(FONT_FAMILY, 8, "bold")).pack(anchor="w", pady=(4, 1))
            entry = tk.Entry(form_frame, bg=BG_CARD, fg=FG_LIGHT, insertbackground=FG_LIGHT, bd=1, relief="flat", font=(FONT_FAMILY, 9))
            entry.pack(fill="x")
            entries[key] = entry
            
        def submit_custom_card():
            k = entries["kanji"].get().strip()
            meaning = entries["meaning"].get().strip()
            yomi = entries["yomi"].get().strip()
            romaji = entries["romaji"].get().strip()
            onyomi = entries["onyomi"].get().strip()
            kunyomi = entries["kunyomi"].get().strip()
            ex_ja = entries["ex_ja"].get().strip()
            ex_en = entries["ex_en"].get().strip()
            
            if not k or not meaning or not yomi or not romaji or not ex_ja or not ex_en:
                messagebox.showerror("Validation Error", "All fields except Onyomi and Kunyomi are required!", parent=modal)
                return
                
            vocab = self.kanji_db.setdefault("vocab", {})
            if k in vocab:
                messagebox.showerror("Conflict Warning", f"Kanji '{k}' is already studied in your database!", parent=modal)
                return
                
            vocab[k] = {
                "kanji": k,
                "meaning": meaning,
                "onyomi": onyomi,
                "kunyomi": kunyomi,
                "stroke_count": len(k),
                "example_ja": ex_ja,
                "example_en": ex_en,
                "kanji_yomi": yomi,
                "kanji_romaji": romaji,
                "example_yomi": yomi,
                "example_romaji": romaji,
                "level": "Custom",
                "srs_stage": 1,
                "next_review": (datetime.now() + timedelta(days=1)).isoformat(),
                "history": []
            }
            
            guardian.save_kanji_data(self.kanji_db)
            modal.destroy()
            
            # Reset active card and redraw panel
            self.active_kanji = vocab[k]
            self.switch_view("kanji_explorer")
            messagebox.showinfo("Success", f"Custom Kanji '{k}' added successfully!", parent=self.root)
            
        btn_submit = tk.Button(
            modal,
            text="SAVE CUSTOM KANJI",
            bg=ACCENT_CYAN,
            fg=FG_LIGHT,
            activebackground="#147ce5",
            bd=0,
            font=(FONT_FAMILY, 9, "bold"),
            pady=10,
            cursor="hand2",
            command=submit_custom_card
        )
        btn_submit.pack(fill="x", side="bottom", padx=20, pady=15)
        self.bind_button_hover(btn_submit, ACCENT_CYAN, "#147ce5")

    # ==================== VIEW 3: GRAMMAR HUB ====================
    def draw_grammar_hub(self):
        """Renders the modular categorized Japanese grammar lesson lists."""
        # Top Header
        header = tk.Frame(self.content_frame, bg=BG_DARK)
        header.pack(fill="x", pady=(0, 15))
        
        tk.Label(
            header,
            text="📖  GRAMMAR HUB & ACADEMY",
            fg=ACCENT_CYAN,
            bg=BG_DARK,
            font=(FONT_FAMILY, 16, "bold")
        ).pack(side="left")
        
        # Grid Container for Lesson lists
        scroll_frame = tk.Frame(self.content_frame, bg=BG_DARK)
        scroll_frame.pack(fill="both", expand=True)
        
        canvas = tk.Canvas(scroll_frame, bg=BG_DARK, highlightthickness=0)
        scrollbar = tk.Scrollbar(scroll_frame, orient="vertical", command=canvas.yview)
        lessons_grid = tk.Frame(canvas, bg=BG_DARK)
        
        lessons_grid.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=lessons_grid, anchor="nw", width=800)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Capture mouse scroll recursively
        def _on_grid_scroll(event):
            if event.delta:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind("<MouseWheel>", _on_grid_scroll)
        
        # Retrieve lesson progress database
        progress = self.kanji_db.setdefault("grammar_progress", {})
        
        # Build cards for each lesson
        idx = 1
        for lesson in GRAMMAR_LESSONS:
            lesson_id = lesson.get("id")
            is_learned = progress.get(lesson_id, False)
            
            # Glowing border highlight if complete
            border_color = ACCENT_GREEN if is_learned else BORDER_COLOR
            card = tk.Frame(
                lessons_grid,
                bg=BG_CARD,
                pady=15,
                padx=20,
                highlightbackground=border_color,
                highlightthickness=1
            )
            card.pack(fill="x", pady=6)
            
            # Header Row
            row_title = tk.Frame(card, bg=BG_CARD)
            row_title.pack(fill="x")
            
            title_text = f"✓  {lesson.get('title')}" if is_learned else lesson.get("title")
            title_color = ACCENT_GREEN if is_learned else FG_LIGHT
            tk.Label(
                row_title,
                text=title_text,
                fg=title_color,
                bg=BG_CARD,
                font=(FONT_FAMILY, 10, "bold")
            ).pack(side="left")
            
            # Short Desc
            tk.Label(
                card,
                text=lesson.get("desc"),
                fg=FG_SECONDARY,
                bg=BG_CARD,
                font=(FONT_FAMILY, 8),
                wraplength=700,
                justify="left"
            ).pack(anchor="w", pady=(6, 4))
            
            # Start button
            def bind_start_lesson(target_idx=idx-1):
                return lambda: self.launch_interactive_lesson(target_idx)
                
            btn_start = tk.Button(
                card,
                text="STUDY LESSON",
                bg=BG_INNER,
                fg=ACCENT_CYAN,
                activebackground=HOVER_COLOR,
                bd=0,
                font=(FONT_FAMILY, 8, "bold"),
                padx=10,
                pady=5,
                cursor="hand2",
                command=bind_start_lesson(idx-1)
            )
            btn_start.pack(anchor="w", pady=(6, 0))
            self.bind_button_hover(btn_start, BG_INNER, HOVER_COLOR)
            
            self.bind_hover_highlight(card, BG_CARD, HOVER_COLOR)
            card.bind("<MouseWheel>", _on_grid_scroll)
            for c in card.winfo_children():
                c.bind("<MouseWheel>", _on_grid_scroll)
                
            idx += 1

    def launch_interactive_lesson(self, lesson_idx):
        """Replaces main content view with the interactive detailed Grammar study card."""
        self.current_lesson_idx = lesson_idx
        lesson = GRAMMAR_LESSONS[lesson_idx]
        
        # Reset selection order
        self.selected_builder_words = []
        
        # Clear view
        for child in self.content_frame.winfo_children():
            child.destroy()
            
        # Lesson Frame Layout
        container = tk.Frame(self.content_frame, bg=BG_DARK)
        container.pack(fill="both", expand=True)
        
        # 1. Back button row
        back_row = tk.Frame(container, bg=BG_DARK)
        back_row.pack(fill="x", pady=(0, 10))
        
        btn_back = tk.Button(
            back_row,
            text="⬅️  BACK TO GRAMMAR LIST",
            bg=BG_CARD,
            fg=FG_LIGHT,
            activebackground=HOVER_COLOR,
            bd=0,
            font=(FONT_FAMILY, 8, "bold"),
            padx=12,
            pady=6,
            cursor="hand2",
            command=lambda: self.switch_view("grammar_hub")
        )
        btn_back.pack(side="left")
        self.bind_button_hover(btn_back, BG_CARD, HOVER_COLOR)
        
        # Main Detail Study Card
        self.lesson_card = tk.Frame(
            container,
            bg=BG_CARD,
            padx=25,
            pady=20,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1
        )
        self.lesson_card.pack(fill="both", expand=True)
        
        # Lesson Title
        tk.Label(
            self.lesson_card,
            text=lesson.get("title"),
            fg=ACCENT_CYAN,
            bg=BG_CARD,
            font=(FONT_FAMILY, 16, "bold")
        ).pack(anchor="w")
        
        tk.Label(
            self.lesson_card,
            text=lesson.get("desc"),
            fg=FG_LIGHT,
            bg=BG_CARD,
            font=(FONT_FAMILY, 10),
            wraplength=750,
            justify="left"
        ).pack(anchor="w", pady=(8, 12))
        
        # Concept Formula Frame
        formula_box = tk.Frame(self.lesson_card, bg=BG_INNER, padx=15, pady=12, highlightbackground=BORDER_COLOR, highlightthickness=1)
        formula_box.pack(fill="x", pady=(0, 15))
        
        tk.Label(
            formula_box,
            text="GRAMMATICAL CONCEPT",
            fg=ACCENT_ORANGE,
            bg=BG_INNER,
            font=(FONT_FAMILY, 8, "bold")
        ).pack(anchor="w")
        
        tk.Label(
            formula_box,
            text=lesson.get("concept"),
            fg=FG_LIGHT,
            bg=BG_INNER,
            font=(FONT_FAMILY, 10, "bold"),
            justify="left"
        ).pack(anchor="w", pady=(4, 0))
        
        # Interactive Sentence Builder Panel
        self.sentence_builder_frame = tk.Frame(self.lesson_card, bg=BG_CARD)
        self.sentence_builder_frame.pack(fill="x", pady=10)
        
        self.render_sentence_builder_game()
        
        # Persistent learning completion
        bottom_row = tk.Frame(self.lesson_card, bg=BG_CARD)
        bottom_row.pack(fill="x", side="bottom", pady=(15, 0))
        
        progress = self.kanji_db.get("grammar_progress", {})
        is_learned = progress.get(lesson.get("id"), False)
        
        def mark_lesson_complete():
            l_id = lesson.get("id")
            progress[l_id] = not progress.get(l_id, False)
            guardian.save_kanji_data(self.kanji_db)
            self.launch_interactive_lesson(lesson_idx)
            
        btn_mark = tk.Button(
            bottom_row,
            text="✓  MARK LESSON COMPLETE" if not is_learned else "✓  UNMARK COMPLETION",
            bg=ACCENT_GREEN if is_learned else ACCENT_CYAN,
            fg=FG_LIGHT,
            activebackground="#147ce5",
            bd=0,
            font=(FONT_FAMILY, 8, "bold"),
            padx=12,
            pady=8,
            cursor="hand2",
            command=mark_lesson_complete
        )
        btn_mark.pack(side="left")
        self.bind_button_hover(btn_mark, ACCENT_GREEN if is_learned else ACCENT_CYAN, "#147ce5")

    def render_sentence_builder_game(self):
        """Constructs the interactive drag/click particle slots game inside grammar lessons."""
        # Clear builder subframe
        for child in self.sentence_builder_frame.winfo_children():
            child.destroy()
            
        lesson = GRAMMAR_LESSONS[self.current_lesson_idx]
        builder = lesson.get("builder")
        
        tk.Label(
            self.sentence_builder_frame,
            text="⚡  INTERACTIVE SENTENCE BUILDER GAME",
            fg=ACCENT_PURPLE,
            bg=BG_CARD,
            font=(FONT_FAMILY, 9, "bold")
        ).pack(anchor="w")
        
        tk.Label(
            self.sentence_builder_frame,
            text=f"Translate this sentence to Japanese: '{builder.get('english')}'",
            fg=FG_SECONDARY,
            bg=BG_CARD,
            font=(FONT_FAMILY, 9)
        ).pack(anchor="w", pady=(2, 8))
        
        # 1. Selection slots display frame (Empty or filled slots)
        slots_panel = tk.Frame(
            self.sentence_builder_frame,
            bg=BG_INNER,
            pady=15,
            padx=15,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1
        )
        slots_panel.pack(fill="x", pady=6)
        
        # Populate selected word badges
        if not self.selected_builder_words:
            lbl_tip = tk.Label(slots_panel, text="Click on the word pill blocks below in correct order...", fg=FG_SECONDARY, bg=BG_INNER, font=(FONT_FAMILY, 9, "italic"))
            lbl_tip.pack()
        else:
            for word in self.selected_builder_words:
                badge = tk.Label(
                    slots_panel,
                    text=word,
                    bg=BG_DARK,
                    fg=ACCENT_CYAN,
                    font=(FONT_FAMILY, 10, "bold"),
                    padx=10,
                    pady=4,
                    relief="flat"
                )
                badge.pack(side="left", padx=3)
                
        # 2. Tray frame containing available word pills
        tray_panel = tk.Frame(self.sentence_builder_frame, bg=BG_CARD, pady=10)
        tray_panel.pack(fill="x")
        
        for option in builder.get("options"):
            # If word is already selected, disable or skip showing
            times_selected = self.selected_builder_words.count(option)
            times_total = builder.get("options").count(option)
            
            # Basic validation
            state_val = "normal"
            bg_c = BG_INNER
            fg_c = FG_LIGHT
            if times_selected >= times_total:
                state_val = "disabled"
                bg_c = BG_CARD
                fg_c = FG_SECONDARY
                
            def make_click_cmd(w=option):
                return lambda: self.select_builder_word(w)
                
            pill = tk.Button(
                tray_panel,
                text=option,
                bg=bg_c,
                fg=fg_c,
                activebackground=HOVER_COLOR,
                activeforeground=FG_LIGHT,
                bd=0,
                font=(FONT_FAMILY, 9, "bold"),
                padx=12,
                pady=6,
                state=state_val,
                cursor="hand2" if state_val == "normal" else "arrow",
                command=make_click_cmd(option)
            )
            pill.pack(side="left", padx=4)
            if state_val == "normal":
                self.bind_button_hover(pill, bg_c, HOVER_COLOR)
                
        # Reset and Check Action controls
        ctrls = tk.Frame(self.sentence_builder_frame, bg=BG_CARD)
        ctrls.pack(fill="x", pady=(5, 0))
        
        btn_reset = tk.Button(
            ctrls,
            text="↻  RESET GAME",
            bg=BG_INNER,
            fg=ACCENT_RED,
            activebackground=HOVER_COLOR,
            bd=0,
            font=(FONT_FAMILY, 8, "bold"),
            padx=10,
            pady=5,
            cursor="hand2",
            command=self.reset_builder_game
        )
        btn_reset.pack(side="left", padx=2)
        self.bind_button_hover(btn_reset, BG_INNER, HOVER_COLOR)
        
        btn_check = tk.Button(
            ctrls,
            text="⚡  EVALUATE SENTENCE",
            bg=ACCENT_CYAN,
            fg=FG_LIGHT,
            activebackground="#147ce5",
            bd=0,
            font=(FONT_FAMILY, 8, "bold"),
            padx=12,
            pady=5,
            cursor="hand2",
            command=self.check_sentence_builder_correctness
        )
        btn_check.pack(side="left", padx=10)
        self.bind_button_hover(btn_check, ACCENT_CYAN, "#147ce5")

    def select_builder_word(self, word):
        """Triggered when user clicks a tray word pill block."""
        self.selected_builder_words.append(word)
        self.render_sentence_builder_game()

    def reset_builder_game(self):
        """Cleans selected word sequence and redraws game board."""
        self.selected_builder_words = []
        self.render_sentence_builder_game()
        # Reset card outlines
        self.lesson_card.config(highlightbackground=BORDER_COLOR)

    def check_sentence_builder_correctness(self):
        """Validates if selected words match the correct grammatical sentence sequence."""
        lesson = GRAMMAR_LESSONS[self.current_lesson_idx]
        builder = lesson.get("builder")
        correct = builder.get("correct_order")
        
        if self.selected_builder_words == correct:
            # Speak Correct response out loud
            guardian.speak_japanese_text("せいかい！ 正解")
            
            # Glowing Green Aura flash highlight success
            self.lesson_card.config(highlightbackground=ACCENT_GREEN, highlightthickness=1)
            messagebox.showinfo("🎉 EXCELLENT!", "Correct sequence built! You have successfully mastered this sentence structure!", parent=self.root)
        else:
            # Speak Mistake response
            guardian.speak_japanese_text("まちがい！ 間違い")
            
            # Glowing Red Aura highlight error
            self.lesson_card.config(highlightbackground=ACCENT_RED, highlightthickness=1)
            messagebox.showerror("❌ MISTAKE", "Ah, that is not quite right! Keep trying and check the grammatical concept above.", parent=self.root)

    # ==================== VIEW 4: SRS REVIEW CENTER ====================
    def draw_srs_review(self):
        """Builds the active SRS card reviewing terminal panel."""
        # Top Header
        header = tk.Frame(self.content_frame, bg=BG_DARK)
        header.pack(fill="x", pady=(0, 20))
        
        tk.Label(
            header,
            text="⚡  SRS REVIEW CENTER",
            fg=ACCENT_CYAN,
            bg=BG_DARK,
            font=(FONT_FAMILY, 16, "bold")
        ).pack(side="left")
        
        # Main body study frame
        self.srs_body_frame = tk.Frame(self.content_frame, bg=BG_DARK)
        self.srs_body_frame.pack(fill="both", expand=True)
        
        # Scan studied nodes for due reviews
        vocab = self.kanji_db.get("vocab", {})
        now = datetime.now()
        
        self.srs_queue = []
        for c in vocab.values():
            nxt = c.get("next_review")
            if nxt:
                try:
                    if datetime.fromisoformat(nxt) <= now:
                        self.srs_queue.append(c)
                except Exception:
                    pass
                    
        # Shuffle review queue for maximum active learning randomized triggers
        random.shuffle(self.srs_queue)
        
        self.srs_current_idx = 0
        self.srs_show_details = False
        self.render_srs_flashcard_state()

    def render_srs_flashcard_state(self):
        """Draws the selected active flashcard in due reviews or final Inbox Zero card."""
        # Clear body frame
        for child in self.srs_body_frame.winfo_children():
            child.destroy()
            
        # 1. Caught up (Inbox Zero)
        if not self.srs_queue or self.srs_current_idx >= len(self.srs_queue):
            inbox_zero = tk.Frame(
                self.srs_body_frame,
                bg=BG_CARD,
                padx=35,
                pady=40,
                highlightbackground=BORDER_COLOR,
                highlightthickness=1
            )
            inbox_zero.pack(fill="x", pady=50)
            
            tk.Label(
                inbox_zero,
                text="🎉  ALL CAUGHT UP!",
                fg=ACCENT_GREEN,
                bg=BG_CARD,
                font=(FONT_FAMILY, 18, "bold")
            ).pack()
            
            tk.Label(
                inbox_zero,
                text="Outstanding work! Your SRS review queue is completely empty.\n"
                     "Explore studied vocabulary or add new manual custom cards to schedule more items.",
                fg=FG_LIGHT,
                bg=BG_CARD,
                font=(FONT_FAMILY, 10),
                pady=15,
                justify="center"
            ).pack()
            
            # Simple button returning to explorer
            btn_go = tk.Button(
                inbox_zero,
                text="EXPLORE KANJI DATABASE",
                bg=ACCENT_CYAN,
                fg=FG_LIGHT,
                activebackground="#147ce5",
                bd=0,
                font=(FONT_FAMILY, 8, "bold"),
                padx=15,
                pady=8,
                cursor="hand2",
                command=lambda: self.switch_view("kanji_explorer")
            )
            btn_go.pack()
            self.bind_button_hover(btn_go, ACCENT_CYAN, "#147ce5")
            return
            
        # 2. Reviews due
        card_data = self.srs_queue[self.srs_current_idx]
        
        # Central card review container
        card_container = tk.Frame(
            self.srs_body_frame,
            bg=BG_CARD,
            padx=35,
            pady=30,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1
        )
        card_container.pack(fill="both", expand=True)
        
        # Queue count index header
        tk.Label(
            card_container,
            text=f"REVIEWING ITEM: {self.srs_current_idx + 1} OF {len(self.srs_queue)}",
            fg=ACCENT_ORANGE,
            bg=BG_CARD,
            font=(FONT_FAMILY, 8, "bold")
        ).pack(anchor="w")
        
        # Large Kanji visual display
        kanji_lbl = tk.Label(
            card_container,
            text=card_data.get("kanji"),
            fg=ACCENT_CYAN,
            bg=BG_CARD,
            font=(FONT_FAMILY, 72, "bold"),
            cursor="hand2"
        )
        kanji_lbl.pack(pady=10)
        HoverTooltip(kanji_lbl, lambda: card_data.get("kanji_romaji", ""))
        
        # Windowless speech triggers on sound
        btn_speak = tk.Button(
            card_container,
            text="🔊 PRONOUNCE KANJI",
            bg=BG_INNER,
            fg=ACCENT_CYAN,
            activebackground=HOVER_COLOR,
            bd=0,
            font=(FONT_FAMILY, 8, "bold"),
            padx=10,
            pady=4,
            cursor="hand2",
            command=lambda: guardian.speak_japanese_text(card_data.get("kanji_yomi", card_data.get("kanji")))
        )
        btn_speak.pack(pady=(0, 15))
        self.bind_button_hover(btn_speak, BG_INNER, HOVER_COLOR)
        
        # If card is hidden, show single click action button to slide details
        if not self.srs_show_details:
            btn_show = tk.Button(
                card_container,
                text="🔍  SHOW MEANING & READINGS",
                bg=ACCENT_CYAN,
                fg=FG_LIGHT,
                activebackground="#147ce5",
                bd=0,
                font=(FONT_FAMILY, 10, "bold"),
                padx=20,
                pady=10,
                cursor="hand2",
                command=self.show_srs_card_details
            )
            btn_show.pack(pady=20)
            self.bind_button_hover(btn_show, ACCENT_CYAN, "#147ce5")
        else:
            # Show all hidden card metrics
            info_frame = tk.Frame(card_container, bg=BG_INNER, padx=20, pady=15, highlightbackground=BORDER_COLOR, highlightthickness=1)
            info_frame.pack(fill="x", pady=10)
            
            lbl_m = tk.Label(
                info_frame,
                text=f"Meaning: {card_data.get('meaning')}".upper(),
                fg=FG_LIGHT,
                bg=BG_INNER,
                font=(FONT_FAMILY, 11, "bold")
            )
            lbl_m.pack(anchor="w")
            
            lbl_o = tk.Label(
                info_frame,
                text=f"Onyomi (音): {card_data.get('onyomi', '(none)')}      Kunyomi (訓): {card_data.get('kunyomi', '(none)')}",
                fg=FG_SECONDARY,
                bg=BG_INNER,
                font=(FONT_FAMILY, 9, "bold")
            )
            lbl_o.pack(anchor="w", pady=(4, 0))
            
            # Show example sentences
            ex_ja = card_data.get("example_ja")
            if ex_ja:
                lbl_e_ja = tk.Label(
                    info_frame,
                    text=f"例句: {ex_ja}",
                    fg=FG_LIGHT,
                    bg=BG_INNER,
                    font=(FONT_FAMILY, 9),
                    wraplength=600,
                    justify="left"
                )
                lbl_e_ja.pack(anchor="w", pady=(10, 2))
                HoverTooltip(lbl_e_ja, lambda: card_data.get("example_romaji", ""))
                
                lbl_e_en = tk.Label(
                    info_frame,
                    text=card_data.get("example_en"),
                    fg=FG_SECONDARY,
                    bg=BG_INNER,
                    font=(FONT_FAMILY, 8, "italic"),
                    wraplength=600,
                    justify="left"
                )
                lbl_e_en.pack(anchor="w")
                
            # Evaluation control buttons (Correct / Incorrect)
            eval_frame = tk.Frame(card_container, bg=BG_CARD)
            eval_frame.pack(fill="x", side="bottom", pady=(10, 0))
            
            btn_correct = tk.Button(
                eval_frame,
                text="✓  I KNEW IT (CORRECT)",
                bg=ACCENT_GREEN,
                fg=FG_LIGHT,
                activebackground="#2aa848",
                bd=0,
                font=(FONT_FAMILY, 9, "bold"),
                padx=15,
                pady=10,
                cursor="hand2",
                command=lambda: self.submit_srs_evaluation(True)
            )
            btn_correct.pack(side="left", fill="x", expand=True, padx=(0, 4))
            self.bind_button_hover(btn_correct, ACCENT_GREEN, "#2aa848")
            
            btn_wrong = tk.Button(
                eval_frame,
                text="✕  WRONG / MISTAKE",
                bg=ACCENT_RED,
                fg=FG_LIGHT,
                activebackground="#e0372d",
                bd=0,
                font=(FONT_FAMILY, 9, "bold"),
                padx=15,
                pady=10,
                cursor="hand2",
                command=lambda: self.submit_srs_evaluation(False)
            )
            btn_wrong.pack(side="right", fill="x", expand=True, padx=(4, 0))
            self.bind_button_hover(btn_wrong, ACCENT_RED, "#e0372d")

    def show_srs_card_details(self):
        """Displays hidden details inside reviews card."""
        self.srs_show_details = True
        self.render_srs_flashcard_state()

    def submit_srs_evaluation(self, is_correct):
        """Applies history, updates SRS levels, schedules next review date, and triggers audio response."""
        card_data = self.srs_queue[self.srs_current_idx]
        kanji_key = card_data["kanji"]
        
        # Save stats and history updates
        stats = self.kanji_db.setdefault("stats", {"total_reviewed": 0, "total_correct": 0})
        stats["total_reviewed"] += 1
        if is_correct:
            stats["total_correct"] += 1
            
        vocab = self.kanji_db.get("vocab", {})
        if kanji_key in vocab:
            vocab[kanji_key].setdefault("history", []).append({
                "date": datetime.now().isoformat(),
                "correct": is_correct
            })
            
            # Recalculate SRS Stage Levels
            current_stage = vocab[kanji_key].get("srs_stage", 1)
            if is_correct:
                next_stage = min(5, current_stage + 1)
                vocab[kanji_key]["srs_stage"] = next_stage
                # Next review delays based on stage
                days_delay = [1, 2, 4, 7, 14, 30][next_stage]
                vocab[kanji_key]["next_review"] = (datetime.now() + timedelta(days=days_delay)).isoformat()
            else:
                vocab[kanji_key]["srs_stage"] = 1 # Reset SRS to level 1 on mistake
                vocab[kanji_key]["next_review"] = (datetime.now() + timedelta(days=1)).isoformat()
                
        guardian.save_kanji_data(self.kanji_db)
        
        # Play speech feedback sound
        if is_correct:
            guardian.speak_japanese_text("せいかい！ 正解")
        else:
            guardian.speak_japanese_text("まちがい！ 間違い")
            
        # Move forward in reviews queue
        self.srs_current_idx += 1
        self.srs_show_details = False
        
        # Redraw
        self.update_sidebar_stats()
        self.render_srs_flashcard_state()

    # ==================== HOVER MOUSE HELPMATES ====================
    def bind_button_hover(self, button, bg_normal, bg_hover):
        def enter(e):
            if button.cget("state") != "disabled":
                button.config(bg=bg_hover)
        def leave(e):
            if button.cget("state") != "disabled":
                button.config(bg=bg_normal)
        button.bind("<Enter>", enter)
        button.bind("<Leave>", leave)

    def bind_hover_highlight(self, widget, bg_normal, bg_hover):
        def enter(e):
            widget.config(bg=bg_hover)
            for child in widget.winfo_children():
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


# ==================== SCRIPT ENTRYPOINT ====================
if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = JapaneseLearningApp(root)
        root.mainloop()
    except Exception as e:
        print(f"Japanese Learning standalone crash: {e}")
