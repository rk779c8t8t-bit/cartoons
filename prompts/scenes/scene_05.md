# Scene 05 — Ryzhik's decision (00:16–00:20)

## Image / video generator prompt (English)
Original high-end cinematic 3D animated family short film, adorable expressive anthropomorphic animal characters, consistent character design, finely detailed soft fur, realistic fur shading, expressive large eyes, physically based materials, global illumination, cinematic lighting, beautiful volumetric sunlight, subtle depth of field, carefully composed vertical frame, natural body mechanics, appealing facial animation, premium animated film quality, detailed environment, believable shadows, smooth camera movement, rich but controlled color palette, emotionally expressive storytelling, polished render, portrait 9:16 composition.

**Action.** Close-up of Ryzhik's amber eyes: fear. He looks at the frightened rabbit, then at a wooden board lying by the path. His brows set — determination. He slips off his backpack, leaves it on the ground and runs to the board, grabbing its end.

**Characters (fixed design, identical in every shot — see docs/character_bible.md):**
- RYZHIK: small light-ginger kitten, child proportions, big round head with full cream cheeks, large amber eyes with dark rims and two catchlights, small pink nose, ω-shaped mouth, triangular ears with pink insides, faint tabby 'M' on forehead, long striped ginger tail, faded worn light-blue school jacket (#86b4d6) with a darker blue patch on the chest and three cream buttons, scuffed brown leather boots (#7a4a2a), small navy backpack (#22336b)

**Emotion.** fear → determination

**Location.** garden path, the board on the paving

**Lighting & palette.** windy daylight; tight warm light on his face

**Camera.** Close-up at eye level (60 mm), then a low tracking camera following him at kitten eye level (30–34 mm).

**Start → end of the action.** Start: face close-up. End: kitten bent over the board, paws on its edge.

**Vertical 9:16 composition.** Face fills the frame at first; during the run the kitten stays in the lower-middle third.

**References.** Use the character reference images in `assets/references/` (`<id>_front.png`, `_threequarter.png`, `_side.png`, `_face.png`) as character/identity references; keep the same seed/model for all scenes if the generator supports it.

## Negative prompt
No dialogue, no text, no subtitles, no logos, no watermark, no extra limbs, no duplicated characters, no distorted paws, no changing clothes, no inconsistent fur color, no flickering facial features, no malformed eyes, no floating props, no abrupt identity changes, no random background characters blocking the action, no graphic injury, no blood, no horror aesthetic.

## How this scene is actually produced in this project
No external generator API was available (see docs/technical_audit.md), so the scene is built and keyframed in code:
`scripts/blender/scenes.py → shot5()` (procedural characters, environment, per-frame character animation, camera moves),
rendered with Blender EEVEE by `scripts/animate_scenes.py`.
