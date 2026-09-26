import os
import sys
import time
import socket
import subprocess
import sounddevice as sd
import numpy as np

# ==========================================
# 1. HARD SINGLE-INSTANCE LOCK
# ==========================================
try:
    lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lock_socket.bind(("127.0.0.1", 65432))
except socket.error:
    sys.exit(0)

# ==========================================
# 2. WHISTLE CONFIGURATION
# ==========================================
SAMPLE_RATE = 44100
BLOCK_SIZE = 4096       # ~0.1 seconds of audio per block

# Frequency band for human whistles
FREQ_MIN = 1200         
FREQ_MAX = 3000         

# Sensitivity tuning
PROMINENCE = 10.0        # Tone must be x times louder than background noise
MIN_MAGNITUDE = 15.0     # Absolute volume threshold (ignores pure silence)
REQUIRED_FRAMES = 3      # Must sustain the whistle for ~0.x seconds
COOLDOWN = 5.0           # Lockout pause after launching

whistle_frames = 0
in_cooldown = False
cooldown_start = 0

def is_leo_already_open():
    """Checks if L.E.O.'s single-instance lock port (65433) is currently held."""
    test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        test_socket.bind(("127.0.0.1", 65433))
        test_socket.close()
        return False
    except socket.error:
        return True

def audio_callback(indata, frames, time_info, status):
    global whistle_frames, in_cooldown, cooldown_start
    
    current_time = time.time()

    if in_cooldown:
        if current_time - cooldown_start > COOLDOWN:
            in_cooldown = False
        else:
            return

    # Flatten the audio chunk into a 1D array
    audio_data = indata[:, 0]
    
    # 1. Fast Fourier Transform: Convert raw audio into a frequency spectrum
    fft_result = np.abs(np.fft.rfft(audio_data))
    freqs = np.fft.rfftfreq(BLOCK_SIZE, 1 / SAMPLE_RATE)
    
    # 2. Isolate the target whistle frequencies
    whistle_indices = np.where((freqs >= FREQ_MIN) & (freqs <= FREQ_MAX))[0]
    
    if len(whistle_indices) == 0:
        return
        
    # 3. Analyze energy levels
    whistle_peak = np.max(fft_result[whistle_indices])
    avg_background = np.mean(fft_result)
    
    # 4. Check if it's a loud, pure tone standing out from background noise
    if whistle_peak > MIN_MAGNITUDE and whistle_peak > (avg_background * PROMINENCE):
        whistle_frames += 1
    else:
        # If the sound breaks or gets muddy, reset the counter
        whistle_frames = 0

    # 5. Trigger L.E.O. if the whistle holds steady
    if whistle_frames >= REQUIRED_FRAMES:
        in_cooldown = True
        cooldown_start = current_time
        whistle_frames = 0
        
        if not is_leo_already_open():
            wt_path = os.path.join(os.environ.get('LOCALAPPDATA', r'C:\Users\Toniz\AppData\Local'), r'Microsoft\WindowsApps\wt.exe')
            try:
                subprocess.Popen([wt_path, "cmd", "/k", r"C:\Users\Toniz\Desktop\Project-LEO\leo.bat"])
            except FileNotFoundError:
                os.startfile(r"C:\Users\Toniz\Desktop\Project-LEO\leo.bat")

try:
    with sd.InputStream(callback=audio_callback, channels=1, samplerate=SAMPLE_RATE, blocksize=BLOCK_SIZE):
        while True:
            time.sleep(0.1)
except KeyboardInterrupt:
    sys.exit(0)
except Exception:
    sys.exit(1)