#!/bin/bash

dismiss() {
  dbus-send --session --type=method_call \
    --dest=org.freedesktop.Notifications \
    /org/freedesktop/Notifications \
    org.freedesktop.Notifications.DismissPopup \
    uint32:$1
}

close() {
  dbus-send --session --type=method_call \
    --dest=org.freedesktop.Notifications \
    /org/freedesktop/Notifications \
    org.freedesktop.Notifications.CloseNotification \
    uint32:$1
}

action() {
  dbus-send --session --type=method_call \
    --dest=org.freedesktop.Notifications \
    /org/freedesktop/Notifications \
    org.freedesktop.Notifications.InvokeAction \
    uint32:$1 string:$2

  eww update info-center_rev=false
}

clear_all() {
  dbus-send --session --type=method_call \
    --dest=org.freedesktop.Notifications \
    /org/freedesktop/Notifications \
    org.freedesktop.Notifications.ClearAll
}

toggle_dnd() {
  dbus-send --session --type=method_call \
    --dest=org.freedesktop.Notifications \
    /org/freedesktop/Notifications \
    org.freedesktop.Notifications.ToggleDND
}

remove_id() {
  dbus-send --session --type=method_call \
    --dest=org.freedesktop.Notifications \
    /org/freedesktop/Notifications \
    org.freedesktop.Notifications.RemovePopupID \
    uint32:$1
}

if [[ $1 == 'dismiss' ]]; then dismiss $2 $3; fi
if [[ $1 == 'close' ]]; then close $2; fi
if [[ $1 == 'action' ]]; then action $2 $3; fi
if [[ $1 == 'clear' ]]; then clear_all; fi
if [[ $1 == 'toggle' ]]; then toggle_dnd; fi
if [[ $1 == 'pop' ]]; then remove_id $2; fi
