import os
import socket
import sys
import time
import math
import ctypes
import winsound
import threading
import tkinter as tk
import io
import contextlib

# ==========================================
# 0. GLOBAL SINGLE-INSTANCE LOCK
# ==========================================
try:
    global_leo_lock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    global_leo_lock.bind(("127.0.0.1", 65433))
except socket.error:
    # Send secret signal 99 to the batch file to instantly kill the window
    sys.exit(99)

from config import GROQ_API_KEY, UNSPLASH_ACCESS_KEY
os.environ["GROQ_API_KEY"] = GROQ_API_KEY

# ==========================================
# 1. SYSTEM STRUCTURES & UTILITIES
# ==========================================
class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long)
    ]

interpreter = None
is_loaded = False
status_text = "INITIALIZING TACTICAL SYSTEMS..."
current_backend = "cloud"
auto_mode = True

def play_boot_sound():
    sound_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "boot.wav")
    if os.path.exists(sound_path):
        try:
            winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception:
            pass

def setup_centered_console():
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        hwnd = kernel32.GetConsoleWindow()

    GA_ROOT = 2
    root_hwnd = user32.GetAncestor(hwnd, GA_ROOT)
    if root_hwnd:
        hwnd = root_hwnd

    sw = user32.GetSystemMetrics(0)
    sh = user32.GetSystemMetrics(1)

    cmd_w, cmd_h = 960, 620
    cmd_x = (sw - cmd_w) // 2
    cmd_y = (sh - cmd_h) // 2

    if hwnd:
        user32.MoveWindow(hwnd, cmd_x, cmd_y, cmd_w, cmd_h, True)
        rect = RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        cmd_x = rect.left
        cmd_y = rect.top
        cmd_w = rect.right - rect.left
        cmd_h = rect.bottom - rect.top

    return cmd_w, cmd_h, cmd_x, cmd_y

def has_internet(timeout=1.5):
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=timeout)
        return True
    except OSError:
        return False

def apply_local_backend():
    interpreter.llm.model = "ollama/qwen3:8b"
    interpreter.llm.api_base = "http://localhost:11434"
    interpreter.llm.context_window = 8192
    interpreter.llm.max_tokens = 300
    interpreter.llm.supports_functions = False
    interpreter.messages = []

def apply_cloud_backend():
    interpreter.llm.model = "groq/openai/gpt-oss-20b"
    interpreter.llm.api_base = None
    interpreter.llm.api_key = GROQ_API_KEY
    interpreter.llm.context_window = 131072
    interpreter.llm.max_tokens = 4096
    interpreter.llm.supports_functions = False
    interpreter.messages = []

def load_leo_backend():
    global interpreter, is_loaded, status_text
    start_time = time.time()

    status_text = "LOADING OPEN-INTERPRETER CORE..."
    from interpreter import interpreter as interp
    import interpreter.core.respond as respond_module

    respond_module.display_markdown_message = lambda *args, **kwargs: None

    status_text = "CONFIGURING LLM BACKEND..."
    interp.llm.api_key = GROQ_API_KEY

    interp.auto_run = True
    interp.verbose = False
    interp.debug_mode = False

    status_text = "MOUNTING SYSTEM MODULES & APIS..."
    interp.system_message = (
        "You are LEO, a helpful tactical AI assistant. ALWAYS IMMEDIATELY EXECUTE Python or PowerShell code. "
        "RESPONSE STYLE: Speak like a voice assistant, not a chatbot. NEVER use markdown tables, bullet lists, headers, or bold text. Keep every response to one short spoken sentence. "
        "Before executing any task, in the SAME response say a brief, natural confirmation (e.g., 'Right away.', 'Processing now.', or 'This might take a moment.') AND immediately include the code to execute it — do not split these into separate responses. "
        "The estimated time is spoken flavor text ONLY. NEVER add time.sleep() or any artificial delay to match it — execute the actual code immediately, with no intentional waiting. "
        "CRITICAL: After execution, respond with ONLY a short one-sentence confirmation, such as 'Task completed successfully.' "
        "For file operations, use PowerShell with $env:USERPROFILE. "
        "For crypto data, use CoinGecko API. "
        "\n\n"
        "SCREEN CAPTURE & DESKTOP VISION: When asked to see, look at, or analyze the screen/desktop/wallpaper, ALWAYS execute this EXACT Python code block: "
        "import base64, os, ollama\n"
        "from PIL import ImageGrab\n"
        "screenshot = ImageGrab.grab()\n"
        "screenshot.thumbnail((768, 768))\n"
        "screenshot_path = os.path.join(os.environ['USERPROFILE'], 'Desktop', 'leo_screen.png')\n"
        "screenshot.save(screenshot_path)\n"
        "res = ollama.chat(\n"
        "    model='moondream',\n"
        "    messages=[{\n"
        "        'role': 'user',\n"
        "        'content': 'Describe what is visible on this screen in detail, including open windows, wallpaper, text, and icons.',\n"
        "        'images': [screenshot_path]\n"
        "    }]\n"
        ")\n"
        "print(res['message']['content'])"
        "\n\n"
        "BROWSER TASKS: to open any website (Google, Wikipedia, or anywhere else), run: "
        "import yt; yt.browse('FULL_URL') — build the correct full URL yourself, e.g. a Google search is 'https://www.google.com/search?q=QUERY', a specific Wikipedia article is 'https://en.wikipedia.org/wiki/Article_Name'. "
        "To search and play a song on YouTube specifically, run: "
        "import yt; yt.youtube_search('QUERY')"
        "\n\n"
        "SYSTEM VOLUME CONTROL: Execute Python with pycaw. Replace 0.30 below with (requested_percent / 100) as a float between 0.0 and 1.0: "
        "import comtypes; comtypes.CoInitialize(); "
        "from pycaw.pycaw import AudioUtilities; "
        "device = AudioUtilities.GetSpeakers(); "
        "volume = device.EndpointVolume; "
        "volume.SetMasterVolumeLevelScalar(0.30, None)"
        "\n\n"
        "FINDING/DOWNLOADING A PICTURE: Use Unsplash API: "
        "import requests, config as cfg; "
        "r = requests.get('https://api.unsplash.com/search/photos', "
        "params={'query': 'SUBJECT', 'per_page': 1}, "
        "headers={'Authorization': f'Client-ID {cfg.UNSPLASH_ACCESS_KEY}'}).json(); "
        "url = r['results'][0]['urls']['regular']; "
        "open(SAVE_PATH, 'wb').write(requests.get(url).content)"
    )

    status_text = "SYSTEM ONLINE. LAUNCHING..."
    interpreter = interp
    apply_cloud_backend()

    # Ensure splash stays visible long enough to view the radar animation
    elapsed = time.time() - start_time
    if elapsed < 2.5:
        time.sleep(2.5 - elapsed)

    is_loaded = True

# ==========================================
# 2. TKINTER GUI RADAR HUD (LAUNCHES IMMEDIATELY)
# ==========================================
def run_splash_screen():
    w, h, x, y = setup_centered_console()

    play_boot_sound()

    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.geometry(f"{w}x{h}+{x}+{y}")

    bg_color = "#020B05"
    canvas = tk.Canvas(root, width=w, height=h, bg=bg_color, highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    cx, cy = w // 2, h // 2

    GREEN_BRIGHT = "#00FF41"
    GREEN_MID    = "#00B33C"
    GREEN_DARK   = "#004D1A"
    GREEN_TEXT   = "#55FF88"

    b_len = 35
    b_pad = 12
    canvas.create_rectangle(b_pad, b_pad, w - b_pad, h - b_pad, outline=GREEN_DARK, width=1)

    canvas.create_line(b_pad, b_pad, b_pad + b_len, b_pad, fill=GREEN_BRIGHT, width=3)
    canvas.create_line(b_pad, b_pad, b_pad, b_pad + b_len, fill=GREEN_BRIGHT, width=3)
    canvas.create_line(w - b_pad, b_pad, w - b_pad - b_len, b_pad, fill=GREEN_BRIGHT, width=3)
    canvas.create_line(w - b_pad, b_pad, w - b_pad, b_pad + b_len, fill=GREEN_BRIGHT, width=3)
    canvas.create_line(b_pad, h - b_pad, b_pad + b_len, h - b_pad, fill=GREEN_BRIGHT, width=3)
    canvas.create_line(b_pad, h - b_pad, b_pad, h - b_pad - b_len, fill=GREEN_BRIGHT, width=3)
    canvas.create_line(w - b_pad, h - b_pad, w - b_pad - b_len, h - b_pad, fill=GREEN_BRIGHT, width=3)
    canvas.create_line(w - b_pad, h - b_pad, w - b_pad, h - b_pad - b_len, fill=GREEN_BRIGHT, width=3)

    canvas.create_line(30, cy, cx - 230, cy, fill=GREEN_DARK, width=1)
    canvas.create_line(cx + 230, cy, w - 30, cy, fill=GREEN_DARK, width=1)
    canvas.create_line(cx, 30, cx, cy - 230, fill=GREEN_DARK, width=1)
    canvas.create_line(cx, cy + 230, cx, h - 50, fill=GREEN_DARK, width=1)

    rings = [
        {"r": 210, "width": 3, "color": GREEN_BRIGHT, "arcs": [(0, 50), (90, 50), (180, 50), (270, 50)], "speed": 1.5},
        {"r": 190, "width": 1, "color": GREEN_MID, "arcs": [(10, 30), (50, 15), (100, 45), (160, 20), (200, 40), (270, 30), (320, 25)], "speed": -2.2},
        {"r": 152, "width": 5, "color": GREEN_BRIGHT, "arcs": [(0, 70), (120, 70), (240, 70)], "speed": 3.0},
        {"r": 122, "width": 2, "color": GREEN_MID, "arcs": [(0, 110), (130, 110), (260, 80)], "speed": -4.0},
        {"r": 95,  "width": 2, "color": GREEN_BRIGHT, "arcs": [(15, 60), (105, 60), (195, 60), (285, 60)], "speed": 4.5},
        {"r": 75,  "width": 1, "color": GREEN_DARK, "arcs": [(0, 360)], "speed": 0}
    ]

    arc_items = []
    for r_info in rings:
        r = r_info["r"]
        bbox = (cx - r, cy - r, cx + r, cy + r)
        group = []
        for start, extent in r_info["arcs"]:
            arc_id = canvas.create_arc(
                bbox, start=start, extent=extent, style="arc",
                outline=r_info["color"], width=r_info["width"]
            )
            group.append((arc_id, start))
        arc_items.append((group, r_info["speed"]))

    tick_items = []
    num_ticks = 36
    r_tick_in = 168
    r_tick_out = 180
    for i in range(num_ticks):
        angle_deg = i * (360 / num_ticks)
        rad = math.radians(angle_deg)
        x1 = cx + r_tick_in * math.cos(rad)
        y1 = cy + r_tick_in * math.sin(rad)
        x2 = cx + r_tick_out * math.cos(rad)
        y2 = cy + r_tick_out * math.sin(rad)
        line_id = canvas.create_line(x1, y1, x2, y2, fill=GREEN_DARK, width=1)
        tick_items.append((line_id, angle_deg))

    num_dots = 24
    r_dots = 136
    dot_items = []
    for i in range(num_dots):
        angle_deg = i * (360 / num_dots)
        rad = math.radians(angle_deg)
        dx = cx + r_dots * math.cos(rad)
        dy = cy + r_dots * math.sin(rad)
        dot_id = canvas.create_oval(dx - 1.5, dy - 1.5, dx + 1.5, dy + 1.5, fill=GREEN_MID, outline="")
        dot_items.append((dot_id, angle_deg))

    canvas.create_text(cx, cy - 8, text="L.E.O.", font=("Consolas", 36, "bold"), fill=GREEN_BRIGHT)
    canvas.create_text(cx, cy + 24, text="TACTICAL HUD", font=("Consolas", 10, "bold"), fill=GREEN_MID)

    status_item = canvas.create_text(cx, h - 30, text=status_text, font=("Consolas", 10, "bold"), fill=GREEN_TEXT)

    threading.Thread(target=load_leo_backend, daemon=True).start()

    def animate():
        if is_loaded:
            root.destroy()
            return

        for group, speed in arc_items:
            if speed == 0:
                continue
            for i, (arc_id, current_start) in enumerate(group):
                new_start = (current_start + speed) % 360
                canvas.itemconfig(arc_id, start=new_start)
                group[i] = (arc_id, new_start)

        tick_speed = 0.8
        for i, (line_id, current_angle) in enumerate(tick_items):
            new_angle = (current_angle + tick_speed) % 360
            rad = math.radians(new_angle)
            x1 = cx + r_tick_in * math.cos(rad)
            y1 = cy + r_tick_in * math.sin(rad)
            x2 = cx + r_tick_out * math.cos(rad)
            y2 = cy + r_tick_out * math.sin(rad)
            canvas.coords(line_id, x1, y1, x2, y2)
            tick_items[i] = (line_id, new_angle)

        dot_speed = -2.0
        for i, (dot_id, current_angle) in enumerate(dot_items):
            new_angle = (current_angle + dot_speed) % 360
            rad = math.radians(new_angle)
            dx = cx + r_dots * math.cos(rad)
            dy = cy + r_dots * math.sin(rad)
            canvas.coords(dot_id, dx - 1.5, dy - 1.5, dx + 1.5, dy + 1.5)
            dot_items[i] = (dot_id, new_angle)

        canvas.itemconfig(status_item, text=status_text)
        root.after(20, animate)

    animate()
    root.mainloop()

# Execute HUD GUI directly on launch
run_splash_screen()

# ==========================================
# 3. TERMINAL INTERACTION LOOP
# ==========================================
os.system('cls' if os.name == 'nt' else 'clear')
print("====================================================")
print("  [ L.E.O. TACTICAL HUD ONLINE ]")
print("  [ AUTO MODE: switches CLOUD/LOCAL based on connection ]")
print("====================================================\n")

while True:
    try:
        user_input = input("\n> ")
    except (EOFError, KeyboardInterrupt):
        print("\n[ LEO OFFLINE ]")
        break

    if not user_input.strip():
        continue

    cmd = user_input.strip().lower()

    if cmd in ("exit", "quit"):
        print("[ LEO OFFLINE ]")
        break

    if cmd == "cloud on":
        apply_cloud_backend()
        current_backend = "cloud"
        auto_mode = False
        print("[ LEO: switched to CLOUD (Groq llama-3.1-70b-versatile) — auto mode OFF ]")
        continue

    if cmd == "cloud off":
        apply_local_backend()
        current_backend = "local"
        auto_mode = False
        print("[ LEO: switched to LOCAL (Qwen3 8B) — auto mode OFF ]")
        continue

    if cmd == "auto":
        auto_mode = True
        print("[ LEO: auto mode ON — will switch based on connection ]")
        continue

    if auto_mode:
        desired = "cloud" if has_internet() else "local"
        if desired != current_backend:
            if desired == "cloud":
                apply_cloud_backend()
            else:
                apply_local_backend()
            current_backend = desired
            print(f"[ LEO: connection changed — auto-switched to {desired.upper()} ]")

        # Keep the last 6 messages so L.E.O. remembers recent context
    if len(interpreter.messages) > 6:
        interpreter.messages = interpreter.messages[-6:]

    real_stdout = sys.stdout
    noise_buffer = io.StringIO()

    try:
        has_printed = False
        with contextlib.redirect_stdout(noise_buffer):
            for chunk in interpreter.chat(user_input, display=False, stream=True):
                if isinstance(chunk, dict):
                    if chunk.get("type") == "message" and chunk.get("content"):
                        real_stdout.write(str(chunk["content"]))
                        real_stdout.flush()
                        has_printed = True

        if not has_printed:
            print("[ Task executed successfully in the background. ]")
        else:
            print()

    except Exception as e:
        if "Rate limit" in str(e) or "429" in str(e):
            print("\n[ LEO: Groq rate limit hit. Please wait ~15 seconds before trying again. ]")
        else:
            print(f"\n[ LEO Error: {e} ]")