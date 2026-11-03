/* Музыкальный клип «Депутат» — процедурная анимация на Canvas 2D.
   Всё изображение рисуется кодом; render(t) детерминированно рисует кадр для времени t (сек). */
'use strict';
const W = 1080, H = 1920;
const D = window.DATA;
const cv = document.getElementById('c');
const ctx = cv.getContext('2d');

/* ---------- утилиты ---------- */
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lerp = (a, b, t) => a + (b - a) * t;
const prog = (t, a, b) => clamp((t - a) / (b - a));
const E = {
  out: t => 1 - Math.pow(1 - t, 3),
  in: t => t * t * t,
  inOut: t => (t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2),
  back: t => { const c1 = 2.2, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); },
  elastic: t => (t <= 0 ? 0 : t >= 1 ? 1 : Math.pow(2, -10 * t) * Math.sin((t * 10 - .75) * (2 * Math.PI) / 3) + 1),
};
const hash = n => { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
const noise = x => { const i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f); return lerp(hash(i), hash(i + 1), u) * 2 - 1; };
const TAU = Math.PI * 2;
function mix(c1, c2, t) { // '#rrggbb'
  const a = parseInt(c1.slice(1), 16), b = parseInt(c2.slice(1), 16);
  const r = Math.round(lerp(a >> 16, b >> 16, t)), g = Math.round(lerp(a >> 8 & 255, b >> 8 & 255, t)), bl = Math.round(lerp(a & 255, b & 255, t));
  return '#' + ((1 << 24) | (r << 16) | (g << 8) | bl).toString(16).slice(1);
}
const C = { ink: '#12060a', deep: '#2a0710', red: '#d7262e', red2: '#8f1020', gold: '#f3c24f', gold2: '#b8862b', gold3: '#7a5418',
  cream: '#f7ecd6', steel: '#5d6b80', orange: '#ff6a1a', yellow: '#ffd36b', green: '#0f2a1c', money: '#6f9a63' };

/* ---------- музыка: огибающие и биты ---------- */
function envAt(arr, t) { const x = t * D.fps, i = Math.floor(x), f = x - i; const a = arr[clamp(i, 0, arr.length - 1)], b = arr[clamp(i + 1, 0, arr.length - 1)]; return lerp(a, b, f); }
const BEATS = D.beats.slice();
{ const per = 60 / D.tempo; while (BEATS[BEATS.length - 1] < 18.3) BEATS.push(BEATS[BEATS.length - 1] + per); }
function beatInfo(t) { let i = -1; for (let k = 0; k < BEATS.length; k++) { if (BEATS[k] <= t) i = k; else break; } return i < 0 ? { i: -1, dt: 99 } : { i, dt: t - BEATS[i] }; }
const MUSIC_END = 18.42;
function beatPulse(t, k = 7) { if (t > MUSIC_END + .3) return 0; const b = beatInfo(t); return b.i < 0 ? 0 : Math.exp(-b.dt * k); }
const energy = t => envAt(D.rms, t);
const WORDS = []; D.lines.forEach((L, li) => L.words.forEach(w => WORDS.push(Object.assign({ li }, w))));
const wordT = txt => { const w = WORDS.find(w => w.text.toLowerCase().startsWith(txt)); return w ? w.start : 0; };
const wordsT = txt => WORDS.filter(w => w.text.toLowerCase().startsWith(txt)).map(w => w.start);
const hit = (t, t0, k = 6) => (t >= t0 ? Math.exp(-(t - t0) * k) : 0);

/* ---------- общие элементы ---------- */
function rays(g, cx, cy, n, rot, c1, c2, R = 2600) {
  g.fillStyle = c1; g.fillRect(-50, -50, W + 100, H + 100);
  g.fillStyle = c2;
  for (let i = 0; i < n; i++) {
    const a0 = rot + i * TAU / n, a1 = a0 + TAU / n / 2;
    g.beginPath(); g.moveTo(cx, cy); g.lineTo(cx + Math.cos(a0) * R, cy + Math.sin(a0) * R); g.lineTo(cx + Math.cos(a1) * R, cy + Math.sin(a1) * R); g.closePath(); g.fill();
  }
}
function radial(g, x, y, r, stops) { const gr = g.createRadialGradient(x, y, 0, x, y, r); stops.forEach(([o, c]) => gr.addColorStop(o, c)); return gr; }
function linear(g, x0, y0, x1, y1, stops) { const gr = g.createLinearGradient(x0, y0, x1, y1); stops.forEach(([o, c]) => gr.addColorStop(o, c)); return gr; }
function glow(g, x, y, r, color, a = 1) { g.save(); g.globalAlpha = a; g.globalCompositeOperation = 'lighter'; g.fillStyle = radial(g, x, y, r, [[0, color], [1, 'rgba(0,0,0,0)']]); g.fillRect(x - r, y - r, 2 * r, 2 * r); g.restore(); }
function sparkle(g, x, y, r, a, color = '#fff6d8') {
  if (a <= 0) return; g.save(); g.globalAlpha = a; g.globalCompositeOperation = 'lighter'; g.fillStyle = color; g.translate(x, y);
  g.beginPath(); for (let i = 0; i < 8; i++) { const rr = i % 2 ? r * .16 : r; const an = i * Math.PI / 4; g.lineTo(Math.cos(an) * rr, Math.sin(an) * rr); } g.closePath(); g.fill();
  g.restore(); glow(g, x, y, r * 1.2, 'rgba(255,220,140,.6)', a);
}
function embers(g, t, n, seed, opt = {}) {
  const { colA = '#ffb347', colB = '#ff5a1f', speed = 1, size = 1, area = [0, 0, W, H], alpha = 1 } = opt;
  g.save(); g.globalCompositeOperation = 'lighter';
  for (let i = 0; i < n; i++) {
    const r1 = hash(seed + i * 3.1), r2 = hash(seed + i * 7.7), r3 = hash(seed + i * 1.3);
    const sp = (120 + r2 * 260) * speed;
    const h = area[3] + 200;
    const y = area[1] + area[3] + 100 - ((r1 * h + t * sp) % h);
    const x = area[0] + r3 * area[2] + noise(t * .8 + i) * 60;
    const s = (2 + r2 * 5) * size;
    const fl = .55 + .45 * Math.sin(t * 9 + i);
    g.globalAlpha = alpha * fl * clamp((y - area[1]) / 300);
    g.fillStyle = i % 3 ? colA : colB;
    g.beginPath(); g.arc(x, y, s, 0, TAU); g.fill();
  }
  g.restore();
}

/* Фигура человека в костюме. (x,y) — центр плеч, s — масштаб (рост ~ 1000*s). */
function drawMan(g, o) {
  const suit = o.suit || '#1a1216', shade = o.shade || mix(suit, '#000000', .35), shirt = o.shirt || '#efe6d6', tie = o.tie || C.red, skin = o.skin || '#e0b08c';
  g.save(); g.translate(o.x, o.y); if (o.rot) g.rotate(o.rot); g.scale(o.s, o.s);
  const passes = o.rim ? [0, 1] : [1];
  for (const pass of passes) {
    const P = (path, fill) => { g.beginPath(); path(); if (pass === 0) { g.strokeStyle = o.rim; g.lineWidth = o.rimW || 14; g.lineJoin = 'round'; g.stroke(); } else { g.fillStyle = fill; g.fill(); } };
    // ноги
    if (!o.noLegs) for (const sd of [-1, 1]) {
      g.save(); g.translate(sd * 44, 318); g.rotate(sd < 0 ? (o.legL || 0) : (o.legR || 0));
      P(() => { g.rect(-37, 0, 74, 330); }, shade);
      P(() => { g.ellipse(sd * 12, 338, 52, 20, 0, 0, TAU); }, '#0b0709');
      g.restore();
    }
    // руки (за корпусом, если опущены)
    const arm = (sd, a, b) => {
      g.save(); g.translate(sd * 100, 20); g.rotate(-sd * a);
      P(() => { g.roundRect(-27, -10, 54, 175, 26); }, suit);
      g.translate(0, 155); g.rotate(-sd * b);
      P(() => { g.roundRect(-24, -8, 48, 160, 24); }, suit);
      P(() => { g.rect(-20, 140, 40, 14); }, shirt);
      P(() => { g.arc(0, 172, 24, 0, TAU); }, skin);
      if (o.watch && sd === 1) P(() => { g.rect(-23, 128, 46, 16); }, C.gold);
      g.restore();
    };
    arm(-1, o.armL || .08, o.foreL || 0); arm(1, o.armR || .08, o.foreR || 0);
    // корпус
    P(() => { g.moveTo(-114, 34); g.quadraticCurveTo(-112, -10, -62, -16); g.lineTo(62, -16); g.quadraticCurveTo(112, -10, 114, 34); g.lineTo(102, 338); g.lineTo(-102, 338); g.closePath(); }, suit);
    P(() => { g.moveTo(-36, -16); g.lineTo(0, 128); g.lineTo(36, -16); g.closePath(); }, shirt);
    P(() => { g.moveTo(-11, -8); g.lineTo(11, -8); g.lineTo(17, 104); g.lineTo(0, 130); g.lineTo(-17, 104); g.closePath(); }, tie);
    if (pass === 1) {
      g.fillStyle = shade;
      for (const sd of [-1, 1]) { g.beginPath(); g.moveTo(sd * 38, -16); g.lineTo(0, 140); g.lineTo(sd * 30, 70); g.lineTo(sd * 66, 42); g.closePath(); g.fill(); }
      g.fillStyle = o.buttons || '#000'; for (const yy of [190, 250]) { g.beginPath(); g.arc(0, yy, 7, 0, TAU); g.fill(); }
      if (o.pin) { g.fillStyle = C.gold; g.beginPath(); g.arc(-62, 40, 9, 0, TAU); g.fill(); g.fillStyle = C.red; g.beginPath(); g.arc(-62, 40, 4.5, 0, TAU); g.fill(); }
      if (o.pocket) { g.fillStyle = o.pocket; g.beginPath(); g.moveTo(52, 60); g.lineTo(88, 56); g.lineTo(80, 76); g.lineTo(58, 78); g.closePath(); g.fill(); }
    }
    // шея и голова
    P(() => { g.rect(-21, -46, 42, 34); }, skin);
    P(() => { g.ellipse(0, -96, 46, 56, 0, 0, TAU); }, skin);
    P(() => { g.ellipse(-46, -92, 9, 15, 0, 0, TAU); g.ellipse(46, -92, 9, 15, 0, 0, TAU); }, skin);
    if (o.hair) P(() => { g.ellipse(0, -128, 48, 30, 0, Math.PI, TAU); g.rect(-48, -130, 12, 26); g.rect(36, -130, 12, 26); }, o.hair);
    if (o.cap) P(() => { g.ellipse(0, -142, 64, 24, 0, 0, TAU); g.rect(-44, -150, 88, 24); }, o.cap);
    if (o.top) P(() => { g.rect(-44, -240, 88, 110); g.ellipse(0, -132, 78, 14, 0, 0, TAU); }, o.top);
    if (pass === 1 && o.face !== false) {
      g.fillStyle = 'rgba(0,0,0,.75)';
      g.beginPath(); g.arc(-16, -100, 5, 0, TAU); g.arc(16, -100, 5, 0, TAU); g.fill();
      if (o.glasses) { g.strokeStyle = o.glasses; g.lineWidth = 4; g.beginPath(); g.arc(-17, -100, 13, 0, TAU); g.moveTo(4, -100); g.arc(17, -100, 13, Math.PI, Math.PI * 3); g.stroke(); }
      if (o.mustache) { g.fillStyle = o.mustache; g.beginPath(); g.ellipse(-13, -70, 16, 7, .2, 0, TAU); g.ellipse(13, -70, 16, 7, -.2, 0, TAU); g.fill(); }
      g.strokeStyle = 'rgba(0,0,0,.6)'; g.lineWidth = 4; g.beginPath(); g.arc(0, -72, 14, .15 * Math.PI, .85 * Math.PI); g.stroke();
      if (o.cap) { g.fillStyle = C.gold; g.beginPath(); g.arc(0, -146, 9, 0, TAU); g.fill(); g.fillStyle = '#111'; g.fillRect(-46, -128, 92, 8); }
    }
  }
  g.restore();
}

/* Пламя: язычки огня поперёк кадра */
function flames(g, t, baseY, height, k, seed = 1, widthMul = 1) {
  if (k <= 0) return;
  const layers = [[C.red2, 1, .95], [C.orange, .72, .9], [C.yellow, .42, .85], ['#fff3c4', .18, .7]];
  g.save();
  layers.forEach(([col, sc, a], li) => {
    g.globalCompositeOperation = li ? 'lighter' : 'source-over';
    g.globalAlpha = a; g.fillStyle = col;
    const N = 15;
    for (let i = 0; i < N; i++) {
      const fx = (i + .5) / N * W + noise(seed + i * 3.3 + t * .7) * 50;
      const hh = height * k * sc * (.55 + .45 * (.5 + .5 * noise(seed * 7 + i * 1.7 + t * 2.3))) * (.75 + .5 * hash(i + seed));
      const ww = 150 * widthMul * (.6 + sc * .6);
      const sway = noise(i * 9.1 + t * 3.1) * 70 * sc;
      g.beginPath();
      g.moveTo(fx - ww / 2, baseY);
      g.bezierCurveTo(fx - ww / 2, baseY - hh * .45, fx + sway - ww * .25, baseY - hh * .7, fx + sway * 1.4, baseY - hh);
      g.bezierCurveTo(fx + sway + ww * .3, baseY - hh * .7, fx + ww / 2, baseY - hh * .45, fx + ww / 2, baseY);
      g.closePath(); g.fill();
    }
    if (li < 2) { g.globalAlpha = li ? .35 : 1; g.fillRect(0, baseY - 2, W, H - baseY + 2); }
  });
  g.restore();
}

/* ---------- СЦЕНЫ ---------- */
// 1. Огонь: «Ты горишь, как огонь — гори! Я горю тоже!»
function sceneFire(g, t, u, p) {
  const ign = E.out(prog(t, .85, 1.25)), burst = hit(t, wordT('гори!'), 2.2), burst2 = hit(t, wordT('горю'), 2.5);
  const k = .12 + .7 * ign + .45 * burst + .2 * beatPulse(t, 6) * ign;
  g.save();
  const z = 1 + .07 * E.inOut(p) + .03 * burst; g.translate(W / 2, H * .62); g.scale(z, z); g.translate(-W / 2, -H * .62);
  g.translate(noise(t * 20) * 14 * burst, noise(t * 20 + 9) * 10 * burst);
  g.fillStyle = linear(g, 0, 0, 0, H, [[0, '#0b0306'], [.45, mix('#1c0509', '#5a0c12', ign)], [.8, mix('#2a0710', '#c2361b', ign)], [1, mix('#3a0b0c', '#ff8a2a', ign)]]);
  g.fillRect(-100, -100, W + 200, H + 200);
  // дым
  g.save(); g.globalAlpha = .35 * ign;
  for (let i = 0; i < 7; i++) { const x = (hash(i) * W + t * 40 * (i % 2 ? 1 : -1)) % (W + 400) - 200, y = 350 + hash(i + 4) * 600 - t * 30; g.fillStyle = radial(g, x, y, 420, [[0, 'rgba(40,10,14,.9)'], [1, 'rgba(40,10,14,0)']]); g.fillRect(x - 420, y - 420, 840, 840); }
  g.restore();
  // город
  const sky = 1380;
  for (let layer = 0; layer < 2; layer++) {
    g.fillStyle = layer ? '#0c0406' : '#1c070b';
    const off = layer ? 0 : 40, sc = layer ? 1 : .75;
    for (let i = 0; i < 22; i++) {
      const bw = 70 + hash(i * 3 + layer) * 90, bx = i * 54 * (layer ? 1.05 : .9) - 60 + off, bh = (180 + hash(i * 5 + layer * 7) * 360) * sc;
      g.fillRect(bx, sky + 260 - bh - layer * 40, bw, bh + 600);
      if (layer) for (let wy = 0; wy < bh / 34 - 1; wy++) for (let wx = 0; wx < bw / 22 - 1; wx++) {
        const on = hash(i * 100 + wx * 7 + wy * 13) > .55; if (!on) continue;
        const fl = .5 + .5 * noise(t * 4 + i + wx * 2 + wy);
        g.fillStyle = `rgba(255,${150 + 60 * fl | 0},80,${(.25 + .6 * fl) * (.3 + .7 * ign)})`;
        g.fillRect(bx + 8 + wx * 22, sky + 260 - bh - 40 + 14 + wy * 34, 10, 16);
        g.fillStyle = '#0c0406';
      }
    }
  }
  flames(g, t, 1800, 820, k, 3);
  g.fillStyle = linear(g, 0, 1780, 0, H, [[0, 'rgba(140,20,10,0)'], [1, 'rgba(90,10,8,.85)']]); g.fillRect(-100, 1780, W + 200, 300);
  glow(g, W / 2, 1700, 900, 'rgba(255,120,40,.55)', ign * (.6 + .4 * burst));
  embers(g, t, 110, 11, { alpha: .3 + .7 * ign, speed: 1 + burst });
  // главный герой — силуэт на фоне огня
  const self = E.out(prog(t, wordT('я') + .0, wordT('я') + .5));
  const breathe = Math.sin(t * 2.2) * 4;
  drawMan(g, { x: W / 2, y: 1060 + breathe, s: .9, suit: '#0d0507', shade: '#070304', shirt: '#1a0a0c', tie: '#2a0a0c', skin: '#0d0507', face: false, rim: `rgba(255,${140 + 80 * burst2 | 0},60,${.55 + .45 * ign})`, rimW: 10 + 12 * burst2 });
  if (self > 0) { // герой сам загорается
    g.save(); g.beginPath(); g.rect(0, 0, W, H); g.clip();
    g.globalCompositeOperation = 'lighter';
    for (let i = 0; i < 9; i++) {
      const fx = W / 2 + (i - 4) * 26 + noise(i + t * 3) * 10, base = 1050 + Math.abs(i - 4) * 4, hh = (90 + 90 * (.5 + .5 * noise(i * 3 + t * 4))) * self;
      g.fillStyle = i % 2 ? 'rgba(255,170,60,.8)' : 'rgba(255,90,30,.8)';
      g.beginPath(); g.moveTo(fx - 26, base); g.quadraticCurveTo(fx + noise(t * 5 + i) * 30, base - hh, fx + 2, base - hh * 1.2); g.quadraticCurveTo(fx + 10, base - hh * .5, fx + 26, base); g.fill();
    }
    g.restore();
    glow(g, W / 2, 1000, 420, 'rgba(255,140,50,.6)', self * (.6 + .4 * burst2));
  }
  g.restore();
}

// 2. Бутик: «Я выбираю костюмчик подороже»
function sceneSuit(g, t, u, p) {
  const bp = beatPulse(t, 6), tCost = wordT('подороже'), tSuit = wordT('костюмчик');
  rays(g, W / 2, -200, 36, t * .08, '#3a0812', '#4d0d1b');
  g.fillStyle = linear(g, 0, 0, 0, H, [[0, 'rgba(10,2,4,.2)'], [1, 'rgba(10,2,4,.85)']]); g.fillRect(0, 0, W, H);
  // арт-деко рамка
  g.strokeStyle = 'rgba(243,194,79,.55)'; g.lineWidth = 4;
  for (let i = 0; i < 3; i++) { g.beginPath(); g.arc(W / 2, 1980, 900 + i * 40, Math.PI, TAU); g.stroke(); }
  // прожектор
  g.save(); g.globalCompositeOperation = 'lighter';
  g.fillStyle = linear(g, 0, 0, 0, 1600, [[0, 'rgba(255,236,190,.35)'], [1, 'rgba(255,236,190,0)']]);
  g.beginPath(); g.moveTo(W / 2 - 90, -20); g.lineTo(W / 2 + 90, -20); g.lineTo(W / 2 + 520, 1700); g.lineTo(W / 2 - 520, 1700); g.closePath(); g.fill(); g.restore();
  // подиум
  g.fillStyle = linear(g, 0, 1560, 0, 1700, [[0, '#d9a441'], [1, '#6b4514']]); g.beginPath(); g.ellipse(W / 2, 1610, 430, 70, 0, 0, TAU); g.fill();
  g.fillStyle = '#2a0a10'; g.beginPath(); g.ellipse(W / 2, 1596, 400, 56, 0, 0, TAU); g.fill();
  // костюм на вешалке
  const pop = 1 + .06 * hit(t, tSuit, 5) + .025 * bp;
  const sw = Math.sin(u * 3.2) * .05;
  g.save(); g.translate(W / 2, 640); g.rotate(sw); g.scale(pop, pop);
  g.strokeStyle = C.gold; g.lineWidth = 10; g.lineCap = 'round';
  g.beginPath(); g.arc(0, -60, 34, Math.PI * 1.05, Math.PI * 2.2); g.stroke();
  g.beginPath(); g.moveTo(0, -26); g.lineTo(-170, 60); g.lineTo(170, 60); g.closePath(); g.stroke();
  // пиджак
  const jacket = () => { g.beginPath(); g.moveTo(-200, 90); g.quadraticCurveTo(-190, 40, -110, 30); g.lineTo(110, 30); g.quadraticCurveTo(190, 40, 200, 90); g.lineTo(230, 520); g.lineTo(170, 540); g.lineTo(160, 760); g.lineTo(-160, 760); g.lineTo(-170, 540); g.lineTo(-230, 520); g.closePath(); };
  jacket(); g.fillStyle = linear(g, -200, 0, 200, 0, [[0, '#141014'], [.5, '#2b2228'], [1, '#100c10']]); g.fill();
  g.save(); jacket(); g.clip(); g.strokeStyle = 'rgba(243,194,79,.22)'; g.lineWidth = 2; for (let x = -240; x < 240; x += 26) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, 800); g.stroke(); }
  // блик
  const sh = ((u * .9) % 1.6) - .3; g.fillStyle = 'rgba(255,240,200,.18)'; g.beginPath(); g.moveTo(-300 + sh * 600, 0); g.lineTo(-200 + sh * 600, 0); g.lineTo(-400 + sh * 600, 800); g.lineTo(-500 + sh * 600, 800); g.fill();
  g.restore();
  g.fillStyle = '#efe6d6'; g.beginPath(); g.moveTo(-60, 30); g.lineTo(0, 260); g.lineTo(60, 30); g.fill();
  g.fillStyle = C.red; g.beginPath(); g.moveTo(-14, 36); g.lineTo(14, 36); g.lineTo(22, 220); g.lineTo(0, 260); g.lineTo(-22, 220); g.fill();
  g.fillStyle = '#0a070a'; for (const sd of [-1, 1]) { g.beginPath(); g.moveTo(sd * 62, 30); g.lineTo(0, 300); g.lineTo(sd * 54, 170); g.lineTo(sd * 120, 120); g.closePath(); g.fill(); }
  g.fillStyle = C.gold; for (const yy of [360, 450]) { g.beginPath(); g.arc(0, yy, 13, 0, TAU); g.fill(); }
  g.fillStyle = C.red; g.beginPath(); g.moveTo(100, 160); g.lineTo(160, 150); g.lineTo(150, 185); g.lineTo(108, 188); g.fill();
  g.strokeStyle = C.gold; g.lineWidth = 4; g.beginPath(); g.moveTo(96, 190); g.lineTo(162, 190); g.stroke();
  g.restore();
  // ценники: количество и «$» растут на «подороже»
  const n = 1 + Math.floor(5 * E.out(prog(t, tCost - .05, tCost + .5)));
  for (let i = 0; i < n; i++) {
    const a = i === 0 ? 1 : E.back(prog(t, tCost + (i - 1) * .09, tCost + (i - 1) * .09 + .25));
    if (a <= 0) continue;
    const ang = -.7 + i * .32 + Math.sin(u * 4 + i) * .08, ax = W / 2 + 230 - i * 10, ay = 1120 + i * 40;
    g.save(); g.translate(ax, ay); g.rotate(ang); g.scale(a, a);
    g.strokeStyle = C.gold; g.lineWidth = 3; g.beginPath(); g.moveTo(0, 0); g.lineTo(0, 70); g.stroke();
    g.translate(0, 70);
    g.fillStyle = C.cream; g.beginPath(); g.moveTo(-44, 20); g.lineTo(0, -10); g.lineTo(44, 20); g.lineTo(44, 120); g.lineTo(-44, 120); g.closePath(); g.fill();
    g.strokeStyle = C.red; g.lineWidth = 4; g.stroke();
    g.fillStyle = C.red; g.font = '700 46px Oswald'; g.textAlign = 'center'; g.fillText('$'.repeat(Math.min(3, 1 + (i >> 1))), 0, 92);
    g.restore();
  }
  for (let i = 0; i < 9; i++) { const ph = (u * 2.2 + hash(i) * 3) % 1; sparkle(g, 150 + hash(i + 2) * 780, 380 + hash(i + 5) * 1100, 30 + 30 * hash(i), Math.sin(ph * Math.PI) * .9); }
}

// 3. Часы и деньги: «Часики «Ролекс» — миллион баксов»
function bill(g, x, y, s, rot, flip) {
  g.save(); g.translate(x, y); g.rotate(rot); g.scale(s, s * flip);
  g.fillStyle = flip > 0 ? '#7fae70' : '#5b8752'; g.fillRect(-120, -55, 240, 110);
  g.strokeStyle = '#2f5a2c'; g.lineWidth = 5; g.strokeRect(-110, -45, 220, 90);
  g.fillStyle = '#b8d8a6'; g.beginPath(); g.ellipse(0, 0, 34, 38, 0, 0, TAU); g.fill();
  g.fillStyle = '#2f5a2c'; g.font = '700 50px Oswald'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText('$', 0, 3);
  g.restore();
}
function sceneWatch(g, t, u, p) {
  const bp = beatPulse(t, 6), tM = wordT('миллион'), tB = wordT('баксов');
  rays(g, W / 2, 1040, 28, -t * .15, '#0b1f15', '#123222');
  g.fillStyle = radial(g, W / 2, 1040, 1100, [[0, 'rgba(243,194,79,.25)'], [.6, 'rgba(0,0,0,0)'], [1, 'rgba(0,0,0,.7)']]); g.fillRect(0, 0, W, H);
  // деньги на заднем плане
  const rain = .35 + .65 * E.out(prog(t, tM - .1, tM + .4)) + .6 * hit(t, tB, 3);
  for (let i = 0; i < 26; i++) {
    if (hash(i + 50) > rain) continue;
    const sp = 280 + hash(i) * 420, y = ((hash(i + 3) * 2400 + u * sp) % 2400) - 240, x = hash(i + 9) * W + Math.sin(u * 2 + i) * 60;
    bill(g, x, y, .55 + hash(i + 1) * .3, u * (hash(i + 2) - .5) * 2 + i, Math.cos(u * 4 + i * 1.7));
  }
  // часы
  const z = .86 + .14 * E.out(prog(u, 0, 1.6)) + .03 * bp + .05 * hit(t, tM, 5);
  const cx = W / 2, cy = 1040, R = 340;
  g.save(); g.translate(cx, cy); g.scale(z, z); g.rotate(-.12 + .1 * E.inOut(p));
  // браслет
  for (const sd of [-1, 1]) for (let i = 0; i < 6; i++) {
    const y0 = sd * (R - 20 + i * 92), w = 300 - i * 10;
    g.fillStyle = linear(g, -w / 2, 0, w / 2, 0, [[0, C.gold3], [.3, C.gold], [.5, '#fff0b8'], [.7, C.gold], [1, C.gold3]]);
    g.fillRect(-w / 2, sd > 0 ? y0 : y0 - 86, w, 86);
    g.fillStyle = 'rgba(0,0,0,.35)'; g.fillRect(-w / 2, sd > 0 ? y0 : y0 - 86, w, 5); g.fillRect(-w / 6, sd > 0 ? y0 : y0 - 86, 5, 86); g.fillRect(w / 6, sd > 0 ? y0 : y0 - 86, 5, 86);
  }
  glow(g, 0, 0, R * 1.6, 'rgba(255,210,120,.35)', .6 + .4 * bp);
  g.fillStyle = linear(g, -R, -R, R, R, [[0, '#fff0b8'], [.35, C.gold], [.7, C.gold3], [1, C.gold]]); g.beginPath(); g.arc(0, 0, R + 40, 0, TAU); g.fill();
  g.strokeStyle = 'rgba(80,50,10,.55)'; g.lineWidth = 6; for (let i = 0; i < 72; i++) { const a = i * TAU / 72; g.beginPath(); g.moveTo(Math.cos(a) * (R + 4), Math.sin(a) * (R + 4)); g.lineTo(Math.cos(a) * (R + 36), Math.sin(a) * (R + 36)); g.stroke(); }
  g.fillStyle = radial(g, -60, -80, R * 1.3, [[0, '#1f6a45'], [.7, '#0c2e1d'], [1, '#06170e']]); g.beginPath(); g.arc(0, 0, R, 0, TAU); g.fill();
  g.save(); g.globalAlpha = .18; for (let i = 0; i < 60; i++) { const a = i * TAU / 60; g.strokeStyle = i % 2 ? '#7fe0a8' : '#000'; g.lineWidth = 3; g.beginPath(); g.moveTo(0, 0); g.lineTo(Math.cos(a) * R, Math.sin(a) * R); g.stroke(); } g.restore();
  for (let i = 0; i < 12; i++) {
    const a = i * TAU / 12 - Math.PI / 2; g.save(); g.rotate(a + Math.PI / 2);
    g.fillStyle = C.gold; if (i % 3 === 0) g.fillRect(-14, -R + 26, 28, 76); else { g.beginPath(); g.arc(0, -R + 50, 15, 0, TAU); g.fill(); }
    g.restore();
    const tw = Math.sin((u * 3 + i * .7) * Math.PI); if (tw > .7) sparkle(g, Math.cos(a) * (R - 60), Math.sin(a) * (R - 60), 26, (tw - .7) * 3);
  }
  // стрелки: секундная тикает в такт
  const bi = beatInfo(t), tick = bi.i + E.elastic(clamp(bi.dt / .25));
  const hand = (ang, len, wd, col) => { g.save(); g.rotate(ang); g.fillStyle = col; g.beginPath(); g.moveTo(-wd / 2, 30); g.lineTo(-wd / 3, -len); g.lineTo(0, -len - 18); g.lineTo(wd / 3, -len); g.lineTo(wd / 2, 30); g.fill(); g.restore(); };
  hand(-.9 + u * .02, R * .5, 30, C.gold); hand(1.1 + u * .2, R * .78, 22, C.gold); hand(tick * TAU / 60 * 4, R * .88, 8, C.red);
  g.fillStyle = C.gold; g.beginPath(); g.arc(0, 0, 18, 0, TAU); g.fill();
  g.fillStyle = 'rgba(255,255,255,.12)'; g.beginPath(); g.arc(0, 0, R, -2.6, -.6); g.arc(0, -R * .35, R * .9, -.6, -2.6, true); g.fill();
  g.fillStyle = C.gold; g.fillRect(R + 34, -34, 40, 68);
  g.restore();
  // передний план — купюры летят на зрителя
  for (let i = 0; i < 12; i++) {
    if (hash(i + 90) > rain * .9) continue;
    const sp = 600 + hash(i) * 500, y = ((hash(i + 13) * 2600 + u * sp) % 2600) - 300, x = hash(i + 19) * W;
    bill(g, x, y, 1 + hash(i + 7) * .5, u * (hash(i + 4) - .5) * 3 + i, Math.cos(u * 5 + i));
  }
}

// 4. Серая толпа: «Сегодня не буду слишком выделяться»
function sceneCrowd(g, t, u, p) {
  const bi = beatInfo(t), bp = beatPulse(t, 7), tS = wordT('слишком'), tV = wordT('выделяться');
  g.fillStyle = linear(g, 0, 0, 0, H, [[0, '#0c0f17'], [.5, '#1f2635'], [1, '#0a0c12']]); g.fillRect(0, 0, W, H);
  // прожекторы ищут
  g.save(); g.globalCompositeOperation = 'lighter';
  for (let i = 0; i < 3; i++) {
    const a = Math.sin(u * .9 + i * 2.1) * .35, x0 = 180 + i * 360;
    g.save(); g.translate(x0, -60); g.rotate(a);
    g.fillStyle = linear(g, 0, 0, 0, 1900, [[0, 'rgba(200,215,255,.22)'], [1, 'rgba(200,215,255,0)']]);
    g.beginPath(); g.moveTo(-30, 0); g.lineTo(30, 0); g.lineTo(260, 1900); g.lineTo(-260, 1900); g.fill(); g.restore();
  }
  g.restore();
  const rows = [[.34, 760, 10, '#3a4252'], [.44, 900, 9, '#454e60'], [.56, 1060, 8, '#525c70'], [.7, 1250, 7, '#5f6a80'], [.88, 1480, 6, '#6b7690']];
  const hero = Math.floor(rows.length - 1);
  rows.forEach(([s, y, n, col], ri) => {
    const sp = 140 * s * (ri % 2 ? 1 : -1), off = (u * sp) % (W / n * 1.0);
    for (let i = -1; i <= n; i++) {
      const x = i * (W / (n - 1)) + off + (ri % 2) * (W / (n - 1)) / 2;
      const isHero = ri === hero && i === 3;
      const bob = ((bi.i + i + ri) % 2 ? 1 : -1) * 6 * bp * s;
      if (isHero) continue;
      drawMan(g, { x, y: y + bob, s, suit: col, shade: mix(col, '#000000', .3), shirt: '#b8bcc6', tie: '#2c3240', skin: mix('#9a8f8a', '#1f2635', .5 - s * .4), face: s > .6, top: ri < 2 ? mix(col, '#000000', .45) : null });
    }
    // туман между рядами
    g.fillStyle = linear(g, 0, y - 300 * s, 0, y + 200, [[0, 'rgba(25,30,44,0)'], [1, 'rgba(25,30,44,.55)']]); g.fillRect(0, y - 300 * s, W, 500 * s + 200);
  });
  // герой в золотом костюме пытается «не выделяться»: золото сереет, но часы и булавка блестят
  const grey = E.inOut(prog(t, tS - .1, tV + .4));
  const [s, y] = rows[hero];
  const hx = 3 * (W / (rows[hero][2] - 1)) + ((u * 140 * s * (hero % 2 ? 1 : -1)) % (W / rows[hero][2])) + (hero % 2) * (W / (rows[hero][2] - 1)) / 2;
  glow(g, hx, y + 120, 420, 'rgba(243,194,79,.5)', (1 - grey) * .8 + .25 * bp);
  drawMan(g, { x: hx, y, s, suit: mix(C.gold, '#6b7690', grey), shade: mix(C.gold2, '#4c5568', grey), shirt: '#f2ead8', tie: C.red, skin: '#d9ab88', pin: true, watch: true, pocket: C.red, armR: .2, foreR: 1.9 * (1 - grey) + .3 });
  sparkle(g, hx - 62 * s, y + 40 * s, 34, .5 + .5 * Math.sin(u * 7));
}

// 5. Здание парламента: «Я очень рад: я депутат»
function sceneParliament(g, t, u, p) {
  const bi = beatInfo(t), bp = beatPulse(t, 6), tD = wordT('депутат');
  const cam = E.inOut(p);
  g.save(); g.translate(0, -60 * cam); const z = 1.06 - .06 * cam; g.translate(W / 2, H / 2); g.scale(z, z); g.translate(-W / 2, -H / 2);
  g.fillStyle = linear(g, 0, 0, 0, H, [[0, '#0a0718'], [.45, '#2a0d2e'], [.75, '#7a1622'], [1, '#2a0710']]); g.fillRect(-100, -100, W + 200, H + 300);
  for (let i = 0; i < 60; i++) { g.fillStyle = `rgba(255,240,220,${.3 + .5 * hash(i)})`; g.fillRect(hash(i + 1) * W, hash(i + 2) * 700, 3, 3); }
  // лучи прожекторов
  g.save(); g.globalCompositeOperation = 'lighter';
  for (const [x0, ph] of [[150, 0], [930, 2], [420, 4], [660, 1]]) {
    const a = Math.sin(u * 1.2 + ph) * .3 + (x0 < 540 ? .25 : -.25);
    g.save(); g.translate(x0, 1520); g.rotate(a); g.fillStyle = linear(g, 0, 0, 0, -1600, [[0, 'rgba(255,220,180,.32)'], [1, 'rgba(255,220,180,0)']]);
    g.beginPath(); g.moveTo(-20, 0); g.lineTo(20, 0); g.lineTo(140, -1600); g.lineTo(-140, -1600); g.fill(); g.restore();
  }
  g.restore();
  // здание
  const bx = W / 2, by = 1520, stone = linear(g, 0, 700, 0, 1520, [[0, '#f3dfc0'], [1, '#b98e6a']]);
  // купол
  g.fillStyle = linear(g, 0, 640, 0, 900, [[0, '#f8e7c8'], [1, '#a37b58']]);
  g.beginPath(); g.ellipse(bx, 890, 170, 180, 0, Math.PI, TAU); g.fill(); g.fillRect(bx - 190, 880, 380, 40);
  g.strokeStyle = C.gold; g.lineWidth = 6; g.beginPath(); g.moveTo(bx, 712); g.lineTo(bx, 560); g.stroke();
  // флаг (бело-сине-красный)
  const fw = 170, fh = 110;
  for (let s = 0; s < 3; s++) {
    g.fillStyle = ['#f4f1ea', '#1f4fb4', '#d52b32'][s];
    g.beginPath();
    for (let i = 0; i <= 20; i++) { const xx = i / 20 * fw, yy = Math.sin(u * 6 - i * .45) * 10 * (i / 20); g.lineTo(bx + xx, 560 + s * fh / 3 + yy); }
    for (let i = 20; i >= 0; i--) { const xx = i / 20 * fw, yy = Math.sin(u * 6 - i * .45) * 10 * (i / 20); g.lineTo(bx + xx, 560 + (s + 1) * fh / 3 + yy); }
    g.fill();
  }
  // фронтон
  g.fillStyle = stone; g.beginPath(); g.moveTo(bx - 470, 1060); g.lineTo(bx, 900); g.lineTo(bx + 470, 1060); g.closePath(); g.fill();
  g.fillStyle = '#8c6448'; g.beginPath(); g.moveTo(bx - 380, 1040); g.lineTo(bx, 935); g.lineTo(bx + 380, 1040); g.closePath(); g.fill();
  g.fillStyle = C.gold; g.beginPath(); g.arc(bx, 1000, 28 + 4 * bp, 0, TAU); g.fill();
  g.fillStyle = stone; g.fillRect(bx - 480, 1060, 960, 50);
  // колонны
  for (let i = 0; i < 8; i++) {
    const x = bx - 420 + i * 120;
    g.fillStyle = '#4a1a1f'; g.fillRect(x - 6, 1110, 132, 340);
    g.fillStyle = linear(g, x, 0, x + 60, 0, [[0, '#a8805f'], [.4, '#fbeed6'], [1, '#9d7353']]); g.fillRect(x - 28, 1110, 56, 340);
    g.fillStyle = '#e8d2b0'; g.fillRect(x - 38, 1110, 76, 18); g.fillRect(x - 38, 1432, 76, 18);
  }
  // окна светятся
  for (let i = 0; i < 7; i++) { const x = bx - 360 + i * 120; g.fillStyle = `rgba(255,200,110,${.5 + .4 * noise(u * 3 + i)})`; g.fillRect(x - 24, 1200, 48, 120); }
  // ступени и красная дорожка
  for (let i = 0; i < 6; i++) { g.fillStyle = mix('#cfb08c', '#6b4a35', i / 6); g.fillRect(bx - 500 - i * 30, 1450 + i * 18, 1000 + i * 60, 18); }
  g.fillStyle = linear(g, 0, 1450, 0, H, [[0, '#b0141d'], [1, '#5c0a10']]); g.beginPath(); g.moveTo(bx - 70, 1450); g.lineTo(bx + 70, 1450); g.lineTo(bx + 380, H + 100); g.lineTo(bx - 380, H + 100); g.fill();
  // депутат поднимается по лестнице
  const ws = E.out(prog(t, tD - .2, tD + .25));
  drawMan(g, { x: bx, y: 1250 + 40 * (1 - ws), s: .26 + .03 * ws, suit: '#18131a', shirt: '#f0e6d4', tie: C.red, pin: true, armR: 2.6 * ws, foreR: .2 * ws });
  glow(g, bx, 1330, 220, 'rgba(255,215,140,.6)', ws);
  g.restore();
  // руки голосуют в такт
  for (let i = 0; i < 9; i++) {
    const ph = (bi.i + i) % 2, up = E.out(clamp(ph ? 1 - bi.dt * 2 : bi.dt * 3)) * clamp((t - 10.9) * 3);
    const x = 40 + i * 125 + hash(i) * 30, base = H + 40;
    g.save(); g.translate(x, base - up * 260 - hash(i + 2) * 80); g.rotate((hash(i + 4) - .5) * .3);
    g.fillStyle = '#0d0508'; g.beginPath(); g.roundRect(-36, 0, 72, 520, 30); g.fill();
    g.beginPath(); g.ellipse(0, -30, 44, 64, 0, 0, TAU); g.fill(); g.beginPath(); g.roundRect(-46, -120, 22, 90, 11); g.roundRect(-20, -138, 22, 100, 11); g.roundRect(6, -132, 22, 96, 11); g.roundRect(30, -110, 20, 80, 10); g.fill();
    g.restore();
  }
}

// 6. Марионетка: «Послушный и верный солдат»
function scenePuppet(g, t, u, p) {
  const bi = beatInfo(t), bp = beatPulse(t, 6), tSol = wordT('солдат'), tP = wordT('послушный');
  rays(g, W / 2, 900, 18, u * .12, '#c81e28', '#a8141e');
  g.fillStyle = C.cream; g.beginPath(); g.arc(W / 2, 900, 430 + 12 * bp, 0, TAU); g.fill();
  g.fillStyle = '#e9d9b6'; g.beginPath(); g.arc(W / 2, 900, 380, 0, TAU); g.fill();
  g.fillStyle = C.ink; g.save(); g.translate(0, 0); g.rotate(-.35); for (let i = 0; i < 4; i++) g.fillRect(-400, 1500 + i * 70 + (u * 60 % 70), 2200, 26); g.restore();
  // рука кукловода и крестовина
  const sway = Math.sin(u * 3) * .08 + ((bi.i % 2) ? 1 : -1) * .1 * bp;
  const hx = W / 2 + Math.sin(u * 3) * 20, hy = 210;
  g.save(); g.translate(hx, hy); g.rotate(sway);
  g.fillStyle = '#7a4a24'; g.fillRect(-230, -16, 460, 32); g.fillRect(-16, -110, 32, 220);
  g.fillStyle = '#1a0a0c'; g.beginPath(); g.roundRect(-70, -230, 140, 190, 60); g.fill(); g.fillRect(-48, -420, 96, 220);
  g.beginPath(); g.roundRect(-96, -120, 40, 120, 20); g.fill();
  g.restore();
  // кукла
  const march = (bi.i % 2 ? 1 : -1) * E.out(clamp(bi.dt * 4)) * .35 * clamp((t - tP) * 4);
  const salute = E.back(prog(t, tSol - .05, tSol + .25));
  const px = W / 2 + Math.sin(u * 3 + .4) * 30, py = 820 - 20 * bp;
  const P = (dx, dy) => { const c = Math.cos(sway), s = Math.sin(sway); return [hx + dx * c - dy * s, hy + dx * s + dy * c]; };
  const s = .82;
  const anchors = [[P(-220, 0), [px - 120 * s, py + 260 * s - salute * 120]], [P(220, 0), [px + 120 * s + salute * 40, py + 220 * s - salute * 260]], [P(0, -100), [px, py - 150 * s]], [P(-120, 0), [px - 40 * s, py + 880 * s]], [P(120, 0), [px + 40 * s, py + 880 * s]]];
  g.strokeStyle = 'rgba(30,10,12,.75)'; g.lineWidth = 2.5;
  for (const [a, b] of anchors) { g.beginPath(); g.moveTo(a[0], a[1]); g.lineTo(b[0], b[1]); g.stroke(); }
  drawMan(g, { x: px, y: py, s, rot: sway * .4, suit: '#17181f', shirt: '#efe6d6', tie: C.red, pin: true, legL: march, legR: -march,
    armL: .25 + .5 * bp, foreL: -.4, armR: .3 + 2.45 * salute, foreR: 2.3 * salute, cap: salute > .02 ? '#2c3a28' : null });
  // фуражка падает на голову на «солдат»
  if (t > tSol - .4 && salute < .02) { const d = prog(t, tSol - .4, tSol - .05); g.fillStyle = "#2c3a28"; g.beginPath(); g.ellipse(px, py - 600 + 470 * E.in(d), 52, 20, 0, 0, TAU); g.fill(); }
  if (salute > 0) glow(g, px, py, 500, 'rgba(255,220,150,.4)', hit(t, tSol, 4));
}

// 7. Плакат-конструктивизм: «Важная миссия — в Единой России»
function scenePoster(g, t, u, p) {
  const bp = beatPulse(t, 6), tR = wordT('россии'), tE = wordT('единой');
  g.fillStyle = '#efe2c4'; g.fillRect(0, 0, W, H);
  // лучи
  const ox = W * .5, oy = 1500;
  g.save(); g.globalAlpha = .95; g.fillStyle = C.red;
  for (let i = 0; i < 16; i++) { const a0 = Math.PI + i * Math.PI / 16 + u * .05, a1 = a0 + Math.PI / 34; g.beginPath(); g.moveTo(ox, oy); g.lineTo(ox + Math.cos(a0) * 3000, oy + Math.sin(a0) * 3000); g.lineTo(ox + Math.cos(a1) * 3000, oy + Math.sin(a1) * 3000); g.fill(); }
  g.restore();
  // полутоновые точки
  g.fillStyle = 'rgba(18,6,10,.16)'; for (let y = 0; y < H; y += 26) for (let x = (y / 26 % 2) * 13; x < W; x += 26) { const r = 6 * clamp(1 - Math.hypot(x - ox, y - oy) / 1900); if (r > .6) { g.beginPath(); g.arc(x, y, r, 0, TAU); g.fill(); } }
  // восходящее солнце
  const sun = E.out(prog(u, 0, 1.2));
  g.fillStyle = C.gold; g.beginPath(); g.arc(ox, oy, 250 + 140 * sun + 14 * bp, Math.PI, TAU); g.fill();
  // развевающаяся лента-триколор
  const ribbon = E.out(prog(t, tE - .3, tE + .4));
  if (ribbon > 0) for (let s = 0; s < 3; s++) {
    g.fillStyle = ['#ffffff', '#1f4fb4', '#d52b32'][s];
    g.beginPath(); const y0 = 1060 + s * 46;
    for (let i = 0; i <= 30; i++) { const x = -40 + i / 30 * (W + 80) * ribbon; g.lineTo(x, y0 + Math.sin(i * .5 - u * 5) * 34 - i * 9); }
    for (let i = 30; i >= 0; i--) { const x = -40 + i / 30 * (W + 80) * ribbon; g.lineTo(x, y0 + 46 + Math.sin(i * .5 - u * 5) * 34 - i * 9); }
    g.fill();
  }
  // чёрные диагонали
  g.save(); g.translate(W / 2, H / 2); g.rotate(-.42); g.fillStyle = C.ink; g.fillRect(-1400, 330 + 40 * (1 - sun), 2800, 30); g.fillRect(-1400, 390 + 40 * (1 - sun), 2800, 12); g.restore();
  // герои снизу (ракурс снизу)
  const rise = E.out(prog(u, 0, .9));
  const figs = [[W / 2 - 300, .62, .08], [W / 2 + 300, .62, -.08], [W / 2, .8, 0]];
  figs.forEach(([x, s, r], i) => drawMan(g, { x, y: 1460 + 380 * (1 - rise) + (i === 2 ? -40 : 0), s, rot: r, suit: '#130a0e', shade: '#000', shirt: '#2a1418', tie: C.red, skin: '#130a0e', face: false, armR: i === 2 ? 2.4 * hit(t, tR, 0) * E.back(prog(t, tR - .1, tR + .2)) : .1, foreR: 0, rim: C.red, rimW: 8 }));
  glow(g, W / 2, 1200, 700, 'rgba(255,220,150,.5)', hit(t, tR, 3));
}

// 8. Семейное древо + финал: «Чей-то тесть, чей-то сват, чей-то брат»
const REL = [
  { k: 'тесть', x: 230, y: 860, o: { mustache: '#d8d2c8', glasses: '#c9a24a', hair: '#cfc8bd' } },
  { k: 'сват', x: 850, y: 820, o: { mustache: '#3a2418', hair: null, top: '#1a1012' } },
  { k: 'брат', x: 540, y: 600, o: { hair: '#3a2418' } },
];
function portrait(g, x, y, s, a, o, seed) {
  if (a <= 0) return;
  g.save(); g.translate(x, y); g.scale(s * a, s * a); g.rotate((hash(seed) - .5) * .12 * (1 - a));
  g.fillStyle = 'rgba(0,0,0,.45)'; g.beginPath(); g.ellipse(14, 20, 150, 190, 0, 0, TAU); g.fill();
  g.fillStyle = linear(g, -150, -190, 150, 190, [[0, '#fff0b8'], [.4, C.gold], [.8, C.gold3], [1, C.gold]]); g.beginPath(); g.ellipse(0, 0, 150, 190, 0, 0, TAU); g.fill();
  g.strokeStyle = 'rgba(90,60,10,.6)'; g.lineWidth = 5; g.beginPath(); g.ellipse(0, 0, 136, 176, 0, 0, TAU); g.stroke();
  g.fillStyle = radial(g, 0, -40, 200, [[0, '#6a1a22'], [1, '#2a0710']]); g.beginPath(); g.ellipse(0, 0, 124, 164, 0, 0, TAU); g.fill();
  g.save(); g.beginPath(); g.ellipse(0, 0, 124, 164, 0, 0, TAU); g.clip();
  drawMan(g, Object.assign({ x: 0, y: 40, s: .62, suit: '#16121a', shirt: '#efe6d6', tie: C.red, pin: true, noLegs: true }, o));
  g.restore(); g.restore();
}
function sceneFamily(g, t, u, p) {
  const bp = beatPulse(t, 6), hitEnd = hit(t, 18.0, 3);
  const out = E.inOut(prog(t, 18.3, 21.9));
  g.save();
  const z = 1 - .2 * out + .03 * hitEnd; g.translate(W / 2, 1000); g.scale(z, z); g.translate(-W / 2, -1000);
  // обои и панели
  g.fillStyle = linear(g, 0, 0, 0, H, [[0, '#2e0c12'], [1, '#170508']]); g.fillRect(-400, -400, W + 800, H + 800);
  g.fillStyle = 'rgba(243,194,79,.07)';
  for (let y = -300; y < H + 300; y += 120) for (let x = -400 + (y / 120 % 2) * 60; x < W + 400; x += 120) { g.beginPath(); g.moveTo(x, y - 34); g.lineTo(x + 24, y); g.lineTo(x, y + 34); g.lineTo(x - 24, y); g.fill(); }
  g.fillStyle = linear(g, 0, 1500, 0, H, [[0, '#3b1a10'], [1, '#1d0b07']]); g.fillRect(-400, 1500, W + 800, H);
  g.fillStyle = C.gold3; g.fillRect(-400, 1494, W + 800, 10);
  glow(g, W / 2, 300, 900, 'rgba(255,190,110,.35)', 1);
  // дальние родственники (появляются в финале)
  for (let i = 0; i < 14; i++) {
    const a = E.back(prog(t, 18.0 + i * .12, 18.3 + i * .12));
    const ang = Math.PI + (i + .5) / 14 * Math.PI, rr = 900 + (i % 3) * 120;
    const x = W / 2 + Math.cos(ang) * rr, y = 1100 + Math.sin(ang) * rr * .95;
    if (a > 0) { g.strokeStyle = 'rgba(243,194,79,.4)'; g.lineWidth = 6; g.beginPath(); g.moveTo(W / 2, 1350); g.quadraticCurveTo(W / 2 + (x - W / 2) * .3, y + 200, x, y); g.stroke(); }
    portrait(g, x, y, .55, a, { hair: hash(i) > .5 ? '#3a2418' : null, mustache: hash(i + 1) > .6 ? '#2a1a12' : null, glasses: hash(i + 2) > .7 ? C.gold : null }, i);
  }
  // ветви от главного портрета
  const base = [W / 2, 1300];
  REL.forEach((r, i) => {
    const tw = wordsT('чей-то')[i] || 16, tn = wordT(r.k);
    const gp = E.inOut(prog(t, tw - .05, tn + .05));
    if (gp <= 0) return;
    g.save(); g.strokeStyle = C.gold; g.lineWidth = 16; g.lineCap = 'round';
    const L = 1300; g.setLineDash([L * gp, L]);
    g.beginPath(); g.moveTo(base[0], base[1]); g.bezierCurveTo(base[0], base[1] - 260, r.x, r.y + 380, r.x, r.y + 150); g.stroke();
    g.restore();
    for (let k = 0; k < 5; k++) { const lp = clamp(gp * 1.2 - k * .15); if (lp > 0) { g.fillStyle = '#c99a3a'; g.save(); g.translate(lerp(base[0], r.x, k / 5 + .1), lerp(base[1] - 120, r.y + 200, k / 5 + .1)); g.rotate(k + i); g.scale(lp, lp); g.beginPath(); g.ellipse(26, 0, 30, 12, 0, 0, TAU); g.fill(); g.restore(); } }
    const a = E.back(prog(t, tn - .06, tn + .22));
    portrait(g, r.x, r.y, .95 + .05 * bp, a, r.o, i + 30);
    if (a > 0) glow(g, r.x, r.y, 300, 'rgba(255,210,120,.5)', hit(t, tn, 5));
  });
  portrait(g, base[0], base[1] + 80, 1.2 + .03 * bp, 1, { pocket: C.red }, 99);
  // финальный удар: денежный салют
  if (t > 17.95) for (let i = 0; i < 26; i++) {
    const tt = t - 18.0; if (tt < 0) break;
    const a = hash(i) * TAU, v = 900 + hash(i + 1) * 900;
    const x = W / 2 + Math.cos(a) * v * Math.min(tt, 1.2) * .9, y = 1250 + Math.sin(a) * v * Math.min(tt, 1.2) * .7 + 260 * tt * tt;
    bill(g, x, y, .5 + hash(i + 3) * .3, tt * 3 + i, Math.cos(tt * 6 + i));
  }
  embers(g, t, 60, 77, { colA: '#ffd36b', colB: '#f3c24f', speed: .35, size: .9, alpha: .55 });
  g.restore();
}

/* ---------- сценарий ---------- */
const SCENES = [
  { id: 'fire', t0: 0, draw: sceneFire, textY: .2 },
  { id: 'suit', t0: 5.05, draw: sceneSuit, textY: .145, tr: 'flash' },
  { id: 'watch', t0: 6.87, draw: sceneWatch, textY: .155, tr: 'slice' },
  { id: 'crowd', t0: 8.89, draw: sceneCrowd, textY: .2, tr: 'zoom' },
  { id: 'parliament', t0: 10.84, draw: sceneParliament, textY: .17, tr: 'wipe' },
  { id: 'puppet', t0: 12.33, draw: scenePuppet, textY: .86, tr: 'flash' },
  { id: 'poster', t0: 13.97, draw: scenePoster, textY: .2, tr: 'slice' },
  { id: 'family', t0: 15.97, draw: sceneFamily, textY: .11, tr: 'iris' },
];
SCENES.forEach((s, i) => { s.t1 = i + 1 < SCENES.length ? SCENES[i + 1].t0 : D.duration + .1; });
const sceneAt = t => { let s = SCENES[0]; for (const x of SCENES) if (t >= x.t0) s = x; return s; };

/* ---------- текст песни ---------- */
const layouts = new Map();
const MAXW = 940;
const fontFor = (acc, size) => (acc ? `900 ${size}px Unbounded` : `700 ${size}px Oswald`);
function layoutLine(L) {
  if (layouts.has(L)) return layouts.get(L);
  const items = L.words.map(w => {
    const txt = w.text.toUpperCase(); let size = w.accent ? 84 : 96;
    ctx.font = fontFor(w.accent, size); let wd = ctx.measureText(txt).width;
    if (wd > MAXW) { size = Math.floor(size * MAXW / wd); ctx.font = fontFor(w.accent, size); wd = ctx.measureText(txt).width; }
    return { w, txt, size, wd };
  });
  const rows = []; let row = [], rw = 0; const GAP = 36;
  for (const it of items) { if (row.length && rw + GAP + it.wd > MAXW) { rows.push(row); row = []; rw = 0; } rw += (row.length ? GAP : 0) + it.wd; row.push(it); }
  if (row.length) rows.push(row);
  let y = 0; const out = [];
  rows.forEach(r => {
    const h = Math.max(...r.map(i => i.size)) * 1.22; const total = r.reduce((a, i) => a + i.wd, 0) + GAP * (r.length - 1);
    let x = -total / 2; y += h;
    r.forEach(i => { out.push(Object.assign(i, { x, y: y - h * .2 })); x += i.wd + GAP; });
  });
  out.forEach(i => (i.y -= y / 2));
  const res = { items: out, height: y };
  layouts.set(L, res); return res;
}
function lineWindow(li) {
  const L = D.lines[li], next = D.lines[li + 1];
  const tin = L.words[0].start - .12;
  const tout = Math.min(next ? next.words[0].start - .08 : 1e9, li === D.lines.length - 1 ? MUSIC_END + .1 : L.end + .9);
  return [tin, tout];
}
function sungFrac(w, t) { // доля пропетых букв (по таймингам букв)
  const ch = w.chars, n = ch.length, lt = t - w.start + .02;
  if (lt <= 0) return 0; if (t >= w.end) return 1;
  let i = 0; while (i < n && ch[i] <= lt) i++;
  const prev = ch[i - 1] || 0, nx = i < n ? ch[i] : w.end - w.start;
  return clamp((i - 1 + clamp((lt - prev) / Math.max(.04, nx - prev))) / n);
}
function drawLyrics(g, t) {
  D.lines.forEach((L, li) => {
    const [tin, tout] = lineWindow(li);
    if (t < tin || t > tout) return;
    const lay = layoutLine(L), sc = sceneAt(L.words[0].start);
    const cy = H * sc.textY, ex = E.in(prog(t, tout - .24, tout));
    // подложка для читаемости
    const vis = clamp((t - tin) / .15) * (1 - ex);
    g.save(); g.globalAlpha = .6 * vis; g.translate(W / 2, cy); g.scale(1, (lay.height + 180) / 1100);
    g.fillStyle = radial(g, 0, 0, 620, [[0, 'rgba(10,3,6,.85)'], [.6, 'rgba(10,3,6,.55)'], [1, 'rgba(10,3,6,0)']]); g.fillRect(-620, -620, 1240, 1240); g.restore();
    lay.items.forEach((it, k) => {
      const w = it.w, t0 = w.start - .06, pin = clamp((t - t0) / (w.accent ? .26 : .2));
      if (pin <= 0) return;
      const seed = li * 31 + k * 7;
      const exk = E.in(clamp((t - (tout - .24 + k * .02)) / .2));
      const alpha = clamp(pin * 3) * (1 - exk);
      if (alpha <= 0) return;
      const sung = sungFrac(w, t), active = t >= w.start && t <= w.end + .05;
      let s = w.accent ? lerp(2.1, 1, E.back(pin)) : lerp(1.45, 1, E.back(pin));
      s *= 1 + (w.accent ? .07 : .03) * beatPulse(t, 8) * (t > w.start ? 1 : 0) + (active ? .04 : 0);
      s *= 1 - .15 * exk;
      const rot = (w.accent ? (hash(seed) - .5) * .5 : (hash(seed) - .5) * .12) * (1 - E.out(pin)) + (w.accent ? (hash(seed + 1) - .5) * .06 : 0);
      const dy = (1 - E.out(pin)) * 50 - exk * 70;
      const cx = W / 2 + it.x + it.wd / 2, yy = cy + it.y + dy;
      g.save(); g.globalAlpha = alpha; g.translate(cx, yy - it.size * .35); g.rotate(rot); g.scale(s, s); g.translate(-it.wd / 2, it.size * .35);
      g.font = fontFor(w.accent, it.size); g.textBaseline = 'alphabetic'; g.textAlign = 'left'; g.lineJoin = 'round';
      if (w.accent) { g.fillStyle = '#5a0a12'; for (let d = 7; d >= 1; d--) g.fillText(it.txt, d * 1.6, d * 2.2); }
      g.strokeStyle = 'rgba(10,3,6,.95)'; g.lineWidth = w.accent ? 12 : 10; g.strokeText(it.txt, 0, 0);
      g.fillStyle = w.accent ? linear(g, 0, -it.size, 0, 0, [[0, '#ffe9a6'], [.55, C.gold], [1, C.gold2]]) : C.cream; g.fillText(it.txt, 0, 0);
      // караоке-заливка по буквам
      if (sung > 0) {
        const letters = [...it.txt]; let cnt = 0, cut = 0; const nL = letters.filter(c => /[А-ЯЁA-Z]/.test(c)).length; const target = sung * nL;
        for (let i = 0; i < letters.length; i++) { if (/[А-ЯЁA-Z]/.test(letters[i])) { if (cnt + 1 > target) { cut = i + (target - cnt); break; } cnt++; } cut = i + 1; }
        const whole = Math.floor(cut), frac = cut - whole;
        const pre = g.measureText(it.txt.slice(0, whole)).width, cw = whole < letters.length ? g.measureText(letters[whole]).width : 0;
        const xw = sung >= 1 ? it.wd + 20 : pre + cw * frac;
        g.save(); g.beginPath(); g.rect(-20, -it.size * 1.3, xw + 20, it.size * 1.7); g.clip();
        g.fillStyle = w.accent ? '#fff7d6' : C.gold; g.fillText(it.txt, 0, 0);
        g.restore();
        if (active && w.accent) { g.save(); g.globalCompositeOperation = 'lighter'; g.globalAlpha = .35 * alpha; g.shadowColor = '#ffcf6a'; g.shadowBlur = 40; g.fillStyle = '#ffcf6a'; g.fillText(it.txt, 0, 0); g.restore(); }
      }
      g.restore();
      // ударная волна для акцентных слов
      if (w.accent) { const rp = prog(t, w.start, w.start + .45); if (rp > 0 && rp < 1) { g.save(); g.globalAlpha = (1 - rp) * .7 * alpha; g.strokeStyle = C.gold; g.lineWidth = 8 * (1 - rp) + 1; g.beginPath(); g.ellipse(cx, yy - it.size * .35, it.wd * .55 + rp * 220, it.size * .7 + rp * 120, 0, 0, TAU); g.stroke(); g.restore(); } }
    });
  });
}

/* ---------- пост-обработка ---------- */
const mk = () => { const c = document.createElement('canvas'); c.width = W; c.height = H; return c; };
const bufA = mk(), bufB = mk(), gA = bufA.getContext('2d'), gB = bufB.getContext('2d');
const grains = [0, 1, 2, 3].map(k => { const c = document.createElement('canvas'); c.width = 360; c.height = 640; const g = c.getContext('2d'); const im = g.createImageData(360, 640); let s = 1234 + k * 999; for (let i = 0; i < im.data.length; i += 4) { s = (s * 16807) % 2147483647; const v = s % 256; im.data[i] = im.data[i + 1] = im.data[i + 2] = v; im.data[i + 3] = 255; } g.putImageData(im, 0, 0); return c; });
const vignette = (() => { const c = mk(), g = c.getContext('2d'); g.fillStyle = radial(g, W / 2, H / 2, H * .72, [[0, 'rgba(0,0,0,0)'], [.6, 'rgba(0,0,0,0)'], [1, 'rgba(0,0,0,.75)']]); g.fillRect(0, 0, W, H); return c; })();

function drawScene(g, sc, t) { g.save(); sc.draw(g, t, t - sc.t0, clamp((t - sc.t0) / (sc.t1 - sc.t0))); g.restore(); }
const TR_IN = .12, TR_OUT = .22;
function render(t) {
  const g = ctx;
  g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1; g.globalCompositeOperation = 'source-over';
  // ищем переход
  let tr = null;
  for (let i = 1; i < SCENES.length; i++) { const s = SCENES[i]; if (t >= s.t0 - TR_IN && t < s.t0 + TR_OUT) tr = { from: SCENES[i - 1], to: s, k: (t - (s.t0 - TR_IN)) / (TR_IN + TR_OUT), type: s.tr }; }
  const bp = beatPulse(t, 8) * (.4 + .6 * energy(t));
  const zoom = 1 + .022 * bp;
  const sh = hit(t, 5.05, 8) + hit(t, 18.0, 6) * 1.2;
  const blit = (src, z = 1, a = 1, dx = 0, dy = 0) => { g.save(); g.globalAlpha = a; g.translate(W / 2 + dx, H / 2 + dy); g.scale(z * zoom, z * zoom); g.drawImage(src, -W / 2, -H / 2); g.restore(); };
  const ox = noise(t * 25) * 24 * sh, oy = noise(t * 25 + 5) * 24 * sh;
  if (!tr) { drawScene(gA, sceneAt(t), t); blit(bufA, 1, 1, ox, oy); }
  else {
    drawScene(gA, tr.from, t); drawScene(gB, tr.to, t);
    const k = tr.k, ke = E.inOut(k);
    switch (tr.type) {
      case 'flash': blit(k < .35 ? bufA : bufB, k < .35 ? 1 + .15 * k : 1.08 - .08 * ke, 1, ox, oy); g.fillStyle = `rgba(255,236,190,${Math.sin(clamp(k * 1.2) * Math.PI) * .95})`; g.fillRect(0, 0, W, H); break;
      case 'zoom': blit(bufA, 1 + 1.4 * E.in(k), 1, ox, oy); blit(bufB, 1.6 - .6 * E.out(k), clamp(k * 2), ox, oy); break;
      case 'slice': { blit(bufA, 1, 1, ox, oy); const n = 8; for (let i = 0; i < n; i++) { const d = clamp(k * 1.6 - i / n * .6), off = (1 - E.out(d)) * W * (i % 2 ? 1 : -1); g.save(); g.beginPath(); g.rect(0, i * H / n, W, H / n + 1); g.clip(); blit(bufB, 1, 1, off, 0); g.restore(); } break; }
      case 'wipe': { blit(bufA, 1, 1, ox, oy); const x = lerp(-700, W + 700, ke); g.save(); g.beginPath(); g.moveTo(-800, 0); g.lineTo(x + 300, 0); g.lineTo(x - 300, H); g.lineTo(-800, H); g.clip(); blit(bufB, 1, 1, ox, oy); g.restore(); g.save(); g.fillStyle = C.red; g.beginPath(); g.moveTo(x + 300, 0); g.lineTo(x + 380, 0); g.lineTo(x - 220, H); g.lineTo(x - 300, H); g.fill(); g.fillStyle = C.gold; g.beginPath(); g.moveTo(x + 380, 0); g.lineTo(x + 400, 0); g.lineTo(x - 200, H); g.lineTo(x - 220, H); g.fill(); g.restore(); break; }
      case 'iris': { blit(bufA, 1 + .1 * k, 1, ox, oy); const r = E.inOut(k) * 1300; g.save(); g.beginPath(); g.arc(W / 2, H * .55, r, 0, TAU); g.clip(); blit(bufB, 1, 1, ox, oy); g.restore(); g.strokeStyle = C.gold; g.lineWidth = 18 * (1 - k) + 2; g.beginPath(); g.arc(W / 2, H * .55, r, 0, TAU); g.stroke(); break; }
    }
  }
  // световые блики
  g.save(); g.globalCompositeOperation = 'screen';
  for (let i = 0; i < 2; i++) { const x = W * (.5 + .45 * noise(t * .3 + i * 10)), y = H * (.5 + .45 * noise(t * .25 + i * 20)); g.fillStyle = radial(g, x, y, 700, [[0, i ? 'rgba(255,110,40,.16)' : 'rgba(255,200,120,.12)'], [1, 'rgba(0,0,0,0)']]); g.fillRect(0, 0, W, H); }
  g.restore();
  g.drawImage(vignette, 0, 0);
  drawLyrics(g, t);
  // зерно плёнки
  g.save(); g.globalCompositeOperation = 'overlay'; g.globalAlpha = .1; g.imageSmoothingEnabled = false; g.drawImage(grains[Math.floor(t * 30) % 4], 0, 0, W, H); g.restore();
  // хроматическая вспышка на сильных долях
  if (sh > .05) { g.save(); g.globalCompositeOperation = 'lighter'; g.globalAlpha = .25 * sh; g.drawImage(cv, 8 * sh, 0); g.restore(); }
  // мягкое затемнение в конце (не до чёрного)
  const fo = prog(t, D.duration - 2.6, D.duration); if (fo > 0) { g.fillStyle = `rgba(18,6,10,${.6 * E.inOut(fo)})`; g.fillRect(0, 0, W, H); }
}

/* ---------- запуск ---------- */
window.render = render;
window.READY = document.fonts.load('900 40px Unbounded', 'АЯ').then(() => Promise.all([document.fonts.load('700 40px Oswald', 'АЯ'), document.fonts.load('700 40px Oswald', '«»—$')])).then(() => document.fonts.ready).then(() => { layouts.clear(); return true; });
if (!/render=1/.test(location.search)) {
  document.body.classList.add('preview'); document.getElementById('hint').hidden = false;
  const au = document.getElementById('a');
  const m = location.search.match(/t=([\d.]+)/);
  window.READY.then(() => {
    render(m ? +m[1] : 0);
    cv.onclick = () => (au.paused ? au.play() : au.pause());
    const loop = () => { if (!au.paused) render(au.currentTime); requestAnimationFrame(loop); }; loop();
  });
}
