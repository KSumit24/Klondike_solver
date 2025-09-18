import pyautogui
from pathlib import Path

def take_screenshot(save_path: Path):
    screenshot = pyautogui.screenshot()
    save_path.parent.mkdir(parents=True, exist_ok=True)
    screenshot.save(str(save_path))
