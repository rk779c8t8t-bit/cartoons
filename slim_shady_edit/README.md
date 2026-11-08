# Eminem — Slim Shady lyric edit

Vertical 1080×1920, 60 fps, H.264 + AAC 320k, 23.3 s. Result: `output/eminem_slim_shady_lyric_edit.mp4`.

- `engine.py` — small motion-graphics engine (rough-edged Anton type, camera/shake, masks, shapes, grain, 2-sample motion blur).
- `scenes.py` — the timeline: 17 scenes, each with its own animation; word times in track seconds.
- `render.py` — `audio <song.mp3>` (cuts 17.82–40.07 s + echo tail on "Shady"), `sheet t1 t2…` (preview frames), `video [fps]`.

Sync: word timestamps from offline ASR (sherpa-onnx zipformer) cross-checked with vocal onsets; tempo ≈103.4 BPM.
Requires: numpy, opencv-python-headless, pillow, librosa, soundfile, scipy, ffmpeg.
