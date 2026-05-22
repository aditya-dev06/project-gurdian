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
    if not os.path.exists(CONFIG_FILE):
        default_config = {
            "github_username": "YOUR_GITHUB_USERNAME",
            "ntfy_topic": "YOUR_UNIQUE_NTFY_TOPIC",
            "tracked_tasks": DEFAULT_TASKS,
            "audit_time": "23:45"
        }
        save_config(default_config)
        return default_config
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except Exception:
        print(f"{RED}⚠️ Error loading config.json. Reverting to default settings.{RESET}")
        return {
            "github_username": "YOUR_GITHUB_USERNAME",
            "ntfy_topic": "YOUR_UNIQUE_NTFY_TOPIC",
            "tracked_tasks": DEFAULT_TASKS,
            "audit_time": "23:45"
        }

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
        return {}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}
    except Exception as e:
        print(f"{RED}❌ Failed to read data file: {e}{RESET}")
        return {}

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
    try:
        requests.post(
            f"https://ntfy.sh/{topic}",
            data=message.encode('utf-8'),
            params={
                "title": title,
                "priority": priority,
                "tags": tags
            },
            timeout=5
        )
    except requests.RequestException as e:
        print(f"{RED}❌ Failed to send push notification: {e}{RESET}")

# ==================== ANALYTICS ENGINE ====================

def calculate_stats():
    """Calculates active streaks and compliance rates over historical records."""
    data = load_data()
    config = load_config()
    tracked_tasks = config.get("tracked_tasks", DEFAULT_TASKS)
    
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

    dates_str = sorted(data.keys())
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

    start_date = min(parsed_dates)
    today = datetime.now().date()

    # Reconstruct timeline from start date to today to ensure missing logged days count as missed streaks
    all_days = []
    curr = start_date
    while curr <= today:
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
    # A streak is active if today is perfect, OR if today is incomplete but yesterday was perfect (user has until midnight).
    current_streak = 0
    check_day = today

    if not perfect_days.get(today, False):
        yesterday = today - timedelta(days=1)
        if perfect_days.get(yesterday, False):
            check_day = yesterday

    while check_day in perfect_days and perfect_days[check_day]:
        current_streak += 1
        check_day -= timedelta(days=1)

    # Longest streak calculation
    longest_streak = 0
    temp_streak = 0
    curr = start_date
    while curr <= today:
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
        window_days = [today - timedelta(days=i) for i in range(days_window)]
        perfect_count = 0
        valid_days = 0
        for d in window_days:
            if d >= start_date:
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
    else:
        print(f"{RED}❌ Unknown command: '{command}'{RESET}")
        print("\nSupported Commands:")
        print("  python guardian.py dashboard      - Launch interactive visual dashboard (default)")
        print("  python guardian.py status         - Display clean status board + live GitHub check")
        print("  python guardian.py done [task]    - Mark a specific manual task as complete")
        print("  python guardian.py warning        - Trigger a 9:00 PM pending warning alarm check")
        print("  python guardian.py test-warn      - Trigger a manual high-priority test warning alarm")
        print("  python guardian.py audit          - Trigger the nightly verification run & alerts")
        print("  python guardian.py setup          - Start persistent configuration wizard")
        print("  python guardian.py schedule       - Register warning alarm & audit with Windows")
        print("  python guardian.py unschedule     - Unregister all tasks from Windows")
        print("  python guardian.py stats          - View historical statistics & recent logs")
        sys.exit(1)
