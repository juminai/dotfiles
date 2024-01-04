#!/usr/bin/env python3
# juminai @ github

import dbus
import time

from mpris import get_property, format_time, clean_name
from utils import generate
    
def get_positions():
    bus_names = session_bus.list_names()
    
    positions = {}

    for name in bus_names:
        if "org.mpris.MediaPlayer2" in name:
            player = session_bus.get_object(name, "/org/mpris/MediaPlayer2")
            player_interface = dbus.Interface(player, "org.freedesktop.DBus.Properties")

            position = get_property(player_interface, "Position")
            position = position // 1000000 if position is not None else -1
            
            positions[clean_name(name)] = {
                "position": position, 
                "positionStr": format_time(position) if position != -1 else -1
            }

    return positions

if __name__ == "__main__":
    session_bus = dbus.SessionBus()
    try:
        while True:
            generate(get_positions())
            time.sleep(1)
    except KeyboardInterrupt:
        pass
