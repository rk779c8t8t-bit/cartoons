#!/usr/bin/env bash
# Контактный лист кадров: tools/sheet.sh "0.5,2,..." out.jpg
set -e; D=$(mktemp -d); node "$(dirname "$0")/render.js" --stills "$1" "$D"
ffmpeg -v error -y -pattern_type glob -i "$D/*.jpg" -vf "scale=270:480,tile=6x$(( ($(echo "$1" | tr ',' '\n' | wc -l)+5)/6 )):padding=4" -frames:v 1 "$2"; rm -rf "$D"
