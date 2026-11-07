#!/bin/bash
# Usage: render_all.sh <scratch_dir_with_assets_fonts_mix> <output.mp4>
set -e
S=$1; OUT=$2; HERE=$(cd "$(dirname "$0")" && pwd)
NF=828; J=4; STEP=$(( (NF + J - 1) / J ))
pids=()
for i in $(seq 0 $((J-1))); do
  st=$((i*STEP)); en=$(( (i+1)*STEP ))
  python3 "$HERE/render.py" --assets $S/assets --fonts $S/fonts --audio $S/mix.wav --start $st --end $en --out $S/seg$i.mp4 > $S/log$i.txt 2>&1 &
  pids+=($!)
done
for p in "${pids[@]}"; do wait $p; done
rm -f $S/list.txt; for i in $(seq 0 $((J-1))); do echo "file '$S/seg$i.mp4'" >> $S/list.txt; done
ffmpeg -v error -y -f concat -safe 0 -i $S/list.txt -i $S/mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -movflags +faststart -shortest "$OUT"
echo done
