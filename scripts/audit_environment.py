#!/usr/bin/env python3
"""Environment audit: tools, hardware, libraries and *presence* (never values) of API keys.
Writes logs/environment.json. Exit code 1 if a mandatory tool is missing."""
import json
import os
import platform
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# generative services we could use if a key were configured (presence check only)
KEY_NAMES = ["OPENAI_API_KEY", "REPLICATE_API_TOKEN", "STABILITY_API_KEY", "RUNWAYML_API_SECRET", "LUMAAI_API_KEY",
             "FAL_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEY", "ELEVENLABS_API_KEY", "KLING_ACCESS_KEY", "PIKA_API_KEY",
             "HF_TOKEN"]
MANDATORY = ["blender", "ffmpeg", "ffprobe", "fluidsynth"]


def out(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=60).stdout.strip()
    except Exception as e:  # noqa: BLE001
        return f"n/a ({e.__class__.__name__})"


def main():
    info = {
        "os": platform.platform(),
        "python": sys.version.split()[0],
        "cpu_count": os.cpu_count(),
        "tools": {},
        "gpu": None,
        "python_libs": {},
        "api_keys_present": {},
    }
    for t in MANDATORY + ["node", "nvidia-smi"]:
        p = shutil.which(t)
        ver = ""
        if p:
            flag = {"node": "--version", "ffmpeg": "-version", "ffprobe": "-version", "nvidia-smi": "-L"}.get(t, "--version")
            lines = out([t, flag]).splitlines()
            ver = lines[0] if lines else ""
        info["tools"][t] = {"path": p, "version": ver}
    info["gpu"] = out(["nvidia-smi", "-L"]) if shutil.which("nvidia-smi") else "no NVIDIA GPU / driver detected"
    du = shutil.disk_usage(ROOT)
    info["disk_free_gb"] = round(du.free / 1e9, 1)
    try:
        with open("/proc/meminfo") as f:
            info["ram_gb"] = round(int(f.readline().split()[1]) / 1e6, 1)
    except OSError:
        pass
    for lib in ("numpy", "scipy", "PIL", "yaml"):
        try:
            m = __import__(lib)
            info["python_libs"][lib] = getattr(m, "__version__", "ok")
        except ImportError:
            info["python_libs"][lib] = None
    for k in KEY_NAMES:
        info["api_keys_present"][k] = bool(os.environ.get(k))
    sf = [s for s in ("/usr/share/sounds/sf2/FluidR3_GM.sf2",) if os.path.exists(s)]
    info["soundfont"] = sf[0] if sf else None
    os.makedirs(os.path.join(ROOT, "logs"), exist_ok=True)
    with open(os.path.join(ROOT, "logs", "environment.json"), "w") as f:
        json.dump(info, f, indent=2)
    print(json.dumps(info, indent=2))
    missing = [t for t in MANDATORY if not info["tools"][t]["path"]]
    if missing:
        print("MISSING mandatory tools:", missing, "-> sudo apt-get install blender ffmpeg fluidsynth fluid-soundfont-gm")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
