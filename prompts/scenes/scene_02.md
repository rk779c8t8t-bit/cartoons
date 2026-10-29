# Scene 02 — Teasing (00:04–00:08)

## Image / video generator prompt (English)
Original high-end cinematic 3D animated family short film, adorable expressive anthropomorphic animal characters, consistent character design, finely detailed soft fur, realistic fur shading, expressive large eyes, physically based materials, global illumination, cinematic lighting, beautiful volumetric sunlight, subtle depth of field, carefully composed vertical frame, natural body mechanics, appealing facial animation, premium animated film quality, detailed environment, believable shadows, smooth camera movement, rich but controlled color palette, emotionally expressive storytelling, polished render, portrait 9:16 composition.

**Action.** Near the school steps the fox kit notices Ryzhik's worn boots, nudges the raccoon; both giggle thoughtlessly and the fox points at the boots. Ryzhik's smile fades, his ears droop, he looks down, turns away and crouches, trying to hide his boots with his paws.

**Characters (fixed design, identical in every shot — see docs/character_bible.md):**
- RYZHIK: small light-ginger kitten, child proportions, big round head with full cream cheeks, large amber eyes with dark rims and two catchlights, small pink nose, ω-shaped mouth, triangular ears with pink insides, faint tabby 'M' on forehead, long striped ginger tail, faded worn light-blue school jacket (#86b4d6) with a darker blue patch on the chest and three cream buttons, scuffed brown leather boots (#7a4a2a), small navy backpack (#22336b)
- FOX: beige (not orange) fox kit (#d9b98a), white cheeks and muzzle, pointed muzzle, big ears with dark tips, neatly combed forelock, olive-green eyes, green school vest (#3f9a55) with V-neck over a white shirt, shiny black shoes, bushy tail with white tip
- RACCOON: grey raccoon kit (#8e9096), dark eye mask, light muzzle, round ears, dark brown eyes, ringed tail, burgundy school vest (#8a2234) over a white shirt, white sneakers with burgundy stripe

**Emotion.** embarrassment; the teasers show ordinary childish tactlessness, not cruelty

**Location.** same courtyard at the entrance steps, clouds rolling in

**Lighting & palette.** overcast, cooler and desaturated light, soft shadows; restrained palette

**Camera.** Medium over-the-shoulder shot on the two classmates (32 mm), then push in and down to a low emotional close-up of Ryzhik (42 mm).

**Start → end of the action.** Start: fox and raccoon chatting. End: close-up of crouched Ryzhik with lowered ears and sad brows.

**Vertical 9:16 composition.** Teasers in the upper-middle of the frame, later Ryzhik's face fills the upper half with his paws over the boots at the bottom.

**References.** Use the character reference images in `assets/references/` (`<id>_front.png`, `_threequarter.png`, `_side.png`, `_face.png`) as character/identity references; keep the same seed/model for all scenes if the generator supports it.

## Negative prompt
No dialogue, no text, no subtitles, no logos, no watermark, no extra limbs, no duplicated characters, no distorted paws, no changing clothes, no inconsistent fur color, no flickering facial features, no malformed eyes, no floating props, no abrupt identity changes, no random background characters blocking the action, no graphic injury, no blood, no horror aesthetic.

## How this scene is actually produced in this project
No external generator API was available (see docs/technical_audit.md), so the scene is built and keyframed in code:
`scripts/blender/scenes.py → shot2()` (procedural characters, environment, per-frame character animation, camera moves),
rendered with Blender EEVEE by `scripts/animate_scenes.py`.
