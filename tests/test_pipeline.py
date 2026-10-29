"""Fast checks that run without Blender: python3 -m pytest tests (or python3 tests/test_pipeline.py)."""
import ast
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from common_cfg import load_config, shot_frames, shot_starts  # noqa: E402


def test_timeline_is_36_seconds():
    cfg = load_config()
    _, total = shot_starts(cfg)
    assert total == cfg["video"]["duration_s"] * cfg["video"]["fps"] == 1080
    assert len(cfg["shots"]) == 9


def test_tails_match_blender_scenes():
    src = open(os.path.join(ROOT, "scripts", "blender", "scenes.py")).read()
    tail = ast.literal_eval(re.search(r"TAIL = (\{.*?\})", src).group(1))
    cfg = load_config()
    for s in cfg["shots"]:
        assert tail[s["id"]] == s.get("tail", 0), s["id"]
        assert shot_frames(cfg, s["id"]) == 120 + tail[s["id"]]


def test_dissolve_tails_fit():
    from assemble_video import timeline
    cfg = load_config()
    tl = timeline(cfg)
    assert len(tl) == 1080
    for shot, f, ps, pf, a in tl:
        if ps is not None:
            assert pf <= shot_frames(cfg, ps) and 0 < a < 1


def test_all_scripts_parse():
    for d in ("scripts", os.path.join("scripts", "blender")):
        for f in os.listdir(os.path.join(ROOT, d)):
            if f.endswith(".py"):
                ast.parse(open(os.path.join(ROOT, d, f)).read())


def test_audio_stems_if_present():
    from scipy.io import wavfile
    for name in ("music", "foley", "ambience"):
        p = os.path.join(ROOT, "assets", "audio", name + ".wav")
        if os.path.exists(p):
            sr, x = wavfile.read(p)
            assert abs(len(x) / sr - 36.0) < 0.01
            assert abs(x).max() < 32767


if __name__ == "__main__":
    for k, v in list(globals().items()):
        if k.startswith("test_"):
            v()
            print("ok", k)
