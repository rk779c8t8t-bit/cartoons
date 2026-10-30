# CLAUDE.md — notes for agents working on this repo

Project: 36 s vertical (1080x1920, 30 fps) wordless 3D cartoon "The Kitten Who Opened a Restaurant"
for the YouTube channel "Little Big Stories".

## How it works
- No AI generators are available in the build environment (no keys, APIs blocked, no GPU). The film is
  procedural 3D: `scripts/lbs3d/` builds characters/kitchen with Blender's `bpy` module and renders with Cycles CPU.
- `scripts/lbs3d/scenes.py`: `Production.frame(scene, t)` sets the whole world state for time `t` (seconds inside
  the scene). Frames are pure functions of (scene, t) -> any frame can be re-rendered independently.
- `scripts/lbs3d/timeline.py` is the single source of truth for scene timing and SFX cue times (shared by audio).
  If you move an on-screen event, move its cue too.
- Character designs are constants in `characters.py` (`MILO`, `MOM`). Do not change them per scene.

## Conventions in the rig
- Characters face -Y (toward the default camera). `rz` > 0 turns them toward +X.
- `lean` > 0 bows forward; `head=(up, tilt, turn)`; arm Euler x < 0 raises the arm forward.
- Arm index 0 = the -X side, index 1 = the +X side (`arm_l` / `arm_r` in `pose()`).
- Countertop surface is z=0, floor is z=-0.92.

## Commands
- `python3 run.py --dry-run` – audit + plan, no rendering
- `python3 run.py --scene N` – re-render one scene, reassemble, validate
- `python3 scripts/animate_scenes.py --scenes all --keyframes 0.3,1.5,2.5,3.6 --width 216 --height 384 --samples 6`
  – quick storyboard stills to check choreography (~1 s per still)
- `python3 -m pytest -q tests`

## Gotchas
- Python must be 3.13 for the bpy 5.2 wheel.
- Render cost ~7.5 s/frame at 540x960, 8 spp on 4 cores. Subsurface is disabled (`core.USE_SSS`) for speed.
- `assets/generated/frames/` is git-ignored (hundreds of MB).
- Never print API key values; `audit_environment.py` only reports SET / not set.
