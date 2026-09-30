import asyncio
import edge_tts
import pygame
import os
import queue
import threading
import re

VOICE = "en-US-ChristopherNeural"
speech_queue = queue.Queue()

def clean_text_for_tts(text):
    if not text:
        return ""
    
    # Remove markdown code blocks ``` ... ```
    text = re.sub(r'```[\s\S]*?```', '', text)
    
    # Remove inline backticked code ` ... `
    text = re.sub(r'`[^`]*`', '', text)
    
    # Remove URLs (http:// or https://)
    text = re.sub(r'https?://\S+', '', text)
    
    # Remove python import lines (e.g. import browser, from x import y)
    text = re.sub(r'\b(import|from)\s+[a-zA-Z0-9_.]+\b.*', '', text, flags=re.IGNORECASE)
    
    # Remove function calls (e.g. browser.browse(...), os.system(...))
    text = re.sub(r'\b[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+\s*\(.*?\)', '', text)
    
    # Remove leftover symbols often found in code
    text = re.sub(r'[;{}<>]', ' ', text)
    
    # Clean up multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def _voice_worker():
    pygame.mixer.init()
    counter = 0
    while True:
        text = speech_queue.get()
        if text is None:
            break
        
        counter += 1
        temp_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"temp_{counter}.mp3")
        
        try:
            asyncio.run(edge_tts.Communicate(text, VOICE).save(temp_file))
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
                
            pygame.mixer.music.unload()
        except Exception as e:
            print(f"[ Voice Error: {e} ]")
        finally:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass
        
        speech_queue.task_done()

# Start background speech thread immediately on import
worker_thread = threading.Thread(target=_voice_worker, daemon=True)
worker_thread.start()

def speak(text):
    cleaned_text = clean_text_for_tts(text)
    if cleaned_text:
        speech_queue.put(cleaned_text)