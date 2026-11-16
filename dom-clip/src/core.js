'use strict';
// ---------- constants ----------
const W = 1080, H = 1920, FPS = 30, DUR = 153.6;
const BPM = 134.2, BEAT = 60 / BPM, PH = 0.22; // beat grid measured from the track

const C = {
  amber: '#ffb547', cyan: '#46d4ff', blue: '#5b8cff', violet: '#9b8cff', pink: '#ff6fa3',
  green: '#3ddc97', red: '#ff4d5e', warm: '#ffcf86', white: '#f4f6fb', teal: '#3fe0d0'
};

// ---------- math ----------
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, t) => a + (b - a) * t;
const inv = (a, b, x) => clamp((x - a) / (b - a));
const sstep = (a, b, x) => { const t = inv(a, b, x); return t * t * (3 - 2 * t); };
const eOC = t => 1 - Math.pow(1 - clamp(t), 3);
const eIC = t => Math.pow(clamp(t), 3);
const eIOC = t => { t = clamp(t); return t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };
const eOQ = t => 1 - Math.pow(1 - clamp(t), 5);
const eOB = t => { t = clamp(t); const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); };
const eOE = t => t >= 1 ? 1 : 1 - Math.pow(2, -10 * clamp(t));
function hash(n) { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); }
function noise1(x) { const i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f); return lerp(hash(i), hash(i + 1), u); }
function rng(seed) {
  let s = seed >>> 0 || 1;
  return () => { s |= 0; s = s + 0x6D2B79F5 | 0; let t = Math.imul(s ^ s >>> 15, 1 | s); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
}
function hexRGB(h) { const n = parseInt(h.slice(1), 16); return [n >> 16 & 255, n >> 8 & 255, n & 255]; }
function hexA(h, a) { const c = hexRGB(h); return `rgba(${c[0]},${c[1]},${c[2]},${a})`; }
function rgbA(c, a) { return `rgba(${c[0] | 0},${c[1] | 0},${c[2] | 0},${a})`; }
function mixRGB(a, b, t) { return [lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t)]; }
function mk(w, h) { const c = document.createElement('canvas'); c.width = Math.max(1, Math.round(w)); c.height = Math.max(1, Math.round(h)); return c; }
function cx2(c) { return c.getContext('2d'); }

// beat helpers
function beatPos(t) { return (t - PH) / BEAT; }
function pulse(t, sharp = 6) { const b = beatPos(t); return Math.exp(-(b - Math.floor(b)) * sharp); }
function barPulse(t, sharp = 4) { const b = beatPos(t) / 4; return Math.exp(-(b - Math.floor(b)) * sharp); }
function snapBeat(t) { return PH + Math.round(beatPos(t)) * BEAT; }

// song energy (0..1)
const ENERGY = [[0, .2], [14.3, .25], [14.9, .45], [42.3, .5], [42.5, .05], [43.5, 1], [72.6, 1], [73.6, .55], [86.2, .55], [86.6, .45], [117.6, .5], [118.6, .9], [120.0, .4], [122.0, 1], [148.0, 1], [149.6, .1], [DUR, 0]];
function energy(t) {
  for (let i = 0; i < ENERGY.length - 1; i++) if (t >= ENERGY[i][0] && t < ENERGY[i + 1][0]) return lerp(ENERGY[i][1], ENERGY[i + 1][1], sstep(ENERGY[i][0], ENERGY[i + 1][0], t));
  return 0;
}
const isChorus = t => (t > 43.5 && t < 72.6) || (t > 118.6 && t < 148);

// ---------- drawing helpers ----------
function rr(g, x, y, w, h, r) { g.beginPath(); g.roundRect(x, y, w, h, r); }
function font(w, s, fam = 'Inter') { return `${w} ${s}px "${fam}"`; }
function text(g, s, x, y, f, col, align = 'center', ls = 0, base = 'alphabetic') {
  g.font = f; g.fillStyle = col; g.textAlign = align; g.textBaseline = base; g.letterSpacing = ls + 'px';
  g.fillText(s, x, y); g.letterSpacing = '0px';
}
function glowText(g, s, x, y, f, col, glow, blur, align = 'center', ls = 0) {
  g.save(); g.shadowColor = glow; g.shadowBlur = blur; text(g, s, x, y, f, col, align, ls); g.restore();
}
function radial(g, x, y, r, col, a0, a1 = 0) {
  const gr = g.createRadialGradient(x, y, 0, x, y, r);
  gr.addColorStop(0, hexA(col, a0)); gr.addColorStop(1, hexA(col, a1));
  g.fillStyle = gr; g.fillRect(x - r, y - r, r * 2, r * 2);
}
function lingrad(g, x0, y0, x1, y1, stops) { const gr = g.createLinearGradient(x0, y0, x1, y1); stops.forEach(s => gr.addColorStop(s[0], s[1])); return gr; }

// soft glow sprite (pre-rendered), drawn with any color via cache
const _glow = {};
function glowSprite(col) {
  if (_glow[col]) return _glow[col];
  const c = mk(128, 128), g = cx2(c), gr = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  gr.addColorStop(0, hexA(col, 1)); gr.addColorStop(.25, hexA(col, .45)); gr.addColorStop(1, hexA(col, 0));
  g.fillStyle = gr; g.fillRect(0, 0, 128, 128); return (_glow[col] = c);
}
function glowDot(g, x, y, r, col, a = 1) { g.globalAlpha *= a; g.drawImage(glowSprite(col), x - r, y - r, r * 2, r * 2); g.globalAlpha /= a || 1; }

// blur by down/up-sampling
const _tmp = [mk(W, H), mk(W, H)];
function drawBlurred(dst, src, amount, alpha = 1) {
  if (alpha <= 0.001) return;
  dst.save(); dst.globalAlpha = alpha;
  if (amount < 0.6) { dst.drawImage(src, 0, 0); dst.restore(); return; }
  const f = clamp(1 / (1 + amount / 2.2), 0.02, 1);
  const w = Math.max(2, Math.round(src.width * f)), h = Math.max(2, Math.round(src.height * f));
  const a = _tmp[0], ag = cx2(a);
  ag.setTransform(1, 0, 0, 1, 0, 0); ag.clearRect(0, 0, w + 2, h + 2);
  ag.imageSmoothingQuality = 'high';
  if (f < 0.5) { // two-step
    const w2 = Math.round(src.width * Math.sqrt(f)), h2 = Math.round(src.height * Math.sqrt(f));
    const b = _tmp[1], bg = cx2(b); bg.setTransform(1, 0, 0, 1, 0, 0); bg.clearRect(0, 0, w2 + 2, h2 + 2); bg.imageSmoothingQuality = 'high';
    bg.drawImage(src, 0, 0, w2, h2); ag.drawImage(b, 0, 0, w2, h2, 0, 0, w, h);
  } else ag.drawImage(src, 0, 0, w, h);
  dst.imageSmoothingQuality = 'high';
  dst.drawImage(a, 0, 0, w, h, 0, 0, src.width, src.height);
  dst.restore();
}

// ---------- glass card (cached body) ----------
const _cards = {};
function cardBody(w, h, r) {
  const k = w + 'x' + h + 'x' + r; if (_cards[k]) return _cards[k];
  const pad = 90, c = mk(w + pad * 2, h + pad * 2), g = cx2(c);
  g.save(); g.shadowColor = 'rgba(0,0,0,0.65)'; g.shadowBlur = 70; g.shadowOffsetY = 26;
  rr(g, pad, pad, w, h, r); g.fillStyle = 'rgba(14,16,22,0.9)'; g.fill(); g.restore();
  rr(g, pad, pad, w, h, r);
  g.fillStyle = lingrad(g, 0, pad, 0, pad + h, [[0, 'rgba(36,39,50,0.92)'], [1, 'rgba(15,17,23,0.94)']]); g.fill();
  g.lineWidth = 2; g.strokeStyle = 'rgba(255,255,255,0.09)'; g.stroke();
  // top sheen
  g.save(); rr(g, pad, pad, w, h, r); g.clip();
  g.fillStyle = lingrad(g, 0, pad, 0, pad + 220, [[0, 'rgba(255,255,255,0.06)'], [1, 'rgba(255,255,255,0)']]); g.fillRect(pad, pad, w, 220);
  g.restore();
  return (_cards[k] = { c, pad });
}
function card(g, x, y, w, h, o = {}) {
  const r = o.r || 46, b = cardBody(w, h, r);
  g.drawImage(b.c, x - b.pad, y - b.pad);
  if (o.accent) { // accent edge glow
    g.save(); rr(g, x, y, w, h, r); g.clip();
    const gr = g.createRadialGradient(x + w / 2, y - 40, 0, x + w / 2, y - 40, w * .7);
    gr.addColorStop(0, hexA(o.accent, .16 * (o.glow ?? 1))); gr.addColorStop(1, hexA(o.accent, 0)); g.fillStyle = gr; g.fillRect(x, y, w, h);
    g.restore();
  }
  if (o.title) {
    g.fillStyle = o.accent || C.white; g.beginPath(); g.arc(x + 52, y + 58, 7, 0, 7); g.fill();
    text(g, o.title, x + 70, y + 67, font(700, 25, 'JetBrains Mono'), o.accent || C.white, 'left', 3);
  }
  if (o.right) text(g, o.right, x + w - 46, y + 67, font(500, 25, 'JetBrains Mono'), 'rgba(255,255,255,0.45)', 'right', 1);
  if (o.label) text(g, o.label, x + w / 2, y + h + 74, font(500, 30), 'rgba(255,255,255,0.5)', 'center', 1);
}
const CARD = { x: 80, y: 560, w: 920, h: 900 };

// ---------- deterministic world assets ----------
let PROJ_READY = false;
const WORLD = {};
function initWorld() {
  WORLD.land110 = topojson.feature(WORLD_110m, WORLD_110m.objects.land);
  WORLD.c110 = topojson.feature(WORLD_110m, WORLD_110m.objects.countries).features;
  WORLD.c50 = topojson.feature(WORLD_50m, WORLD_50m.objects.countries).features;
  WORLD.borders50 = topojson.mesh(WORLD_50m, WORLD_50m.objects.countries, (a, b) => a !== b);
  WORLD.graticule = d3.geoGraticule10();
  PROJ_READY = true;
}
const CITY = {
  london: [-0.13, 51.5], prague: [14.42, 50.08], nice: [7.26, 43.7], paris: [2.35, 48.86], frankfurt: [8.68, 50.11],
  vienna: [16.37, 48.21], munich: [11.58, 48.14], zurich: [8.54, 47.37], milan: [9.19, 45.46], barcelona: [2.17, 41.39],
  lisbon: [-9.14, 38.72], berlin: [13.4, 52.52], istanbul: [28.98, 41.0], tbilisi: [44.8, 41.7], dubai: [55.27, 25.2],
  bangkok: [100.5, 13.75], bali: [115.2, -8.65], newyork: [-74, 40.7], belgrade: [20.46, 44.8], yerevan: [44.5, 40.18],
  amsterdam: [4.9, 52.37], madrid: [-3.7, 40.42], rome: [12.5, 41.9], budapest: [19.04, 47.5], warsaw: [21.0, 52.23]
};
