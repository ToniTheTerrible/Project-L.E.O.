import os, urllib.parse, time, subprocess
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

PORT = 9222
_driver = None


def _attach():
    opts = Options()
    opts.add_experimental_option("debuggerAddress", f"127.0.0.1:{PORT}")
    try:
        d = webdriver.Chrome(options=opts)
        d.title  # confirms the window is actually alive
        return d
    except Exception:
        return None


def _get_driver():
    global _driver

    # Reuse the cached connection if it's still alive
    if _driver is not None:
        try:
            _driver.title
            return _driver
        except Exception:
            _driver = None

    # Try attaching to an already-running LEO Chrome
    d = _attach()

    # Otherwise launch Chrome with the debug port and wait for it
    if d is None:
        user_data = os.path.join(os.environ['USERPROFILE'], 'AppData', 'Local', 'Google', 'Chrome', 'User Data', 'LEOProfile')
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        if not os.path.exists(chrome_path):
            chrome_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

        subprocess.Popen(f'"{chrome_path}" --remote-debugging-port={PORT} --user-data-dir="{user_data}"', shell=True)

        for _ in range(20):
            time.sleep(0.5)
            d = _attach()
            if d is not None:
                break

    _driver = d
    return d


def browse(url):
    driver = _get_driver()
    if driver is None:
        print("Could not attach to Chrome.")
        return
    driver.get(url)


def youtube_search(query=""):
    driver = _get_driver()
    if driver is None:
        print("Could not attach to Chrome.")
        return
    if query:
        driver.get(f'https://www.youtube.com/results?search_query={urllib.parse.quote(query)}')
        try:
            first = WebDriverWait(driver, 8).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "ytd-video-renderer a#video-title"))
            )
            first.click()
        except Exception:
            pass
    else:
        driver.get('https://www.youtube.com')