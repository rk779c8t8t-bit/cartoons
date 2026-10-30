# Automatic validation report

File: `output/final_short.mp4`

| Check | Result | Detail |
|---|---|---|
| MP4 exists | PASS | /home/user/cartoons/output/final_short.mp4 |
| file not empty | PASS | 31.00 MB |
| ffprobe reads file | PASS |  |
| video stream present | PASS |  |
| audio stream present | PASS |  |
| resolution 1080x1920 | PASS | 1080x1920 |
| aspect 9:16 | PASS | 0.5625 |
| FPS 30 | PASS | 30.000 |
| duration 30-40 s | PASS | 36.000 s |
| video codec H.264 | PASS | h264 High yuv420p |
| audio codec AAC | PASS | aac 48000 Hz 2 ch |
| audio/video durations match (sync) | PASS | video 36.000s / audio 36.000s |
| frame count = 1080 | PASS | 1080 frames |
| no black frames | PASS | 0 black segments |
| no frozen/paused segments >0.8 s | PASS | 0 found [] |
| loudness ~ -14 LUFS (YouTube) | PASS | -14.7 LUFS |
| no clipping (true peak <= -1 dBTP) | PASS | -1.1 dBTP |
| no silent gaps > 0.7 s | PASS | [] |
| all 9 scenes present (8 cuts detected at 4 s marks) | PASS | diffs [39.5, 42.2, 43.8, 47.5, 42.9, 39.7, 40.4, 41.9] |
| visible action in every scene | PASS | mean frame diff/0.2s [13.31, 14.31, 14.4, 10.4, 9.59, 12.21, 15.56, 7.58, 14.33] |
| no flicker (adjacent-frame luminance jump < 12) | PASS | max 6.57 |

Frame difference at the 8 scene boundaries: [39.5, 42.2, 43.8, 47.5, 42.9, 39.7, 40.4, 41.9]
Mean motion per scene (frame diff over 0.2 s): [13.31, 14.31, 14.4, 10.4, 9.59, 12.21, 15.56, 7.58, 14.33]

Contact sheet (3 frames per scene, 3 scenes per row): `output/contact_sheet.png`

Visual criteria (character consistency, no extra limbs, no text/watermarks, story readability) are reviewed manually from the contact sheet and the video: see docs/quality_report.md.
