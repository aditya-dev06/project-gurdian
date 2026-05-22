import os
import sys
import json
import requests
from datetime import datetime, timedelta

# Ensure UTF-8 output encoding for standard streams to prevent Windows Console UnicodeEncodeErrors
if sys.stdout is not None and getattr(sys.stdout, 'encoding', None) != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ==================== DESIGN CONSTANTS (ANSI COLORS) ====================
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
WHITE = "\033[97m"
BOLD = "\033[1m"
UNDERLINE = "\033[4m"
RESET = "\033[0m"

# ==================== CONFIGURATION PATHS ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
DATA_FILE = os.path.join(BASE_DIR, "guardian_data.json")

DEFAULT_TASKS = ["dsa", "dev-project", "language-study"]

#Curated 52-week roadmap for Tokyo Japan Software Engineer MNC Prep
JAPAN_MNC_ROADMAP = [
    "Research Japanese MNC engineering cultures (e.g., Mercari vs Rakuten vs LINE vs PayPay vs Sony) and their tech stacks.",
    "Draft a Japanese format resume (Rirekisho 履歴書) layout and fill in basic personal/educational details.",
    "Translate your core software engineering skills and projects into professional Japanese terminology.",
    "Complete your initial Japanese format resume (Rirekisho) and get feedback or self-review for typical formatting errors.",
    "Understand the Shokumukeirekisho (職務経歴書 - Work Experience Portfolio) format and outline your past professional experience.",
    "Write a detailed Shokumukeirekisho entry for your primary developer project, focusing on technical impact.",
    "Practice a standard Japanese self-introduction (Jikoshoukai 自己紹介) tailored for software engineer roles.",
    "Refine and rehearse your 2-minute Jikoshoukai out loud, recording yourself to polish pronunciation and pacing.",
    "Review microservices architecture patterns commonly used in high-scale Japanese apps (e.g., Mercari, PayPay).",
    "Study database scaling and caching strategies (Redis, Memcached) for high-concurrency systems.",
    "Deep dive into Rakuten's technology ecosystem and their global engineering standards (e.g., English-first culture).",
    "Analyze LINE/Yahoo Japan's tech stack, engineering blog, and their open-source contributions.",
    "Study Mercari's engineering blog, focusing on their Go-based microservices and Kubernetes infrastructure.",
    "Analyze PayPay's technical platform, focusing on their massive transaction processing and backend scalability.",
    "Perform a system design mock for a localized high-traffic service (e.g., a digital payment or e-commerce platform).",
    "Review distributed systems concepts: event-driven architecture, message queues (Kafka, RabbitMQ) and consistency.",
    "Learn fundamental Japanese business manners (Manners/Etiquette) for tech interviews and business communications.",
    "Study Japanese business Keigo (敬語) basics: Sonkeigo (honorific), Kenjougo (humble), and Teineigo (polite).",
    "Practice writing professional Japanese business emails for application follow-ups or interview scheduling.",
    "Rehearse common polite phrases for entering and exiting an interview room (both virtual and in-person settings).",
    "Formulate answers to standard behavioral questions in Japanese, focusing on teamwork and problem-solving.",
    "Practice describing a technical challenge you resolved using the STAR method, translated into natural Japanese.",
    "Study Japanese workplace culture: concepts of Ho-Ren-So (Report, Contact, Consult) and Kaizen (Continuous Improvement).",
    "Draft a comprehensive Q&A document in Japanese addressing why you want to work in Japan (Shiboudouki 志望動機).",
    "Research the visa application process and requirements for highly skilled professional (HSP) visa in Japan.",
    "Conduct a mock technical pitch of your favorite personal project completely in Japanese.",
    "Study system design for a global content delivery network (CDN) and edge computing solutions.",
    "Review API design best practices, REST vs gRPC vs GraphQL, and how large-scale Japanese companies manage internal APIs.",
    "Practice dry-run coding exercises (LeetCode/Codility style) and practice explaining your thought process in simple Japanese.",
    "Study cloud infrastructure optimization (AWS/GCP cost savings and auto-scaling) for international tech hubs.",
    "Research Woven by Toyota (Woven Planet) and their smart city/automotive software initiatives.",
    "Research Sony's software divisions, Playstation network architecture, and their modern backend stacks.",
    "Deep dive into security practices for web applications (OWASP Top 10) and how Japanese financial apps handle compliance.",
    "Study containerization and orchestration using Kubernetes, Docker, and service meshes (Istio/Linkerd).",
    "Rehearse polite clarification questions in Japanese for when you don't fully understand an interviewer's question.",
    "Practice explaining complex computer science concepts (e.g., concurrency vs parallelism) using basic Japanese vocabulary.",
    "Design a highly available chat application (system design) and review how Japanese communication giants (like LINE) implement it.",
    "Analyze how Japanese e-commerce giants handle seasonal high-load events (e.g., Rakuten Super Sale, Black Friday).",
    "Rehearse a mock behavioral interview with a peer or AI, focusing on alignment with Japanese corporate values.",
    "Review front-end performance optimization techniques and modern framework trends in the Japanese tech market.",
    "Study DevOps principles: CI/CD pipelines, green-blue deployments, and monitoring/alerting (Prometheus, Grafana).",
    "Practice detailing your contributions to open-source software or community projects in natural business Japanese.",
    "Study SQL vs NoSQL trade-offs and design a scalable schema for a localized reservation/booking system.",
    "Understand the concept of \"Chokusetsu Oubo\" (direct application) vs utilizing specialized tech recruiters in Japan.",
    "Review load balancing algorithms, reverse proxies (Nginx, Envoy), and high-availability networking.",
    "Prepare a list of insightful questions to ask Japanese interviewers (Gyakushitsumon 逆質問) to show deep interest.",
    "Practice discussing modern agile methodologies, Scrum practices, and cross-functional team collaborations in Japanese.",
    "Review distributed caching patterns and study write-through vs write-behind caching strategies.",
    "Do a full mock system design interview for a distributed ride-sharing or food delivery app in Japan.",
    "Rehearse your complete interview package (Jikoshoukai, Shiboudouki, Shokumukeirekisho highlights) in a full dress rehearsal.",
    "Review final technical checklists: data structures, algorithms, and key system design trade-offs.",
    "Polish your professional presence, clean up your public GitHub, and finalize your target application pipelines for Tokyo MNCs!"
]

# ==================== HELPER UTILITIES ====================

def clear_screen():
    """Clears the terminal screen for a smooth console GUI experience."""
    os.system("cls" if os.name == "nt" else "clear")

def print_header(title):
    """Prints a beautiful styled CLI header."""
    print(f"\n{BOLD}{CYAN}=== {title} ==={RESET}\n")

# ==================== DATA & CONFIG MANAGEMENT ====================

def load_config():
    """Loads settings from config.json, creating a template if missing."""
    default_config = {
        "github_username": "YOUR_GITHUB_USERNAME",
        "ntfy_topic": "YOUR_UNIQUE_NTFY_TOPIC",
        "tracked_tasks": DEFAULT_TASKS,
        "audit_time": "23:45",
        "start_date": "",
        "end_date": "",
        "gemini_api_key": "",
        "japan_mnc_prep_active": True
    }
    if not os.path.exists(CONFIG_FILE):
        save_config(default_config)
        return default_config
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
        
        # Migration: Ensure all keys exist
        modified = False
        for k, v in default_config.items():
            if k not in config:
                config[k] = v
                modified = True
        
        if modified:
            save_config(config)
        return config
    except Exception:
        print(f"{RED}⚠️ Error loading config.json. Reverting to default settings.{RESET}")
        return default_config

def save_config(config):
    """Saves settings to config.json."""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"{RED}❌ Failed to write config.json: {e}{RESET}")

def load_data():
    """Loads the tracking data from the local JSON file."""
    if not os.path.exists(DATA_FILE):
        return {"weekend_history": []}
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            data = {}
        if "weekend_history" not in data:
            data["weekend_history"] = []
            save_data(data)
        return data
    except json.JSONDecodeError:
        return {"weekend_history": []}
    except Exception as e:
        print(f"{RED}❌ Failed to read data file: {e}{RESET}")
        return {"weekend_history": []}

def save_data(data):
    """Saves the tracking data to the local JSON file."""
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"{RED}❌ Failed to save data file: {e}{RESET}")

def initialize_today(data, date_str, tracked_tasks):
    """Ensures today's date exists in the database with all manual tasks set to false."""
    if date_str not in data:
        data[date_str] = {task: False for task in tracked_tasks}
        # github-commit will be initialized as false or calculated live
        data[date_str]["github-commit"] = False
    else:
        # If tasks list changed in config, synchronize today's keys
        day_data = data[date_str]
        for task in tracked_tasks:
            if task not in day_data:
                day_data[task] = False
        if "github-commit" not in day_data:
            day_data["github-commit"] = False
    return data

# ==================== CORE SERVICES ====================

def check_github_commit_today(username):
    """Queries the public GitHub API to verify if a commit was made today."""
    if not username or username == "YOUR_GITHUB_USERNAME":
        return False
    url = f"https://api.github.com/users/{username}/events/public"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            return False
        
        events = response.json()
        today_str = datetime.utcnow().strftime("%Y-%m-%d")
        
        for event in events:
            # Look for pushes or commits created today
            if event.get("type") == "PushEvent" and today_str in event.get("created_at", ""):
                return True
        return False
    except Exception:
        # Fallback to False to alert during nightly audit
        return False

def send_alert(topic, title, message, priority="high", tags="warning"):
    """Dispatches a real-time push notification alert via ntfy.sh."""
    if not topic or topic == "YOUR_UNIQUE_NTFY_TOPIC":
        print(f"{YELLOW}⚠️ Notification skipped: ntfy topic is not configured.{RESET}")
        return
        
    # Map priority text to numeric values for universal mobile app compatibility
    priority_map = {
        "max": "5",
        "urgent": "5",
        "high": "4",
        "default": "3",
        "normal": "3",
        "low": "2",
        "min": "1"
    }
    numeric_priority = priority_map.get(str(priority).lower(), str(priority))
    
    # Clean non-ASCII characters (like emojis) from the Title to prevent HTTP header UnicodeEncodeErrors.
    # ntfy will prepend emojis automatically on the phone based on the 'Tags' header!
    clean_title = title.encode('ascii', 'ignore').decode('ascii').strip()
    
    try:
        headers = {
            "Title": clean_title,
            "Priority": str(numeric_priority),
            "Tags": str(tags)
        }
        requests.post(
            f"https://ntfy.sh/{topic}",
            data=message.encode('utf-8'),
            headers=headers,
            timeout=5
        )
    except requests.RequestException as e:
        print(f"{RED}❌ Failed to send push notification: {e}{RESET}")

# ==================== TIMELINE & WEEKEND PREP SERVICES ====================

def is_within_timeline(reference_date=None):
    """Checks if the reference_date (default today) falls within the start_date and end_date timeline bounds configured in config.json."""
    config = load_config()
    start_date_str = config.get("start_date", "").strip()
    end_date_str = config.get("end_date", "").strip()
    
    if reference_date is None:
        reference_date = datetime.now().date()
    elif isinstance(reference_date, str):
        try:
            reference_date = datetime.strptime(reference_date, "%Y-%m-%d").date()
        except ValueError:
            return True
        
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            if reference_date < start_date:
                return False
        except ValueError:
            pass
            
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            if reference_date > end_date:
                return False
        except ValueError:
            pass
            
    return True

def get_current_weekend_saturday_date(reference_date=None):
    """If reference_date (default today) is Saturday or Sunday, returns the date of that Saturday as a string (YYYY-MM-DD). Otherwise returns None."""
    if reference_date is None:
        reference_date = datetime.now().date()
    elif isinstance(reference_date, str):
        try:
            reference_date = datetime.strptime(reference_date, "%Y-%m-%d").date()
        except ValueError:
            return None
            
    # monday = 0, ..., saturday = 5, sunday = 6
    weekday = reference_date.weekday()
    if weekday == 5: # Saturday
        return reference_date.strftime("%Y-%m-%d")
    elif weekday == 6: # Sunday
        saturday = reference_date - timedelta(days=1)
        return saturday.strftime("%Y-%m-%d")
    return None

def generate_gemini_task_via_api(api_key, history):
    """Calls Gemini API to generate a subsequent progressive Japan MNC tech prep task."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    # Build history context
    history_summary = ""
    if history:
        history_summary = "Here is the history of previous weekend prep tasks and notes the user completed:\n"
        for i, entry in enumerate(history):
            history_summary += f"- Weekend {i+1} Date: {entry.get('date')}, Task: {entry.get('task_title')}, Completed: {entry.get('completed')}, Notes: {entry.get('notes')}\n"
    else:
        history_summary = "This is the user's very first weekend preparation task."

    prompt = (
        "You are an expert career coach and senior staff engineer specializing in helping software developers land elite engineering roles "
        "at major Multi-National Corporations (MNCs) in Tokyo, Japan (such as Rakuten, Mercari, LINE, Yahoo Japan, PayPay, Sony, and Woven by Toyota).\n\n"
        "Your task is to generate a highly actionable, high-impact weekend study/preparation micro-task for the user. "
        "The micro-task should take between 1 to 2 hours to complete and should cover one of the following key areas in a progressive, structured manner:\n"
        "1. Drafting and polishing Japanese-format resumes (Rirekisho 履歴書) and detailed work history sheets (Shokumukeirekisho 職務経歴書).\n"
        "2. Practicing standard Japanese business manners, self-introductions (Jikoshoukai 自己紹介), behavioral answers, and Keigo (敬語) basics for interviews.\n"
        "3. Reviewing system design patterns, distributed caching, database scaling, microservices architectures, and technical stacks utilized by high-scale companies in Japan.\n"
        "4. Researching target Japanese tech company engineering cultures, tech blogs, open-source initiatives, and interview patterns.\n\n"
        f"{history_summary}\n"
        "Analyze the user's progress. Based on what they have done (or if they are just starting), generate the next logical, progressive, and highly effective task. "
        "IMPORTANT rules:\n"
        "- The task must be extremely concrete, specific, and actionable. Do not give generic advice.\n"
        "- Keep the task description short, punchy, and compelling (maximum 1-2 sentences).\n"
        "- Reply ONLY with the task description. Do not include any introductory remarks, markdown formatting (like bolding or backticks), or extra conversational text. Just output the task text itself."
    )
    
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=10)
    if response.status_code == 200:
        res_json = response.json()
        try:
            task_text = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
            task_text = task_text.replace("`", "").replace('"', '').strip()
            return task_text
        except (KeyError, IndexError) as e:
            raise Exception(f"Failed to parse Gemini response: {e}")
    else:
        raise Exception(f"Gemini API returned status code {response.status_code}: {response.text}")

def get_or_create_weekend_task(reference_date=None):
    """Gets the weekend task for the current weekend. If none exists, creates one and saves it."""
    sat_date_str = get_current_weekend_saturday_date(reference_date)
    if not sat_date_str:
        return None

    data = load_data()
    if "weekend_history" not in data:
        data["weekend_history"] = []

    # Check if we already have an entry for this Saturday
    for entry in data["weekend_history"]:
        if entry.get("date") == sat_date_str:
            return entry

    # Create a new task!
    config = load_config()
    api_key = config.get("gemini_api_key", "").strip()
    is_active = config.get("japan_mnc_prep_active", True)
    
    if not is_active:
        return None

    task_title = ""
    source = "Curated Roadmap"
    
    if api_key and api_key != "YOUR_GEMINI_API_KEY":
        try:
            task_title = generate_gemini_task_via_api(api_key, data["weekend_history"])
            source = "Gemini AI"
        except Exception as e:
            print(f"{YELLOW}⚠️ Gemini API generation failed ({e}). Falling back to Curated Roadmap.{RESET}")
    
    if not task_title:
        week_idx = len(data["weekend_history"]) % 52
        task_title = JAPAN_MNC_ROADMAP[week_idx]
        source = "Curated Roadmap"

    new_entry = {
        "date": sat_date_str,
        "task_title": task_title,
        "source": source,
        "notes": "",
        "completed": False
    }
    
    data["weekend_history"].append(new_entry)
    save_data(data)
    return new_entry

def show_weekend_status():
    """Displays the current weekend prep task, completed state, and notes."""
    sat_date_str = get_current_weekend_saturday_date()
    if not sat_date_str:
        print(f"{YELLOW}📅 Today is a weekday. Weekend Japan MNC Prep is only active on Saturdays and Sundays!{RESET}")
        return
        
    entry = get_or_create_weekend_task()
    if not entry:
        print(f"{YELLOW}⚠️ Weekend Japan MNC Prep is currently disabled or inactive.{RESET}")
        return
        
    print_header("🎌 WEEKEND JAPAN MNC PREP")
    status = f"{GREEN}🟢 COMPLETED{RESET}" if entry.get("completed") else f"{RED}🔴 PENDING{RESET}"
    print(f"📅 Weekend Date : {WHITE}{sat_date_str}{RESET}")
    print(f"🎯 Target Task  : {BOLD}{CYAN}{entry.get('task_title')}{RESET}")
    print(f"💡 Task Source  : {YELLOW}{entry.get('source')}{RESET}")
    print(f"📊 Status       : {status}")
    print(f"📝 Study Notes  : {WHITE}{entry.get('notes') if entry.get('notes') else '(No notes recorded yet)'}{RESET}")
    print("-" * 51)
    print("Commands:")
    print("  python guardian.py weekend-done          - Toggle task completion")
    print("  python guardian.py weekend-notes [text]  - Record your study/research notes")

def toggle_weekend_complete_cli():
    """Toggles completion of the current weekend task."""
    sat_date_str = get_current_weekend_saturday_date()
    if not sat_date_str:
        print(f"{RED}❌ Today is not a weekend day!{RESET}")
        return
        
    data = load_data()
    if "weekend_history" not in data:
        data["weekend_history"] = []
        
    found = False
    for entry in data["weekend_history"]:
        if entry.get("date") == sat_date_str:
            entry["completed"] = not entry.get("completed", False)
            found = True
            status = "completed" if entry["completed"] else "pending"
            print(f"✅ {GREEN}Weekend task marked as {status}!{RESET}")
            break
            
    if not found:
        entry = get_or_create_weekend_task()
        # Find and save
        data = load_data()
        for e in data["weekend_history"]:
            if e.get("date") == sat_date_str:
                e["completed"] = True
                print(f"✅ {GREEN}Weekend task marked as completed!{RESET}")
                break
                
    save_data(data)

def save_weekend_notes_cli(notes_text):
    """Saves study/research notes for the current weekend task."""
    sat_date_str = get_current_weekend_saturday_date()
    if not sat_date_str:
        print(f"{RED}❌ Today is not a weekend day!{RESET}")
        return
        
    if not notes_text:
        print(f"{RED}❌ Please provide non-empty notes text.{RESET}")
        return
        
    data = load_data()
    if "weekend_history" not in data:
        data["weekend_history"] = []
        
    found = False
    for entry in data["weekend_history"]:
        if entry.get("date") == sat_date_str:
            entry["notes"] = notes_text
            found = True
            print(f"✅ {GREEN}Study notes saved successfully for this weekend!{RESET}")
            break
            
    if not found:
        entry = get_or_create_weekend_task()
        # Find and save
        data = load_data()
        for e in data["weekend_history"]:
            if e.get("date") == sat_date_str:
                e["notes"] = notes_text
                print(f"✅ {GREEN}Study notes saved successfully for this weekend!{RESET}")
                break
                
    save_data(data)

def show_weekend_history_cli():
    """Displays the entire history of weekend prep tasks and notes logged."""
    data = load_data()
    history = data.get("weekend_history", [])
    
    if not history:
        print(f"{YELLOW}📅 No weekend history logs found. Get started this Saturday!{RESET}")
        return
        
    print_header("📚 JAPAN MNC PREP HISTORY LOG")
    for entry in reversed(history):
        status = f"{GREEN}✓{RESET}" if entry.get("completed") else f"{RED}✗{RESET}"
        print(f"📅 {BOLD}{entry.get('date')}{RESET} [{status}] ({entry.get('source')})")
        print(f"   🎯 {CYAN}{entry.get('task_title')}{RESET}")
        if entry.get("notes"):
            print(f"   📝 Notes: {WHITE}{entry.get('notes')}{RESET}")
        else:
            print(f"   📝 Notes: {YELLOW}(No notes logged){RESET}")
        print("-" * 51)

# ==================== ANALYTICS ENGINE ====================

def calculate_stats():
    """Calculates active streaks and compliance rates over historical records."""
    data = load_data()
    config = load_config()
    tracked_tasks = config.get("tracked_tasks", DEFAULT_TASKS)
    config_start_str = config.get("start_date", "").strip()
    config_end_str = config.get("end_date", "").strip()
    
    stats = {
        "current_streak": 0,
        "longest_streak": 0,
        "perfect_days_count": 0,
        "total_days_tracked": 0,
        "compliance_7d": 0.0,
        "compliance_30d": 0.0
    }
    
    if not data:
        return stats

    # Only consider YYYY-MM-DD keys from the database
    dates_str = []
    for k in data.keys():
        if k != "weekend_history":
            dates_str.append(k)
    dates_str = sorted(dates_str)
    
    if not dates_str:
        return stats

    parsed_dates = []
    for d_str in dates_str:
        try:
            parsed_dates.append(datetime.strptime(d_str, "%Y-%m-%d").date())
        except ValueError:
            continue

    if not parsed_dates:
        return stats

    db_start_date = min(parsed_dates)
    today = datetime.now().date()

    # Parse config start date if provided
    config_start = None
    if config_start_str:
        try:
            config_start = datetime.strptime(config_start_str, "%Y-%m-%d").date()
        except ValueError:
            pass
            
    # Parse config end date if provided
    config_end = None
    if config_end_str:
        try:
            config_end = datetime.strptime(config_end_str, "%Y-%m-%d").date()
        except ValueError:
            pass

    # The effective start date for stats is the config_start if specified,
    # otherwise the minimum parsed date in the database.
    effective_start = config_start if config_start else db_start_date
    
    # The effective end date for stats is the config_end if specified and it's in the past,
    # otherwise today.
    effective_end = today
    if config_end and config_end < today:
        effective_end = config_end

    # If the timeline window hasn't started yet, or we're fully outside, return empty stats safely
    if effective_start > effective_end:
        return stats

    # Reconstruct timeline within effective bounds
    all_days = []
    curr = effective_start
    while curr <= effective_end:
        all_days.append(curr)
        curr += timedelta(days=1)

    perfect_days = {}
    for day in all_days:
        day_str = day.strftime("%Y-%m-%d")
        if day_str not in data:
            perfect_days[day] = False
            continue

        day_data = data[day_str]
        # Check all manual tasks configured
        manual_ok = all(day_data.get(task, False) for task in tracked_tasks)
        # Check recorded github-commit
        github_ok = day_data.get("github-commit", False)

        perfect_days[day] = manual_ok and github_ok

    # Current streak calculation:
    # A streak is active if effective_end (e.g. today) is perfect, OR if effective_end is incomplete but yesterday was perfect.
    current_streak = 0
    check_day = effective_end

    if not perfect_days.get(effective_end, False):
        yesterday = effective_end - timedelta(days=1)
        if perfect_days.get(yesterday, False):
            check_day = yesterday

    while check_day in perfect_days and perfect_days[check_day]:
        current_streak += 1
        check_day -= timedelta(days=1)

    # Longest streak calculation
    longest_streak = 0
    temp_streak = 0
    curr = effective_start
    while curr <= effective_end:
        if perfect_days.get(curr, False):
            temp_streak += 1
            if temp_streak > longest_streak:
                longest_streak = temp_streak
        else:
            temp_streak = 0
        curr += timedelta(days=1)

    perfect_days_count = sum(1 for d, perf in perfect_days.items() if perf)
    total_days = len(perfect_days)

    # Calculate compliance for 7-day and 30-day windows
    def get_compliance(days_window):
        window_days = [effective_end - timedelta(days=i) for i in range(days_window)]
        perfect_count = 0
        valid_days = 0
        for d in window_days:
            if d >= effective_start:
                valid_days += 1
                if perfect_days.get(d, False):
                    perfect_count += 1
        return (perfect_count / valid_days * 100.0) if valid_days > 0 else 0.0

    stats["current_streak"] = current_streak
    stats["longest_streak"] = longest_streak
    stats["perfect_days_count"] = perfect_days_count
    stats["total_days_tracked"] = total_days
    stats["compliance_7d"] = get_compliance(7)
    stats["compliance_30d"] = get_compliance(30)

    return stats

# ==================== INTERACTIVE CLI MENU ====================

def run_setup_wizard():
    """Runs a polished console prompt interface to configure persistent settings."""
    clear_screen()
    print(f"{BOLD}{CYAN}============================================={RESET}")
    print(f"{BOLD}{CYAN}          GUARDIAN TRACKER SETUP             {RESET}")
    print(f"{BOLD}{CYAN}============================================={RESET}")
    print("Welcome! Let's configure your daily goals. Settings will be saved persistently.\n")

    config = load_config()

    # Get GitHub Username
    current_username = config.get("github_username", "")
    username_prompt = f"Enter GitHub Username [{current_username}]: " if current_username else "Enter GitHub Username: "
    username = input(username_prompt).strip()
    if not username and current_username:
        username = current_username
    elif not username:
        username = "YOUR_GITHUB_USERNAME"

    # Get ntfy.sh Topic
    current_topic = config.get("ntfy_topic", "")
    topic_prompt = f"Enter unique ntfy.sh Topic [{current_topic}]: " if current_topic else "Enter unique ntfy.sh Topic (e.g., aditya_guardian_alerts): "
    topic = input(topic_prompt).strip()
    if not topic and current_topic:
        topic = current_topic
    elif not topic:
        topic = "YOUR_UNIQUE_NTFY_TOPIC"

    # Configure tracked tasks
    current_tasks = ", ".join(config.get("tracked_tasks", DEFAULT_TASKS))
    print(f"\nCurrent tracked tasks: {YELLOW}{current_tasks}{RESET}")
    tasks_input = input("Enter custom tasks separated by commas (or press Enter to keep current): ").strip()
    if tasks_input:
        tracked_tasks = [t.strip().lower() for t in tasks_input.split(",") if t.strip()]
    else:
        tracked_tasks = config.get("tracked_tasks", DEFAULT_TASKS)

    # Configure Audit Time
    current_time = config.get("audit_time", "23:45")
    time_prompt = f"Enter daily audit time (HH:MM format) [{current_time}]: "
    audit_time = input(time_prompt).strip()
    if not audit_time:
        audit_time = current_time

    # Save
    config["github_username"] = username
    config["ntfy_topic"] = topic
    config["tracked_tasks"] = tracked_tasks
    config["audit_time"] = audit_time
    save_config(config)

    print(f"\n{GREEN}✅ Configuration saved successfully to config.json!{RESET}")
    input("\nPress [Enter] to continue...")

def interactive_dashboard():
    """Displays a premium interactive habit tracking terminal dashboard."""
    # Check if wizard should be forced (unconfigured values)
    config = load_config()
    if (config.get("github_username") == "YOUR_GITHUB_USERNAME" or 
        config.get("ntfy_topic") == "YOUR_UNIQUE_NTFY_TOPIC"):
        run_setup_wizard()
        config = load_config()

    github_live_status = None
    github_check_time = None

    while True:
        clear_screen()
        today = datetime.now().strftime("%Y-%m-%d")
        tracked_tasks = config.get("tracked_tasks", DEFAULT_TASKS)
        github_user = config.get("github_username", "")
        ntfy_topic = config.get("ntfy_topic", "")
        
        # Load records and initialize today
        data = load_data()
        data = initialize_today(data, today, tracked_tasks)
        save_data(data)
        
        # Query Github status live once or on manual refresh
        if github_live_status is None:
            github_live_status = check_github_commit_today(github_user)
            github_check_time = datetime.now().strftime("%I:%M %p")
            # Cache it immediately in today's dataset
            data[today]["github-commit"] = github_live_status
            save_data(data)

        # Calculate statistics
        stats = calculate_stats()

        # Render Header & Streak Board
        print(f"{BOLD}{CYAN}==================================================={RESET}")
        print(f"{BOLD}{CYAN}          🛡️  GUARDIAN DAILY GOAL BOARD             {RESET}")
        print(f"{BOLD}{CYAN}==================================================={RESET}")
        print(f"📅 Date: {BOLD}{WHITE}{today}{RESET}  |  🤖 GitHub: {BOLD}{WHITE}{github_user}{RESET}")
        print(f"🔔 Topic: {BOLD}{WHITE}{ntfy_topic}{RESET}")
        print("-" * 51)
        
        # Streak Cards
        streak_color = GREEN if stats["current_streak"] > 0 else RED
        print(f"🔥 Current Streak  : {streak_color}{stats['current_streak']} days{RESET}")
        print(f"🏆 Longest Streak  : {GREEN}{stats['longest_streak']} days{RESET}")
        print(f"📊 Compliance Rates: {YELLOW}7-Day: {stats['compliance_7d']:.1f}%{RESET} | {YELLOW}30-Day: {stats['compliance_30d']:.1f}%{RESET}")
        print("-" * 51)

        # Task Items List
        print(f"{BOLD}Daily Targets:{RESET}")
        idx = 1
        tasks_map = {}
        for task in tracked_tasks:
            completed = data[today].get(task, False)
            status_icon = f"{GREEN}🟢 DONE{RESET}" if completed else f"{RED}🔴 INCOMPLETE{RESET}"
            print(f"  [{idx}] {task.upper().ljust(18)} : {status_icon}")
            tasks_map[idx] = task
            idx += 1

        # Github Commit
        git_icon = f"{GREEN}🟢 DONE{RESET}" if github_live_status else f"{RED}🔴 INCOMPLETE{RESET}"
        print(f"  [G] {'GITHUB-COMMIT'.ljust(18)} : {git_icon} {CYAN}(Checked live at {github_check_time}){RESET}")
        print("-" * 51)

        # Operations Instructions
        print(f"{BOLD}Menu Actions:{RESET}")
        print("  [1-N] Toggle completions | [R] Refresh GitHub | [A] Test Nightly Audit")
        print("  [S]   Configure Settings | [H] View Stats Summary | [Q] Exit Dashboard")
        print("-" * 51)

        choice = input(f"{BOLD}{WHITE}Choose an action: {RESET}").strip().lower()

        if choice.isdigit():
            val = int(choice)
            if val in tasks_map:
                task_name = tasks_map[val]
                data[today][task_name] = not data[today].get(task_name, False)
                save_data(data)
                # Recalculate stats inside loop
            else:
                print(f"{RED}Invalid task selection index.{RESET}")
                os.system("timeout /t 1 >nul" if os.name == "nt" else "sleep 1")
        elif choice == "r":
            print(f"{CYAN}Refreshing GitHub commit status...{RESET}")
            github_live_status = check_github_commit_today(github_user)
            github_check_time = datetime.now().strftime("%I:%M %p")
            data[today]["github-commit"] = github_live_status
            save_data(data)
        elif choice == "a":
            print(f"{CYAN}Simulating nightly audit run...{RESET}")
            run_nightly_audit(force_test=True)
            input("\nPress [Enter] to return...")
        elif choice == "s":
            run_setup_wizard()
            config = load_config()
            github_live_status = None # Reset so it fetches fresh for the new user
        elif choice == "h":
            show_history_summary()
        elif choice == "q":
            print(f"\n{BOLD}{GREEN}Keep pushing! Stay accountable. Goodbye! 🛡️{RESET}\n")
            break
        else:
            print(f"{RED}Invalid selection.{RESET}")
            os.system("timeout /t 1 >nul" if os.name == "nt" else "sleep 1")

# ==================== CLI COMMAND ACTIONS ====================

def mark_task_complete(task_name):
    """Marks a specific manual task as completed for today (CLI direct access)."""
    config = load_config()
    tracked_tasks = config.get("tracked_tasks", DEFAULT_TASKS)
    
    data = load_data()
    today = datetime.now().strftime("%Y-%m-%d")
    data = initialize_today(data, today, tracked_tasks)
    
    clean_task = task_name.lower().strip()
    if clean_task in data[today]:
        if data[today][clean_task]:
            print(f"ℹ️ '{clean_task}' was already completed today!")
        else:
            data[today][clean_task] = True
            save_data(data)
            print(f"✅ {GREEN}Awesome job! '{clean_task}' marked as complete for today.{RESET}")
    else:
        print(f"❌ {RED}Error: '{clean_task}' is not a recognized task. Choose from: {tracked_tasks}{RESET}")

def show_status():
    """Prints a clean visual status board of all daily tasks + live GitHub status."""
    config = load_config()
    tracked_tasks = config.get("tracked_tasks", DEFAULT_TASKS)
    github_user = config.get("github_username", "")

    data = load_data()
    today = datetime.now().strftime("%Y-%m-%d")
    data = initialize_today(data, today, tracked_tasks)
    
    print_header(f"GOAL BOARD FOR {today}")
    for task in tracked_tasks:
        completed = data[today].get(task, False)
        status_icon = f"{GREEN}🟢 DONE{RESET}" if completed else f"{RED}🔴 INCOMPLETE{RESET}"
        print(f"{task.ljust(18)} : {status_icon}")
    
    # Run live GitHub check for transparency
    print(f"{'github-commit'.ljust(18)} : {CYAN}Checking live...{RESET}", end="\r")
    github_ok = check_github_commit_today(github_user)
    git_icon = f"{GREEN}🟢 DONE{RESET}" if github_ok else f"{RED}🔴 INCOMPLETE{RESET}"
    print(f"{'github-commit'.ljust(18)} : {git_icon} (Checked live)")
    
    # Save the status live
    data[today]["github-commit"] = github_ok
    save_data(data)
    
    stats = calculate_stats()
    print("-" * 35)
    print(f"🔥 Current Streak : {GREEN}{stats['current_streak']} Days{RESET}")
    print(f"📊 Compliance (7d): {YELLOW}{stats['compliance_7d']:.1f}%{RESET}")
    print("-" * 35)

def show_history_summary():
    """Displays a complete breakdown of achievements and historical stats."""
    clear_screen()
    stats = calculate_stats()
    data = load_data()
    config = load_config()
    tracked_tasks = config.get("tracked_tasks", DEFAULT_TASKS)

    print(f"{BOLD}{MAGENTA}==================================================={RESET}")
    print(f"{BOLD}{MAGENTA}        🛡️  GUARDIAN STATISTICS & HISTORICAL LOG    {RESET}")
    print(f"{BOLD}{MAGENTA}==================================================={RESET}")
    print(f"🔥 Active Streak       : {GREEN}{stats['current_streak']} days{RESET}")
    print(f"🏆 Longest Streak      : {GREEN}{stats['longest_streak']} days{RESET}")
    print(f"🎯 Total Tracked Days  : {WHITE}{stats['total_days_tracked']}{RESET}")
    print(f"🏆 Perfect Days Logged : {GREEN}{stats['perfect_days_count']}{RESET}")
    print(f"📈 7-Day Compliance    : {YELLOW}{stats['compliance_7d']:.1f}%{RESET}")
    print(f"📈 30-Day Compliance   : {YELLOW}{stats['compliance_30d']:.1f}%{RESET}")
    print("-" * 51)
    
    print(f"{BOLD}Recent logs (Last 7 Days):{RESET}")
    today = datetime.now().date()
    for i in range(7):
        day = today - timedelta(days=i)
        day_str = day.strftime("%Y-%m-%d")
        if day_str in data:
            day_data = data[day_str]
            manual_ok = all(day_data.get(task, False) for task in tracked_tasks)
            github_ok = day_data.get("github-commit", False)
            
            status_text = f"{GREEN}🏆 PERFECT{RESET}" if (manual_ok and github_ok) else f"{RED}❌ INCOMPLETE{RESET}"
            task_details = []
            for t in tracked_tasks:
                marker = "✓" if day_data.get(t, False) else "✗"
                task_details.append(f"{t}:{marker}")
            git_marker = "git:✓" if github_ok else "git:✗"
            task_details.append(git_marker)
            
            print(f"  {day_str} : {status_text} ({', '.join(task_details)})")
        else:
            print(f"  {day_str} : {YELLOW}⚪ NO LOG DATA{RESET}")
            
    print("-" * 51)
    input("\nPress [Enter] to go back...")

def run_nightly_audit(force_test=False):
    """Audits all goals, saves results, and fires alerts if missing."""
    if not is_within_timeline() and not force_test:
        print(f"{YELLOW}⚠️ Outside of configured timeline bounds. Skipping Nightly Audit.{RESET}")
        return
    config = load_config()
    tracked_tasks = config.get("tracked_tasks", DEFAULT_TASKS)
    github_user = config.get("github_username", "")
    ntfy_topic = config.get("ntfy_topic", "")
    
    data = load_data()
    today = datetime.now().strftime("%Y-%m-%d")
    data = initialize_today(data, today, tracked_tasks)
    
    # Check GitHub Commit Today
    print(f"{CYAN}Checking GitHub commit for username '{github_user}'...{RESET}")
    github_ok = check_github_commit_today(github_user)
    
    # Save today's final audit state into the JSON
    data[today]["github-commit"] = github_ok
    save_data(data)
    
    # Recalculate stats for the notification card
    stats = calculate_stats()
    
    missed_tasks = [task for task in tracked_tasks if not data[today].get(task, False)]
    if not github_ok:
        missed_tasks.append("github-commit")
        
    if missed_tasks:
        alert_title = "🚨 GUARDIAN ALARM: GOALS MISSED"
        alert_msg = (
            f"Failed tasks today:\n" +
            "\n".join([f"• {task.upper()}" for task in missed_tasks]) +
            f"\n\n🔥 Streak Reset Imminent! Current Streak: {stats['current_streak']} days."
            "\nFix it before midnight to secure your streak!"
        )
        send_alert(ntfy_topic, alert_title, alert_msg, priority="max", tags="skull,angry")
        print(f"{RED}🚨 Audit Failed! Alarm dispatched via ntfy.sh.{RESET}")
        print(f"Missed: {missed_tasks}")
    else:
        # Success notification
        alert_title = "🏆 PERFECT DAY ACHIEVED!"
        alert_msg = (
            f"All habits and commits verified successfully!\n\n"
            f"🔥 Active Streak: {stats['current_streak']} Days!\n"
            f"🏆 Keep building your legacy."
        )
        # Default priority is sufficient to notify without max emergency alerts
        send_alert(ntfy_topic, alert_title, alert_msg, priority="default", tags="partying_face,muscle,rocket")
        print(f"{GREEN}🏆 Audit Passed! Perfect Day alert dispatched via ntfy.sh.{RESET}")

# ==================== WINDOWS TASK SCHEDULER CLI ====================

def run_warning_check():
    """Runs a 9:00 PM warning check. If any tasks are incomplete, fires a high-priority loud alarm to the phone."""
    if not is_within_timeline():
        print(f"{YELLOW}⚠️ Outside of configured timeline bounds. Skipping 9:00 PM Warning Alarm check.{RESET}")
        return
    config = load_config()
    tracked_tasks = config.get("tracked_tasks", DEFAULT_TASKS)
    github_user = config.get("github_username", "")
    ntfy_topic = config.get("ntfy_topic", "")
    
    data = load_data()
    today = datetime.now().strftime("%Y-%m-%d")
    data = initialize_today(data, today, tracked_tasks)
    
    # Check GitHub Commit
    print(f"{CYAN}⏰ Running 9:00 PM Warning Check for username '{github_user}'...{RESET}")
    github_ok = check_github_commit_today(github_user)
    
    # Check missed tasks
    missed_tasks = [task for task in tracked_tasks if not data[today].get(task, False)]
    if not github_ok:
        missed_tasks.append("github-commit")
        
    if missed_tasks:
        stats = calculate_stats()
        alert_title = "⏰ GUARDIAN WARNING: GOALS PENDING!"
        alert_msg = (
            f"You still have incomplete goals for today:\n" +
            "\n".join([f"• {task.upper()}" for task in missed_tasks]) +
            f"\n\n🔥 Save your {stats['current_streak']} day streak!"
            "\nYou have 3 hours left until midnight!"
        )
        # Using priority "max" triggers a loud ringtone alarm sound on ntfy mobile apps
        send_alert(ntfy_topic, alert_title, alert_msg, priority="max", tags="rotating_light,alarm_clock,muscle")
        print(f"{YELLOW}🚨 Warning Alarm Dispatched! Loud alarm notification sent via ntfy.sh.{RESET}")
        print(f"Pending tasks: {missed_tasks}")
    else:
        print(f"{GREEN}🏆 Outstanding! All habits and commits already perfect. No warning alarm needed!{RESET}")

def run_test_warning():
    """Fires a test warning alarm check immediately with priority max to verify the phone plays sound/alert."""
    config = load_config()
    ntfy_topic = config.get("ntfy_topic", "")
    
    print(f"{CYAN}📢 Dispatching high-priority TEST WARNING ALARM to topic '{ntfy_topic}'...{RESET}")
    alert_title = "🔊 GUARDIAN: TEST ALARM ACTIVE"
    alert_msg = (
        "This is an urgent test of your Guardian sound alarm!\n"
        "If you can hear a loud ringtone, your phone notification sound is configured correctly! 🛡️\n\n"
        "Keep up the great work today!"
    )
    send_alert(ntfy_topic, alert_title, alert_msg, priority="max", tags="rotating_light,alarm_clock,loud_sound")
    print(f"{GREEN}✅ Test Alarm Dispatched! Check your phone now for a loud alarm sound.{RESET}")

def register_windows_task():
    """Registers both the 9:00 PM warning alarm and the nightly audit with the native Windows Task Scheduler."""
    if os.name != "nt":
        print(f"{RED}❌ Windows Task Scheduler is only supported on Windows OS.{RESET}")
        return

    config = load_config()
    audit_time = config.get("audit_time", "23:45")
    warning_time = config.get("warning_time", "21:00")
    
    # Create precise paths to the script and python executable
    python_exe = sys.executable
    script_path = os.path.abspath(__file__)
    
    # 1. Register the 9:00 PM Warning Alarm task
    warn_task = "GuardianDailyWarning"
    warn_action = f'\\"{python_exe}\\" \\"{script_path}\\" warning'
    
    print(f"{CYAN}Registering daily warning alarm task '{warn_task}' at {warning_time}...{RESET}")
    os.system(f'schtasks /delete /tn "{warn_task}" /f >nul 2>&1')
    warn_cmd = f'schtasks /create /tn "{warn_task}" /tr "{warn_action}" /sc daily /st {warning_time} /f'
    warn_res = os.system(warn_cmd)
    
    # 2. Register the Nightly Audit task
    audit_task = "GuardianDailyAudit"
    audit_action = f'\\"{python_exe}\\" \\"{script_path}\\" audit'
    
    print(f"{CYAN}Registering final daily audit task '{audit_task}' at {audit_time}...{RESET}")
    os.system(f'schtasks /delete /tn "{audit_task}" /f >nul 2>&1')
    audit_cmd = f'schtasks /create /tn "{audit_task}" /tr "{audit_action}" /sc daily /st {audit_time} /f'
    audit_res = os.system(audit_cmd)
    
    if warn_res == 0 and audit_res == 0:
        # Apply robust settings (run on battery, start when available, wake to run)
        power_cmd_warn = f'powershell -Command "Set-ScheduledTask -TaskName \\"{warn_task}\\" -Settings (New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -WakeToRun)" >nul 2>&1'
        power_cmd_audit = f'powershell -Command "Set-ScheduledTask -TaskName \\"{audit_task}\\" -Settings (New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -WakeToRun)" >nul 2>&1'
        os.system(power_cmd_warn)
        os.system(power_cmd_audit)
        
        print(f"\n{GREEN}✅ Success! Both Guardian tasks successfully scheduled in Windows Task Scheduler:{RESET}")
        print(f"  🔔 {BOLD}Warning Alarm:{RESET} Every day at {warning_time} (Rings loudly if tasks are pending)")
        print(f"  🏆 {BOLD}Nightly Audit:{RESET} Every day at {audit_time} (Finalizes daily records)")
    else:
        print(f"{RED}❌ Failed to create one or both scheduled tasks. Run as Administrator if needed.{RESET}")

def unregister_windows_task():
    """Removes both Guardian tasks from the Windows Task Scheduler."""
    if os.name != "nt":
        print(f"{RED}❌ Task Scheduler is only supported on Windows OS.{RESET}")
        return
        
    warn_task = "GuardianDailyWarning"
    audit_task = "GuardianDailyAudit"
    
    print(f"{CYAN}Removing scheduled tasks from Windows...{RESET}")
    res1 = os.system(f'schtasks /delete /tn "{warn_task}" /f >nul 2>&1')
    res2 = os.system(f'schtasks /delete /tn "{audit_task}" /f >nul 2>&1')
    
    if res1 == 0 or res2 == 0:
        print(f"{GREEN}✅ Success! Guardian tasks successfully removed from Windows.{RESET}")
    else:
        print(f"{RED}❌ Failed to remove tasks or they were not registered.{RESET}")

# ==================== MAIN ROUTER CONTROLLER ====================

if __name__ == "__main__":
    # If no arguments provided, launch the beautiful interactive dashboard!
    if len(sys.argv) < 2:
        interactive_dashboard()
        sys.exit(0)
        
    command = sys.argv[1].lower()
    
    if command == "interactive" or command == "dashboard":
        interactive_dashboard()
    elif command == "status":
        show_status()
    elif command == "done":
        if len(sys.argv) < 3:
            print(f"{RED}❌ Error: Please specify the task name. Example: python guardian.py done dsa{RESET}")
        else:
            mark_task_complete(sys.argv[2])
    elif command == "audit":
        run_nightly_audit()
    elif command == "warning" or command == "warn":
        run_warning_check()
    elif command == "test-warn" or command == "test-warning":
        run_test_warning()
    elif command == "setup":
        run_setup_wizard()
    elif command == "schedule":
        register_windows_task()
    elif command == "unschedule":
        unregister_windows_task()
    elif command == "stats" or command == "history":
        show_history_summary()
    elif command == "weekend":
        show_weekend_status()
    elif command == "weekend-done":
        toggle_weekend_complete_cli()
    elif command == "weekend-notes":
        if len(sys.argv) < 3:
            print(f"{RED}❌ Error: Please specify the notes content. Example: python guardian.py weekend-notes \"My notes\" {RESET}")
        else:
            save_weekend_notes_cli(" ".join(sys.argv[2:]))
    elif command == "weekend-history":
        show_weekend_history_cli()
    else:
        print(f"{RED}❌ Unknown command: '{command}'{RESET}")
        print("\nSupported Commands:")
        print("  python guardian.py dashboard       - Launch interactive visual dashboard (default)")
        print("  python guardian.py status          - Display clean status board + live GitHub check")
        print("  python guardian.py done [task]     - Mark a specific manual task as complete")
        print("  python guardian.py warning         - Trigger a 9:00 PM pending warning alarm check")
        print("  python guardian.py test-warn       - Trigger a manual high-priority test warning alarm")
        print("  python guardian.py audit           - Trigger the nightly verification run & alerts")
        print("  python guardian.py setup           - Start persistent configuration wizard")
        print("  python guardian.py schedule        - Register warning alarm & audit with Windows")
        print("  python guardian.py unschedule      - Unregister all tasks from Windows")
        print("  python guardian.py stats           - View historical statistics & recent logs")
        print("  python guardian.py weekend         - View modern Weekend Japan MNC Prep task and notes")
        print("  python guardian.py weekend-done    - Complete/Undo the current weekend Japan MNC Prep task")
        print("  python guardian.py weekend-notes   - Record study/research notes for the current weekend")
        print("  python guardian.py weekend-history - View historical logged records of all weekend work")
        sys.exit(1)
