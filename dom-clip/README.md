# MORGENSHTERN — «Дом» · вертикальный анимированный клип

Процедурный клип 1080×1920, 30 fps, синхронизированный с оригинальной дорожкой.
Вся графика рисуется кодом (Canvas 2D) кадр за кадром. Готовых картинок нет.

## Структура
- `src/core.js`: константы (темп 134.2 BPM, сетка долей), easing, стеклянные карточки, размытие.
- `src/art.js`: заранее отрисованные иллюстрации: Лондон, Прага, Ницца, ночные города, пустая квартира, аэропорт, облака, самолёт, птицы, дом, штампы, карта Европы.
- `src/lyrics.js`: текст песни с таймингом по словам (снят с дорожки Whisper-моделью) и HUD плеера.
- `src/scenes.js`: сцены и таймлайн.
- `src/main.js`: композитинг (свечение, частицы, переходы, зерно, виньетка).
- `tools/stills.js`: рендер отдельных кадров для проверки.
- `tools/render.js`: рендер диапазона кадров в mp4 через ffmpeg.

## Рендер
```bash
export NODE_PATH=$(npm root -g)          # playwright
N=4608; for i in 0 1 2 3; do node tools/render.js $((i*N/4)) $(((i+1)*N/4)) seg$i.mp4 & done; wait
printf "file 'seg%d.mp4'\n" 0 1 2 3 > list.txt
ffmpeg -f concat -i list.txt -i "Morgenshtern - Дом.mp3" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k -shortest dom.mp4
```

Карта мира: [world-atlas](https://github.com/topojson/world-atlas) (Natural Earth, public domain), d3-geo, topojson-client.
