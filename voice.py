import asyncio
import edge_tts
import pygame
import os
import queue
import threading
import re
import tempfile
import time

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

VOICE = "en-US-ChristopherNeural"
EDGE_RETRY_SECONDS = 300  # after an Edge failure, try the online voice again after this long

speech_queue = queue.Queue()
_edge_ok = True
_edge_retry_at = 0.0
_fallback_notice_shown = False
_mixer_ready = False


def clean_text_for_tts(text):
    if not text:
        return ""

    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`[^`]*`', '', text)
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'(?m)^\s*(import|from)\s+\S+.*$', '', text)
    text = re.sub(r'\b[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+\s*\(.*?\)', '', text)
    text = re.sub(r'[;{}<>]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def _speak_edge(text, counter):
    temp_file = os.path.join(tempfile.gettempdir(), f"leo_tts_{os.getpid()}_{counter}.mp3")
    try:
        asyncio.run(edge_tts.Communicate(text, VOICE).save(temp_file))
        pygame.mixer.music.load(temp_file)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.music.unload()
    finally:
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception:
                pass


def _speak_windows(text):
    if pyttsx3 is None:
        return False
    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", 185)
        for v in engine.getProperty("voices"):
            name = v.name.lower()
            if "david" in name or "mark" in name:
                engine.setProperty("voice", v.id)
                break
        engine.say(text)
        engine.runAndWait()
        engine.stop()
        return True
    except Exception:
        return False


def _voice_worker():
    global _edge_ok, _edge_retry_at, _fallback_notice_shown, _mixer_ready

    # The Windows voice uses COM, which must be initialised in this thread
    try:
        import comtypes
        comtypes.CoInitialize()
    except Exception:
        pass

    try:
        pygame.mixer.init()
        _mixer_ready = True
    except Exception:
        _mixer_ready = False

    counter = 0
    while True:
        text = speech_queue.get()
        if text is None:
            break
        counter += 1

        spoken = False
        if _mixer_ready and (_edge_ok or time.time() >= _edge_retry_at):
            try:
                _speak_edge(text, counter)
                _edge_ok = True
                spoken = True
            except Exception as e:
                if "No audio was received" in str(e):
                    spoken = True  # nothing speakable in that text, not a failure
                else:
                    _edge_ok = False
                    _edge_retry_at = time.time() + EDGE_RETRY_SECONDS

        if not spoken:
            if _speak_windows(text) and not _fallback_notice_shown:
                _fallback_notice_shown = True
                print("[ Voice: online voice unavailable, using the Windows voice ]")

        speech_queue.task_done()


worker_thread = threading.Thread(target=_voice_worker, daemon=True)
worker_thread.start()


def speak(text):
    cleaned_text = clean_text_for_tts(text)
    # Only queue text that has actual letters or numbers
    if cleaned_text and any(c.isalnum() for c in cleaned_text):
        speech_queue.put(cleaned_text)