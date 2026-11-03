#!/usr/bin/env bash
# Извлекает аудио из исходника: tools/prepare_audio.sh input.mov|mp3|wav
set -e; cd "$(dirname "$0")/.."; mkdir -p src/audio work
ffmpeg -v error -y -i "$1" -vn -c:a aac -b:a 256k src/audio/song.m4a 2>/dev/null || true
case "$1" in *.mov|*.mp4|*.m4a) ffmpeg -v error -y -i "$1" -vn -c:a copy src/audio/song.m4a;; esac
ffmpeg -v error -y -i src/audio/song.m4a -ac 1 -ar 16000 work/song16k.wav
ffmpeg -v error -y -i src/audio/song.m4a -af "pan=mono|c0=0.5*c0+0.5*c1,highpass=f=150,lowpass=f=6000,dynaudnorm" -ar 16000 work/voc16k.wav
