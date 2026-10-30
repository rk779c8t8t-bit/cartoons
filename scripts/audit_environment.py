#!/usr/bin/env python3
"""Technical audit of the production environment.

Checks OS, Python, Node, FFmpeg/FFprobe, GPU, disk, RAM, Python libraries, Blender (bpy),
render engines, network reachability of AI generation APIs and presence (never values!)
of API-key environment variables. Writes logs/audit.json and prints a summary.

  python3 scripts/audit_environment.py            # full audit (incl. network probes)
  python3 scripts/audit_environment.py --offline  # skip network probes
"""
import argparse
import importlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Official generation APIs we would use if available (key name -> provider, probe host)
AI_PROVIDERS = {
    "OPENAI_API_KEY": ("OpenAI (gpt-image / Sora video)", "https://api.openai.com/v1/models"),
    "REPLICATE_API_TOKEN": ("Replicate (SDXL, Flux, video models)", "https://api.replicate.com/v1/models"),
    "RUNWAYML_API_SECRET": ("Runway (Gen-3/Gen-4 image-to-video)", "https://api.dev.runwayml.com"),
    "LUMAAI_API_KEY": ("Luma Dream Machine", "https://api.lumalabs.ai"),
    "FAL_KEY": ("fal.ai (Flux, Kling, Veo...)", "https://fal.run"),
    "STABILITY_API_KEY": ("Stability AI", "https://api.stability.ai"),
    "GEMINI_API_KEY": ("Google Gemini / Veo", "https://generativelanguage.googleapis.com"),
    "GOOGLE_API_KEY": ("Google Gemini / Veo", "https://generativelanguage.googleapis.com"),
    "KLING_API_KEY": ("Kling AI", "https://api.klingai.com"),
    "ELEVENLABS_API_KEY": ("ElevenLabs (SFX/music)", "https://api.elevenlabs.io"),
    "HF_TOKEN": ("Hugging Face (model downloads)", "https://huggingface.co"),
}
PY_LIBS = ["numpy", "scipy", "PIL", "bpy", "torch", "diffusers", "cv2", "moviepy", "pytest"]


def run(cmd, timeout=20):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return (r.stdout or r.stderr).strip()
    except Exception as e:  # noqa: BLE001
        return f"ERROR: {e}"


def probe(url, timeout=8):
    """HTTP reachability only (no auth, no paid request). Returns status string."""
    out = run(["curl", "-sS", "-o", "/dev/null", "-m", str(timeout), "-w", "%{http_code}", url], timeout=timeout + 4)
    if out.isdigit() and out != "000":
        return f"reachable (HTTP {out})"
    return "blocked/unreachable"


def audit(offline=False):
    A = {"time": time.strftime("%Y-%m-%d %H:%M:%S")}
    A["os"] = f"{platform.system()} {platform.release()} ({platform.machine()})"
    A["python"] = sys.version.split()[0]
    A["node"] = run(["node", "--version"]) if shutil.which("node") else "missing"
    A["ffmpeg"] = run(["ffmpeg", "-version"]).splitlines()[0] if shutil.which("ffmpeg") else "missing"
    A["ffprobe"] = run(["ffprobe", "-version"]).splitlines()[0] if shutil.which("ffprobe") else "missing"
    A["gpu"] = run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"]) if shutil.which("nvidia-smi") else "none (no nvidia-smi)"
    A["cpu_cores"] = os.cpu_count()
    try:
        with open("/proc/meminfo") as f:
            A["ram_gb"] = round(int(f.readline().split()[1]) / 1024 / 1024, 1)
    except Exception:  # noqa: BLE001
        A["ram_gb"] = "?"
    du = shutil.disk_usage(ROOT)
    A["disk_free_gb"] = round(du.free / 1e9, 1)
    libs = {}
    for lib in PY_LIBS:
        try:
            m = importlib.import_module(lib)
            libs[lib] = getattr(m, "__version__", "ok")
            if lib == "bpy":
                libs[lib] = m.app.version_string
        except Exception:  # noqa: BLE001
            libs[lib] = "missing"
    A["python_libs"] = libs
    A["imagemagick"] = "present" if shutil.which("convert") else "missing"
    A["blender_cli"] = shutil.which("blender") or "missing (using pip bpy module instead)"
    A["api_keys"] = {k: ("SET" if os.environ.get(k) else "not set") for k in AI_PROVIDERS}
    if not offline:
        seen = {}
        for k, (name, url) in AI_PROVIDERS.items():
            if url not in seen:
                seen[url] = probe(url)
        A["api_reachability"] = {AI_PROVIDERS[k][0]: seen[AI_PROVIDERS[k][1]] for k in AI_PROVIDERS}
        A["pypi_reachable"] = probe("https://pypi.org/simple/")
    usable = [AI_PROVIDERS[k][0] for k in AI_PROVIDERS
              if os.environ.get(k) and (offline or "reachable" in A.get("api_reachability", {}).get(AI_PROVIDERS[k][0], ""))]
    A["usable_ai_generators"] = usable
    A["strategy"] = ("AI image/video generation" if usable else
                     "PRIORITY 4 fallback: procedural 3D animation rendered with Blender Cycles (bpy), "
                     "synthesized music/SFX (numpy/scipy), assembled with FFmpeg")
    return A


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true")
    a = ap.parse_args()
    A = audit(a.offline)
    os.makedirs(os.path.join(ROOT, "logs"), exist_ok=True)
    with open(os.path.join(ROOT, "logs", "audit.json"), "w") as f:
        json.dump(A, f, indent=2, ensure_ascii=False)
    for k, v in A.items():
        if isinstance(v, dict):
            print(f"{k}:")
            for kk, vv in v.items():
                print(f"   {kk:42s} {vv}")
        else:
            print(f"{k:20s} {v}")
    return A


if __name__ == "__main__":
    main()
