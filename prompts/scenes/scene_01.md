# Scene 01 — Introduction (00:00–00:04)

## Image / video generator prompt (English)
Original high-end cinematic 3D animated family short film, adorable expressive anthropomorphic animal characters, consistent character design, finely detailed soft fur, realistic fur shading, expressive large eyes, physically based materials, global illumination, cinematic lighting, beautiful volumetric sunlight, subtle depth of field, carefully composed vertical frame, natural body mechanics, appealing facial animation, premium animated film quality, detailed environment, believable shadows, smooth camera movement, rich but controlled color palette, emotionally expressive storytelling, polished render, portrait 9:16 composition.

**Action.** Morning. Ryzhik walks along the front of a cosy animal school toward its arched wooden door, hugging his small navy backpack to his chest. He stops, looks up at the building, then turns his head toward camera with a shy, hopeful smile.

**Characters (fixed design, identical in every shot — see docs/character_bible.md):**
- RYZHIK: small light-ginger kitten, child proportions, big round head with full cream cheeks, large amber eyes with dark rims and two catchlights, small pink nose, ω-shaped mouth, triangular ears with pink insides, faint tabby 'M' on forehead, long striped ginger tail, faded worn light-blue school jacket (#86b4d6) with a darker blue patch on the chest and three cream buttons, scuffed brown leather boots (#7a4a2a), small navy backpack (#22336b)

**Emotion.** hope, slight nervousness

**Location.** sunny school courtyard paved with light stone, cream two-storey school with terracotta roof, little bell tower, flower boxes, round topiary planters, lamp posts, white fence, green trees, blue sky with soft clouds

**Lighting & palette.** low warm morning sun from front-left, soft blue fill, golden highlights on fur, gentle leaf motion; palette cream, terracotta, sky blue, ginger

**Camera.** Start: high wide establishing shot (22 mm) showing the whole school with the tiny kitten. Crane down to ground level on his scuffed boots (40 mm), then rise smoothly to a medium close-up of his face (48 mm).

**Start → end of the action.** Start: kitten small, walking from frame left. End: medium close-up, kitten looking toward camera with a shy smile, school door behind him.

**Vertical 9:16 composition.** School and sky in the upper third, kitten on the lower third; boots fill the frame during the tilt; final face close-up centred with headroom for the ears.

**References.** Use the character reference images in `assets/references/` (`<id>_front.png`, `_threequarter.png`, `_side.png`, `_face.png`) as character/identity references; keep the same seed/model for all scenes if the generator supports it.

## Negative prompt
No dialogue, no text, no subtitles, no logos, no watermark, no extra limbs, no duplicated characters, no distorted paws, no changing clothes, no inconsistent fur color, no flickering facial features, no malformed eyes, no floating props, no abrupt identity changes, no random background characters blocking the action, no graphic injury, no blood, no horror aesthetic.

## How this scene is actually produced in this project
No external generator API was available (see docs/technical_audit.md), so the scene is built and keyframed in code:
`scripts/blender/scenes.py → shot1()` (procedural characters, environment, per-frame character animation, camera moves),
rendered with Blender EEVEE by `scripts/animate_scenes.py`.
