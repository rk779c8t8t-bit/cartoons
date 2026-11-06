# ЭФИР — music animation (1080p, 60 fps, 13 s)

`EFIR_animation_1080p60.mp4` is a cel-shaded 3D cartoon built in code with Three.js and set to the original track from the reference clip.

## Story (synced to 114 BPM, one beat every 0.525 s)
| Time | What happens |
|---|---|
| 0–1.25 | Dark bedroom. The camera pushes into an old CRT TV showing a 2000s music show. |
| 1.25–2.1 | Inside the TV: a pop crooner sings on a disco stage. |
| 2.1–2.62 | Lights flicker and he looks up as a rapper in a red beanie falls through the sky. |
| **2.62 drop** | Superhero landing: the shockwave lifts the floor tiles, the crowd is knocked back and the light palette turns red. |
| 2.62–4.72 | The MC raps on the beat. The crooner is stunned, shrugs, then starts nodding along. |
| 4.72–6.82 | They dance together while the studio walls fall off the roof on the beats and the night city appears. |
| 6.82–7.35 | Both jump, and a flying boombox catches them. |
| 7.35–8.92 | Flight through a tunnel of TVs that flash on every kick. |
| 9.44–9.97 break | Bullet time: everything freezes and the camera orbits 180°. |
| 9.97–11.02 | Restart: confetti burst, every TV turns red and they converge into a ring. |
| 11.02–13.0 | The camera pulls back out of the TV, the CRT switches off on the last hit, then the end title. |

## Re-render
```
npm i three@0.160.0
node render.js frames 60 0 780 1920 1080
ffmpeg -framerate 60 -i frames/f_%05d.jpg -i music.wav -c:v libx264 -crf 16 -pix_fmt yuv420p -c:a aac -b:a 320k out.mp4
```
`music.wav` = the reference clip's audio, trimmed to 13 s. `env60.json` holds the audio envelopes used for lip sync.
