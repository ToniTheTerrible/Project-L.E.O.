# Project L.E.O.

**L.E.O. — Local Electronic Operator.** A personal, JARVIS-style AI assistant for Windows, built on [Open Interpreter](https://github.com/OpenInterpreter/open-interpreter). L.E.O. takes natural-language commands, writes and runs code to carry them out, and answers in a short spoken sentence. It runs in a terminal behind a custom sci-fi HUD splash screen and can be launched hands-free with a hotkey or a whistle.

## Capabilities

- File and folder operations (PowerShell)
- System volume control (`pycaw`)
- Web search (DuckDuckGo via `ddgs`)
- Browser control and YouTube playback through a real, persistent Chrome session (Selenium)
- Screen description with a local vision model (`moondream`)
- Image search and download (Unsplash API)
- Sending and reading email (Gmail SMTP/IMAP)
- Persistent personal memory stored in Google Drive
- Spoken responses (`edge-tts`)

## LLM backend

- **Cloud (default):** Anthropic Claude Haiku 4.5 through prepaid API credit. Change the model with `CLOUD_MODEL` at the top of `leo.py`.
- **Local (automatic fallback):** Ollama running `qwen3:8b`, used when no internet connection is detected.
- **Vision:** Ollama running `moondream`, always local.

Switching is automatic by default. Manual commands in the chat loop: `cloud on`, `cloud off`, `auto`.

## Requirements

- Windows 10/11 (64-bit)
- Python 3.10+
- Google Chrome
- [Ollama](https://ollama.com)

## Setup

**1. Install dependencies**
```powershell
pip install open-interpreter pycaw comtypes requests selenium sounddevice numpy ollama pillow edge-tts pygame ddgs google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

**2. Pull the local models**
```powershell
ollama pull qwen3:8b
ollama pull moondream
```

**3. Create `config.py`** in the project folder. It is git-ignored and never committed, so you must create it on each machine:
```python
ANTHROPIC_API_KEY = "your_anthropic_key"
UNSPLASH_ACCESS_KEY = "your_unsplash_access_key"
EMAIL_SENDER = "you@gmail.com"
EMAIL_PASSWORD = "your_gmail_app_password"
EMAIL_RECEIVER = "default_recipient@gmail.com"

# Optional but recommended: restrict who L.E.O. can email
# ALLOWED_RECIPIENTS = ["friend@gmail.com"]
```

**4. Google Drive memory (optional)**
Create a Google Cloud project, enable the Drive API, create an OAuth client of type *Desktop app*, and save the download as `credentials.json` in the project folder. The first run opens a browser login and creates `token.json`. Both files are git-ignored.

**5. Run**
```powershell
python leo.py
```
or double-click `leo.bat`, which is what the triggers launch.

## Files

| File | Purpose |
|---|---|
| `leo.py` | Entry point: HUD splash, Open Interpreter setup, backend switching, chat loop |
| `browser.py` | Persistent Chrome control via remote debugging (dedicated `LEOProfile`) |
| `vision.py` | Screenshot capture and description with `moondream` |
| `search_module.py` | Web search |
| `email_module.py` | Send and read email, with an attachment security guard and optional recipient allowlist |
| `drive_memory.py` | Persistent personal memory in Google Drive (`remember` / `recall`) |
| `voice.py` | Text-to-speech queue using `edge-tts` and `pygame` |
| `whistle.py` | Background whistle detector (FFT, 1200-3000 Hz) that launches `leo.bat` |
| `leo_whistle.vbs` | Silently launches `whistle.py` at login |
| `leo.bat` | Launches `leo.py` from its own folder |
| `boot.wav` | Startup sound |
| `old versions/` | Changelog snapshots of earlier versions |

## Triggers

- **ROG key** (via GHelper): `wt.exe cmd.exe /k "<path to project>\leo.bat"`
- **Whistle:** a shortcut to `leo_whistle.vbs` in the Windows Startup folder (`shell:startup`)

All scripts locate their own folder at runtime. If you move the project, only the GHelper command and the Startup shortcut need updating.

## Security notes

- L.E.O. runs with `auto_run = True`: it executes the code it writes **without asking for confirmation**. Run it only on a machine you control.
- API keys live only in `config.py`. `config.py`, `credentials.json` and `token.json` are git-ignored.
- Text from emails and web search is treated as untrusted. The prompt tells the model not to follow instructions found in it, and `email_module.py` blocks attaching project files and anything named like a credential.
- Set `ALLOWED_RECIPIENTS` to restrict who L.E.O. can email.

## Troubleshooting

- **Whistle stops working after an edit:** an old `pythonw.exe` is still holding the lock port. End it in Task Manager or reboot.
- **"Model not found":** check `CLOUD_MODEL` in `leo.py` against the current Anthropic model names.
- **Drive memory asks you to log in again:** the OAuth consent screen is probably in *Testing* mode, where Google expires tokens after 7 days. Set it to Internal or publish it.
- **Windows folders cannot end in a period:** this is why the project folder is `Project-LEO`.