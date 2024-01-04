# juminai @ github

import json
import os
import gi
import subprocess
import sys

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk

cache = os.path.expandvars("$XDG_CACHE_HOME/eww")

cache_apps = os.path.join(cache, "apps")
cache_notifications = os.path.join(cache, "notifications")
cache_mpris = os.path.join(cache, "mpris")
cache_weather = os.path.join(cache, "weather")

apps_file = os.path.join(cache_apps, "apps.json")
dock_file = os.path.join(cache_apps, "dock.json")
frequency_file = os.path.join(cache_apps, "frequency.json")
notifications_file = os.path.join(cache_notifications, "notifications.json")

for file in [cache, cache_apps, cache_notifications, cache_mpris, cache_weather]:
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
        "apps": apps_file,
        "dock": dock_file,
        "frequency": frequency_file,
        "notifications": notifications_file
    }

    return file_paths.get(name, None)


def load(file):
    file = get_file(file)

    try:
        with open(file, "r") as log:
            return json.load(log)
    except (FileNotFoundError, json.JSONDecodeError):
        if file == notifications_file:
            return {
                "dnd": False, 
                "notifications": [],
                "popups": []
            }

        if file == frequency_file:
            return {}

        if file in [dock_file, apps_file]:
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