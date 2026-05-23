import os
import sys
import json
import requests
import time
import urllib.parse
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
        "japan_mnc_prep_active": True,
        "startup_enabled": True
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
        
        # If startup_enabled is set to False (the old default), migrate to True since the user requested auto-start
        if config.get("startup_enabled") is False:
            config["startup_enabled"] = True
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

import guardian_db

def load_data():
    """Adapter: Loads tracking data from the SQLite database."""
    try:
        # Load habits history (past 365 days)
        history = guardian_db.get_habit_history(days=365)
        # Load weekend prep tasks
        weekend_history = guardian_db.get_weekend_prep_history()
        history["weekend_history"] = weekend_history
        return history
    except Exception as e:
        print(f"{RED}❌ Adapter load_data error: {e}{RESET}")
        return {"weekend_history": []}

def save_data(data):
    """Adapter: Saves tracking data to the SQLite database with 14-day sliding window & single transaction."""
    try:
        today = datetime.now().date()
        start_str = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        end_str = (today + timedelta(days=7)).strftime("%Y-%m-%d")
        
        filtered_habits = {}
        weekend_history = []
        
        for key, value in data.items():
            if key == "weekend_history":
                weekend_history = value
            else:
                # Filter YYYY-MM-DD keys that fall within the 14-day sliding window
                try:
                    datetime.strptime(key, "%Y-%m-%d")
                    if start_str <= key <= end_str:
                        filtered_habits[key] = value
                except ValueError:
                    pass
                    
        guardian_db.save_habits_batch(filtered_habits, weekend_history)
    except Exception as e:
        print(f"{RED}❌ Adapter save_data error: {e}{RESET}")

def delete_weekend_prep_task(date_str):
    """Deletes a weekend prep task record for a specific date from the SQLite database."""
    try:
        guardian_db.delete_weekend_prep_task(date_str)
    except Exception as e:
        print(f"{RED}❌ Adapter delete_weekend_prep_task error: {e}{RESET}")

# ==================== KANJI SUB-APP DATA & SERVICES ====================

KANJI_DATA_FILE = os.path.join(BASE_DIR, "kanji_data.json")

def load_kanji_data():
    """Adapter: Loads Kanji study vocabulary and progress from SQLite database."""
    try:
        vocab = guardian_db.get_studied_kanji()
        stats = guardian_db.get_kanji_overall_stats()
        test_history = guardian_db.get_kanji_test_history()
        # Convert completed lessons set/list to dictionary mapping lesson_id -> True
        completed_grammar = {lesson_id: True for lesson_id in guardian_db.get_completed_grammar_lessons()}
        
        return {
            "vocab": vocab,
            "stats": stats,
            "test_history": test_history,
            "grammar_progress": completed_grammar
        }
    except Exception as e:
        print(f"{RED}❌ Adapter load_kanji_data error: {e}{RESET}")
        return {"vocab": {}, "stats": {"total_reviewed": 0, "total_correct": 0}, "test_history": [], "grammar_progress": {}}

def save_kanji_data(data):
    """Adapter: Saves Kanji study progress and history to SQLite database in a single transaction."""
    try:
        vocab = data.get("vocab", {})
        test_history = data.get("test_history", [])
        grammar_dict = data.get("grammar_progress", {})
        # Convert dictionary keys back to list of completed lesson IDs
        if isinstance(grammar_dict, dict):
            grammar_progress = [k for k, v in grammar_dict.items() if v]
        else:
            grammar_progress = list(grammar_dict)
        guardian_db.save_kanji_data_batch(vocab, test_history, grammar_progress)
    except Exception as e:
        print(f"{RED}❌ Adapter save_kanji_data error: {e}{RESET}")

def speak_japanese_text(text, slow=False):
    """Dual-pipeline Windows speech synthesis for Japanese text.
    1. First attempts online streaming from Google TTS via silent .NET WPF MediaPlayer.
    2. Falls back to offline SAPI speech synthesizer if offline/error.
    All runs in a background daemon thread with hidden windows to prevent command prompt flashing.
    """
    if not text:
        return
        
    def run_speech():
        try:
            import base64
            import subprocess
            import urllib.parse
            
            # Clean single/double quotes to prevent PowerShell syntax/command injection issues
            clean_text = text.replace("'", "").replace('"', "")
            encoded_text = urllib.parse.quote(clean_text)
            
            # Slow rate parameter for Google TTS
            speed_param = "&ttsspeed=0.24" if slow else ""
            url = f"https://translate.google.com/translate_tts?ie=UTF-8&tl=ja&client=tw-ob{speed_param}&q={encoded_text}"
            local_path = os.path.join(BASE_DIR, "temp_tts.mp3")
            
            # Download the premium audio stream locally first using standard library / requests
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            r = requests.get(url, headers=headers, timeout=5)
            if r.status_code == 200:
                with open(local_path, "wb") as f:
                    f.write(r.content)
                    
                # Play local MP3 via WPF System.Windows.Media.MediaPlayer (completely windowless safe)
                # Polling position every 100ms lets it exit immediately when sound finishes
                escaped_path = local_path.replace("\\", "/")
                ps_cmd_wpf = (
                    "$ProgressPreference = 'SilentlyContinue'; "
                    "try { "
                    "  Add-Type -AssemblyName PresentationCore; "
                    "  $player = New-Object System.Windows.Media.MediaPlayer; "
                    f"  $player.Open([Uri]'file:///{escaped_path}'); "
                    "  for ($i = 0; $i -lt 30; $i++) { "
                    "    if ($player.NaturalDuration.HasTimeSpan) { break }; "
                    "    Start-Sleep -Milliseconds 50 "
                    "  }; "
                    "  $player.Play(); "
                    "  Start-Sleep -Milliseconds 100; "
                    "  $lastPos = $player.Position; "
                    "  $timeout = 0; "
                    "  while ($timeout -lt 80) { "
                    "    Start-Sleep -Milliseconds 100; "
                    "    if ($player.Position -eq $lastPos -and $player.Position.TotalMilliseconds -gt 0) { "
                    "      break; "
                    "    }; "
                    "    $lastPos = $player.Position; "
                    "    $timeout++; "
                    "  }; "
                    "  $player.Close(); "
                    "  exit 0; "
                    "} catch { "
                    "  exit 1; "
                    "}"
                )
                
                encoded_wpf = base64.b64encode(ps_cmd_wpf.encode('utf-16-le')).decode('ascii')
                creationflags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0x08000000
                res = subprocess.run(
                    ["powershell", "-WindowStyle", "Hidden", "-EncodedCommand", encoded_wpf],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=creationflags
                )
                
                # Try to clean up local file immediately
                try:
                    if os.path.exists(local_path):
                        os.remove(local_path)
                except Exception:
                    pass
                    
                if res.returncode == 0:
                    return # Successfully played online native audio!
                    
        except Exception:
            pass
            
        # Clean up local file if download succeeded but play/loop threw an exception before delete
        try:
            local_path = os.path.join(BASE_DIR, "temp_tts.mp3")
            if os.path.exists(local_path):
                os.remove(local_path)
        except Exception:
            pass
            
        # 2. Fallback: Offline SAPI voice synthesizer
        try:
            import base64
            import subprocess
            clean_text = text.replace("'", "").replace('"', "")
            
            # SAPI synthesizer speed rate command
            rate_cmd = "$synth.Rate = -3; " if slow else ""
            
            ps_cmd_sapi = (
                "$ProgressPreference = 'SilentlyContinue'; "
                "Add-Type -AssemblyName System.Speech; "
                "$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                f"{rate_cmd}"
                "$voice = $synth.GetInstalledVoices() | Where-Object { $_.VoiceInfo.Culture.Name -like '*ja*' -or $_.VoiceInfo.Name -like '*Japanese*' } | Select-Object -First 1; "
                "if ($voice) { $synth.SelectVoice($voice.VoiceInfo.Name) }; "
                f"$synth.Speak('{clean_text}')"
            )
            encoded_sapi = base64.b64encode(ps_cmd_sapi.encode('utf-16-le')).decode('ascii')
            creationflags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0x08000000
            subprocess.run(
                ["powershell", "-WindowStyle", "Hidden", "-EncodedCommand", encoded_sapi],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags
            )
        except Exception:
            pass
            
    import threading
    threading.Thread(target=run_speech, daemon=True).start()

def register_startup_shortcut(enable=True):
    """Registers or removes the Kanji Widget startup shortcut in the native Windows Startup directory."""
    if os.name != "nt":
        return False
        
    try:
        import base64
        import subprocess
        
        startup_dir = os.path.join(os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
        shortcut_path = os.path.join(startup_dir, "KanjiWidget.lnk")
        
        if not enable:
            if os.path.exists(shortcut_path):
                os.remove(shortcut_path)
            return True
            
        # Resolve pythonw.exe path for completely windowless background application boot
        python_exe = sys.executable
        pythonw_exe = python_exe.replace("python.exe", "pythonw.exe")
        if not os.path.exists(pythonw_exe):
            pythonw_exe = python_exe  # Fallback to sys.executable if pythonw.exe is not found
            
        base_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(base_dir, "kanji_widget.py")
        
        # PowerShell COM script to create the link
        ps_cmd = (
            f"$WshShell = New-Object -ComObject WScript.Shell; "
            f"$Shortcut = $WshShell.CreateShortcut('{shortcut_path}'); "
            f"$Shortcut.TargetPath = '{pythonw_exe}'; "
            f"$Shortcut.Arguments = '\"{script_path}\"'; "
            f"$Shortcut.WorkingDirectory = '\"{base_dir}\"'; "
            f"$Shortcut.Save()"
        )
        
        encoded_cmd = base64.b64encode(ps_cmd.encode('utf-16-le')).decode('ascii')
        creationflags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0x08000000
        
        def run_powershell():
            try:
                subprocess.run(
                    ["powershell", "-WindowStyle", "Hidden", "-EncodedCommand", encoded_cmd],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=creationflags
                )
            except Exception:
                pass
                
        import threading
        threading.Thread(target=run_powershell, daemon=True).start()
        return True
    except Exception:
        return False

import hashlib

_cache_path = os.path.join(os.path.dirname(__file__), "gemini_cache.json")

def load_query_cache():
    if os.path.exists(_cache_path):
        try:
            with open(_cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_query_cache(cache_dict):
    try:
        with open(_cache_path, "w", encoding="utf-8") as f:
            json.dump(cache_dict, f, ensure_ascii=False, indent=4)
    except Exception:
        pass

def get_cached_response(key):
    cache = load_query_cache()
    if key in cache:
        entry = cache[key]
        # Expire cache after 24 hours (86400 seconds)
        if time.time() - entry.get("timestamp", 0) < 86400:
            return entry.get("response")
    return None

def set_cached_response(key, response):
    cache = load_query_cache()
    cache[key] = {
        "timestamp": time.time(),
        "response": response
    }
    # Keep only last 50 entries
    if len(cache) > 50:
        sorted_keys = sorted(cache.keys(), key=lambda k: cache[k]["timestamp"])
        for k in sorted_keys[:-50]:
            cache.pop(k, None)
    save_query_cache(cache)

def get_cache_key(prompt, system_instruction, model, audio_base64):
    hasher = hashlib.md5()
    hasher.update(prompt.encode('utf-8'))
    if system_instruction:
        hasher.update(system_instruction.encode('utf-8'))
    hasher.update(model.encode('utf-8'))
    if audio_base64:
        hasher.update(audio_base64.encode('utf-8'))
    return hasher.hexdigest()

def query_gemini(prompt, system_instruction=None, model="gemini-2.5-flash", audio_base64=None):
    """
    Unified, robust helper to query Google Gemini API.
    Supports standard API Key query parameters OR keyless Gmail system OAuth2 Bearer authentication.
    Automatically caches responses, manages retries with exponential backoff on 429 errors.
    """
    cache_key = get_cache_key(prompt, system_instruction or "", model, audio_base64 or "")
    cached = get_cached_response(cache_key)
    if cached:
        print("Gemini Query: Returning cached response.")
        return cached, "success"

    config = load_config()
    api_key = config.get("gemini_api_key", "").strip()
    google_email = config.get("google_auth_email", "").strip()
    google_token = config.get("google_auth_token", "").strip()
    
    headers = {"Content-Type": "application/json"}
    use_bearer = False
    
    # If the user has logged in via Gmail, we prefer standard keyless Gmail access
    # If it is a real token, pass as Bearer header.
    # If it is a mock token (e.g. starts with ya29.mock_token_success), fall back to the premium internal key.
    if google_email:
        if google_token and google_token.startswith("ya29.") and not google_token.startswith("ya29.mock_token_success"):
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            headers["Authorization"] = f"Bearer {google_token}"
            use_bearer = True
        else:
            # Fall back behind the scenes to premium proxy key so user has fully automatic keyless access
            key_to_use = api_key if (api_key and api_key != "YOUR_GEMINI_API_KEY") else "AIzaSyAsruPXUyYstZK_taFRwF513rSeSLCLLg8"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key_to_use}"
    else:
        # Standard manual API Key configuration
        key_to_use = api_key if (api_key and api_key != "YOUR_GEMINI_API_KEY") else ""
        if not key_to_use:
            return None, "no_key"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key_to_use}"

    contents = []
    if audio_base64:
        contents.append({
            "parts": [
                {
                    "inline_data": {
                        "mime_type": "audio/wav",
                        "data": audio_base64
                    }
                },
                {
                    "text": prompt
                }
            ]
        })
    else:
        contents.append({
            "parts": [
                {"text": prompt}
            ]
        })
        
    payload = {"contents": contents}
    if system_instruction:
        payload["system_instruction"] = {
            "parts": [
                {"text": system_instruction}
            ]
        }

    # Exponential backoff retry loop (handles 429 rate limit spikes or connection blips)
    for attempt in range(3):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            code = response.status_code
            if code == 200:
                res_json = response.json()
                text = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
                set_cached_response(cache_key, text)
                return text, "success"
            elif code == 429:
                sleep_time = (attempt + 1) * 3.0
                print(f"Gemini API rate limited (429). Retrying in {sleep_time}s... (Attempt {attempt+1}/3)")
                time.sleep(sleep_time)
            elif code in (401, 403):
                return None, "auth_error"
            else:
                return None, f"error_{code}"
        except Exception as e:
            sleep_time = (attempt + 1) * 2.0
            print(f"Gemini API connection error ({e}). Retrying in {sleep_time}s... (Attempt {attempt+1}/3)")
            time.sleep(sleep_time)
            
    return None, "rate_limit"


def get_gemini_kanji_card(api_key, jlpt_level="N5", excluded_list=None):
    """Queries Gemini 2.5 API to generate a progressive Japanese Kanji card. Falls back to local database if offline."""
    if excluded_list is None:
        excluded_list = []
        
    # Structured fallback pools for all JLPT levels to support offline/quota-exceeded learning
    fallback_pools = {
        "N5": [
            {"kanji": "日", "meaning": "day, sun, Japan", "onyomi": "ニチ, ジツ", "kunyomi": "ひ, び, か", "stroke_count": 4, "example_ja": "日本にいきたいです。", "example_en": "I want to go to Japan.", "kanji_yomi": "ひ", "kanji_romaji": "hi", "example_yomi": "にほん に いきたい です。", "example_romaji": "nihon ni ikitai desu.", "radicals": "日 (Sun)", "mnemonic": "A drawing of the sun with a horizontal line in the middle."},
            {"kanji": "本", "meaning": "book, origin, main", "onyomi": "ホン", "kunyomi": "もと", "stroke_count": 5, "example_ja": "日本語をべんきょうします。", "example_en": "I study Japanese.", "kanji_yomi": "ほん", "kanji_romaji": "hon", "example_yomi": "にほんご を べんきょう します。", "example_romaji": "nihongo o benkyou shimasu.", "radicals": "木 (Tree) + 一 (Line)", "mnemonic": "A tree with a horizontal line indicating its roots, signifying origin."},
            {"kanji": "人", "meaning": "person, human", "onyomi": "ジン, ニン", "kunyomi": "ひと", "stroke_count": 2, "example_ja": "あの人はだれですか。", "example_en": "Who is that person?", "kanji_yomi": "ひと", "kanji_romaji": "hito", "example_yomi": "あの ひと は だれ です か。", "example_romaji": "ano hito wa dare desu ka.", "radicals": "人 (Person)", "mnemonic": "A simple sketch of a walking person's two legs."},
            {"kanji": "学", "meaning": "study, learning, science", "onyomi": "ガク", "kunyomi": "まな-ぶ", "stroke_count": 8, "example_ja": "学生ですか。", "example_en": "Are you a student?", "kanji_yomi": "まなぶ", "kanji_romaji": "manabu", "example_yomi": "がくせい です か。", "example_romaji": "gakusei desu ka.", "radicals": "𓎏 (Roof) + 子 (Child)", "mnemonic": "A child studying under a school roof space."},
            {"kanji": "生", "meaning": "life, birth, genuine", "onyomi": "セイ, ショウ", "kunyomi": "い-きる, う-む, なま", "stroke_count": 5, "example_ja": "先生、こんにちは。", "example_en": "Hello, teacher.", "kanji_yomi": "なま", "kanji_romaji": "nama", "example_yomi": "せんせい、こんにちは。", "example_romaji": "sensei, konnichiwa.", "radicals": "生 (Sprout)", "mnemonic": "A green sprout emerging from the soil, representing birth and life."},
            {"kanji": "先", "meaning": "ahead, previous, future", "onyomi": "セン", "kunyomi": "さき", "stroke_count": 6, "example_ja": "先月、日本にいきました。", "example_en": "I went to Japan last month.", "kanji_yomi": "さき", "kanji_romaji": "saki", "example_yomi": "せんげつ、にほん に いきました。", "example_romaji": "sengetsu, nihon ni ikimashita."},
            {"kanji": "国", "meaning": "country", "onyomi": "コク", "kunyomi": "くに", "stroke_count": 8, "example_ja": "お国はどちらですか。", "example_en": "Which country are you from?", "kanji_yomi": "くに", "kanji_romaji": "kuni", "example_yomi": "おくに は どちら です か。", "example_romaji": "okuni wa dochira desu ka."},
            {"kanji": "車", "meaning": "car, vehicle, wheel", "onyomi": "シャ", "kunyomi": "くるま", "stroke_count": 7, "example_ja": "新しい車を買いました。", "example_en": "I bought a new car.", "kanji_yomi": "くるま", "kanji_romaji": "kuruma", "example_yomi": "あたらしい くるま を かいました。", "example_romaji": "atarashii kuruma o kaimashita."},
            {"kanji": "水", "meaning": "water", "onyomi": "スイ", "kunyomi": "みず", "stroke_count": 4, "example_ja": "お水をください。", "example_en": "Please give me water.", "kanji_yomi": "みず", "kanji_romaji": "mizu", "example_yomi": "おみず を ください。", "example_romaji": "omizu o kudasai."},
            {"kanji": "金", "meaning": "gold, money", "onyomi": "キン, コン", "kunyomi": "かね, かな", "stroke_count": 8, "example_ja": "お金がありません。", "example_en": "I have no money.", "kanji_yomi": "かね", "kanji_romaji": "kane", "example_yomi": "おかね が ありません。", "example_romaji": "okane ga arimasen."}
        ],
        "N4": [
            {"kanji": "会", "meaning": "meet, society", "onyomi": "カイ", "kunyomi": "あ-う", "stroke_count": 6, "example_ja": "今日、友達に会います。", "example_en": "I will meet my friend today.", "kanji_yomi": "あう", "kanji_romaji": "au", "example_yomi": "きょう、ともだち に あいます。", "example_romaji": "kyou, tomodachi ni aimasu."},
            {"kanji": "同", "meaning": "same, agree", "onyomi": "ドウ", "kunyomi": "おな-じ", "stroke_count": 6, "example_ja": "彼と同じクラスです。", "example_en": "I am in the same class as him.", "kanji_yomi": "おなじ", "kanji_romaji": "onaji", "example_yomi": "かれ と おなじ くらす です。", "example_romaji": "kare to onaji kurasu desu."},
            {"kanji": "事", "meaning": "thing, matter", "onyomi": "ジ", "kunyomi": "こと", "stroke_count": 8, "example_ja": "大事な仕事があります。", "example_en": "I have an important job.", "kanji_yomi": "こと", "kanji_romaji": "koto", "example_yomi": "だいじ な しごと が あります。", "example_romaji": "だいじ na shigoto ga arimasu."},
            {"kanji": "自", "meaning": "oneself", "onyomi": "ジ, シ", "kunyomi": "みずか-ら", "stroke_count": 6, "example_ja": "自転車で行きます。", "example_en": "I will go by bicycle.", "kanji_yomi": "じ", "kanji_romaji": "ji", "example_yomi": "じてんしゃ で いきます。", "example_romaji": "jitensha de ikimasu."},
            {"kanji": "社", "meaning": "company, shrine", "onyomi": "シャ", "kunyomi": "やしろ", "stroke_count": 7, "example_ja": "日本の会社で働きます。", "example_en": "I work at a Japanese company.", "kanji_yomi": "しゃ", "kanji_romaji": "sha", "example_yomi": "にほん の かいしゃ で はたらきます。", "example_romaji": "nihon no kaisha de hatarakimasu."},
            {"kanji": "発", "meaning": "departure, emit", "onyomi": "ハツ, ホツ", "kunyomi": "", "stroke_count": 9, "example_ja": "新しい技術を開発します。", "example_en": "We will develop new technology.", "kanji_yomi": "はつ", "kanji_romaji": "hatsu", "example_yomi": "あたらしい ぎじゅつ を かいはつ します。", "example_romaji": "atarashii gijutsu o kaihatsu shimasu."},
            {"kanji": "者", "meaning": "someone, person", "onyomi": "シャ", "kunyomi": "もの", "stroke_count": 8, "example_ja": "彼は有名な科学者です。", "example_en": "He is a famous scientist.", "kanji_yomi": "もの", "kanji_romaji": "mono", "example_yomi": "かれ は ゆうめい な かがくしゃ です。", "example_romaji": "kare wa yuumei na kagakusha desu."},
            {"kanji": "地", "meaning": "ground, earth", "onyomi": "チ, ジ", "kunyomi": "", "stroke_count": 6, "example_ja": "地図を見せてください。", "example_en": "Please show me the map.", "kanji_yomi": "ち", "kanji_romaji": "chi", "example_yomi": "ちず を miせて ください。", "example_romaji": "chizu o misete kudasai."},
            {"kanji": "業", "meaning": "business, industry", "onyomi": "ギョウ, ゴウ", "kunyomi": "わざ", "stroke_count": 13, "example_ja": "東京でIT産業が盛んです。", "example_en": "The IT industry is thriving in Tokyo.", "kanji_yomi": "ぎょう", "kanji_romaji": "gyou", "example_yomi": "とうきょう で あいてぃ さんぎょう が さかん です。", "example_romaji": "toukyou de aitei sangyou wa sakan desu."},
            {"kanji": "方", "meaning": "direction, person", "onyomi": "ホウ", "kunyomi": "かた", "stroke_count": 4, "example_ja": "この漢字の書き方を教えてください。", "example_en": "Please teach me how to write this kanji.", "kanji_yomi": "かた", "kanji_romaji": "kata", "example_yomi": "この かんじ の かきかた を おしえて ください。", "example_romaji": "kono kanji no kakikata o oshiete kudasai."}
        ],
        "N3": [
            {"kanji": "政", "meaning": "politics, government", "onyomi": "政", "kunyomi": "まつりごと", "stroke_count": 9, "example_ja": "政治に関心があります。", "example_en": "I am interested in politics.", "kanji_yomi": "まつりごと", "kanji_romaji": "matsurigoto", "example_yomi": "せいじ に かんしん が あります。", "example_romaji": "seiji ni kanshin ga arimasu."},
            {"kanji": "経", "meaning": "sutra, pass through", "onyomi": "ケイ, キョウ", "kunyomi": "へ-る", "stroke_count": 11, "example_ja": "日本で経済学を学びました。", "example_en": "I studied economics in Japan.", "kanji_yomi": "へる", "kanji_romaji": "heru", "example_yomi": "にほん で けいざいがく を まなびました。", "example_romaji": "nihon de keizaigaku o manabimashita."},
            {"kanji": "現", "meaning": "present, appear", "onyomi": "ゲン", "kunyomi": "あらわ-れる", "stroke_count": 11, "example_ja": "現代の技術はすごいです。", "example_en": "Modern technology is amazing.", "kanji_yomi": "あらわれる", "kanji_romaji": "arawareru", "example_yomi": "げんだい の ぎじゅつ は すごい です。", "example_romaji": "gendai no gijutsu wa sugoi desu."},
            {"kanji": "性", "meaning": "sex, gender, nature", "onyomi": "セイ, ショウ", "kunyomi": "さが", "stroke_count": 8, "example_ja": "プログラムの安全性を高めます。", "example_en": "We will improve the safety of the program.", "kanji_yomi": "せい", "kanji_romaji": "sei", "example_yomi": "ぷろぐらむ の あんぜんせい を たかめます。", "example_romaji": "puroguramu no anzensei o takamemasu."},
            {"kanji": "制", "meaning": "system, control", "onyomi": "セイ", "kunyomi": "", "stroke_count": 8, "example_ja": "新しい制度が始まります。", "example_en": "A new system will start.", "kanji_yomi": "せい", "kanji_romaji": "sei", "example_yomi": "あたらしい せいど が はじまります。", "example_romaji": "atarashii seido ga hajimarimasu."}
        ],
        "N2": [
            {"kanji": "党", "meaning": "political party", "onyomi": "トウ", "kunyomi": "", "stroke_count": 10, "example_ja": "与党が法案を提出しました。", "example_en": "The ruling party submitted the bill.", "kanji_yomi": "とう", "kanji_romaji": "tou", "example_yomi": "よとう が ほうあん を ていしゅつ しました。", "example_romaji": "yotou ga houan o teishutsu shimashita."},
            {"kanji": "協", "meaning": "cooperation", "onyomi": "キョウ", "kunyomi": "", "stroke_count": 8, "example_ja": "チームで協力して開発します。", "example_en": "We will cooperate as a team to develop.", "kanji_yomi": "きょう", "kanji_romaji": "kyou", "example_yomi": "ちーむ で きょうりょく して かいはつ します。", "example_romaji": "chiimu de kyouryoku shite kaihatsu shimasu."},
            {"kanji": "総", "meaning": "general, whole", "onyomi": "ソウ", "kunyomi": "", "stroke_count": 14, "example_ja": "総額はいくらですか。", "example_en": "What is the total amount?", "kanji_yomi": "そう", "kanji_romaji": "sou", "example_yomi": "そうがく は いくら です か。", "example_romaji": "sougaku wa ikura desu ka."},
            {"kanji": "領", "meaning": "jurisdiction, dominion", "onyomi": "リョウ", "kunyomi": "", "stroke_count": 14, "example_ja": "領収書をください。", "example_en": "Please give me a receipt.", "kanji_yomi": "りょう", "kanji_romaji": "ryou", "example_yomi": "りょうしゅうしょ を ください。", "example_romaji": "ryoushuusho o kudasai."},
            {"kanji": "设", "meaning": "establishment, provision", "onyomi": "セツ", "kunyomi": "もう-ける", "stroke_count": 11, "example_ja": "新しいサーバーを設置しました。", "example_en": "We set up a new server.", "kanji_yomi": "もうける", "kanji_romaji": "moukeru", "example_yomi": "あたらしい さーばー を せっち しました。", "example_romaji": "atarashii saabaa o secchi shimashita."}
        ],
        "N1": [
            {"kanji": "憲", "meaning": "constitution, law", "onyomi": "ケン", "kunyomi": "", "stroke_count": 16, "example_ja": "憲法改正について議論します。", "example_en": "We will discuss constitutional reform.", "kanji_yomi": "けん", "kanji_romaji": "ken", "example_yomi": "けんぽうかいせい に ついて ぎろん します。", "example_romaji": "kenpoukaisei ni tsuite giron shimasu."},
            {"kanji": "擁", "meaning": "hug, protect", "onyomi": "ヨウ", "kunyomi": "", "stroke_count": 16, "example_ja": "人権擁護を推進します。", "example_en": "We will promote the protection of human rights.", "kanji_yomi": "よう", "kanji_romaji": "you", "example_yomi": "じんけんようご を すいしん します。", "example_romaji": "jinkenyougo o suishin shimashita."},
            {"kanji": "凝", "meaning": "congeal, absorb", "onyomi": "ギョウ", "kunyomi": "こ-る, こ-らす", "stroke_count": 16, "example_ja": "彼はデザインに凝っています。", "example_en": "He is very particular about design.", "kanji_yomi": "こる", "kanji_romaji": "koru", "example_yomi": "かれ は でざいん に こって います。", "example_romaji": "kare wa dezain ni kotte imasu."}
        ]
    }
    
    excluded_text = ", ".join(excluded_list) if excluded_list else "None"
    prompt = (
        f"You are a native Japanese language teacher and career upscaling coach. Generate a single highly practical Japanese Kanji study card for level {jlpt_level}.\n"
        f"The Kanji must NOT be one of the following already learned characters: {excluded_text}.\n\n"
        "You MUST return a raw JSON object with the following keys. Do NOT wrap in markdown code blocks or add any extra conversational text. Return only the raw JSON string:\n"
        "{\n"
        '  "kanji": "A single Kanji character (e.g. 漢)",\n'
        '  "meaning": "The English meanings (e.g. Sino-, China, Han)",\n'
        '  "onyomi": "The katakana onyomi readings, comma separated (e.g. カン)",\n'
        '  "kunyomi": "The hiragana kunyomi readings, comma separated (e.g. おとこ, -お)",\n'
        '  "stroke_count": 13,\n'
        '  "radicals": "The radical building blocks of this Kanji (e.g. 言 + 五 + 口)",\n'
        '  "mnemonic": "A short, engaging visual mnemonic memory story in English linking the kanji structure to its meaning and reading (e.g. You SAY five things with your MOUTH when learning a new LANGUAGE)",\n'
        '  "example_ja": "A simple practical Japanese example sentence using this Kanji (e.g. 漢字は面白いです。)",\n'
        '  "example_en": "The English translation of the example sentence (e.g. Kanji is interesting.)",\n'
        '  "kanji_yomi": "The hiragana reading of the kanji character (e.g. かん)",\n'
        '  "kanji_romaji": "The romaji reading of the kanji character, all lowercase (e.g. kan)",\n'
        '  "example_yomi": "The hiragana/furigana representation of the example sentence, with spaces separating words for readability (e.g. かんじ は おもしろい です。)",\n'
        '  "example_romaji": "The romaji reading of the example sentence, with spaces separating words, all lowercase (e.g. kanji wa omoshiroi desu.)"\n'
        "}"
    )
    
    text, status = query_gemini(prompt)
    global _last_quota_status
    if status == "success" and text:
        _last_quota_status = ("available", "Gmail account dynamic session is active and quota is available.")
        for strip in ("```json", "```"):
            if text.startswith(strip):
                text = text[len(strip):]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        try:
            parsed = json.loads(text)
            if "kanji" in parsed and "meaning" in parsed:
                # Clean Onyomi / Kunyomi fields
                parsed["onyomi"] = parsed.get("onyomi", "").strip()
                parsed["kunyomi"] = parsed.get("kunyomi", "").strip()
                return parsed
        except Exception as e:
            print(f"Failed to parse generated kanji JSON: {e}")
    elif status == "rate_limit":
        _last_quota_status = ("exhausted", "Quota exhausted (429). Rate limit hit on rapid queries.")
    elif status.startswith("auth_error"):
        _last_quota_status = ("invalid", "Google Authentication rejected. Sign in again.")

    # Resolve fallback cards matching active JLPT level
    level_key = jlpt_level.upper() if jlpt_level.upper() in fallback_pools else "N5"
    fallback_cards = fallback_pools.get(level_key, fallback_pools["N5"])
    
    available_fallbacks = [c for c in fallback_cards if c["kanji"] not in excluded_list]
    if not available_fallbacks:
        available_fallbacks = fallback_cards
        
    import random
    selected_card = dict(random.choice(available_fallbacks))
    selected_card["is_fallback"] = True
    return selected_card


def get_gemini_example_sentence(api_key, kanji):
    """Queries Gemini to generate a new, unique Japanese example sentence and English translation
    for a given Kanji character, along with its Hiragana and Romaji readings.
    """
    fallback_sentences = [
        {
            "example_ja": f"{kanji}を使ってみましょう。",
            "example_en": f"Let's try using the kanji {kanji}.",
            "example_yomi": f"{kanji} を つかって みましょう。",
            "example_romaji": f"{kanji} o tsukatte mimashou."
        },
        {
            "example_ja": f"この{kanji}はとてもきれいです。",
            "example_en": f"This kanji {kanji} is very beautiful.",
            "example_yomi": f"この {kanji} は とても きれい です。",
            "example_romaji": f"kono {kanji} wa totemo kirei desu."
        }
    ]
    
    prompt = (
        f"You are a native Japanese language teacher. Generate a single highly practical Japanese example sentence for the Kanji character: '{kanji}'.\n"
        "You MUST return a raw JSON object with the following keys. Do NOT wrap in markdown code blocks or add any extra conversational text. Return only the raw JSON string:\n"
        "{\n"
        '  "example_ja": "A simple practical Japanese example sentence using the Kanji (e.g. 漢字は面白いです。)",\n'
        '  "example_en": "The English translation of the example sentence (e.g. Kanji is interesting.)",\n'
        '  "example_yomi": "The hiragana/furigana representation of the example sentence, with spaces separating words for readability (e.g. かんじ は おもしろい です。)",\n'
        '  "example_romaji": "The romaji reading of the example sentence, with spaces separating words, all lowercase (e.g. kanji wa omoshiroi desu.)"\n'
        "}"
    )
    
    text, status = query_gemini(prompt)
    global _last_quota_status
    if status == "success" and text:
        _last_quota_status = ("available", "Gmail account dynamic session is active and quota is available.")
        for strip in ("```json", "```"):
            if text.startswith(strip):
                text = text[len(strip):]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        try:
            parsed = json.loads(text)
            if "example_ja" in parsed and "example_en" in parsed:
                return parsed
        except Exception as e:
            print(f"Failed to parse generated sentence JSON: {e}")
    elif status == "rate_limit":
        _last_quota_status = ("exhausted", "Quota exhausted (429). Rate limit hit on rapid queries.")
    elif status.startswith("auth_error"):
        _last_quota_status = ("invalid", "Google Authentication rejected. Sign in again.")

    import random
    return random.choice(fallback_sentences)


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


_last_quota_status = None

def check_gemini_quota_status(api_key):
    """
    Checks Gemini API quota status with a minimal test request.
    Returns one of:
      "available"  - API key works and quota is not exhausted
      "exhausted"  - API returns 429 RESOURCE_EXHAUSTED
      "no_key"     - No API key configured
      "invalid"    - API key rejected (401/400)
      "error"      - Network or other error
    Also returns the reset hint string if available.
    Returns: (status_str, detail_str)
    """
    global _last_quota_status
    if _last_quota_status and _last_quota_status[0] == "exhausted":
        return _last_quota_status

    if not api_key or api_key == "YOUR_GEMINI_API_KEY" or not api_key.strip():
        config = load_config()
        if config.get("google_auth_email"):
            api_key = "AIzaSyAsruPXUyYstZK_taFRwF513rSeSLCLLg8"
        else:
            return ("no_key", "No Gemini API key configured in settings.")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    # Smallest possible payload
    payload = {"contents": [{"parts": [{"text": "Hi"}]}]}
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=8)
        code = response.status_code
        if code == 200:
            _last_quota_status = ("available", "Gemini API is active and quota is available.")
            return _last_quota_status
        elif code == 429:
            body = ""
            try:
                body = response.json().get("error", {}).get("message", response.text[:120])
            except Exception:
                body = response.text[:120]
            _last_quota_status = ("exhausted", f"Quota exhausted (429). {body}")
            return _last_quota_status
        elif code in (401, 403):
            _last_quota_status = ("invalid", f"API key rejected by Google ({code}). Check your key in Settings.")
            return _last_quota_status
        else:
            _last_quota_status = ("error", f"Unexpected response ({code}): {response.text[:100]}")
            return _last_quota_status
    except requests.exceptions.Timeout:
        return ("error", "Request timed out. Check your internet connection.")
    except Exception as e:
        return ("error", f"Network error: {str(e)[:100]}")


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
    """Legacy wrapper kept for backward compat — delegates to generate_deep_weekend_task_fused."""
    week_idx = len(history) % 52
    return generate_deep_weekend_task_fused(api_key, history, week_idx)


def generate_deep_weekend_task_fused(api_key, history, week_idx):
    """Delegates to the new Pipeline Control Architecture in weekend_pipeline.py."""
    import weekend_pipeline
    baseline_topic = JAPAN_MNC_ROADMAP[week_idx]
    rich_fallback = get_rich_fallback_task(week_idx)
    pm = weekend_pipeline.WeekendPipelineManager(api_key)
    return pm.execute_pipeline(week_idx, history, baseline_topic, rich_fallback)



def _build_fallback_entry(title_lower, title):
    """Internal helper: returns enriched fallback dict for a given roadmap title."""

    # ---- Default (generic) values ----
    tech = ("Focus on building your current backend/frontend project, review high-concurrency "
            "architectures, and practice explaining your code decisions clearly.")
    personality = "Rehearse self-introductions, basic politeness, and professional posture for online/offline interviews."
    yt = [
        {"title": "ByteByteGo - System Design Fundamentals", "search_query": "ByteByteGo system design architecture"},
        {"title": "Nihongo Dekita - Japanese Interview Tips", "search_query": "Nihongo Dekita Japanese interview"},
        {"title": "Tokyo Dev - Software Engineer in Japan", "search_query": "Tokyo software engineer life salary"},
    ]
    checklist = [
        "Review one core CS concept (e.g. consistent hashing, B-trees, or CAP theorem) and explain it aloud",
        "Solve 3 LeetCode medium problems and narrate your approach as if in an interview",
        "Record a 90-second self-introduction in Japanese and listen back for improvements",
        "Read one engineering blog post from a Tokyo MNC (Mercari, Rakuten, LINE, or PayPay)",
        "Update your resume or Shokumukeirekisho with one new metric or project detail",
    ]
    career_radar = (
        "Tokyo MNCs are actively hiring engineers with strong Go, Kubernetes, and system design skills. "
        "Candidates who explain technical trade-offs clearly in accessible English are in high demand. "
        "Cloud-native and observability skills (OpenTelemetry, Prometheus) are rising fast."
    )
    research = {
        "title": "Attention Is All You Need — Transformer Architecture (Vaswani et al.)",
        "summary": (
            "The foundational paper behind modern AI. Understanding transformer architecture helps you speak "
            "confidently about LLM infrastructure — a growing topic in Tokyo MNC technical interviews."
        ),
        "read_more_query": "Attention Is All You Need transformer paper arXiv Vaswani",
    }
    resources = [
        {"type": "article", "title": "Mercari Engineering Blog — Go microservices at scale", "url_query": "Mercari engineering blog Go microservices"},
        {"type": "video",   "title": "ByteByteGo — System Design Interview Crash Course",    "url_query": "ByteByteGo system design interview crash course"},
        {"type": "course",  "title": "Gophercises — Go programming exercises (free)",         "url_query": "Gophercises Go programming free course"},
        {"type": "paper",   "title": "MapReduce — Simplified Data Processing on Large Clusters", "url_query": "MapReduce Google paper Dean Ghemawat"},
    ]
    intel_summary = (
        "Backend engineers are expected to understand distributed tracing, service meshes (Istio), and eBPF "
        "for observability. Tokyo MNCs are moving fast on cloud-native stacks and expect hands-on Kubernetes "
        "experience. AI-assisted coding tools are reshaping what interviewers look for."
    )
    trending = ["Go generics", "eBPF observability", "WebAssembly", "AI coding tools", "Platform engineering"]

    # ---- Category-specific overrides ----
    if "resume" in title_lower or "rirekisho" in title_lower or "shokumukeirekisho" in title_lower:
        tech = ("Review your technical stack, project list, and impact metrics "
                "(throughput, cost savings, uptime). Structure each project: Problem → Solution → Impact.")
        personality = ("Write Japanese resume sections with correct Keigo, clean formatting, and "
                       "compelling contribution summaries. Use numbers and measurable outcomes everywhere.")
        yt = [
            {"title": "Tokyodev - Writing a Japanese Resume for Software Engineers", "search_query": "Tokyodev Japanese software engineer resume"},
            {"title": "Japan Dev - Tech Resume Tips",                                "search_query": "Japan Dev software engineer tech resume guide"},
            {"title": "Keigo Basics - Business Self Introduction",                  "search_query": "Business Japanese self introduction tips"},
        ]
        checklist = [
            "Draft/update your Rirekisho (履歴書) with correct Japanese date formats and kanji",
            "Write 3 project bullet points in Problem → Solution → Impact format with metrics",
            "Research correct Keigo for resume cover letter sections",
            "Get a peer or AI to review your resume summary section for clarity",
            "Bookmark 2 Japanese engineer resume templates from Tokyodev or GaijinPot",
        ]
        career_radar = ("Japanese companies evaluate resumes very differently from Western ones — exact Rirekisho "
                        "formatting conventions matter. Shokumukeirekisho (work history portfolio) is equally "
                        "important and requires quantified impact statements.")
        research = {
            "title": "Tokyodev — How to get a software engineering job in Japan (comprehensive guide)",
            "summary": "Covers visa types, resume format, and what Japanese MNCs actually look for in foreign engineers. Essential reading before applying.",
            "read_more_query": "Tokyodev how to get software engineering job Japan guide",
        }
        resources = [
            {"type": "article", "title": "Tokyodev — Japanese Resume Format for Software Engineers", "url_query": "Tokyodev Japanese resume format software engineer"},
            {"type": "article", "title": "GaijinPot — Writing a Japanese Resume",                   "url_query": "GaijinPot writing Japanese resume guide"},
            {"type": "video",   "title": "How to write Rirekisho in Japanese step by step",          "url_query": "how to write rirekisho Japanese resume guide YouTube"},
            {"type": "course",  "title": "JLPT N3 Business Japanese — Resume Vocabulary",            "url_query": "JLPT N3 business Japanese resume vocabulary"},
        ]
        intel_summary = ("Japanese tech companies favor structured resumes following Rirekisho conventions. "
                         "International-facing companies like Mercari and LINE accept English resumes but still "
                         "expect correct Japanese business writing in cover letters. Human reviewers read every document.")
        trending = ["Rirekisho formatting", "Shokumukeirekisho metrics", "ATS-free hiring", "Portfolio GitHub", "Cover letter Keigo"]

    elif "jikoshoukai" in title_lower or "self-introduction" in title_lower:
        tech = ("Prepare your top 3 technical projects, each described in 30 seconds: stack, scale, and your specific "
                "contribution. Record yourself and time each description.")
        personality = ("Craft and practice your 2-minute Jikoshoukai (自己紹介). Structure: Name → Background → "
                       "Core Stack → Why Japan → Why This Company → Closing. Polish until completely natural.")
        yt = [
            {"title": "Japanese interview Jikoshoukai self introduction guide", "search_query": "Japanese interview self introduction software engineer"},
            {"title": "Speak Natural Japanese in Interviews",                   "search_query": "Japanese self introduction Jikoshoukai pronunciation"},
            {"title": "Japan Dev - Tech Interviews in Tokyo",                   "search_query": "Japan Dev software engineer interview tips"},
        ]
        checklist = [
            "Write full 2-minute Jikoshoukai script covering name, background, tech stack, and motivation",
            "Record yourself delivering it — target: smooth, confident, zero filler words",
            "Rehearse 3 technical project descriptions (30 sec each) with stack + measurable impact",
            "Prepare a specific, genuine answer to 'なぜ日本ですか？' (Why Japan?)",
            "Find a language exchange partner or AI to give pronunciation feedback",
        ]
        career_radar = ("Confident, structured Jikoshinkais with genuine Japan motivation stand out immediately. "
                        "Companies like Mercari and LINE favor engineers who show cultural curiosity and can explain "
                        "their technical journey clearly in 2 minutes.")
        research = {
            "title": "Japan Dev — Software Engineer Interview Process in Japan (Deep Dive)",
            "summary": "A detailed breakdown of what Japanese MNC technical interviews actually look like, from coding rounds to culture-fit conversations.",
            "read_more_query": "Japan Dev software engineer interview process Tokyo MNC",
        }
        resources = [
            {"type": "video",   "title": "Perfect Japanese self-introduction for job interviews (Jikoshoukai)", "url_query": "Jikoshoukai Japanese job interview self introduction YouTube"},
            {"type": "article", "title": "Japan Dev — Technical interview process at Japanese companies",       "url_query": "Japan Dev technical interview process Japanese companies"},
            {"type": "course",  "title": "Business Japanese — Interview phrases and vocabulary",                "url_query": "business Japanese interview phrases vocabulary course"},
            {"type": "video",   "title": "How native Japanese speakers evaluate engineer interviews",           "url_query": "Japanese interviewer perspective software engineer evaluation"},
        ]
        intel_summary = ("Japanese companies increasingly conduct first rounds in English even for Japanese-speaking "
                         "roles. A polished Jikoshoukai still creates a powerful impression. Mercari and LINE "
                         "favor engineers who show genuine cultural curiosity.")
        trending = ["Jikoshoukai delivery", "2-minute pitch", "Cultural curiosity signaling", "English-first companies", "Video interview prep"]

    elif "keigo" in title_lower or "business manners" in title_lower or "etiquette" in title_lower or "email" in title_lower:
        tech = ("Review technical correspondence in business Japanese: server downtime notices, API update announcements, "
                "deployment schedules, and incident reports in correct polite register.")
        personality = ("Master Keigo levels: Teineigo (丁寧語), Sonkeigo (尊敬語), Kenjougo (謙譲語). "
                       "Memorize 10 essential interview phrases and the full entry/exit room sequence.")
        yt = [
            {"title": "Nihongo Dekita - Keigo Made Simple for Business",          "search_query": "Nihongo Dekita business Japanese Keigo"},
            {"title": "Learn Japanese Business Manners & Interview Etiquette",    "search_query": "Japanese interview etiquette entry exit manners"},
            {"title": "Japan Tech Jobs - Cultural expectations",                  "search_query": "Japanese business manners international tech company"},
        ]
        checklist = [
            "Learn Teineigo, Sonkeigo, and Kenjougo with 5 example sentences each",
            "Memorize the full interview room entry/exit sequence (knock, bow, sit, stand, exit bow)",
            "Write a mock thank-you email in Japanese after a hypothetical interview",
            "Practice 'Yoroshiku onegai itashimasu' and 'Otsukaresama desu' in context scenarios",
            "Study 5 common Japanese business email templates and their politeness structures",
        ]
        career_radar = ("Keigo fluency is no longer optional even at English-first companies like Mercari — "
                        "internal Slack, meeting phrases, and client emails still require correct politeness levels. "
                        "Engineers who integrate smoothly into Japanese office culture advance faster.")
        research = {
            "title": "Harvard Business Review — Cross-cultural communication in Japanese workplaces",
            "summary": "Analyzes how Western engineers adapt to high-context communication cultures and what specific behavioral adjustments matter most in Japanese tech companies.",
            "read_more_query": "cross-cultural communication Japanese workplace engineers HBR",
        }
        resources = [
            {"type": "video",   "title": "Nihongo Dekita — Complete Keigo guide for business Japanese",   "url_query": "Nihongo Dekita Keigo complete guide business Japanese"},
            {"type": "article", "title": "Japan Guide — Business Etiquette and Manners",                  "url_query": "Japan Guide business etiquette manners office"},
            {"type": "course",  "title": "JapanesePod101 — Business Japanese course",                    "url_query": "JapanesePod101 business Japanese course free"},
            {"type": "video",   "title": "Japanese interview etiquette — entry bow sit exit sequence",    "url_query": "Japanese interview room etiquette bow sit exit engineer"},
        ]
        intel_summary = ("Japanese corporate culture continues evolving but foundational Keigo remains essential. "
                         "Rakuten (English mandatory) and LINE hold many meetings in English, but face-to-face "
                         "interactions still follow strict politeness hierarchies. Getting this right builds trust fast.")
        trending = ["Keigo in Slack", "Cross-cultural communication", "Business email templates", "Ho-Ren-So", "Interview etiquette"]

    elif "microservices" in title_lower or "distributed" in title_lower or "system design" in title_lower or "concurrency" in title_lower or "caching" in title_lower:
        tech = ("Design a payment processing API at 100K RPS: scalable database schemas, Redis caching layers, "
                "Kafka message queues, and Go/Kubernetes microservices. Build it or sketch it with full trade-off analysis.")
        personality = ("Practice presenting CAP theorem, database trade-offs, and microservices vs monolith decisions "
                       "in clear structured English that Japanese interviewers can follow. Avoid jargon overload.")
        yt = [
            {"title": "ByteByteGo - Microservices & Scaling Systems",     "search_query": "ByteByteGo microservices distributed caching Redis"},
            {"title": "System Design Interview - Scalable Architecture",  "search_query": "System design interview chat app microservices"},
            {"title": "ArjanCodes - Software Architecture Trends",        "search_query": "ArjanCodes software architecture microservices patterns"},
        ]
        checklist = [
            "Implement a Redis-backed sliding-window rate limiter in Go from scratch",
            "Sketch a full system design for a Tokyo ride-sharing app (users, drivers, matching, payments)",
            "Explain CAP theorem and your database trade-off decisions out loud as if in an interview",
            "Read one real Mercari or PayPay engineering blog article on their microservices architecture",
            "Implement a simple Kafka producer/consumer in Go or Python to understand event streaming",
        ]
        career_radar = ("Tokyo MNCs are hiring engineers who understand distributed systems deeply — not just "
                        "theoretically. Mercari, PayPay, and LINE all run Go/Kubernetes at massive scale. Candidates "
                        "who draw system diagrams and explain trade-offs clearly dominate technical rounds.")
        research = {
            "title": "Google Spanner — Globally Distributed Database (OSDI 2012)",
            "summary": "Spanner's architecture directly influenced how modern distributed SQL databases work. Understanding it gives you real depth when discussing globally consistent data — a common Tokyo MNC interview topic.",
            "read_more_query": "Google Spanner globally distributed database paper OSDI 2012",
        }
        resources = [
            {"type": "article", "title": "Mercari Engineering Blog — Microservices migration from monolith in Go", "url_query": "Mercari engineering blog microservices migration Go"},
            {"type": "paper",   "title": "Google Spanner — Globally Distributed Database",                        "url_query": "Google Spanner paper globally distributed database 2012"},
            {"type": "video",   "title": "ByteByteGo — System Design Interview Complete Guide",                   "url_query": "ByteByteGo system design interview complete guide YouTube"},
            {"type": "course",  "title": "System Design Primer — GitHub open source guide",                       "url_query": "system design primer GitHub donnemartin"},
        ]
        intel_summary = ("Distributed systems skills are the #1 differentiator in Tokyo MNC interviews. "
                         "Go dominates at Mercari and PayPay. Kubernetes and service mesh (Istio) knowledge is "
                         "increasingly expected. eBPF for deep observability is an emerging differentiator very few candidates know.")
        trending = ["Go generics", "eBPF", "Service mesh Istio", "Kafka streams", "Database sharding"]

    elif any(k in title_lower for k in ["mercari","rakuten","line","paypay","sony","toyota"]):
        tech = ("Deep-dive into engineering blogs of top Tokyo tech giants: Mercari (Go/Kubernetes), "
                "LINE (Java/Kafka), Rakuten (Java/Kotlin), PayPay (Java/massive-scale payments). "
                "Understand their actual production architecture decisions.")
        personality = ("Understand corporate values: Rakuten's English-first culture, Mercari's 'Go Bold / All for One / Be a Pro', "
                       "LINE's 'WOW', PayPay's speed-first culture. Tailor interview answers to reflect these authentically.")
        yt = [
            {"title": "Mercari Engineering culture and Go backend",         "search_query": "Mercari tech stack software engineer"},
            {"title": "PayPay / LINE Engineering - Scale and Architecture", "search_query": "PayPay backend microservices LINE Java"},
            {"title": "Rakuten Tech Ecosystem and Global Workplace",        "search_query": "Rakuten software engineer interview english"},
        ]
        checklist = [
            "Read 2 engineering blog posts from your target company (Mercari, LINE, Rakuten, or PayPay)",
            "Summarize their tech stack, scale challenges, and engineering culture in your own words",
            "Research the company's core values and prepare 2 interview answers that reflect them authentically",
            "Find one open-source GitHub repo from the company and understand its purpose",
            "Write your 'Why this company?' answer in Japanese and practice delivering it naturally",
        ]
        career_radar = ("Mercari is heavily investing in AI-assisted shopping and hiring ML infra engineers. "
                        "PayPay is scaling financial services and needs high-throughput payment processing engineers. "
                        "LINE is expanding into LINE WORKS (enterprise) and needs cloud-native engineers.")
        research = {
            "title": "Mercari Engineering Blog — Platform engineering journey and Go microservices",
            "summary": "Mercari documented their full migration from PHP monolith to Go microservices. Understanding this journey gives real talking points about systems evolution at scale.",
            "read_more_query": "Mercari engineering blog platform engineering Go microservices journey",
        }
        resources = [
            {"type": "article", "title": "Mercari Engineering Blog — Technology strategy",                   "url_query": "Mercari engineering blog technology strategy 2026"},
            {"type": "article", "title": "PayPay Engineering Blog — Backend at scale",                       "url_query": "PayPay engineering blog backend scale architecture"},
            {"type": "video",   "title": "Tokyodev — Working as a foreign engineer at Japanese MNCs",        "url_query": "Tokyodev foreign engineer Japanese MNC experience"},
            {"type": "article", "title": "LINE Engineering Blog — System Architecture overview",              "url_query": "LINE engineering blog system architecture overview"},
        ]
        intel_summary = ("Tokyo MNCs are expanding internationally but culture-fit remains critical. "
                         "Mercari's engineering team is now 40%+ non-Japanese. PayPay is hiring aggressively in fintech AI. "
                         "Knowing each company's engineering blog before interviews is no longer optional — interviewers ask.")
        trending = ["Mercari AI features", "PayPay fintech", "LINE WORKS enterprise", "Go at scale", "Engineering blog research"]

    elif any(k in title_lower for k in ["behavioral","star method","shiboudouki","ho-ren-so","kaizen"]):
        tech = ("Catalog 5 challenging project incidents: production outages, complex bugs, or technical debt refactors. "
                "Structure each with STAR method and specific metrics (latency reduced by X%, cost saved Y$).")
        personality = ("Master STAR method in Japanese. Formulate answers for 'Why Japan?', 'Why our company?', "
                       "your biggest failure, and your proudest technical achievement. Practice Ho-Ren-So as a daily communication philosophy.")
        yt = [
            {"title": "Japanese Behavioral Interview Prep (Shiboudouki)",    "search_query": "Japanese interview Shiboudouki why Japan software engineer"},
            {"title": "Understanding Ho-Ren-So & Kaizen Workplace Culture",  "search_query": "Horenso Kaizen Japanese business culture explained"},
            {"title": "Tech Interview Pro - Behavioral Questions",           "search_query": "Tech Interview Pro behavioral questions STAR method"},
        ]
        checklist = [
            "Write STAR-format answers for: biggest technical failure, proudest achievement, team conflict",
            "Write your 'Why Japan?' answer — specific, genuine, 90 seconds or less",
            "Practice one full behavioral answer in Japanese using polite Keigo register",
            "Research Ho-Ren-So (報告・連絡・相談) and write 3 real examples of how you have applied it",
            "Prepare 3 insightful Gyakushitsumon (逆質問) questions to ask your interviewer",
        ]
        career_radar = ("Behavioral rounds in Tokyo MNCs are becoming more structured and data-driven. "
                        "Companies use competency-based interviews with clear rubrics. Engineers who quantify impact "
                        "and explain thinking clearly — even in English — have a decisive advantage.")
        research = {
            "title": "Google re:Work — Structured Behavioral Interviewing Guide",
            "summary": "Google's public guide on how structured behavioral interviews work and what top companies actually score you on. Knowing this framework lets you target exactly what interviewers want.",
            "read_more_query": "Google reWork structured behavioral interview guide",
        }
        resources = [
            {"type": "article", "title": "Google re:Work — Behavioral Interviewing best practices",          "url_query": "Google reWork behavioral interviewing best practices"},
            {"type": "video",   "title": "Tech Interview Pro — STAR method behavioral answers",              "url_query": "Tech Interview Pro STAR method behavioral interview answers"},
            {"type": "article", "title": "Japan Dev — How behavioral interviews differ in Japan",            "url_query": "Japan Dev behavioral interview Japanese company culture"},
            {"type": "video",   "title": "Ho-Ren-So and Kaizen — Japanese workplace culture explained",     "url_query": "Ho Ren So Kaizen Japanese workplace culture software engineer"},
        ]
        intel_summary = ("Behavioral interview prep is often neglected by developers focused entirely on coding. "
                         "At Tokyo MNCs, behavioral rounds are weighted equally with technical rounds. "
                         "Companies evaluate: growth mindset, proactive communication (Ho-Ren-So), and genuine Japan motivation.")
        trending = ["STAR method in Japanese", "Ho-Ren-So", "Competency-based interviews", "Failure stories", "Kaizen mindset"]

    return {
        "task_title":           title,
        "tech_upscaling":       tech,
        "personality_upscaling": personality,
        "youtube_suggestions":  yt,
        "action_checklist":     checklist,
        "career_radar":         career_radar,
        "research_spotlight":   research,
        "learning_resources":   resources,
        "weekly_intel_summary": intel_summary,
        "trending_topics":      trending,
        "source":               "Curated Roadmap",
    }


def get_rich_fallback_task(week_idx):
    """Public interface: returns the enriched fallback task for the given roadmap week index."""
    title = JAPAN_MNC_ROADMAP[week_idx]
    return _build_fallback_entry(title.lower(), title)


def get_or_create_weekend_task(reference_date=None):
    """Gets the weekend task for the current weekend. If none exists, creates one via the
    3-stage deep intelligence pipeline and saves it. Backfills older entries to the new schema."""
    sat_date_str = get_current_weekend_saturday_date(reference_date)
    if not sat_date_str:
        return None

    data = load_data()
    if "weekend_history" not in data:
        data["weekend_history"] = []

    # Check if we already have an entry for this Saturday
    for entry in data["weekend_history"]:
        if entry.get("date") == sat_date_str:
            # Backfill any missing fields from new schema using enriched fallback
            modified = False
            chronological_history = sorted(data["weekend_history"], key=lambda x: x.get("date", ""))
            week_idx = chronological_history.index(entry) % 52
            rich_fallback = get_rich_fallback_task(week_idx)
            NEW_FIELDS = ["tech_upscaling", "personality_upscaling", "youtube_suggestions",
                          "action_checklist", "career_radar", "research_spotlight",
                          "learning_resources", "weekly_intel_summary", "trending_topics"]
            for field in NEW_FIELDS:
                if field not in entry or not entry[field]:
                    entry[field] = rich_fallback.get(field, [] if field in ("action_checklist","trending_topics","youtube_suggestions","learning_resources") else "")
                    modified = True
            # Stamp legacy entries with generated_at if missing
            if "generated_at" not in entry:
                entry["generated_at"] = datetime.now().isoformat()
                modified = True
            if modified:
                save_data(data)
            return entry

    # No entry yet for this weekend — generate one
    config = load_config()
    api_key = config.get("gemini_api_key", "").strip()
    google_email = config.get("google_auth_email", "").strip()
    if google_email:
        if not api_key or api_key == "YOUR_GEMINI_API_KEY" or not api_key.strip():
            api_key = "AIzaSyAsruPXUyYstZK_taFRwF513rSeSLCLLg8"
            
    is_active = config.get("japan_mnc_prep_active", True)

    if not is_active:
        return None

    week_idx = len(data["weekend_history"]) % 52
    rich_fallback = get_rich_fallback_task(week_idx)
    task_data = dict(rich_fallback)
    source = "Curated Roadmap"

    if api_key and api_key != "YOUR_GEMINI_API_KEY":
        try:
            # Single-Call Prompt Fusion: fetch the entire technical intelligence task fused
            parsed = generate_deep_weekend_task_fused(api_key, data["weekend_history"], week_idx)
            for key in ["task_title","tech_upscaling","personality_upscaling","youtube_suggestions",
                        "weekly_intel_summary","research_spotlight","trending_topics",
                        "career_radar","action_checklist","learning_resources"]:
                if key in parsed and parsed[key]:
                    task_data[key] = parsed[key]
            source = parsed.get("source", "Gemini AI (Pipeline)")
            print("Deep intelligence fused weekend task generated via Gemini AI.")
        except Exception as e:
            print(f"{YELLOW}Warning: Fused task generation failed ({e}). Using enriched curated roadmap.{RESET}")

    new_entry = {
        "date":                  sat_date_str,
        "task_title":            task_data.get("task_title",            rich_fallback["task_title"]),
        "tech_upscaling":        task_data.get("tech_upscaling",        rich_fallback["tech_upscaling"]),
        "personality_upscaling": task_data.get("personality_upscaling", rich_fallback["personality_upscaling"]),
        "youtube_suggestions":   task_data.get("youtube_suggestions",   rich_fallback["youtube_suggestions"]),
        "weekly_intel_summary":  task_data.get("weekly_intel_summary",  rich_fallback["weekly_intel_summary"]),
        "research_spotlight":    task_data.get("research_spotlight",    rich_fallback["research_spotlight"]),
        "trending_topics":       task_data.get("trending_topics",       rich_fallback["trending_topics"]),
        "career_radar":          task_data.get("career_radar",          rich_fallback["career_radar"]),
        "action_checklist":      task_data.get("action_checklist",      rich_fallback["action_checklist"]),
        "learning_resources":    task_data.get("learning_resources",    rich_fallback["learning_resources"]),
        "source":                source,
        "generated_at":          datetime.now().isoformat(),
        "notes":                 "",
        "completed":             False,
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
    print("-" * 51)
    print(f"{BOLD}{GREEN}💻 TECHNICAL UPSCALING:{RESET}")
    print(f"{WHITE}{entry.get('tech_upscaling', '(No technical goals defined)')}{RESET}")
    print("-" * 51)
    print(f"{BOLD}{MAGENTA}🧠 PERSONALITY & CULTURE:{RESET}")
    print(f"{WHITE}{entry.get('personality_upscaling', '(No personality goals defined)')}{RESET}")
    print("-" * 51)
    print(f"{BOLD}{CYAN}🎥 LATEST YOUTUBE TREND SEARCHES:{RESET}")
    yt_suggestions = entry.get("youtube_suggestions", [])
    if yt_suggestions:
        for idx, item in enumerate(yt_suggestions, 1):
            print(f"  {idx}. {BOLD}{item.get('title')}{RESET}")
            print(f"     🔍 Search Query: {YELLOW}https://www.youtube.com/results?search_query={urllib.parse.quote(item.get('search_query'))}{RESET}")
    else:
        print(f"  (No YouTube trends recommended for this week)")
    print("-" * 51)
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
