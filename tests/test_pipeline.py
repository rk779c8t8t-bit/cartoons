"""Fast tests (no rendering): timeline consistency, easing math, audio synthesis, final video."""
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from lbs3d import timeline  # noqa: E402


def test_timeline_length():
    assert timeline.N_SCENES == 9
    assert 30 <= timeline.DURATION <= 40
    assert timeline.DURATION == 36


def test_cues_inside_film_and_sorted():
    times = [c[0] for c in timeline.SFX_CUES]
    assert times == sorted(times)
    assert all(0 <= t < timeline.DURATION for t in times)


def test_every_scene_has_sound_events():
    for k in range(timeline.N_SCENES):
        assert any(k * 4 <= c[0] < (k + 1) * 4 for c in timeline.SFX_CUES), f"scene {k + 1} has no cue"


def test_kf_and_easing():
    pytest.importorskip("bpy")
    from lbs3d.core import kf, smooth, seg
    assert kf(0.5, [(0, 0.0), (1, 1.0)], ease=lambda x: x) == pytest.approx(0.5)
    assert smooth(0) == 0 and smooth(1) == 1
    assert seg(5, 0, 10) == 0.5


def test_audio_cue_synthesis_produces_sound():
    import numpy as np
    import create_audio as ca
    for _, name, _ in timeline.SFX_CUES:
        x = ca.fx(name)
        assert np.isfinite(x).all()
        assert np.max(np.abs(x)) > 1e-3, name


@pytest.mark.skipif(not os.path.exists(os.path.join(ROOT, "output", "final_short.mp4")), reason="video not built")
def test_final_video_specs():
    out = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json",
                          os.path.join(ROOT, "output", "final_short.mp4")], capture_output=True, text=True).stdout
    P = json.loads(out)
    v = [s for s in P["streams"] if s["codec_type"] == "video"][0]
    a = [s for s in P["streams"] if s["codec_type"] == "audio"][0]
    assert (v["width"], v["height"]) == (1080, 1920)
    assert v["codec_name"] == "h264" and a["codec_name"] == "aac"
    assert v["r_frame_rate"] == "30/1"
    assert 30 <= float(P["format"]["duration"]) <= 40
