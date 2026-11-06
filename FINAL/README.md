# Eminem × Toly Summer — "TWO WORLDS" music edit

| File | What it is |
|---|---|
| `final_edit.mp4` | Finished edit: 1080×1920 (9:16), 30 fps, H.264 High, AAC 320 kbps, ~13 s, ready for TikTok / Reels |
| `original_audio.wav` | Audio extracted losslessly from the reference video (PCM 16-bit, 44.1 kHz) |
| `project_files/` | Everything needed to rebuild or change the edit |

## The idea

This is a new visual story, not a copy of the reference. Two worlds collide.

* **Toly Summer** lives in a warm, golden **mountain realm**: sun rays, fog, gold dust, the fairy on his sleeve.
* **Eminem** lives in a cold **steel world**: concrete, blue backlight, light beams, falling ash.
* The edit cuts between the two worlds faster and faster. It merges them in a double exposure (Eminem's face in the sky over Toly's mountains), goes almost dark during the silence before the drop, and on the drop explodes into a **face-off** split with a glowing seam, a shockwave and a gold particle burst.

## Music map (librosa analysis)

* Tempo **≈114 BPM**. The kick enters at **3.70 s** and repeats every 0.525 s.
* Intro accents: 0.03, 0.84, 1.35, 1.76, **2.11** (strongest hi-hat), 3.03, 3.40.
* Silence at 10.75–10.83 s, then the **drop at 10.86 s** (the loudest moment) and a second swell at 11.36 s.
* The music in the reference ends at ~11.8 s; after that comes the TikTok outro, which is dropped. To keep the ending from sounding cut off, the drop gets a filtered echo tail that fades out by 13.0 s.

| Time | Section | What happens |
|---|---|---|
| 0.00–0.84 | INTRO | Toly's eyes come out of darkness as a light sweep passes over |
| 0.84–2.11 | INTRO | Whip-zoom out into the realm → glitch cut to Eminem's eyes → orbit around Eminem → flash |
| 2.11–3.70 | BUILD UP | Tilt up the golden vest → Eminem in light beams → diagonal split → push into the fairy, white-out |
| 3.70–6.85 | MAIN | Hero shots from below on every kick, extreme close-ups, zoom punch on the snare, sliding "eye strips" that swap on the kick |
| 6.85–8.95 | MAIN | Eminem with motion echo trails → double exposure → half-beat quick cuts (mouth / eyes / earring / vest) |
| 8.95–10.86 | FINAL | Worlds merge (double exposure) → stutter alternation with rising tension → near-dark "breath" |
| 10.86–13.0 | DROP | Face-off split, shockwave, particle burst, heavy shake, slow push, glow fade-out |

Effects used: speed ramps, motion blur (4 sub-frames, 180° shutter), zoom/whip blur, beat-synced head nods and turns, 2.5D parallax and camera "orbit" (perspective yaw), flashes, shake, glitch, chromatic aberration, shockwave, bloom, light leaks, god rays, fog, particles, a separate colour grade for each world, vignette and film grain. There is no text and there are no watermarks.

## Rebuilding

Requirements: Python 3.10+, FFmpeg, and
`pip install numpy opencv-contrib-python-headless rembg onnxruntime librosa torch`.
Torch is only needed for the Real-ESRGAN upscale.

```bash
cd project_files
# optional, for the best faces: put RealESRGAN_x4plus.pth into project_files/models/
#   https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth
python3 prep.py          # audio extract, 4x upscale, cutouts, background plates -> assets/build/
python3 render.py        # renders ../final_edit.mp4 (about 4–6 min on 4 CPU cores)
python3 check.py         # QA: format, black frames, A/V length, audio tail, contact sheet
```

Faster iteration:

```bash
python3 render.py --still 3.9 10.9          # PNG/JPG stills of chosen moments -> stills/
python3 render.py --preview --out test.mp4  # half-res, no motion blur
python3 render.py --start 8 --end 11        # render only a range
```

## Editing guide (all in `render.py`)

* **Cut times:** `SHOTS` holds (start, end, shot function). `KICKS`, `DROP` and `INTRO_HITS` hold the beat grid.
* **Flash / shake / glitch timing:** `FLASH_HITS`, `SHAKE_HITS`, `GLITCH_WIN` hold (time, strength) entries.
* **Framing of a shot:** every `sh_*` function calls `char_cam(char, focus, face_width_px, screen_pos, rot, yaw, pitch)`. `focus` is a facial landmark (`eyes`, `mouth`, `fairy`, `vest`, `earring`, …) defined in `load_assets`.
* **Head motion:** the third argument of `person(ch, M, (turn_deg, nod_px, sway_px))`. `beat_nod()` makes the nod hit on each kick.
* **Colours:** `grade()` holds the looks `realm`, `steel` and `duo`.
* **Audio ending:** `make_audio()`.

## Tools and limits

* Free tools only: FFmpeg, OpenCV, NumPy, librosa (beat analysis), rembg/IS-Net (cutouts), and Real-ESRGAN x4plus on CPU (cleaner, sharper faces). No paid APIs or keys.
* No video or image generation model was reachable from the build machine (no GPU, and model hubs were blocked). Every frame is therefore built from the two supplied photos, which keeps both faces exactly as in the references. Movement comes from camera work, parallax, perspective "orbits" and a localized head-turn/nod warp. Facial expressions (mouth, eyes) are not changed, because faking them without a proper model would distort the faces.
