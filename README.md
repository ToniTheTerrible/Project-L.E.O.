# Project L.E.O.

A locally-executed, tactical AI assistant built on Open Interpreter, with a hybrid cloud/local LLM backend, a custom sci-fi HUD, voice-free hands-free triggers (hotkey + whistle detection), and real browser/system control.

## Overview

L.E.O. runs as a command-line assistant with a Tkinter splash screen HUD. It defaults to a cloud LLM (Groq) for speed and quality, automatically falling back to a local model (via Ollama) if there's no internet connection. It can execute PowerShell/Python for file operations, control system volume, browse the web and control YouTube through a real Chrome window, take and describe screenshots, and pull images from Unsplash — all through natural-language commands.

## Requirements

- Windows 10/11 (64-bit — required for Win32 API window centering and audio)
- Python 3.10+
- Google Chrome installed
- [Ollama](https://ollama.com) installed, for the local fallback model and vision model
- Internet access for cloud mode (Groq, CoinGecko, Unsplash); not required for local mode

## Setup

**1. Install Python dependencies:**
```powershell
pip install open-interpreter pycaw comtypes requests selenium sounddevice numpy ollama pillow
```

**2. Pull local models via Ollama:**
```powershell
ollama pull qwen3:8b
ollama pull moondream
```

**3. Create your own `config.py`** in the project folder (this file is git-ignored and never committed — you must create it yourself on each machine you run this on):
```python
GROQ_API_KEY = "your_groq_api_key"
UNSPLASH_ACCESS_KEY = "your_unsplash_access_key"
```

**4. Run it:**
```powershell
python leo.py
```
or use `leo.bat`, which is what the hotkey and whistle triggers actually launch.

## Architecture

- **`leo.py`** — main entry point: HUD splash screen, Open Interpreter setup, hybrid backend switching, terminal chat loop.
- **`browser.py`** — browser control module. Attaches to a real Chrome instance via remote debugging (a dedicated profile, `LEOProfile`) so browser tasks reuse one persistent tab/session across commands instead of opening new windows each time. Exposes `browse(url)` for general sites and `youtube_search(query)` for YouTube specifically.
- **`config.py`** — holds API keys, excluded from git via `.gitignore`. Must be recreated manually on any new machine.
- **`whistle.py`** — background listener using FFT-based pitch detection on the default microphone; launches `leo.bat` when a sustained whistle in the 1200–3000 Hz range is detected. Runs at Windows login via a shortcut in the Startup folder, pointing at `leo_whistle.vbs`.
- **`leo_whistle.vbs`** — silently launches `whistle.py` with `pythonw.exe` (no visible console window) at startup.
- **`leo.bat`** — sets the working directory and launches `leo.py`; also used directly by the ROG key hotkey binding (via GHelper).
- **`boot.wav`** — startup sound played asynchronously alongside the HUD splash animation.

## LLM Backend

L.E.O. runs a hybrid setup:
- **Cloud (default):** Groq, running `openai/gpt-oss-20b`.
- **Local (automatic fallback):** Ollama, running `qwen3:8b`, used automatically when no internet connection is detected.
- **Vision (screen description):** Ollama, running `moondream`, used locally regardless of which backend is active — this keeps vision tasks free and independent of Groq's model availability.

Backend switching is connection-based and automatic by default (`auto` mode). Manual override commands are available in the chat loop: `cloud on`, `cloud off`, `auto`.

## Triggers

- **ROG key**, bound via GHelper to: `wt.exe cmd.exe /k "C:\Users\Toniz\Desktop\Project-LEO\leo.bat"`
- **Whistle detection**, running persistently in the background from Windows Startup.

## Capabilities

- File and folder operations (via PowerShell)
- System volume control (via `pycaw`)
- Cryptocurrency price lookups (via CoinGecko API)
- General web browsing and YouTube search/playback (via Selenium + a real Chrome window)
- Screen capture and description (via `moondream`, local)
- Image search and download (via Unsplash API)

## Version History

See `/old versions` for the full changelog of prior iterations, from the initial CLI release through HUD development, audio, native browser control, screen reading, hybrid auto-mode, and whistle activation.