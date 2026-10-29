# Scene 08 — Reconciliation (00:28–00:32)

## Image / video generator prompt (English)
Original high-end cinematic 3D animated family short film, adorable expressive anthropomorphic animal characters, consistent character design, finely detailed soft fur, realistic fur shading, expressive large eyes, physically based materials, global illumination, cinematic lighting, beautiful volumetric sunlight, subtle depth of field, carefully composed vertical frame, natural body mechanics, appealing facial animation, premium animated film quality, detailed environment, believable shadows, smooth camera movement, rich but controlled color palette, emotionally expressive storytelling, polished render, portrait 9:16 composition.

**Action.** The fox kit offers Ryzhik a paw; the raccoon kneels and gently wipes mud from Ryzhik's worn boot with a small cloth. Ryzhik is surprised, then accepts with a kind smile and shakes the fox's paw. Puppy and rabbit watch happily.

**Characters (fixed design, identical in every shot — see docs/character_bible.md):**
- RYZHIK: small light-ginger kitten, child proportions, big round head with full cream cheeks, large amber eyes with dark rims and two catchlights, small pink nose, ω-shaped mouth, triangular ears with pink insides, faint tabby 'M' on forehead, long striped ginger tail, faded worn light-blue school jacket (#86b4d6) with a darker blue patch on the chest and three cream buttons, scuffed brown leather boots (#7a4a2a), small navy backpack (#22336b)
- DRUZHOK: small cream puppy (#efd9b4) with a brown patch around the left eye, soft floppy brown ears, warm brown eyes, big dark nose, bright cobalt-blue jacket (#2f6fd0) with yellow buttons, red rubber boots, bright yellow umbrella
- PUSHINKA: smallest of the group, white rabbit with a grey cap of fur and grey outer ears, long ears with pink insides, big dark shiny eyes, two front teeth, mint-green overalls (#8fe0c4) over a cream shirt, pink sneakers, small orange backpack
- FOX: beige (not orange) fox kit (#d9b98a), white cheeks and muzzle, pointed muzzle, big ears with dark tips, neatly combed forelock, olive-green eyes, green school vest (#3f9a55) with V-neck over a white shirt, shiny black shoes, bushy tail with white tip
- RACCOON: grey raccoon kit (#8e9096), dark eye mask, light muzzle, round ears, dark brown eyes, ringed tail, burgundy school vest (#8a2234) over a white shirt, white sneakers with burgundy stripe

**Emotion.** sincere apology, kindness; no humiliation

**Location.** garden path, school behind

**Lighting & palette.** golden late-afternoon light

**Camera.** Medium close-up (34–40 mm), gentle push.

**Start → end of the action.** Start: fox approaching. End: handshake, everyone smiling, boot clean.

**Vertical 9:16 composition.** Ryzhik centred, fox on the left, kneeling raccoon on the right, friends behind.

**References.** Use the character reference images in `assets/references/` (`<id>_front.png`, `_threequarter.png`, `_side.png`, `_face.png`) as character/identity references; keep the same seed/model for all scenes if the generator supports it.

## Negative prompt
No dialogue, no text, no subtitles, no logos, no watermark, no extra limbs, no duplicated characters, no distorted paws, no changing clothes, no inconsistent fur color, no flickering facial features, no malformed eyes, no floating props, no abrupt identity changes, no random background characters blocking the action, no graphic injury, no blood, no horror aesthetic.

## How this scene is actually produced in this project
No external generator API was available (see docs/technical_audit.md), so the scene is built and keyframed in code:
`scripts/blender/scenes.py → shot8()` (procedural characters, environment, per-frame character animation, camera moves),
rendered with Blender EEVEE by `scripts/animate_scenes.py`.
