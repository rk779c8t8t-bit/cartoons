"""Shared config helpers for the pipeline scripts."""
import os
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_config():
    with open(os.path.join(ROOT, "config", "project.yaml")) as f:
        return yaml.safe_load(f)


def shot_frames(cfg, shot):
    """Frames rendered for a shot = its own duration + tail used for the dissolve into the next shot."""
    s = cfg["shots"][shot - 1]
    return s["frames"] + s.get("tail", 0)


def shot_starts(cfg):
    """Start frame (0-based) of each shot on the final timeline."""
    starts, t = [], 0
    for s in cfg["shots"]:
        starts.append(t)
        t += s["frames"]
    return starts, t
