import pyautogui
import time
from datetime import datetime
from pathlib import Path
import sys

def take_screenshot(save_to_file=True, delay=3):
    print(f"\n[STEP] Taking screenshot...")
    print(f"[INFO] You have {delay} seconds to switch to the Solitaire window.")

    for i in range(delay, 0, -1):
        print(f"[{i}]...", end="", flush=True)
        time.sleep(1)
    print("\n[INFO] Capturing now!")

    image = pyautogui.screenshot()

    if save_to_file:
        save_path = Path(__file__).resolve().parent.parent / "vision" / "screenshots"
        save_path.mkdir(parents=True, exist_ok=True)

        filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        full_path = save_path / filename
        image.save(full_path)
        print(f"[INFO] Screenshot saved to: {full_path}")

        return str(full_path)  # ✅ Return the image path for loading later

    return image  # fallback (not used in current project)
