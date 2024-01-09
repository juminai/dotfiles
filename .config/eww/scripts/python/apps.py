#!/usr/bin/env python3
# juminai @ github

import gi
import dbus
import dbus.service

gi.require_version("Gtk", "3.0")

from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import Gio, GLib
from hyprland import update_dock
from utils import load, get_themed_icon, update_eww, write_file

class Apps(dbus.service.Object):
    def __init__(self):
        super().__init__(
            dbus.service.BusName(
                "com.juminai.Apps", 
                bus=dbus.SessionBus()
            ), "/com/juminai/Apps"
        )

        self.populate()


    def installed_apps(self):
        app_info = Gio.AppInfo
        app_infos = app_info.get_all()

        app_list = []

        for app_info in app_infos:
            if app_info.should_show():
                get_icon = app_info.get_icon()
                app_icon = None

                if get_icon:
                    if get_icon.get_names():
                        icon_name = get_icon.get_names()[0]
                        app_icon = get_themed_icon(icon_name)

                app_id = app_info.get_id()

                app = {
                    "name": app_info.get_name(),
                    "executable": app_info.get_executable(),
                    "icon": app_icon,
                    "description": app_info.get_description(),
                    "id": app_id,
                    "frequency": load("frequency").get(app_id, 0),
                }

                app_list.append(app)

        app_list.sort(
            key=lambda x: x["frequency"],
            reverse=True
        )
        return app_list


    def populate(self):
        self.apps = self.installed_apps()
        update_eww("apps", self.apps)
        write_file("apps", self.apps)


    @dbus.service.method("com.juminai.Apps", in_signature="s", out_signature="")
    def Query(self, query):
        filtered = []

        for app in self.apps:
            if query.lower() in app["name"].lower():
                filtered.append(app)

        update_eww("apps", filtered)


    @dbus.service.method("com.juminai.Apps", in_signature="s", out_signature="")
    def UpdateFreq(self, app):
        frequencies = load("frequency")

        if app not in frequencies:
            frequencies[app] = 1
        else:
            frequencies[app] += 1

        write_file("frequency", frequencies)
        self.populate()


    @dbus.service.method("com.juminai.Apps", in_signature="s", out_signature="")
    def Add(self, app):
        dock_apps = load("dock")

        if app not in dock_apps:
            dock_apps.append(app)
        else:
            dock_apps.remove(app)
    
        write_file("dock", dock_apps)
        update_dock()


if __name__ == "__main__":
    DBusGMainLoop(set_as_default=True)
    loop = GLib.MainLoop()
    Apps()
    try:
        loop.run()
    except KeyboardInterrupt:
        loop.quit()
