# «Над котёнком все смеялись» — 3D-мультфильм для Shorts / TikTok / Reels

Вертикальный (1080×1920, 9:16, 30 fps) 36-секундный 3D-мультфильм без слов о котёнке Рыжике в старых ботинках,
над которым смеялись, пока он не спас крольчиху. Всё создаётся **локально и кодом**: процедурные 3D-персонажи и школа в Blender,
покадровая анимация, рендер EEVEE, оригинальная музыка (MIDI → FluidSynth), синтезированные шумы, монтаж в FFmpeg.

**Готовое видео:** `output/final_short.mp4` (превью 540×960: `output/preview.mp4`, контактный лист: `output/contact_sheet.jpg`).

## Структура
```
run.py                     единый запуск всего конвейера
config/project.yaml        формат, сцены, хронометраж, параметры рендера
docs/                      библия персонажей, раскадровка, тех. аудит, отчёт о качестве
prompts/characters|scenes  подробные англ. промты (для внешних генераторов, если появятся)
scripts/
  audit_environment.py     аудит среды (инструменты, GPU, наличие ключей без вывода значений)
  generate_assets.py       эталонные изображения персонажей -> assets/references/
  animate_scenes.py        рендер 9 сцен (параллельно, с возобновлением)
  create_audio.py          music.wav, foley.wav, ambience.wav -> assets/audio/
  assemble_video.py        монтаж, растворения, сведение, H.264/AAC
  validate_video.py        проверка итогового файла
  blender/                 код сцен: characters.py, env.py, scenes.py, props.py, render_shot.py …
assets/references|audio|generated   ресурсы (кадры рендера в generated/frames, в git не хранятся)
output/                    итоговые видео и отчёты
logs/                      логи рендера, статусы, результаты проверки
tests/                     быстрые проверки без Blender
```

## Необходимые программы
- Linux (проверено на Ubuntu 24.04), Python ≥ 3.10
- Blender 4.0+ (`blender` в PATH; GPU не нужен — EEVEE работает через программный OpenGL)
- FFmpeg/FFprobe с libx264 и AAC
- FluidSynth и GM-саундфонт FluidR3

```bash
sudo apt-get install -y blender ffmpeg fluidsynth fluid-soundfont-gm
pip install -r requirements.txt
```

## API
Не требуются. Конвейер полностью локальный и бесплатный. `.env.example` перечисляет переменные, которые аудит лишь
проверяет на наличие (на случай подключения внешнего генератора в будущем). Настоящий `.env` в git не попадает.

## Запуск
```bash
python3 run.py              # полный цикл; готовые кадры/звук/референсы переиспользуются
python3 run.py --dry-run    # только проверки и план рендера, ничего не рендерится, сеть и платные сервисы не используются
python3 run.py --preview    # быстрый превью-рендер (25 %, каждый 15-й кадр) в output/preview_frames/
```
Полный рендер на 4 ядрах CPU занимает ≈ 4 часа (≈13 с/кадр при 2 параллельных процессах Blender).
Прерванный рендер продолжается с места остановки — просто запустите команду снова.

### Пересоздать отдельные сцены
```bash
python3 run.py --force-shot 4 6     # перерендерить сцены 4 и 6, затем заново смонтировать
python3 run.py --force-all          # всё заново (кадры, звук, референсы)
python3 scripts/create_audio.py --force   # только звук
python3 scripts/assemble_video.py && python3 scripts/validate_video.py   # только монтаж и проверка
```
Отдельный кадр для отладки:
`blender -b --factory-startup -P scripts/blender/render_shot.py -- --shot 3 --out /tmp/s3 --pct 25 --samples 4 --frames 60`

## Типичные ошибки
| Симптом | Решение |
|---|---|
| `blender not found` | `sudo apt-get install blender` или добавить Blender в PATH |
| `EGL Error … fallback to surfaceless EGL` в логе | это нормально для сервера без дисплея |
| `N rendered frames missing` при монтаже | рендер не завершён — `python3 scripts/animate_scenes.py` дорендерит недостающее |
| Очень медленный рендер | уменьшить `render.samples` или `resolution_percent` в `config/project.yaml`, увеличить `workers` при наличии ядер |
| `fluidsynth / GM soundfont missing` | `sudo apt-get install fluidsynth fluid-soundfont-gm` |
| Проверка «audio dropouts» не прошла | пересоздать звук `create_audio.py --force` |

## Как сделано
- **Персонажи** (`characters.py`): иерархия суставов + меши-примитивы, шейдерный мех, глаза с радужкой и бликами,
  мимика (брови, веки, взгляд, shape keys рта, уши, хвост), автоматическая походка/бег, моргания, «дыхание».
- **Окружение** (`env.py`): школа, двор, сад, большое дерево с отламывающейся веткой, камень, доска, лужи, трава, цветы,
  дождь (частицы), летящие листья, качание крон.
- **Звук** (`create_audio.py`): музыка написана нотами в коде (пианино, челеста, струнные, пиццикато, литавры, валторна, флейта)
  по структуре ТЗ; шумы и атмосфера — синтез (шаги, зонт, треск, скрип, удар, шорохи, дождь, ветер, птицы). Голосов нет.
Подробнее: `docs/technical_audit.md`, `docs/quality_report.md`.
