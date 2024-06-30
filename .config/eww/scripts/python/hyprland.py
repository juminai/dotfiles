#!/usr/bin/env python3
# juminai @ github

import json
import os
import subprocess
import sys

from utils import load, update_eww, generate

SIGNATURE = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE")
RUNTIME = os.environ.get("XDG_RUNTIME_DIR")

apps = load("apps")


def run_command(command):
    result = subprocess.check_output(command, text=True)
    return json.loads(result)


def fix_name(window_class):
    classes = {
        "brave": "brave",
        "telegram": "telegram",
        "inkscape": "inkscape",
        "nautilus": "nautilus",
        "transmissionbt": "transmission",
    }
    
    window_class = window_class.lower()
    
    for key, value in classes.items():
        if key in window_class:
            return value
    return window_class
    
    return window_class


def get_app_info(window_class):
    app_name = fix_name(window_class)
    app_icon = None
    app_id = None

    for app in apps:
        if app_name in app["executable"].lower():
            app_id = app["id"]
            app_name = app["name"]
            app_icon = app["icon"]
            break

    return {
        "id": app_id,
        "class": app_name,
        "icon": app_icon
    }


def get_workspaces():
    clients = run_command(["hyprctl", "clients", "-j"])
    data = {i: [] for i in range(1, 8)}

    for client in clients:
        workspace_id = client["workspace"]["id"]
        mapped = client["mapped"]
        window_class = client["class"]

        if window_class == "" or not mapped:
            continue
        
        app = get_app_info(window_class)

        window = {
            "id": app["id"],
            "class": app["class"],
            "icon": app["icon"],
            "address": client["address"],
            "at": client["at"],
            "size": client["size"],
        }

        data[workspace_id].append(window)

    workspaces = [
        {   
            "id": workspace_id,
            "windows": windows
        } for workspace_id, windows in data.items()
    ]

    return workspaces


def get_active():
    active_workspace = run_command(["hyprctl", "activeworkspace", "-j"])
    active_window = run_command(["hyprctl", "activewindow", "-j"])

    active = {
        "workspace": active_workspace["id"],
        "address": None,
        "id": None,
        "class": None,
        "icon": None
    }

    if active_window:
        active_class = active_window["class"]
        active["address"] = active_window["address"]
        active.update(get_app_info(active_class))

    return active


def get_dock_apps(workspaces):
    dock = load("dock")
    dock_apps = {
        "favorite": [], 
        "impostor": []
    }

    for workspace in workspaces:
        if workspace["windows"]:
            for window in workspace["windows"]:
                if window["id"]:

                    app =  {
                        "name": window["class"],
                        "icon": window["icon"],
                        "id": window["id"],
                        "address": window["address"]
                    }
            
                    if window["id"] in dock:
                        dock_apps["favorite"].append(app)
                    else:
                        dock_apps["impostor"].append(app)

    for app in apps:
        if app["id"] in dock:
            if not any(i["id"] == app["id"] for i in dock_apps["favorite"]):
                dock_apps["favorite"].append(
                    {
                        "name": app["name"],
                        "icon": app["icon"],
                        "id": app["id"],
                        "address": None
                    }
                )

    dock_apps["favorite"] = sorted(
        dock_apps["favorite"], 
        key=lambda x: x["name"]
    )

    return dock_apps


def update_dock():
    update_eww("dock", get_dock_apps(get_workspaces()))


def monitor_socat():
    socat = ["socat", "-u", f"UNIX-CONNECT:{RUNTIME}/hypr/{SIGNATURE}/.socket2.sock", "-"]
    with subprocess.Popen(socat, stdout=subprocess.PIPE, text=True) as process:
        for line in process.stdout:
            workspaces = get_workspaces()

            if line.startswith((
                "activewindow>>",
                "closewindow>>", 
                "openwindow>>"
            )):
                generate(workspaces)
                update_eww("dock", get_dock_apps(workspaces))
                update_eww("active", get_active())

            elif line.startswith((
                "movewindow>>", 
                "changefloatingmode>>", 
                "fullscreen>>"
            )):
                generate(workspaces)
            
            elif line.startswith("workspace>>"):
                update_eww("active", get_active())

if __name__ == "__main__":
    try:
        workspaces = get_workspaces()
        generate(workspaces)
        update_eww("dock", get_dock_apps(workspaces))
        update_eww("active", get_active())
        monitor_socat()
    except KeyboardInterrupt:
        pass