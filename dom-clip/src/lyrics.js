'use strict';
// Word timings measured from the attached track (Whisper word timestamps, checked against the beat grid).
// "/" = line break. hl = highlighted words (accent colour).
const LYR_RAW = [
  ['Дом — всё, что спрятано / в слове этом,', [14.82, 16.0, 16.66, 16.78, 17.42, 17.7, 18.48], 19.45, ['Дом'], C.amber],
  ['стало просто сном', [19.66, 20.96, 21.76], 22.9, ['сном'], C.amber],
  ['Я скитаюсь / по всей планете', [23.24, 23.78, 24.4, 24.74, 25.26], 26.3, ['планете'], C.cyan],
  ['вечным чужаком', [26.45, 28.38], 29.6, ['чужаком'], C.cyan],
  ['За окном горят / огней узоры', [29.74, 30.56, 31.38, 31.94, 32.6], 33.8, ['огней', 'узоры'], C.warm],
  ['Я не помню, / что это за город', [33.9, 34.54, 34.74, 35.2, 35.4, 35.78, 36.28], 37.6, ['город'], C.violet],
  ['Но я знаю, что мне / снова скоро пора', [37.82, 38.1, 38.28, 38.82, 38.92, 39.14, 39.56, 40.5], 42.45, ['пора'], C.amber],
  // chorus 1
  ['Лондон, Прага, Ницца', [43.55, 44.64, 45.16], 46.05, ['Лондон,', 'Прага,', 'Ницца'], null],
  ['Новый паспорт, / новый штамп', [46.12, 47.0, 48.32, 48.64], 50.5, ['штамп'], C.red],
  ['Гонка по границам', [50.68, 51.62, 52.02], 53.4, ['границам'], C.cyan],
  ['Моя жизнь — / мой чемодан', [53.5, 54.1, 55.0, 55.26], 57.65, ['чемодан'], C.violet],
  ['Лондон, Прага, Ницца', [57.82, 58.96, 59.78], 60.65, ['Лондон,', 'Прага,', 'Ницца'], null],
  ['Я летаю над землёй', [60.78, 60.96, 62.3, 62.74], 65.0, ['летаю'], C.blue],
  ['Вольный, будто птица', [65.16, 66.0, 66.48], 67.85, ['Вольный,', 'птица'], C.blue],
  ['Только птицы / возвращаются домой', [68.0, 68.3, 69.42, 71.54], 73.6, ['домой'], C.warm],
  // verse 2
  ['Стоит только где-то / стать своим хоть на чуть-чуть', [86.46, 87.54, 88.16, 88.94, 89.58, 90.56, 91.0, 91.42], 92.85, ['своим'], C.green],
  ['Снова под запретом,', [93.36, 94.44, 95.26], 96.3, ['запретом,'], C.red],
  ['снова отправляюсь в путь', [96.36, 96.96, 98.94, 99.18], 100.15, ['путь'], C.cyan],
  ['Пусть родных и близких / я не видел много лет', [100.5, 101.52, 102.24, 102.54, 103.64, 103.96, 104.46, 105.22, 105.92], 107.25, ['родных', 'близких'], C.warm],
  ['Вечно в самолётах, / мне нет места на земле', [107.5, 108.74, 109.1, 110.92, 111.02, 111.64, 112.42, 112.9], 114.15, ['самолётах,'], C.blue],
  ['Мне нет места на земле', [114.26, 114.62, 115.22, 115.94, 116.48], 118.55, ['земле'], C.blue],
  // chorus 2
  ['Лондон, Прага, Ницца', [118.8, 119.8, 120.6], 121.55, ['Лондон,', 'Прага,', 'Ницца'], null],
  ['Новый паспорт, / новый штамп', [121.64, 122.22, 123.54, 123.88], 125.75, ['штамп'], C.red],
  ['Гонка по границам', [125.88, 126.84, 127.24], 128.75, ['границам'], C.cyan],
  ['Моя жизнь — / мой чемодан', [128.84, 129.32, 130.24, 130.5], 132.85, ['чемодан'], C.violet],
  ['Лондон, Прага, Ницца', [132.96, 134.14, 135.02], 135.9, ['Лондон,', 'Прага,', 'Ницца'], null],
  ['Я летаю над землёй', [136.02, 136.18, 137.48, 137.98], 140.25, ['летаю'], C.blue],
  ['Вольный, будто птица', [140.36, 141.5, 141.72], 143.05, ['Вольный,', 'птица'], C.blue],
  ['Только птицы / возвращаются домой', [143.18, 143.52, 144.62, 146.74], 149.6, ['домой'], C.warm],
];
const CITY_COL = { 'Лондон,': C.cyan, 'Прага,': C.amber, 'Ницца': C.pink };
const LYR = LYR_RAW.map(([str, times, end, hl, acc]) => {
  const lines = str.split(' / ').map(l => l.split(' '));
  let k = 0; const out = [];
  for (const ln of lines) out.push(ln.map(w => ({ w, t: w === '—' ? times[Math.max(0, k - 1)] + .3 : times[k++], hl: hl.includes(w), col: acc || CITY_COL[w] || C.white })));
  if (k !== times.length) console.warn('timing mismatch', str, k, times.length);
  return { lines: out, start: times[0], end, acc };
});

function drawLyrics(g, t) {
  for (let i = 0; i < LYR.length; i++) {
    const b = LYR[i], next = LYR[i + 1];
    const a0 = b.start - .42, a1 = Math.min(b.end, next ? next.start - .08 : 1e9);
    if (t < a0 || t > a1 + .3) continue;
    const ain = eOC(inv(a0, b.start - .05, t)), aout = 1 - inv(a1, a1 + .3, t);
    const alpha = ain * aout; if (alpha <= 0) continue;
    const fs = 58, lh = 74, y0 = 300 - (b.lines.length - 1) * lh / 2 + (1 - ain) * 26 - (1 - aout) * 16;
    g.save(); g.globalAlpha = alpha;
    g.font = font(600, fs); g.letterSpacing = '0px'; g.textBaseline = 'alphabetic'; g.textAlign = 'left';
    const sp = g.measureText(' ').width;
    b.lines.forEach((ln, li) => {
      const ws = ln.map(o => g.measureText(o.w).width);
      const tot = ws.reduce((s, v) => s + v, 0) + sp * (ln.length - 1);
      let x = W / 2 - tot / 2; const y = y0 + li * lh;
      ln.forEach((o, wi) => {
        const k = sstep(o.t - .06, o.t + .16, t);
        const base = [255, 255, 255], hc = hexRGB(o.hl ? o.col : C.white);
        const col = mixRGB([120, 126, 140], hc, k);
        const pop = o.hl ? eOB(inv(o.t, o.t + .3, t)) : 1;
        g.save();
        if (o.hl && k > 0) { g.shadowColor = rgbA(hc, .8 * k); g.shadowBlur = 26; }
        const sc = o.hl ? 1 + .04 * Math.sin(Math.PI * clamp(inv(o.t, o.t + .35, t))) : 1;
        g.translate(x + ws[wi] / 2, y - fs * .35); g.scale(sc, sc);
        g.fillStyle = rgbA(col, lerp(.55, 1, k)); g.fillText(o.w, -ws[wi] / 2, fs * .35);
        g.restore();
        x += ws[wi] + sp;
      });
    });
    g.restore();
  }
}

function drawPlayer(g, t) {
  const x0 = 90, x1 = 990, y = 1712;
  g.save();
  text(g, 'Дом', x0, y, font(700, 38), C.white, 'left');
  text(g, 'MORGENSHTERN', x0, y + 42, font(500, 26), 'rgba(255,255,255,0.5)', 'left', 1);
  const by = y + 92; const p = clamp(t / DUR);
  rr(g, x0, by - 3, x1 - x0, 6, 3); g.fillStyle = 'rgba(255,255,255,0.18)'; g.fill();
  rr(g, x0, by - 3, (x1 - x0) * p, 6, 3); g.fillStyle = 'rgba(255,255,255,0.92)'; g.fill();
  g.fillStyle = C.white; g.beginPath(); g.arc(x0 + (x1 - x0) * p, by, 9, 0, 7); g.fill();
  const fmt = s => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
  text(g, fmt(t), x0, by + 46, font(500, 24, 'JetBrains Mono'), 'rgba(255,255,255,0.5)', 'left');
  text(g, fmt(DUR), x1, by + 46, font(500, 24, 'JetBrains Mono'), 'rgba(255,255,255,0.5)', 'right');
  g.restore();
}
