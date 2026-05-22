# 🛡️ Project Guardian: Unified Habit, Commit, and Advanced Japanese learning Suite

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)]()

**Project Guardian** is an elite, high-fidelity productivity and learning application suite designed specifically for Windows. It integrates automated daily habit auditing and GitHub commit checking with a state-of-the-art Japanese Language & Kanji Academy—complete with native AI Speech-to-Speech voice conversation practice and instant deep linguistic analysis.

The suite consists of three interconnected systems operating seamlessly off a shared database:
1. 🛡️ **Guardian Dashboard (`guardian_gui.py` / `guardian.py`)**: A premium habit checklist and automated daily Git auditor with compliance trackers.
2. 🎓 **Japanese Academy (`japanese_learning_app.py`)**: A full-sized learning application mapping lessons, flashcards, sentence builders, and AI speech practice to specific JLPT levels.
3. 📌 **Kanji Desktop Widget (`kanji_widget.py`)**: An always-on-top, frameless desktop flashcard companion with automatic focus-stealing pop-up quizzes.

---

## 🎨 Premium Apple Space Black Design & Dracula Aesthetics

The entire suite is crafted with gorgeous, high-contrast, distraction-free modern aesthetics:
* **Color Palette**: A curated fusion of **Apple Space Black** (`#09090B` backgrounds, `#121214` space cards, `#1C1C1E` inner dark frames, and Royal Blue `#0071E3` accents) and **Dracula Dark Mode** elements for maximum visual comfort.
* **Micro-Animations**: Features fluid-motion dynamic progress bars scrolling at 60fps, glowing green borders when tasks are completed, hover scaling, and asynchronous fading flashes on button triggers.
* **Acoustic feedback**: Real-time asynchronous chimes via standard library `winsound` play sweet auditory confirmations the instant tasks are completed or quizzes are correct.

---

## 🚀 Key Systems & Core Features

### 1. 🎓 Japanese Language & Kanji Academy (`japanese_learning_app.py`)
A full-screen interactive space dedicated to comprehensive Japanese learning, structured around standard **JLPT Levels (N5 to N1)**:
* **Global Difficulty Selector**: Instantly switches active levels to recalibrate available grammar lessons, studied Kanji decks, sentence puzzles, and AI tutor complexity.
* **Kanji Explorer & Progressive Generator**: 
  * Displays studied Kanji characters marked with a green checkmark (`✓`) and unstudied ones showing a locked padlock (`🔒`).
  * Features an **Asynchronous progressive AI generator** utilizing Gemini to dynamically create, parse, and add new studied Kanji to your deck matching your exact level without duplicates.
* **Grammar Hub & Interactive Sentence Builder**: Clickable grammar word pills designed with neon glowing hover states that let you construct Japanese sentences dynamically. Validates syntactic structure instantly with visual and acoustic rewards.
* **⚡ Fluid-Motion SRS Reviews**: Shuffled spaced repetition flashcards that slide open with a 150ms height transition to reveal detailed Kunyomi, Onyomi, and vocabulary readings.

### 2. 🎙️ Native Speech-to-Speech & 💡 Deep Explanations (Sensei Mode)
Our state-of-the-art conversational engine gives you access to a native Japanese Sensei directly on your desktop:
* **🎙️ WinMM.dll Audio Recording (Speech-to-Speech)**: Allows you to speak directly into your microphone. It executes thread-safe background recording using native Windows Multimedia commands through PowerShell. **No buggy external Python audio packages (like `PyAudio` or `sounddevice`) are required.**
* **Ticking Countdown State**: The purple record button transitions to a pulsing crimson **`🔴 REC (5s)...`** ticking down in real-time, locking out inputs while you speak.
* **Multimodal API Integration**: Encodes recorded WAV files to base64, submitting them directly to **Gemini 2.5 Flash** for high-fidelity speech transcription, grammar correction, and natural Japanese response.
* **💡 Inline Deep Explanation Panels**: Click the **`💡 EXPLAIN`** button on any Sensei message bubble to pop open an inline Space-Black modal container that breaks down the response into:
  1. **Grammar & Structure**: Analysis of sentence structures and verb stem conjugations.
  2. **Vocabulary & Readings**: Deep definitions and Hiragana/Romaji transcriptions for all kanji.
  3. **Particles**: Exhaustive description of particles used (e.g. は, が, を, に, ね).
  4. **Formality & Nuance**: Guidance on politeness registers (Keigo, casual, polite) and situational contexts.
* **Offline branching trees**: Includes structured offline scenarios (e.g., "At a Japanese Restaurant", "Hotel Check-In") pre-populated with explanations, so you can study even when offline.

### 3. 📌 Frameless Desktop Kanji Widget (`kanji_widget.py`)
A custom, frameless study companion that anchors directly to your desktop:
* **Always-on-Top & Dragging**: Toggle window pinning with `📌` and drag it anywhere on your screen.
* **⚡ Asynchronous Pre-fetching**: Instantly loads cards in `<1ms` by maintaining an asynchronous background pre-fetch cache buffer.
* **Slow Speed Toggle (`🐢 SLOW`)**: Adjusts voice synthesis pace by 40% for perfect syllable parsing and listing comprehension.
* **⏰ Focus-Stealing Pop-Up Quizzes**: Steals active focus at configurable intervals (1–60 mins) centering a topmost multiple-choice question on screen, dynamically adjusting your studied card's SRS interval based on your response.

---

## 🛠️ Technology Stack & Architecture

* **UI Engine**: Native Tkinter + Canvas, fully customized with flat borders, hover bindings, and responsive layouts.
* **Voice Synthesis (TTS)**: Dual-pipeline speech synthesis. Fetches high-fidelity native audio from Google TTS (primary) or falls back to standard Windows SAPI (`System.Speech.Synthesis`) offline, rendering silently in the background using hidden Windows Media Player COM handles.
* **Voice Capture (STT)**: Native PowerShell commands targeting `winmm.dll` MCI sound recording.
* **AI Engine**: Gemini 2.5 API via custom structured JSON REST payloads.
* **Database**: Bidirectional real-time local tracking via `kanji_data.json` and `guardian_data.json`.

---

## 📦 Setup & Installation

### Prerequisites
* Windows OS
* Python 3.8 or higher installed on your system.

### 1. Clone the Repository
```powershell
git clone https://github.com/aditya-dev06/project-gurdian.git
cd project-gurdian
```

### 2. Install Python Dependencies
Create a virtual environment (recommended) and install the necessary dependencies:
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```
*(Dependencies include: `requests` and `pillow`. Zero external audio compile packages are required!)*

### 3. Configure API Credentials
Create a `config.json` file in the root folder (or use the main settings panel inside the GUI):
```json
{
  "gemini_api_key": "YOUR_GEMINI_API_KEY_HERE",
  "github_username": "YOUR_GITHUB_USERNAME",
  "startup_enabled": true
}
```

### 4. Running the Applications
Run any of the suite modules directly from your shell:

* **To launch the Unified Habit & Commit Dashboard**:
  ```powershell
  python guardian_gui.py
  ```
* **To launch the Standalone Japanese Academy**:
  ```powershell
  python japanese_learning_app.py
  ```
* **To launch the Desktop Companion Widget**:
  ```powershell
  python kanji_widget.py
  ```

---

## ⌨️ Command Line Interface (CLI) Reference

Project Guardian features a robust, color-coded CLI companion (`guardian.py`) that can be executed directly from PowerShell:

| Command | Description | Example |
| :--- | :--- | :--- |
| `python guardian.py status` | Prints a visual board of all habits with live GitHub commit check | `python guardian.py status` |
| `python guardian.py done [task]` | Marks a specific manual daily task as completed | `python guardian.py done dsa` |
| `python guardian.py stats` | Displays habit compliance metrics (7-day/30-day perfect streaks) | `python guardian.py stats` |
| `python guardian.py schedule` | Registers daily background task scheduler jobs in Windows | `python guardian.py schedule` |
| `python guardian.py unschedule` | Safely removes background jobs from Windows Task Scheduler | `python guardian.py unschedule` |
| `python guardian.py test-warn` | Instantly dispatches a test priority notification alert | `python guardian.py test-warn` |

---

## 📂 File Structure

```
guardian-tracker/
├── guardian.py               # CLI Task Runner, Scheduler, and Git Auditor
├── guardian_gui.py           # Unified Habits & Compliance Dashboard (GUI)
├── guardian_data.json        # Stored local habit histories and logs
├── japanese_learning_app.py  # Standard-grade JLPT Japanese Learning Academy
├── kanji_widget.py           # Desktop Frameless Companion Widget with pop-up quizzes
├── kanji_data.json           # SRS studied kanji vocab and grammar databases
├── record_audio.ps1          # Background audio capture utility script
└── config.json               # Local API Keys and GitHub configuration
```

---

## 🔒 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

*Developed with 💙 for premium desktop learning and flawless habit tracking.*
