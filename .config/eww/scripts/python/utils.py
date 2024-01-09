# juminai @ github

import json
import os
import gi
import subprocess
import sys

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk

CACHE = os.path.expandvars("$XDG_CACHE_HOME/eww")

APPS_DIR = os.path.join(CACHE, "apps")
NOTIFICATIONS_DIR = os.path.join(CACHE, "notifications")
MPRIS_DIR = os.path.join(CACHE, "mpris")
WEATHER_DIR = os.path.join(CACHE, "weather")
COLORS_DIR = os.path.join(CACHE, "colors")
TEMPLATES_DIR = os.path.join(COLORS_DIR, "templates")

APPS_JSON = os.path.join(APPS_DIR, "apps.json")
DOCK_JSON = os.path.join(APPS_DIR, "dock.json")
FREQUENCY_JSON = os.path.join(APPS_DIR, "frequency.json")
NOTIFICATIONS_JSON = os.path.join(NOTIFICATIONS_DIR, "notifications.json")
CURRENT_JSON = os.path.join(COLORS_DIR, "current.json")
WALLPAPER_PATH = os.path.join(COLORS_DIR, "wall.png")

for file in [
    CACHE, 
    APPS_DIR, 
    NOTIFICATIONS_DIR,
    MPRIS_DIR, 
    WEATHER_DIR, 
]:
    os.makedirs(file, exist_ok=True)

def get_themed_icon(icon_name):
    theme = Gtk.IconTheme.get_default()

    if "Screenshot" in icon_name:
        icon_name = "com.github.maoschanz.DynamicWallpaperEditor"

    if "Color Picker" in icon_name:
        icon_name = "gcolor3"

    icon_name = [icon_name, icon_name.lower(), icon_name.capitalize()]

    for name in icon_name:
        icon = theme.lookup_icon(name.split()[0], 128, 0)
        if icon:
            return icon.get_filename()
    return None


def get_file(name):
    file_paths = {
        "apps": APPS_JSON,
        "dock": DOCK_JSON,
        "frequency": FREQUENCY_JSON,
        "notifications": NOTIFICATIONS_JSON
    }

    return file_paths.get(name, None)


def load(file):
    file = get_file(file)

    try:
        with open(file, "r") as log:
            return json.load(log)
    except (FileNotFoundError, json.JSONDecodeError):
        if file == NOTIFICATIONS_JSON:
            return {
                "dnd": False, 
                "notifications": [],
                "popups": []
            }

        if file == FREQUENCY_JSON:
            return {}

        if file in [DOCK_JSON, APPS_JSON]:
            return []


def update_eww(var, content):
    subprocess.run([
        "eww", "update", f"{var}={json.dumps(content)}"
    ])


def write_file(file, content):
    file = get_file(file)

    with open(file, "w") as log:
        json.dump(content, log, indent=2)


def generate(content):
    sys.stdout.write(json.dumps(content) + "\n")
    sys.stdout.flush()