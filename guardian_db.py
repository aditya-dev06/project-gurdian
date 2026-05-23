import sqlite3
import os
import json
import time
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "guardian_db.sqlite")

def check_and_heal_system():
    """Performs an automatic startup audit to detect crashes, repair config files, and self-heal SQLite databases/schemas."""
    config_path = os.path.join(BASE_DIR, "config.json")
    default_config = {
        "github_username": "aditya-dev06",
        "ntfy_topic": "aditya_guardian",
        "tracked_tasks": ["dsa", "dev-project", "language-study"],
        "audit_time": "23:45",
        "start_date": "",
        "end_date": "",
        "gemini_api_key": "YOUR_GEMINI_API_KEY",
        "japan_mnc_prep_active": True,
        "startup_enabled": True,
        "running": False
    }

    # 1. Self-Heal Configuration File
    config = {}
    config_ok = False
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            config_ok = True
        except Exception:
            pass

    if not config_ok or not isinstance(config, dict):
        config = default_config
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)
            print("Self-Healed: Corrupted config.json has been restored to default template.")
        except Exception:
            pass
    else:
        # Merge missing default keys
        merged = False
        for k, v in default_config.items():
            if k not in config:
                config[k] = v
                merged = True
        if merged:
            try:
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=4)
                print("Self-Healed: Merged missing parameters into config.json.")
            except Exception:
                pass

    # Detect previous crash state
    if config.get("running", False):
        print("Crash Detection: Detected that the application did not exit cleanly on the last session. Initiating correction...")
        try:
            crash_log_path = os.path.join(BASE_DIR, "gui_crash_log.txt")
            with open(crash_log_path, "a", encoding="utf-8") as f:
                f.write(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Crash Correction System: Detected abnormal exit. Performed self-healing audit.\n")
        except Exception:
            pass
    
    # Mark running flag as True for current active run
    config["running"] = True
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
    except Exception:
        pass

    # 2. Self-Heal Database File (Corruptions, Locks, and Schema Mismatches)
    db_ok = False
    has_prev_crash = config.get("running", False)
    conn = None
    
    if os.path.exists(DB_FILE):
        try:
            # Connect with a single unified connection to prevent lock contention
            conn = sqlite3.connect(DB_FILE, timeout=10.0)
            cursor = conn.cursor()
            
            # If a crash was detected, perform a rapid quick_check. Otherwise, run a microsecond connectivity test.
            if has_prev_crash:
                cursor.execute("PRAGMA quick_check;")
                res = cursor.fetchone()
                if res and res[0] == "ok":
                    db_ok = True
            else:
                cursor.execute("SELECT name FROM sqlite_master LIMIT 1;")
                db_ok = True
        except Exception as e:
            print(f"Database integrity/connection check failed: {e}. Initiating recovery...")
            db_ok = False
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
                conn = None

    if not db_ok:
        if os.path.exists(DB_FILE):
            # Backup corrupted DB before deleting
            corrupt_backup = DB_FILE + f".corrupt_{int(time.time())}"
            try:
                os.rename(DB_FILE, corrupt_backup)
                print(f"Backup corrupted database to: {corrupt_backup}")
            except Exception:
                try:
                    os.remove(DB_FILE)
                except Exception:
                    pass
        
        # fresh initialization
        print("Recreating database file and rebuilding core schemas...")
        try:
            conn = sqlite3.connect(DB_FILE, timeout=10.0)
            db_ok = True
        except Exception as e:
            print(f"Failed to create new database file: {e}")

    # 3. Schema Alterations (Proactive recovery of missing columns)
    if db_ok and conn:
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(studied_kanji);")
            columns = [c[1] for c in cursor.fetchall()]
            
            # Rich N4/N5 support columns added in recent iterations
            rich_cols = {
                "kanji_yomi": "TEXT",
                "kanji_romaji": "TEXT",
                "example_yomi": "TEXT",
                "example_romaji": "TEXT",
                "level": "TEXT",
                "srs_stage": "INTEGER DEFAULT 1",
                "next_review": "TEXT",
                "repetition_count": "INTEGER DEFAULT 0",
                "easiness_factor": "REAL DEFAULT 2.5",
                "interval_days": "INTEGER DEFAULT 0"
            }
            
            modified = False
            for col, col_type in rich_cols.items():
                if col not in columns:
                    print(f"Schema Correction: Adding missing column '{col}' to studied_kanji table...")
                    cursor.execute(f"ALTER TABLE studied_kanji ADD COLUMN {col} {col_type};")
                    modified = True
                    
            # Check if chat_messages has pronunciation scoring columns
            cursor.execute("PRAGMA table_info(chat_messages);")
            msg_columns = [c[1] for c in cursor.fetchall()]
            chat_cols = {
                "transcription": "TEXT",
                "yomi": "TEXT",
                "romaji": "TEXT",
                "en": "TEXT",
                "corrections": "TEXT",
                "pronunciation_score": "INTEGER",
                "pitch_accent_score": "INTEGER",
                "accent_feedback": "TEXT",
                "ai_explain": "TEXT"
            }
            for col, col_type in chat_cols.items():
                if col not in msg_columns:
                    print(f"Schema Correction: Adding missing column '{col}' to chat_messages table...")
                    cursor.execute(f"ALTER TABLE chat_messages ADD COLUMN {col} {col_type};")
                    modified = True
            
            if modified:
                conn.commit()
        except Exception as e:
            print(f"Schema correction failed: {e}")
        finally:
            try:
                conn.close()
            except Exception:
                pass

# Run the Crash Detection, Correction, and Self-Healing audit immediately on module load
check_and_heal_system()

def get_db_connection():
    """Returns a SQLite connection with dict-like row factory and concurrency enhancements."""
    conn = sqlite3.connect(DB_FILE, timeout=30.0)
    conn.row_factory = sqlite3.Row
    # Enable foreign keys and Write-Ahead Logging (WAL) for concurrent read/write stability
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        conn.execute("PRAGMA journal_mode = WAL;")
    except sqlite3.OperationalError:
        pass
    return conn

def init_db():
    """Creates the SQLite database and tables if they do not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Habits Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS habits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        active INTEGER DEFAULT 1,
        created_at TEXT NOT NULL
    );
    """)
    
    # 2. Habit Logs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS habit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        habit_id INTEGER NOT NULL,
        log_date TEXT NOT NULL,
        completed INTEGER NOT NULL CHECK (completed IN (0, 1)),
        FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE,
        UNIQUE(habit_id, log_date)
    );
    """)
    
    # 3. Studied Kanji Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS studied_kanji (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kanji TEXT UNIQUE NOT NULL,
        meaning TEXT,
        onyomi TEXT,
        kunyomi TEXT,
        stroke_count INTEGER,
        example_ja TEXT,
        example_en TEXT,
        kanji_yomi TEXT,
        kanji_romaji TEXT,
        example_yomi TEXT,
        example_romaji TEXT,
        level TEXT, -- N5, N4, N3, N2, N1
        srs_stage INTEGER DEFAULT 1,
        repetition_count INTEGER DEFAULT 0,
        easiness_factor REAL DEFAULT 2.5,
        interval_days INTEGER DEFAULT 0,
        next_review TEXT,
        added_at TEXT NOT NULL
    );
    """)
    
    # 4. Kanji Review History Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS kanji_review_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kanji_id INTEGER NOT NULL,
        review_date TEXT NOT NULL,
        correct INTEGER NOT NULL CHECK (correct IN (0, 1)),
        FOREIGN KEY (kanji_id) REFERENCES studied_kanji(id) ON DELETE CASCADE
    );
    """)
    
    # 5. Kanji Tests Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS kanji_tests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        test_date TEXT NOT NULL,
        score TEXT NOT NULL,
        percentage REAL NOT NULL
    );
    """)
    
    # 6. Weekend Prep Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS weekend_prep (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT UNIQUE NOT NULL,
        task_title TEXT NOT NULL,
        source TEXT,
        notes TEXT,
        completed INTEGER NOT NULL CHECK (completed IN (0, 1)),
        tech_upscaling TEXT,
        personality_upscaling TEXT,
        youtube_suggestions TEXT, -- JSON String
        intel_data TEXT -- JSON String containing all new intelligence fields
    );
    """)
    
    # 7. Grammar Progress Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS grammar_progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lesson_index INTEGER UNIQUE NOT NULL,
        completed_at TEXT NOT NULL
    );
    """)
    
    # 8. Chat Messages Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scenario TEXT NOT NULL,
        sender TEXT NOT NULL CHECK (sender IN ('user', 'ai')),
        text TEXT NOT NULL,
        transcription TEXT,
        yomi TEXT,
        romaji TEXT,
        en TEXT,
        corrections TEXT,
        pronunciation_score INTEGER,
        pitch_accent_score INTEGER,
        accent_feedback TEXT,
        ai_explain TEXT,
        timestamp TEXT NOT NULL
    );
    """)

    # 9. Todo Tasks Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS todo_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_text TEXT NOT NULL,
        completed INTEGER DEFAULT 0 CHECK (completed IN (0, 1)),
        created_date TEXT NOT NULL,
        completed_at TEXT
    );
    """)

    # Migration: Add intel_data column to weekend_prep if missing
    try:
        cursor.execute("SELECT intel_data FROM weekend_prep LIMIT 1")
    except sqlite3.OperationalError:
        try:
            cursor.execute("ALTER TABLE weekend_prep ADD COLUMN intel_data TEXT")
            print("Successfully migrated weekend_prep table to include intel_data.")
        except Exception as ex:
            print(f"Failed to migrate weekend_prep table: {ex}")
            
    conn.commit()
    conn.close()
    
    # Run migrations if legacy JSONs exist
    migrate_legacy_data()

def migrate_legacy_data():
    """Migrates historical data from old JSON files if present."""
    # 1. Migrate Habits and Weekend Prep (from guardian_data.json)
    legacy_guardian_json = os.path.join(BASE_DIR, "guardian_data.json")
    if os.path.exists(legacy_guardian_json):
        print("Migrating legacy guardian_data.json to SQLite database...")
        try:
            with open(legacy_guardian_json, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Identify all habit names mentioned
            habit_names = set()
            for date_str, habits_dict in data.items():
                if date_str != "weekend_history":
                    for h_name in habits_dict.keys():
                        habit_names.add(h_name)
            
            # Default fallback if empty
            if not habit_names:
                habit_names = {"dsa", "dev-project", "language-study", "github-commit"}
                
            # Insert habits
            for h_name in habit_names:
                cursor.execute("""
                INSERT OR IGNORE INTO habits (name, active, created_at)
                VALUES (?, 1, ?)
                """, (h_name, datetime.now().strftime("%Y-%m-%d")))
                
            # Insert habit logs
            for date_str, habits_dict in data.items():
                if date_str != "weekend_history":
                    for h_name, completed in habits_dict.items():
                        # Get habit ID
                        cursor.execute("SELECT id FROM habits WHERE name = ?", (h_name,))
                        row = cursor.fetchone()
                        if row:
                            h_id = row['id']
                            cursor.execute("""
                            INSERT OR IGNORE INTO habit_logs (habit_id, log_date, completed)
                            VALUES (?, ?, ?)
                            """, (h_id, date_str, 1 if completed else 0))
            
            # Insert weekend prep tasks
            weekend_tasks = data.get("weekend_history", [])
            for task in weekend_tasks:
                date_str = task.get("date", datetime.now().strftime("%Y-%m-%d"))
                yt_suggestions = json.dumps(task.get("youtube_suggestions", []))
                cursor.execute("""
                INSERT OR IGNORE INTO weekend_prep 
                (date, task_title, source, notes, completed, tech_upscaling, personality_upscaling, youtube_suggestions)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    date_str,
                    task.get("task_title", ""),
                    task.get("source", "Gemini AI"),
                    task.get("notes", ""),
                    1 if task.get("completed", False) else 0,
                    task.get("tech_upscaling", ""),
                    task.get("personality_upscaling", ""),
                    yt_suggestions
                ))
                
            conn.commit()
            conn.close()
            
            # Backup the legacy file to prevent double-migration
            os.replace(legacy_guardian_json, legacy_guardian_json + ".bak")
            print("Successfully migrated guardian_data.json to SQLite database!")
            
        except Exception as e:
            print(f"Error migrating guardian_data.json: {e}")
            
    # 2. Migrate Studied Kanji and Reviews (from kanji_data.json)
    legacy_kanji_json = os.path.join(BASE_DIR, "kanji_data.json")
    if os.path.exists(legacy_kanji_json):
        print("Migrating legacy kanji_data.json to SQLite database...")
        try:
            with open(legacy_kanji_json, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Insert Kanji
            vocab = data.get("vocab", {})
            for kanji_char, k_data in vocab.items():
                added_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                next_review = k_data.get("next_review")
                if next_review:
                    # Clean upISO format standard
                    try:
                        # Convert ISO format strings safely
                        dt = datetime.fromisoformat(next_review.replace("Z", ""))
                        next_review = dt.strftime("%Y-%m-%d %H:%M:%S")
                    except Exception:
                        pass
                
                cursor.execute("""
                INSERT OR IGNORE INTO studied_kanji 
                (kanji, meaning, onyomi, kunyomi, stroke_count, example_ja, example_en, 
                 kanji_yomi, kanji_romaji, example_yomi, example_romaji, level, srs_stage, next_review, added_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    kanji_char,
                    k_data.get("meaning", ""),
                    k_data.get("onyomi", ""),
                    k_data.get("kunyomi", ""),
                    k_data.get("stroke_count", 0),
                    k_data.get("example_ja", ""),
                    k_data.get("example_en", ""),
                    k_data.get("kanji_yomi", ""),
                    k_data.get("kanji_romaji", ""),
                    k_data.get("example_yomi", ""),
                    k_data.get("example_romaji", ""),
                    k_data.get("level", "N5"),
                    k_data.get("srs_stage", 1),
                    next_review,
                    added_at
                ))
                
                # Get Kanji ID to insert review history
                cursor.execute("SELECT id FROM studied_kanji WHERE kanji = ?", (kanji_char,))
                row = cursor.fetchone()
                if row:
                    k_id = row['id']
                    history = k_data.get("history", [])
                    for rev in history:
                        rev_date = rev.get("date", added_at)
                        try:
                            dt = datetime.fromisoformat(rev_date.replace("Z", ""))
                            rev_date = dt.strftime("%Y-%m-%d %H:%M:%S")
                        except Exception:
                            pass
                        cursor.execute("""
                        INSERT INTO kanji_review_history (kanji_id, review_date, correct)
                        VALUES (?, ?, ?)
                        """, (k_id, rev_date, 1 if rev.get("correct", True) else 0))
            
            # Insert Test History
            test_hist = data.get("test_history", [])
            for test in test_hist:
                test_date = test.get("date", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                try:
                    dt = datetime.fromisoformat(test_date.replace("Z", ""))
                    test_date = dt.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    pass
                cursor.execute("""
                INSERT INTO kanji_tests (test_date, score, percentage)
                VALUES (?, ?, ?)
                """, (test_date, test.get("score", "0/0"), test.get("percentage", 0.0)))
                
            # Insert Grammar Progress
            grammar_progress = data.get("grammar_progress", [])
            # In old data, lessons might be a dictionary or list
            if isinstance(grammar_progress, list):
                for l_idx in grammar_progress:
                    cursor.execute("""
                    INSERT OR IGNORE INTO grammar_progress (lesson_index, completed_at)
                    VALUES (?, ?)
                    """, (l_idx, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            elif isinstance(grammar_progress, dict):
                for l_idx, comp in grammar_progress.items():
                    if comp:
                        cursor.execute("""
                        INSERT OR IGNORE INTO grammar_progress (lesson_index, completed_at)
                        VALUES (?, ?)
                        """, (int(l_idx), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        
            conn.commit()
            conn.close()
            
            # Backup legacy file
            os.replace(legacy_kanji_json, legacy_kanji_json + ".bak")
            print("Successfully migrated kanji_data.json to SQLite database!")
            
        except Exception as e:
            print(f"Error migrating kanji_data.json: {e}")

# Helper Functions for Habit tracking
def log_habit(date_str, habit_name, completed):
    """Logs the status of a specific habit for a given date."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Ensure habit exists
        cursor.execute("INSERT OR IGNORE INTO habits (name, created_at) VALUES (?, ?)", 
                       (habit_name, datetime.now().strftime("%Y-%m-%d")))
        
        # Get habit ID
        cursor.execute("SELECT id FROM habits WHERE name = ?", (habit_name,))
        row = cursor.fetchone()
        if row:
            h_id = row['id']
            cursor.execute("""
            INSERT INTO habit_logs (habit_id, log_date, completed)
            VALUES (?, ?, ?)
            ON CONFLICT(habit_id, log_date) DO UPDATE SET completed = excluded.completed
            """, (h_id, date_str, 1 if completed else 0))
            conn.commit()
    except Exception as e:
        print(f"Error logging habit: {e}")
    finally:
        conn.close()

def get_habits_for_date(date_str):
    """Returns a dictionary of all habits and their completed status for a date."""
    conn = get_db_connection()
    cursor = conn.cursor()
    habits = {}
    try:
        # Fetch active habits
        cursor.execute("SELECT id, name FROM habits WHERE active = 1")
        all_active = cursor.fetchall()
        
        for h in all_active:
            h_id = h['id']
            h_name = h['name']
            cursor.execute("SELECT completed FROM habit_logs WHERE habit_id = ? AND log_date = ?", (h_id, date_str))
            log = cursor.fetchone()
            habits[h_name] = bool(log['completed']) if log else False
    except Exception as e:
        print(f"Error reading habits for date: {e}")
    finally:
        conn.close()
    return habits

def get_all_habit_names():
    """Returns a list of all active habit names."""
    conn = get_db_connection()
    cursor = conn.cursor()
    names = []
    try:
        cursor.execute("SELECT name FROM habits WHERE active = 1")
        names = [row['name'] for row in cursor.fetchall()]
    except Exception as e:
        print(f"Error fetching habit names: {e}")
    finally:
        conn.close()
    return names

def add_custom_habit(habit_name):
    """Adds a custom daily habit, setting it to active in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Check if habit already exists
        cursor.execute("SELECT id FROM habits WHERE name = ?", (habit_name,))
        row = cursor.fetchone()
        if row:
            # Set active = 1
            cursor.execute("UPDATE habits SET active = 1 WHERE id = ?", (row['id'],))
        else:
            # Insert new active habit
            cursor.execute("INSERT INTO habits (name, active, created_at) VALUES (?, 1, ?)",
                           (habit_name, datetime.now().strftime("%Y-%m-%d")))
        conn.commit()
    except Exception as e:
        print(f"Error adding custom habit: {e}")
    finally:
        conn.close()

def remove_custom_habit(habit_name):
    """Deletes/deactivates a custom daily habit in the database (keeps historical logs)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE habits SET active = 0 WHERE name = ?", (habit_name,))
        conn.commit()
    except Exception as e:
        print(f"Error removing custom habit: {e}")
    finally:
        conn.close()


def get_habit_history(days=30):
    """Returns a dictionary mapping date strings to habit states over the past N days."""
    conn = get_db_connection()
    cursor = conn.cursor()
    history = {}
    try:
        cursor.execute("SELECT name FROM habits WHERE active = 1")
        habit_names = [r['name'] for r in cursor.fetchall()]
        
        # Calculate dates
        today = datetime.now()
        for i in range(days):
            d = today - timedelta(days=i)
            d_str = d.strftime("%Y-%m-%d")
            history[d_str] = {}
            # Pre-populate false
            for h in habit_names:
                history[d_str][h] = False
                
        # Fill in logged entries
        cursor.execute("""
        SELECT h.name, hl.log_date, hl.completed
        FROM habit_logs hl
        JOIN habits h ON hl.habit_id = h.id
        WHERE hl.log_date >= ? AND h.active = 1
        """, ((today - timedelta(days=days)).strftime("%Y-%m-%d"),))
        
        logs = cursor.fetchall()
        for log in logs:
            d_str = log['log_date']
            h_name = log['name']
            if d_str in history:
                history[d_str][h_name] = bool(log['completed'])
    except Exception as e:
        print(f"Error fetching habit history: {e}")
    finally:
        conn.close()
    return history

# Helper Functions for Japanese Academy (studied_kanji)
def get_studied_kanji(level=None):
    """Returns a dict mapping kanji characters to their studied details."""
    conn = get_db_connection()
    cursor = conn.cursor()
    vocab = {}
    try:
        if level:
            cursor.execute("SELECT * FROM studied_kanji WHERE level = ?", (level,))
        else:
            cursor.execute("SELECT * FROM studied_kanji")
        rows = cursor.fetchall()
        for r in rows:
            kanji_char = r['kanji']
            # Fetch review history
            cursor.execute("SELECT review_date, correct FROM kanji_review_history WHERE kanji_id = ?", (r['id'],))
            revs = cursor.fetchall()
            history = [{"date": rev['review_date'], "correct": bool(rev['correct'])} for rev in revs]
            
            vocab[kanji_char] = {
                "kanji": r['kanji'],
                "meaning": r['meaning'],
                "onyomi": r['onyomi'],
                "kunyomi": r['kunyomi'],
                "stroke_count": r['stroke_count'],
                "example_ja": r['example_ja'],
                "example_en": r['example_en'],
                "kanji_yomi": r['kanji_yomi'] or "",
                "kanji_romaji": r['kanji_romaji'] or "",
                "example_yomi": r['example_yomi'] or "",
                "example_romaji": r['example_romaji'] or "",
                "level": r['level'],
                "srs_stage": r['srs_stage'],
                "repetition_count": r['repetition_count'] if 'repetition_count' in r.keys() else 0,
                "easiness_factor": r['easiness_factor'] if 'easiness_factor' in r.keys() else 2.5,
                "interval_days": r['interval_days'] if 'interval_days' in r.keys() else 0,
                "next_review": r['next_review'],
                "history": history
            }
    except Exception as e:
        print(f"Error fetching studied kanji: {e}")
    finally:
        conn.close()
    return vocab

def save_studied_kanji(kanji, meaning, onyomi, kunyomi, stroke_count, example_ja, example_en, level, srs_stage=1, next_review=None, kanji_yomi="", kanji_romaji="", example_yomi="", example_romaji=""):
    """Adds or updates a Kanji's studied parameters."""
    conn = get_db_connection()
    cursor = conn.cursor()
    added_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not next_review:
        next_review = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute("""
        INSERT INTO studied_kanji 
        (kanji, meaning, onyomi, kunyomi, stroke_count, example_ja, example_en, 
         kanji_yomi, kanji_romaji, example_yomi, example_romaji, level, srs_stage, next_review, added_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(kanji) DO UPDATE SET
            meaning=excluded.meaning, onyomi=excluded.onyomi, kunyomi=excluded.kunyomi,
            stroke_count=excluded.stroke_count, example_ja=excluded.example_ja, example_en=excluded.example_en,
            kanji_yomi=excluded.kanji_yomi, kanji_romaji=excluded.kanji_romaji, 
            example_yomi=excluded.example_yomi, example_romaji=excluded.example_romaji,
            level=excluded.level, srs_stage=excluded.srs_stage, next_review=excluded.next_review
        """, (
            kanji, meaning, onyomi, kunyomi, stroke_count, example_ja, example_en,
            kanji_yomi, kanji_romaji, example_yomi, example_romaji, level, srs_stage, next_review, added_at
        ))
        conn.commit()
    except Exception as e:
        print(f"Error saving studied kanji {kanji}: {e}")
    finally:
        conn.close()

def log_kanji_review(kanji, correct, quality=4):
    """Records a new SRS review evaluation, dynamically calculating next interval using standard SM-2 logic."""
    vocab = get_studied_kanji()
    if kanji not in vocab:
        return
        
    card = vocab[kanji]
    
    # Connect and compute SM-2 values
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, repetition_count, easiness_factor, interval_days FROM studied_kanji WHERE kanji = ?", (kanji,))
        row = cursor.fetchone()
        if not row:
            return
            
        k_id = row['id']
        n = row['repetition_count'] or 0
        ef = row['easiness_factor'] or 2.5
        interval = row['interval_days'] or 0
        
        # Enforce quality bounds based on correct parameter
        if not correct and quality >= 3:
            quality = 1
        elif correct and quality < 3:
            quality = 4
            
        # 1. Update Easiness Factor (EF)
        ef_new = ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        if ef_new < 1.3:
            ef_new = 1.3
            
        # 2. Update Repetition Count (n) and Interval (I)
        if quality < 3:
            n_new = 0
            interval_new = 1
            next_stage = 1
        else:
            if n == 0:
                interval_new = 1
            elif n == 1:
                interval_new = 6
            else:
                interval_new = int(round(interval * ef_new))
            n_new = n + 1
            next_stage = min(5, n_new)
            
        next_time = datetime.now() + timedelta(days=interval_new)
        next_review_str = next_time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Update studied_kanji
        cursor.execute("""
        UPDATE studied_kanji
        SET srs_stage = ?, repetition_count = ?, easiness_factor = ?, interval_days = ?, next_review = ?
        WHERE id = ?
        """, (next_stage, n_new, ef_new, interval_new, next_review_str, k_id))
        
        # Log review history
        cursor.execute("""
        INSERT INTO kanji_review_history (kanji_id, review_date, correct)
        VALUES (?, ?, ?)
        """, (k_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 1 if correct else 0))
        
        conn.commit()
    except Exception as e:
        print(f"Error logging review for {kanji}: {e}")
    finally:
        conn.close()

def get_kanji_overall_stats():
    """Calculates overall correct/incorrect totals."""
    conn = get_db_connection()
    cursor = conn.cursor()
    stats = {"total_reviewed": 0, "total_correct": 0}
    try:
        cursor.execute("SELECT COUNT(*) as total FROM kanji_review_history")
        stats["total_reviewed"] = cursor.fetchone()["total"]
        
        cursor.execute("SELECT COUNT(*) as correct FROM kanji_review_history WHERE correct = 1")
        stats["total_correct"] = cursor.fetchone()["correct"]
    except Exception as e:
        print(f"Error reading overall kanji stats: {e}")
    finally:
        conn.close()
    return stats

# Helper Functions for Kanji Test Modal
def get_kanji_test_history():
    """Returns the list of all test history entries."""
    conn = get_db_connection()
    cursor = conn.cursor()
    history = []
    try:
        cursor.execute("SELECT * FROM kanji_tests ORDER BY test_date DESC")
        rows = cursor.fetchall()
        for r in rows:
            history.append({
                "date": r["test_date"],
                "score": r["score"],
                "percentage": r["percentage"]
            })
    except Exception as e:
        print(f"Error fetching test history: {e}")
    finally:
        conn.close()
    return history

def log_kanji_test(score_str, percentage):
    """Logs the results of a multiple-choice challenge modal."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO kanji_tests (test_date, score, percentage)
        VALUES (?, ?, ?)
        """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), score_str, percentage))
        conn.commit()
    except Exception as e:
        print(f"Error logging kanji test: {e}")
    finally:
        conn.close()

# Helper Functions for Grammar Curriculums
def get_completed_grammar_lessons():
    """Returns a set of lesson indices completed by the user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    completed = set()
    try:
        cursor.execute("SELECT lesson_index FROM grammar_progress")
        completed = {row["lesson_index"] for row in cursor.fetchall()}
    except Exception as e:
        print(f"Error fetching grammar progress: {e}")
    finally:
        conn.close()
    return completed

def log_grammar_lesson(lesson_index):
    """Marks a grammar lesson completed."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT OR IGNORE INTO grammar_progress (lesson_index, completed_at)
        VALUES (?, ?)
        """, (lesson_index, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
    except Exception as e:
        print(f"Error marking lesson {lesson_index} completed: {e}")
    finally:
        conn.close()

# Helper Functions for Weekend Prep Tasks
def get_weekend_prep_history():
    """Returns all weekend prep entries with intelligence fields."""
    conn = get_db_connection()
    cursor = conn.cursor()
    history = []
    try:
        # Check if intel_data column exists first to be safe
        has_intel_data = False
        try:
            cursor.execute("SELECT intel_data FROM weekend_prep LIMIT 1")
            has_intel_data = True
        except Exception:
            pass

        if has_intel_data:
            cursor.execute("SELECT date, task_title, source, notes, completed, tech_upscaling, personality_upscaling, youtube_suggestions, intel_data FROM weekend_prep ORDER BY date DESC")
        else:
            cursor.execute("SELECT date, task_title, source, notes, completed, tech_upscaling, personality_upscaling, youtube_suggestions FROM weekend_prep ORDER BY date DESC")
            
        rows = cursor.fetchall()
        for r in rows:
            entry = {
                "date": r["date"],
                "task_title": r["task_title"],
                "source": r["source"],
                "notes": r["notes"],
                "completed": bool(r["completed"]),
                "tech_upscaling": r["tech_upscaling"],
                "personality_upscaling": r["personality_upscaling"],
                "youtube_suggestions": json.loads(r["youtube_suggestions"] or "[]")
            }
            
            # Unpack intel_data JSON if available
            if has_intel_data and r["intel_data"]:
                try:
                    intel = json.loads(r["intel_data"])
                    entry["action_checklist"] = intel.get("action_checklist", [])
                    entry["career_radar"] = intel.get("career_radar", "")
                    entry["research_spotlight"] = intel.get("research_spotlight", {})
                    entry["learning_resources"] = intel.get("learning_resources", [])
                    entry["weekly_intel_summary"] = intel.get("weekly_intel_summary", "")
                    entry["trending_topics"] = intel.get("trending_topics", [])
                    entry["generated_at"] = intel.get("generated_at", "")
                except Exception as ex:
                    print(f"Error parsing intel_data JSON: {ex}")
            
            history.append(entry)
    except Exception as e:
        print(f"Error reading weekend history: {e}")
    finally:
        conn.close()
    return history

def save_weekend_prep_task(date_str, task_title, source, completed, notes, tech, personality, youtube_suggestions_list):
    """Saves or updates a weekend technical prep checklist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        yt_json = json.dumps(youtube_suggestions_list)
        cursor.execute("""
        INSERT INTO weekend_prep 
        (date, task_title, source, notes, completed, tech_upscaling, personality_upscaling, youtube_suggestions)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(date) DO UPDATE SET
            task_title=excluded.task_title, source=excluded.source, notes=excluded.notes,
            completed=excluded.completed, tech_upscaling=excluded.tech_upscaling,
            personality_upscaling=excluded.personality_upscaling, youtube_suggestions=excluded.youtube_suggestions
        """, (date_str, task_title, source, 1 if completed else 0, notes, tech, personality, yt_json))
        conn.commit()
    except Exception as e:
        print(f"Error saving weekend prep: {e}")
    finally:
        conn.close()

# Helper Functions for conversation Practice (chat_messages)
def save_chat_message(scenario, sender, text, transcription=None, yomi=None, romaji=None, en=None, corrections=None, pronunciation_score=None, pitch_accent_score=None, accent_feedback=None, ai_explain=None):
    """Appends an online/offline AI conversation message logs, with pronunciation scores."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO chat_messages
        (scenario, sender, text, transcription, yomi, romaji, en, corrections, 
         pronunciation_score, pitch_accent_score, accent_feedback, ai_explain, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            scenario, sender, text, transcription, yomi, romaji, en, corrections,
            pronunciation_score, pitch_accent_score, accent_feedback, ai_explain,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()
    except Exception as e:
        print(f"Error saving chat message: {e}")
    finally:
        conn.close()

def get_chat_history(scenario, limit=50):
    """Returns chat message list for a specific scenario."""
    conn = get_db_connection()
    cursor = conn.cursor()
    history = []
    try:
        cursor.execute("""
        SELECT * FROM chat_messages 
        WHERE scenario = ? 
        ORDER BY id ASC 
        LIMIT ?
        """, (scenario, limit))
        rows = cursor.fetchall()
        for r in rows:
            history.append({
                "sender": r["sender"],
                "text": r["text"],
                "transcription": r["transcription"],
                "yomi": r["yomi"] or "",
                "romaji": r["romaji"] or "",
                "en": r["en"] or "",
                "corrections": r["corrections"],
                "pronunciation_score": r["pronunciation_score"],
                "pitch_accent_score": r["pitch_accent_score"],
                "accent_feedback": r["accent_feedback"],
                "ai_explain": r["ai_explain"]
            })
    except Exception as e:
        print(f"Error reading chat history: {e}")
    finally:
        conn.close()
    return history

def clear_chat_history(scenario):
    """Clears chat history logs for a scenario."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM chat_messages WHERE scenario = ?", (scenario,))
        conn.commit()
    except Exception as e:
        print(f"Error clearing chat history: {e}")
    finally:
        conn.close()

def save_habits_batch(habits_dict, weekend_history_list=None):
    """Saves a batch of habit records and weekend prep tasks in a single database connection and transaction.
    habits_dict: dict mapping YYYY-MM-DD -> dict of {habit_name: completed}
    weekend_history_list: list of weekend prep task dicts
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 1. Save habits
        if habits_dict:
            # First, ensure all habits referenced in the dictionary exist in the habits table
            all_habit_names = set()
            for date_str, daily_habits in habits_dict.items():
                if date_str != "weekend_history" and isinstance(daily_habits, dict):
                    for h_name in daily_habits.keys():
                        all_habit_names.add(h_name)
            
            created_date = datetime.now().strftime("%Y-%m-%d")
            for h_name in all_habit_names:
                cursor.execute("INSERT OR IGNORE INTO habits (name, created_at) VALUES (?, ?)", (h_name, created_date))
            
            # Pre-cache all habit IDs to avoid selecting in the loop
            cursor.execute("SELECT id, name FROM habits")
            habit_id_map = {row["name"]: row["id"] for row in cursor.fetchall()}
            
            # Insert or update habit logs in a single transaction
            for date_str, daily_habits in habits_dict.items():
                if date_str != "weekend_history" and isinstance(daily_habits, dict):
                    for h_name, completed in daily_habits.items():
                        h_id = habit_id_map.get(h_name)
                        if h_id is not None:
                            cursor.execute("""
                            INSERT INTO habit_logs (habit_id, log_date, completed)
                            VALUES (?, ?, ?)
                            ON CONFLICT(habit_id, log_date) DO UPDATE SET completed = excluded.completed
                            """, (h_id, date_str, 1 if completed else 0))

        # 2. Save weekend prep tasks
        if weekend_history_list:
            for task in weekend_history_list:
                date_str = task.get("date") or datetime.now().strftime("%Y-%m-%d")
                yt_suggestions = task.get("youtube_suggestions") or []
                yt_json = json.dumps(yt_suggestions)
                
                # Bundle new intelligence fields into intel_data JSON
                intel_fields = {
                    "action_checklist": task.get("action_checklist", []),
                    "career_radar": task.get("career_radar", ""),
                    "research_spotlight": task.get("research_spotlight", {}),
                    "learning_resources": task.get("learning_resources", []),
                    "weekly_intel_summary": task.get("weekly_intel_summary", ""),
                    "trending_topics": task.get("trending_topics", []),
                    "generated_at": task.get("generated_at", "")
                }
                intel_json = json.dumps(intel_fields)
                
                cursor.execute("""
                INSERT INTO weekend_prep 
                (date, task_title, source, notes, completed, tech_upscaling, personality_upscaling, youtube_suggestions, intel_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(date) DO UPDATE SET
                    task_title=excluded.task_title, source=excluded.source, notes=excluded.notes,
                    completed=excluded.completed, tech_upscaling=excluded.tech_upscaling,
                    personality_upscaling=excluded.personality_upscaling, youtube_suggestions=excluded.youtube_suggestions,
                    intel_data=excluded.intel_data
                """, (
                    date_str,
                    task.get("task_title", ""),
                    task.get("source", "Gemini AI"),
                    task.get("notes", ""),
                    1 if task.get("completed", False) else 0,
                    task.get("tech_upscaling", ""),
                    task.get("personality_upscaling", ""),
                    yt_json,
                    intel_json
                ))

        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error in save_habits_batch: {e}")
    finally:
        conn.close()

def save_kanji_data_batch(vocab_dict, test_history_list, grammar_list):
    """Saves studied Kanji vocabulary, test history, and grammar progress in a single transaction."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 1. Save vocab (studied_kanji)
        for kanji_char, k_data in vocab_dict.items():
            added_at = k_data.get("added_at") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            next_review = k_data.get("next_review") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            cursor.execute("""
            INSERT INTO studied_kanji 
            (kanji, meaning, onyomi, kunyomi, stroke_count, example_ja, example_en, 
             kanji_yomi, kanji_romaji, example_yomi, example_romaji, level, srs_stage, next_review, added_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(kanji) DO UPDATE SET
                meaning=excluded.meaning, onyomi=excluded.onyomi, kunyomi=excluded.kunyomi,
                stroke_count=excluded.stroke_count, example_ja=excluded.example_ja, example_en=excluded.example_en,
                kanji_yomi=excluded.kanji_yomi, kanji_romaji=excluded.kanji_romaji, 
                example_yomi=excluded.example_yomi, example_romaji=excluded.example_romaji,
                level=excluded.level, srs_stage=excluded.srs_stage, next_review=excluded.next_review
            """, (
                kanji_char,
                k_data.get("meaning", ""),
                k_data.get("onyomi", ""),
                k_data.get("kunyomi", ""),
                k_data.get("stroke_count", 0),
                k_data.get("example_ja", ""),
                k_data.get("example_en", ""),
                k_data.get("kanji_yomi", ""),
                k_data.get("kanji_romaji", ""),
                k_data.get("example_yomi", ""),
                k_data.get("example_romaji", ""),
                k_data.get("level", "N5"),
                k_data.get("srs_stage", 1),
                next_review,
                added_at
            ))
            
        # 2. Save test history without duplicating existing test dates
        for test in test_history_list:
            test_date = test.get("date") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("SELECT 1 FROM kanji_tests WHERE test_date = ?", (test_date,))
            if not cursor.fetchone():
                cursor.execute("""
                INSERT INTO kanji_tests (test_date, score, percentage)
                VALUES (?, ?, ?)
                """, (test_date, test.get("score", "0/0"), test.get("percentage", 0.0)))
                
        # 3. Save grammar progress
        # First, delete all records not in the incoming active grammar list (allowing unchecking)
        if grammar_list:
            placeholders = ",".join("?" for _ in grammar_list)
            cursor.execute(f"DELETE FROM grammar_progress WHERE lesson_index NOT IN ({placeholders})", grammar_list)
        else:
            cursor.execute("DELETE FROM grammar_progress")
            
        # Then, insert active ones
        for l_idx in grammar_list:
            cursor.execute("""
            INSERT OR IGNORE INTO grammar_progress (lesson_index, completed_at)
            VALUES (?, ?)
            """, (l_idx, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error in save_kanji_data_batch: {e}")
    finally:
        conn.close()


def delete_weekend_prep_task(date_str):
    """Deletes a weekend prep task record for a specific date from the SQLite database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM weekend_prep WHERE date = ?", (date_str,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error in delete_weekend_prep_task: {e}")
    finally:
        conn.close()

# Helper Functions for Daily One-off To-Do Tasks
def add_todo_task(task_text, date_str):
    """Inserts a new daily one-off todo task into SQLite."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO todo_tasks (task_text, created_date, completed) VALUES (?, ?, 0)", (task_text, date_str))
        conn.commit()
    except Exception as e:
        print(f"Error adding todo task: {e}")
    finally:
        conn.close()

def get_todo_tasks(date_str):
    """Returns a list of dictionaries of all todo tasks for a given date."""
    conn = get_db_connection()
    cursor = conn.cursor()
    tasks = []
    try:
        cursor.execute("SELECT id, task_text, completed, created_date, completed_at FROM todo_tasks WHERE created_date = ?", (date_str,))
        rows = cursor.fetchall()
        for r in rows:
            tasks.append({
                "id": r["id"],
                "task_text": r["task_text"],
                "completed": bool(r["completed"]),
                "created_date": r["created_date"],
                "completed_at": r["completed_at"]
            })
    except Exception as e:
        print(f"Error fetching todo tasks: {e}")
    finally:
        conn.close()
    return tasks

def toggle_todo_task(task_id, completed):
    """Toggles the completed status of a specific todo task in SQLite."""
    conn = get_db_connection()
    cursor = conn.cursor()
    comp_val = 1 if completed else 0
    comp_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if completed else None
    try:
        cursor.execute("UPDATE todo_tasks SET completed = ?, completed_at = ? WHERE id = ?", (comp_val, comp_at, task_id))
        conn.commit()
    except Exception as e:
        print(f"Error toggling todo task: {e}")
    finally:
        conn.close()

def delete_todo_task(task_id):
    """Deletes a specific todo task from SQLite database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM todo_tasks WHERE id = ?", (task_id,))
        conn.commit()
    except Exception as e:
        print(f"Error deleting todo task: {e}")
    finally:
        conn.close()

# Auto-run table initialization on import
init_db()


