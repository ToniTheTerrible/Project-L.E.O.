import asyncio
import edge_tts
import pygame
import os
import queue
import threading
import re
import tempfile

VOICE = "en-US-ChristopherNeural"
speech_queue = queue.Queue()
_voice_enabled = True
_error_shown = False


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


def _voice_worker():
    global _voice_enabled, _error_shown
    try:
        pygame.mixer.init()
    except Exception as e:
        _voice_enabled = False
        print(f"[ Voice disabled: {e} ]")
        return

    counter = 0
    while True:
        text = speech_queue.get()
        if text is None:
            break

        counter += 1
        temp_file = os.path.join(tempfile.gettempdir(), f"leo_tts_{os.getpid()}_{counter}.mp3")

        try:
            asyncio.run(edge_tts.Communicate(text, VOICE).save(temp_file))
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)

            pygame.mixer.music.unload()
        except Exception as e:
            # Empty-audio errors are harmless; show any other error only once per session
            if "No audio was received" not in str(e) and not _error_shown:
                _error_shown = True
                print(f"[ Voice Error: {e} ]")
        finally:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass

        speech_queue.task_done()


worker_thread = threading.Thread(target=_voice_worker, daemon=True)
worker_thread.start()


def speak(text):
    if not _voice_enabled:
        return
    cleaned_text = clean_text_for_tts(text)
    # Only queue text that has actual letters or numbers
    if cleaned_text and any(c.isalnum() for c in cleaned_text):
        speech_queue.put(cleaned_text)