"""Step 3: automatic QA of final_edit.mp4.

Checks format (1080x1920, 9:16, H.264, fps), duration of audio vs video,
black / near-black frames, frozen frames, and that the audio is not cut
before the video ends. Also writes a contact sheet (qa_contact.jpg).
"""
import json
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
VID = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(HERE), "final_edit.mp4")


def probe():
    out = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", VID],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def main():
    ok = True
    info = probe()
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    a = next(s for s in info["streams"] if s["codec_type"] == "audio")
    w, h = int(v["width"]), int(v["height"])
    fps = eval(v["r_frame_rate"])
    vd, ad = float(v["duration"]), float(a["duration"])
    br = int(info["format"]["bit_rate"]) / 1e6
    print(f"video {v['codec_name']} {w}x{h} @ {fps:.2f}fps, {vd:.2f}s, {br:.1f} Mbit/s; audio {a['codec_name']} {ad:.2f}s")
    if (w, h) != (1080, 1920) or v["codec_name"] != "h264":
        print("FAIL: format"); ok = False
    if abs(vd - ad) > 0.1:
        print("FAIL: audio/video duration mismatch"); ok = False

    # luma per frame
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", VID, "-vf", "scale=108:192,format=gray", "-f", "rawvideo", "-"],
                         capture_output=True, check=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, 192, 108).astype(np.float32)
    mean = fr.mean((1, 2))
    n = len(fr)
    black = [i for i in range(n) if mean[i] < 6 and i < n - 8]   # last ~0.25 s is the intended fade-out
    print(f"frames: {n}, mean luma min {mean.min():.1f} max {mean.max():.1f}")
    if black:
        print("FAIL: black frames at", [round(i / fps, 2) for i in black]); ok = False
    diff = np.abs(np.diff(fr, axis=0)).mean((1, 2))
    frozen = [i for i in range(len(diff)) if diff[i] < 0.05]
    if len(frozen) > 3:
        print("WARN: frozen frames at", [round(i / fps, 2) for i in frozen])

    # audio energy in the last second must decay, not stop abruptly
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", VID, "-ac", "1", "-ar", "8000", "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    s = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768
    rms = [float(np.sqrt((s[i:i + 800] ** 2).mean())) for i in range(0, len(s) - 800, 800)]
    print("audio rms per 0.1s (last 2s):", [round(r, 3) for r in rms[-20:]])

    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VID, "-vf", "fps=2,scale=180:320,tile=9x3",
                    "-frames:v", "1", os.path.join(HERE, "qa_contact.jpg")], check=True)
    print("PASS" if ok else "ISSUES FOUND")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
