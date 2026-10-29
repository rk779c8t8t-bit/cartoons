# Scene 07 — Realisation (00:24–00:28)

## Image / video generator prompt (English)
Original high-end cinematic 3D animated family short film, adorable expressive anthropomorphic animal characters, consistent character design, finely detailed soft fur, realistic fur shading, expressive large eyes, physically based materials, global illumination, cinematic lighting, beautiful volumetric sunlight, subtle depth of field, carefully composed vertical frame, natural body mechanics, appealing facial animation, premium animated film quality, detailed environment, believable shadows, smooth camera movement, rich but controlled color palette, emotionally expressive storytelling, polished render, portrait 9:16 composition.

**Action.** The rescued rabbit runs up and hugs Ryzhik. The puppy stands proudly, wagging. The fox and raccoon watch in surprise, exchange guilty looks and lower their ears. The sun breaks through.

**Characters (fixed design, identical in every shot — see docs/character_bible.md):**
- RYZHIK: small light-ginger kitten, child proportions, big round head with full cream cheeks, large amber eyes with dark rims and two catchlights, small pink nose, ω-shaped mouth, triangular ears with pink insides, faint tabby 'M' on forehead, long striped ginger tail, faded worn light-blue school jacket (#86b4d6) with a darker blue patch on the chest and three cream buttons, scuffed brown leather boots (#7a4a2a), small navy backpack (#22336b)
- DRUZHOK: small cream puppy (#efd9b4) with a brown patch around the left eye, soft floppy brown ears, warm brown eyes, big dark nose, bright cobalt-blue jacket (#2f6fd0) with yellow buttons, red rubber boots, bright yellow umbrella
- PUSHINKA: smallest of the group, white rabbit with a grey cap of fur and grey outer ears, long ears with pink insides, big dark shiny eyes, two front teeth, mint-green overalls (#8fe0c4) over a cream shirt, pink sneakers, small orange backpack
- FOX: beige (not orange) fox kit (#d9b98a), white cheeks and muzzle, pointed muzzle, big ears with dark tips, neatly combed forelock, olive-green eyes, green school vest (#3f9a55) with V-neck over a white shirt, shiny black shoes, bushy tail with white tip
- RACCOON: grey raccoon kit (#8e9096), dark eye mask, light muzzle, round ears, dark brown eyes, ringed tail, burgundy school vest (#8a2234) over a white shirt, white sneakers with burgundy stripe

**Emotion.** gratitude, respect, guilt

**Location.** garden path, school in the background

**Lighting & palette.** sun growing warmer and stronger during the shot

**Camera.** Medium group shot, slow push-in to Ryzhik's face (30→46 mm).

**Start → end of the action.** Start: hug in the group. End: close-up of Ryzhik smiling.

**Vertical 9:16 composition.** Hug on the right third, the two guilty classmates on the left, school roof in the top.

**References.** Use the character reference images in `assets/references/` (`<id>_front.png`, `_threequarter.png`, `_side.png`, `_face.png`) as character/identity references; keep the same seed/model for all scenes if the generator supports it.

## Negative prompt
No dialogue, no text, no subtitles, no logos, no watermark, no extra limbs, no duplicated characters, no distorted paws, no changing clothes, no inconsistent fur color, no flickering facial features, no malformed eyes, no floating props, no abrupt identity changes, no random background characters blocking the action, no graphic injury, no blood, no horror aesthetic.

## How this scene is actually produced in this project
No external generator API was available (see docs/technical_audit.md), so the scene is built and keyframed in code:
`scripts/blender/scenes.py → shot7()` (procedural characters, environment, per-frame character animation, camera moves),
rendered with Blender EEVEE by `scripts/animate_scenes.py`.
