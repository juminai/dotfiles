#!/usr/bin/env python3
# juminai @ github

import gi
import datetime
import os
import dbus
import dbus.service

gi.require_version("GdkPixbuf", "2.0")

from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib, GdkPixbuf
from bs4 import BeautifulSoup
from utils import get_themed_icon, cache_notifications, load, update_eww, write_file

class Notifications(dbus.service.Object):
    def __init__(self):
        bus_name = dbus.service.BusName("org.freedesktop.Notifications", dbus.SessionBus())
        dbus.service.Object.__init__(self, bus_name, "/org/freedesktop/Notifications")

        self.list = load("notifications")
        self.dnd = self.list["dnd"]
        self.active_popups = {}
        update_eww("notifications", self.list)

    @dbus.service.method("org.freedesktop.Notifications", in_signature="susssasa{sv}i", out_signature="u")
    def Notify(
        self, 
        app_name, 
        replaces_id, 
        app_image, 
        summary, 
        body, 
        actions, 
        hints, 
        expire_timeout,
    ):

        notification_id = self.get_id(replaces_id)

        details = {
            "id": notification_id,
            "appName": app_name or None,
            "appIcon": get_themed_icon(app_name),
            "summary": self.clean_text(summary) or None,
            "body": self.clean_text(body) or None,
            "actions": self.get_actions(actions),
            "urgency": self.get_urgency(hints),
            "time": int(datetime.datetime.now().timestamp()),
            "image": self.get_app_image(app_image, hints, notification_id),
        }

        self.save_notification(details)

        if not self.dnd:
            self.save_popup(details)

        return notification_id


    @dbus.service.method("org.freedesktop.Notifications", in_signature="", out_signature="ssss")
    def GetServerInformation(self):
        return (
            "dbus notifications", 
            "klyn", 
            "1.0", 
            "1.2"
        )


    @dbus.service.method("org.freedesktop.Notifications", in_signature="", out_signature="as")
    def GetCapabilities(self):
        return (
            "actions", 
            "body", 
            "icon-static", 
            "persistence"
        )


    @dbus.service.signal("org.freedesktop.Notifications", signature="us")
    def ActionInvoked(self, notification_id, action):
        return (notification_id, action)


    @dbus.service.method("org.freedesktop.Notifications", in_signature="us", out_signature="")
    def InvokeAction(self, notification_id, action):
        self.ActionInvoked(notification_id, action)


    @dbus.service.signal("org.freedesktop.Notifications", signature="uu")
    def NotificationClosed(self, notification_id, reason):
        return (notification_id, reason)
 
   
    @dbus.service.method("org.freedesktop.Notifications", in_signature="", out_signature="")
    def ToggleDND(self):
        self.dnd = not self.dnd
        self.list["dnd"] = self.dnd

        self.update()


    @dbus.service.method("org.freedesktop.Notifications", in_signature="u", out_signature="")
    def CloseNotification(self, notification_id):
        for i in self.list["notifications"]:
            if i["id"] == notification_id:
                self.list["notifications"].remove(i)
                break

        self.NotificationClosed(notification_id, 2)
        self.DismissPopup(notification_id)

        self.update()


    @dbus.service.method("org.freedesktop.Notifications", in_signature="u", out_signature="")
    def DismissPopup(self, notification_id):
        for i in self.list["popups"]:
            if i["id"] == notification_id:
                self.list["popups"].remove(i)
                break

        self.RemovePopupID(notification_id)

        self.update()


    @dbus.service.method("org.freedesktop.Notifications", in_signature="u", out_signature="")
    def RemovePopupID(self , notification_id):
        if notification_id in self.active_popups:
            GLib.source_remove(self.active_popups[notification_id])
            self.active_popups.pop(notification_id, None)


    @dbus.service.method("org.freedesktop.Notifications", in_signature="", out_signature="")
    def ClearAll(self):
        for i in self.list["notifications"]:
            self.NotificationClosed(i["id"], 2)

        self.list = {
            "dnd": self.dnd,
            "notifications": [],
            "popups": []
        }
        
        for i in self.active_popups.keys():
            GLib.source_remove(self.active_popups[i])
        self.active_popups = {}

        self.update()


    def save_notification(self, notification):
        for i in self.list["notifications"]:
            if i["id"] == notification["id"]:
                self.list["notifications"].remove(i)
                break

        self.list["notifications"].insert(0, notification)

        self.update()


    def save_popup(self, notification):
        for i in self.list["popups"]:
            if i["id"] == notification["id"]:
                self.list["popups"].remove(i)
                GLib.source_remove(self.active_popups[i["id"]])
                break

        if len(self.list["popups"]) >= 3:
            oldest_popup = self.list["popups"].pop(0)
            self.DismissPopup(oldest_popup["id"])
    
        self.list["popups"].append(notification)
        
        popup_id = notification["id"]
        self.active_popups[popup_id] = GLib.timeout_add_seconds(
            5, 
            self.DismissPopup, 
            popup_id
        )

        self.update()


    def clean_text(self, text):
        soup = BeautifulSoup(text, 'html.parser')
        cleaned_text = soup.get_text(separator=' ', strip=True)

        return cleaned_text


    def get_app_image(self, app_image, hints, notification_id):
        image = None

        if app_image:
            if os.path.isfile(app_image) or app_image.startswith("file://"):
                image = app_image
            else:
                image = get_themed_icon(app_image)

        if "image-data" in hints:
            image_data = hints["image-data"]
            image_path = f"{cache_notifications}/{notification_id}"
            self.save_img_byte(image_data, image_path)
            image = image_path
    
        return image


    def save_img_byte(self, px_args, save_path: str):
        GdkPixbuf.Pixbuf.new_from_bytes(
            width=px_args[0],
            height=px_args[1],
            has_alpha=px_args[3],
            data=GLib.Bytes(px_args[6]),
            colorspace=GdkPixbuf.Colorspace.RGB,
            rowstride=px_args[2],
            bits_per_sample=px_args[4],
        ).savev(save_path, "png")

    
    def get_urgency(self, hints):
        urgency = None

        if "urgency" in hints:
            urgency = hints["urgency"]
            if urgency == 0:
                urgency = "low"
            elif urgency == 1:
                urgency = "normal"
            elif urgency == 2:
                urgency = "critical"

        return urgency


    def get_id(self, replaces_id):
        if replaces_id != 0:
            notification_id = replaces_id
        else:
            if self.list.get("notifications", []):
                notification_id = self.list.get("notifications", [])[0]["id"] + 1
            else:
                notification_id = 1

        return notification_id


    def get_actions(self, actions):
        actions = list(actions)
        pairs = []

        for i in range(0, len(actions), 2):
            if actions[i + 1] != "":
                pairs.append({
                    "label": actions[i + 1],
                    "id": actions[i]
                })

        return pairs

    
    def update(self):
        update_eww("notifications", self.list)
        write_file("notifications",
            {
                "dnd": self.list["dnd"],
                "notifications": self.list["notifications"],
                "popups": []
            }
        )


if __name__ == "__main__":
    DBusGMainLoop(set_as_default=True)
    loop = GLib.MainLoop()
    Notifications()
    try:
        loop.run()
    except KeyboardInterrupt:
        loop.quit()
