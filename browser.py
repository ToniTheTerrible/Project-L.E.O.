import os, urllib.parse, time, subprocess
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def _get_driver():
    port = 9222
    user_data = os.path.join(os.environ['USERPROFILE'], 'AppData', 'Local', 'Google', 'Chrome', 'User Data', 'LEOProfile')

    opts = Options()
    opts.add_experimental_option("debuggerAddress", f"127.0.0.1:{port}")

    driver = None
    try:
        driver = webdriver.Chrome(options=opts)
        driver.title
    except Exception:
        driver = None

    if driver is None:
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        if not os.path.exists(chrome_path):
            chrome_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

        subprocess.Popen(f'"{chrome_path}" --remote-debugging-port={port} --user-data-dir="{user_data}"', shell=True)

        for _ in range(20):
            time.sleep(0.5)
            try:
                driver = webdriver.Chrome(options=opts)
                driver.title
                break
            except Exception:
                driver = None

    return driver

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
        time.sleep(2.5)
        try:
            driver.execute_script("document.querySelector('ytd-video-renderer a#video-title').click();")
        except Exception:
            pass
    else:
        driver.get('https://www.youtube.com')