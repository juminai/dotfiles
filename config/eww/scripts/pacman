#!/bin/bash

while true; do
  pkgs="$(yay -Q | wc -l)"

  updates_arch=$(checkupdates 2>/dev/null | wc -l)
  updates_arch=${updates_arch:-0}

  updates_aur=$(yay -Qum 2>/dev/null | wc -l)
  updates_aur=${updates_aur:-0}

  updates=$((updates_arch + updates_aur))

  echo '{"packages": '$pkgs', "updates": '$updates'}'
  sleep 600
done
