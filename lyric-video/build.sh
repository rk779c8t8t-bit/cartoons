#!/usr/bin/env bash
# Полная сборка: анализ -> рендер кадров (параллельно) -> склейка -> оригинальная аудиодорожка
# ./build.sh song.mp3 asr.json [lyrics.txt] [out.mp4]
set -euo pipefail
cd "$(dirname "$0")"
SONG=$1; ASR=$2; LYR=${3:-}; OUT=${4:-build/lyric_video.mp4}
JOBS=${JOBS:-4}
python3 prepare.py "$SONG" "$ASR" $LYR
N=$(node -e "const fs=require('fs');eval(fs.readFileSync('build/data.js','utf8').replace('window.DATA','global.D'));console.log(Math.ceil(D.dur*D.fps))")
CH=$(( (N + JOBS - 1) / JOBS ))
rm -f build/part_*.mp4 build/parts.txt
for ((j=0;j<JOBS;j++)); do
  S=$((j*CH)); E=$(( S+CH < N ? S+CH : N ))
  node render.js build/part_$j.mp4 $S $E &
  echo "file 'part_$j.mp4'" >> build/parts.txt
done
wait
ffmpeg -v error -y -f concat -safe 0 -i build/parts.txt -c copy build/video_only.mp4
# аудио: AAC 320 kbps — воспроизводится на iPhone, в TikTok, Reels и Shorts
ffmpeg -v error -y -i build/video_only.mp4 -i "$SONG" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k -movflags +faststart "$OUT"
echo "DONE -> $OUT ($N frames)"
