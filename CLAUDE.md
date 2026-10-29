# CLAUDE.md

Project: vertical 3D animated short «Над котёнком все смеялись» built fully locally (no GPU, no API keys).

- One command: `python3 run.py` (`--dry-run`, `--force-shot N`, `--force-all`, `--preview`).
- Shots live in `scripts/blender/scenes.py` (`shot1()`…`shot9()`), characters in `scripts/blender/characters.py`
  (design constants = `CHARACTERS`, keep in sync with `docs/character_bible.md`), environment in `scripts/blender/env.py`.
- Keyframing rules: `Actor.key()` keys every channel and must be called in chronological order per actor;
  use `Actor.key_only()` / `hold_only()` for channels keyed inside a `walk()` span.
- Character conventions: faces -Y at rot=0; `spine_rx>0` leans forward; `head_rx>0` looks down; `sh_*_x>0` swings arm forward.
- Timeline/tails: `config/project.yaml` and `TAIL` in `scenes.py` must match.
- Rendering is slow (~13 s/frame on CPU). Preview with `scripts/contact_sheet.py` on low-res frames before a full render.
- Frames: `assets/generated/frames/` (git-ignored). Final: `output/final_short.mp4`.
- Never print API key values; never add paid services without the user's consent.
