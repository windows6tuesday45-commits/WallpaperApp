"""
OldWindowsWallpaperApp.py (Updated with OS compatibility message box)

This app only runs on Windows XP, Vista, 7, 8, and 8.1.
If opened on Windows 10 or 11, a message will appear and the program will close.
"""

import os
import sys
import json
import ctypes
import urllib.request
import shutil
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import platform
import winreg

# Optional: Pillow for image conversion
try:
    from PIL import Image
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

APP_NAME = "OldWindowsWallpaperApp"
SETTINGS_FILENAME = "settings.json"

# ✅ OS Compatibility Check – This runs BEFORE the window opens
def check_os_compatibility():
    current = platform.release()

    if current in ["10", "11"]:
        ans = messagebox.askyesno(
            "Unsupported Windows Version",
            f"You are using Windows {current}.\n\n"
            "This program is designed ONLY for:\n"
            "- Windows XP, Vista, 7, 8, and 8.1\n\n"
            "Are you actually using one of those older systems?\n\n"
            "Yes = I am using an older system\n"
            "No  = I am using Windows 10 or 11"
        )
        if not ans:
            messagebox.showerror("Program Closing",
                                 "This program cannot run on Windows 10 or 11.\nClosing now.")
            sys.exit()
        else:
            messagebox.showinfo("Continue",
                                "Okay! The program will continue since you confirmed you're using an older OS.")
    else:
        messagebox.showinfo("Compatible System",
                            f"Detected Windows {current}.\nThis system is supported.\nThe program will now start.")

# ✅ Run OS check
check_os_compatibility()

# ✅ Settings and Storage Functions
def get_appdata_dir():
    if os.name == "nt":
        appdata = os.getenv("APPDATA")
        if appdata:
            folder = os.path.join(appdata, APP_NAME)
            os.makedirs(folder, exist_ok=True)
            return folder
    return os.path.dirname(os.path.abspath(__file__))

APP_DIR = get_appdata_dir()
WALLPAPER_STORE = os.path.join(APP_DIR, "wallpapers")
os.makedirs(WALLPAPER_STORE, exist_ok=True)
SETTINGS_PATH = os.path.join(APP_DIR, SETTINGS_FILENAME)

DEFAULT_SETTINGS = {
    "last_wallpaper": "",
    "style": "stretch",
    "favorites": []
}

def load_settings():
    try:
        if os.path.exists(SETTINGS_PATH):
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                for k, v in DEFAULT_SETTINGS.items():
                    if k not in data:
                        data[k] = v
                return data
    except:
        pass
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
    except Exception as e:
        messagebox.showerror("Save Error", f"Cannot save settings:\n{e}")

# ✅ Registry Settings for Wallpaper Style
def set_wallpaper_registry_style(style):
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", 0, winreg.KEY_SET_VALUE)
        if style == "tile":
            winreg.SetValueEx(key, "WallpaperStyle", 0, winreg.REG_SZ, "0")
            winreg.SetValueEx(key, "TileWallpaper", 0, winreg.REG_SZ, "1")
        elif style == "center":
            winreg.SetValueEx(key, "WallpaperStyle", 0, winreg.REG_SZ, "0")
            winreg.SetValueEx(key, "TileWallpaper", 0, winreg.REG_SZ, "0")
        elif style == "stretch":
            winreg.SetValueEx(key, "WallpaperStyle", 0, winreg.REG_SZ, "2")
            winreg.SetValueEx(key, "TileWallpaper", 0, winreg.REG_SZ, "0")
        elif style == "fill":
            winreg.SetValueEx(key, "WallpaperStyle", 0, winreg.REG_SZ, "10")
            winreg.SetValueEx(key, "TileWallpaper", 0, winreg.REG_SZ, "0")
        winreg.CloseKey(key)
    except:
        pass

# ✅ Convert to BMP for older systems if required
def convert_to_bmp_if_needed(src_path):
    win_release = platform.release().lower()
    need_bmp = 'xp' in win_release

    ext = os.path.splitext(src_path)[1].lower()
    if not need_bmp:
        return src_path

    if ext == ".bmp":
        return src_path

    if not PIL_AVAILABLE:
        messagebox.showwarning("Pillow Missing",
                               "BMP conversion is needed for Windows XP.\nInstall Pillow (pip install pillow).")
        return src_path

    try:
        img = Image.open(src_path)
        bmp_path = os.path.join(WALLPAPER_STORE, f"{abs(hash(src_path))}.bmp")
        img = img.convert("RGB")
        img.save(bmp_path, "BMP")
        return bmp_path
    except Exception as e:
        messagebox.showerror("Error", f"Cannot convert to BMP:\n{e}")
        return src_path

# ✅ Apply Wallpaper
def apply_wallpaper(path, style):
    if not os.path.exists(path):
        return False

    final_path = convert_to_bmp_if_needed(path)
    set_wallpaper_registry_style(style)

    ctypes.windll.user32.SystemParametersInfoW(20, 0, final_path, 3)
    return True

# ✅ GUI Application Class
class WallpaperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Old Windows Wallpaper App")
        self.settings = load_settings()

        # Menu Bar
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open Image", command=self.open_image)
        file_menu.add_command(label="Save Settings", command=lambda: save_settings(self.settings))
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Check for Updates", command=self.check_for_updates)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

        # Buttons
        tk.Button(root, text="Open Image", command=self.open_image).pack(pady=5)
        tk.Button(root, text="Apply Wallpaper", command=self.apply_current).pack(pady=5)

    def open_image(self):
        img_path = filedialog.askopenfilename(
            title="Select Wallpaper",
            filetypes=[("Images", "*.bmp *.jpg *.jpeg *.png")]
        )
        if img_path:
            self.settings["last_wallpaper"] = img_path

    def apply_current(self):
        if not self.settings["last_wallpaper"]:
            messagebox.showwarning("No File", "Please open an image first.")
            return
        if apply_wallpaper(self.settings["last_wallpaper"], self.settings["style"]):
            messagebox.showinfo("Success", "Wallpaper applied successfully!")

    def check_for_updates(self):
        messagebox.showinfo("Updates", "No update server configured.")

    def show_about(self):
        messagebox.showinfo("About", "Old Windows Wallpaper App\nCreated in Python\nFor XP, Vista, 7, 8, 8.1")

# ✅ Main Program Launcher
if __name__ == "__main__":
    root = tk.Tk()
    app = WallpaperApp(root)
    root.mainloop()
