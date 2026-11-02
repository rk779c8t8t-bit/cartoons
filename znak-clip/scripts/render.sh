#!/usr/bin/env bash
# Full render: 1080x1920, 30fps, H.264 + AAC 320k.
set -e
cd "$(dirname "$0")/.."
npx remotion render src/index.ts ZnakDora out/znak_dora_verse.mp4 \
  --codec=h264 --crf=17 --pixel-format=yuv420p \
  --audio-codec=aac --audio-bitrate=320k \
  --concurrency=4 --log=info
