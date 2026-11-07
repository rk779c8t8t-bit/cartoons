# TOLY SUMMER × EMINEM — анимационный клип

Готовое видео: `output/eminem_toly_animated.mp4` (1080×1920, 30 fps, 15 с, H.264 + AAC).

## Как устроено
Все кадры генерируются кодом (Python + Skia + OpenCV), без платных API.

| Файл | Что делает |
|---|---|
| `src/build_chars.py` | Из фото делает стилизованные «вектор-комикс» головы (вырезка GrabCut, cel-shading, XDoG-контур) + риг (глаза, рот, брови, шея) |
| `src/character.py` | Анимационный риг: mesh-warp головы (повороты, открытие челюсти/липсинк, моргание, брови), векторные тела, позы рук |
| `src/audio.py` | Саундтрек (синт. интро-райзер + музыка из мэшапа + реверб-аутро) и тайминг слогов/битов |
| `src/fx.py` | Окружение: огонь, город, лучи, прожекторы, толпа, 3D-частицы, 3D-икосаэдр, кольца |
| `src/typo.py` | Кинетическая типографика (побуквенные входы, капсулы-выделения, глитч, выходы) |
| `src/scenes.py` | Сцены, камера, переходы (разбитое стекло, whip-pan, глитч, вспышки), таймлайн |
| `src/render.py` | Параллельный рендер кадров + сборка FFmpeg |

## Пересборка
```
pip install opencv-python-headless numpy pillow librosa scipy soundfile skia-python
python3 src/build_chars.py && python3 src/audio.py && python3 src/render.py
```
Финальную надпись «TOLY SUMMER × EMINEM» можно отключить: `SHOW_TITLE = False` в `src/scenes.py`.

## Таймлайн
0.0 интро → 2.05 Toly «Гори, я горю тоже» → 4.4 разбитие стекла → 4.55 «Now, this looks like a job for me»
→ 6.6 «So everybody, just follow me» → 8.6 «’Cause we need a little controversy»
→ 10.6 «’Cause it feels so empty without me» → 12.6 финал с обоими героями.
