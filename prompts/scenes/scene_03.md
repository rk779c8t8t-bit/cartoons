# Scene 03 — A friend appears (00:08–00:12)

## Image / video generator prompt (English)
Original high-end cinematic 3D animated family short film, adorable expressive anthropomorphic animal characters, consistent character design, finely detailed soft fur, realistic fur shading, expressive large eyes, physically based materials, global illumination, cinematic lighting, beautiful volumetric sunlight, subtle depth of field, carefully composed vertical frame, natural body mechanics, appealing facial animation, premium animated film quality, detailed environment, believable shadows, smooth camera movement, rich but controlled color palette, emotionally expressive storytelling, polished render, portrait 9:16 composition.

**Action.** Light rain. Ryzhik stands alone against the school wall hugging himself. The puppy walks in carrying a closed yellow umbrella, raises it and opens it above both of them. Ryzhik notices the rain has stopped hitting him, looks up surprised, turns to the puppy and gives a small grateful smile; the puppy smiles and wags his tail.

**Characters (fixed design, identical in every shot — see docs/character_bible.md):**
- RYZHIK: small light-ginger kitten, child proportions, big round head with full cream cheeks, large amber eyes with dark rims and two catchlights, small pink nose, ω-shaped mouth, triangular ears with pink insides, faint tabby 'M' on forehead, long striped ginger tail, faded worn light-blue school jacket (#86b4d6) with a darker blue patch on the chest and three cream buttons, scuffed brown leather boots (#7a4a2a), small navy backpack (#22336b)
- DRUZHOK: small cream puppy (#efd9b4) with a brown patch around the left eye, soft floppy brown ears, warm brown eyes, big dark nose, bright cobalt-blue jacket (#2f6fd0) with yellow buttons, red rubber boots, bright yellow umbrella

**Emotion.** loneliness turning into warmth and gratitude

**Location.** school wall with a window and flower box, wet paving with puddles and ripples

**Lighting & palette.** cold blue-grey rain light outside, warm yellow glow reflected from the umbrella onto both faces

**Camera.** Intimate two-shot from the front-right (34→42 mm), slow push-in.

**Start → end of the action.** Start: kitten alone in rain. End: both under the open umbrella, kitten smiling.

**Vertical 9:16 composition.** Umbrella canopy across the top of the frame, both characters full-height below it, rain streaks in front and behind.

**References.** Use the character reference images in `assets/references/` (`<id>_front.png`, `_threequarter.png`, `_side.png`, `_face.png`) as character/identity references; keep the same seed/model for all scenes if the generator supports it.

## Negative prompt
No dialogue, no text, no subtitles, no logos, no watermark, no extra limbs, no duplicated characters, no distorted paws, no changing clothes, no inconsistent fur color, no flickering facial features, no malformed eyes, no floating props, no abrupt identity changes, no random background characters blocking the action, no graphic injury, no blood, no horror aesthetic.

## How this scene is actually produced in this project
No external generator API was available (see docs/technical_audit.md), so the scene is built and keyframed in code:
`scripts/blender/scenes.py → shot3()` (procedural characters, environment, per-frame character animation, camera moves),
rendered with Blender EEVEE by `scripts/animate_scenes.py`.
