#!/usr/bin/env python3
# juminai @ github

import dbus
import gi
import os
import requests
import time
import cairosvg

from io import BytesIO
from PIL import Image, ImageFilter, ImageEnhance
from gi.repository import GLib
from dbus.mainloop.glib import DBusGMainLoop
from utils import get_themed_icon, cache_mpris, update_eww

previous = None

def get_property(player_interface, prop):
    try:
        return player_interface.Get("org.mpris.MediaPlayer2.Player", prop)
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


def art(artwork, title, player):
    invalid_chars = '"\'/\\|'

    for char in invalid_chars:
        title = title.replace(char, "_")

    save_path = f"{cache_mpris}/{title}"

    if not artwork or len(artwork) > 200:
        save_path = f"{cache_mpris}/{player}"
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
    image = Image.open(artwork)

    blurred = image.filter(ImageFilter.GaussianBlur(radius=5))
    blurred = ImageEnhance.Brightness(blurred).enhance(0.5)
    blurred.save(save_path, format="PNG")


def svg_to_png(svg_path, png_path):
    if not os.path.exists(png_path):
        cairosvg.svg2png(url=svg_path, write_to=png_path)
        blur_img(png_path, png_path)

    return png_path

   
def mpris_data():
    bus_names = session_bus.list_names()

    players = []

    for name in bus_names:
        if "org.mpris.MediaPlayer2" in name:
            player = session_bus.get_object(name, "/org/mpris/MediaPlayer2")
            player_interface = dbus.Interface(player, "org.freedesktop.DBus.Properties")
            metadata = get_property(player_interface, "Metadata")
            playback_status = get_property(player_interface, "PlaybackStatus")

            if playback_status == "Stopped" or metadata is None:
                continue
            
            player_name = clean_name(name)

            volume = get_property(player_interface, "Volume")
            loop_status = get_property(player_interface, "LoopStatus")
            shuffle = bool(get_property(player_interface, "Shuffle"))
            can_go_next = bool(get_property(player_interface, "CanGoNext"))
            can_go_previous = bool(get_property(player_interface, "CanGoPrevious"))
            can_play = bool(get_property(player_interface, "CanPlay"))
            can_pause = bool(get_property(player_interface, "CanPause"))

            title = metadata.get("xesam:title", "Unknown")
            artist = metadata.get("xesam:artist", ["Unknown"])
            album = metadata.get("xesam:album", "Unknown")
            artwork = metadata.get("mpris:artUrl", None)
            length = metadata.get("mpris:length", -1) // 1000000 or -1

            player_data = {
                "name": player_name,
                "title": title,
                "artist": artist[0] if artist else "",
                "album": album,
                "artUrl": art(artwork, title, player_name),
                "status": playback_status,
                "length": length,
                "lengthStr": format_time(length) if length != -1 else -1,
                "loop": loop_status,
                "shuffle": shuffle,
                "volume": int(volume * 100) if volume is not None else -1,
                "canGoNext": can_go_next,
                "canGoPrevious": can_go_previous,
                "canPlay": can_play,
                "canPause": can_pause,
                "icon": get_icon(player_name),
            }
            
            players.append(player_data)

    return players


def properties_changed():
    session_bus.add_signal_receiver(
        emit,
        dbus_interface="org.freedesktop.DBus.Properties",
        signal_name="PropertiesChanged",
        path="/org/mpris/MediaPlayer2"
    )


def player_changed():
    session_bus.add_signal_receiver(
        emit,
        dbus_interface="org.freedesktop.DBus",
        signal_name="NameOwnerChanged",
        path="/org/freedesktop/DBus"
    )


def emit(interface, changed_properties, invalidated_properties):
    if "org.mpris.MediaPlayer2" in interface:
        global previous
        current = mpris_data()

        if current != previous:
            update_eww("mpris", current)
            previous = current


if __name__ == "__main__":
    DBusGMainLoop(set_as_default=True)
    session_bus = dbus.SessionBus()
    loop = GLib.MainLoop()
    
    try:
        update_eww("mpris", mpris_data())
        properties_changed()
        player_changed()
        loop.run()
    except KeyboardInterrupt:
        loop.quit()
