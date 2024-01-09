#!/usr/bin/env python3
# juminai @ github

import dbus
import gi
import os
import requests
import time
import cairosvg
import hashlib

from io import BytesIO
from PIL import Image, ImageFilter, ImageEnhance
from gi.repository import GLib
from dbus.mainloop.glib import DBusGMainLoop
from utils import get_themed_icon, MPRIS_DIR, update_eww

def get_property(interface, prop):
    try:
        return interface.Get("org.mpris.MediaPlayer2.Player", prop)
    except dbus.exceptions.DBusException:
        return None


def format_time(seconds):
    if seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes:02d}:{remaining_seconds:02d}"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        remaining_seconds = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{remaining_seconds:02d}"
    

def clean_name(name):
    name = name.split(".instance")[0]
    name = name.replace("org.mpris.MediaPlayer2.", "")
    return name


def get_icon(name):
    player_name = clean_name(name)
    icon = get_themed_icon(player_name)
    return icon


def get_artwork(artwork, title, player):
    file_name = hashlib.sha1(f"{title}_{player}".encode()).hexdigest()
    save_path = f"{MPRIS_DIR}/{file_name}"

    if not artwork or len(artwork) > 200:
        save_path = f"{MPRIS_DIR}/{player}"
        artwork = svg_to_png(get_icon(player), save_path)

    if not os.path.exists(save_path):
        if artwork.startswith("https://"):
            link = requests.get(artwork)
            artwork = BytesIO(link.content)
        else:
            artwork = artwork.replace("file://", "")

        blur_img(artwork, save_path)
    
    return save_path


def blur_img(artwork, save_path):
    try:
        image = Image.open(artwork)
        if image.mode != "RGB":
            image = image.convert("RGB")

        blurred = image.filter(ImageFilter.GaussianBlur(radius=5))
        blurred = ImageEnhance.Brightness(blurred).enhance(0.5)
        blurred.save(save_path, format="PNG")
    except FileNotFoundError:
        pass


def svg_to_png(svg_path, png_path):
    if not os.path.exists(png_path):
        cairosvg.svg2png(url=svg_path, write_to=png_path)
        blur_img(png_path, png_path)

    return png_path


def get_players():
    bus_names = bus.list_names()
    
    mpris_players = []
    for name in bus_names:
        if "org.mpris.MediaPlayer2" in name:
            mpris_players.append(name)
            
    return mpris_players

   
def mpris_data():
    player_names =  get_players()

    players = []

    for name in player_names:
        player = bus.get_object(name, "/org/mpris/MediaPlayer2")
        interface = dbus.Interface(player, "org.freedesktop.DBus.Properties")
        metadata = get_property(interface, "Metadata")
        playback_status = get_property(interface, "PlaybackStatus")

        if playback_status == "Stopped" or metadata is None:
            continue
        
        player_name = clean_name(name)
        title = metadata.get("xesam:title", "Unknown")
        artist = metadata.get("xesam:artist", ["Unknown"])[0]
        album = metadata.get("xesam:album", "Unknown")
        artwork = metadata.get("mpris:artUrl", None)
        length = metadata.get("mpris:length", -1) // 1000000 or -1
        volume = get_property(interface, "Volume")
        loop_status = get_property(interface, "LoopStatus")
        shuffle = bool(get_property(interface, "Shuffle"))
        can_go_next = bool(get_property(interface, "CanGoNext"))
        can_go_previous = bool(get_property(interface, "CanGoPrevious"))
        can_play = bool(get_property(interface, "CanPlay"))
        can_pause = bool(get_property(interface, "CanPause"))

        player_data = {
            "name": player_name,
            "title": title,
            "artist": artist,
            "album": album,
            "artUrl": get_artwork(artwork, title, player_name),
            "status": playback_status,
            "length": length,
            "lengthStr": format_time(length) if length != -1 else -1,
            "volume": int(volume * 100) if volume is not None else -1,
            "loop": loop_status,
            "shuffle": shuffle,
            "canGoNext": can_go_next,
            "canGoPrevious": can_go_previous,
            "canPlay": can_play,
            "canPause": can_pause,
            "icon": get_icon(player_name),
        }
        
        players.append(player_data)

    return players


def get_positions():
    player_names =  get_players()

    positions = {}

    for name in player_names:
        player = bus.get_object(name, "/org/mpris/MediaPlayer2")
        interface = dbus.Interface(player, "org.freedesktop.DBus.Properties")

        position = get_property(interface, "Position")
        position = position // 1000000 if position is not None else -1
        
        positions[clean_name(name)] = {
            "position": position, 
            "positionStr": format_time(position) if position != -1 else -1
        }

    return positions


def properties_changed():
    bus.add_signal_receiver(
        emit,
        dbus_interface="org.freedesktop.DBus.Properties",
        signal_name="PropertiesChanged",
        path="/org/mpris/MediaPlayer2"
    )


def player_changed():
    bus.add_signal_receiver(
        emit,
        dbus_interface="org.freedesktop.DBus",
        signal_name="NameOwnerChanged",
        path="/org/freedesktop/DBus"
    )


def update_positions():
    update_eww("positions", get_positions())
    return True


def emit(interface, changed_properties, invalidated_properties):
    if "org.mpris.MediaPlayer2" in interface:
        if "Rate" not in changed_properties:
            update_eww("mpris", mpris_data())


if __name__ == "__main__":
    DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    loop = GLib.MainLoop()
    
    try:
        update_eww("mpris", mpris_data())
        properties_changed()
        player_changed()
        GLib.timeout_add(1000, update_positions)
        loop.run()
    except KeyboardInterrupt:
        loop.quit()