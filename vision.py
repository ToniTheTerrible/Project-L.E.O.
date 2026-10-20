import os, tempfile
import ollama
from PIL import ImageGrab


def describe_screen(question="Describe what is visible on this screen in detail, including open windows, wallpaper, text, and icons."):
    img = ImageGrab.grab()
    img.thumbnail((768, 768))
    path = os.path.join(tempfile.gettempdir(), "leo_screen.png")
    img.save(path)
    res = ollama.chat(
        model="moondream",
        messages=[{"role": "user", "content": question, "images": [path]}]
    )
    return res["message"]["content"]