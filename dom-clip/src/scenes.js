'use strict';
// =================== scenes ===================
const SC = [];
function S(a, b, draw, o = {}) { SC.push(Object.assign({ a, b, draw, tin: .4, tout: .4, fin: 'blur', fout: 'blur', acc: C.blue }, o)); }
const lazy = f => { let v; return () => v || (v = f()); };
const scratch = [mk(W, H), mk(W, H)];
const clr = c => { const g = cx2(c); g.setTransform(1, 0, 0, 1, 0, 0); g.clearRect(0, 0, c.width, c.height); g.globalAlpha = 1; return g; };

// ---------------- INTRO: world clocks ----------------
function scIntro(g, t) {
  const a1 = sstep(.3, 1.3, t) * (1 - sstep(2.3, 3.0, t));
  if (a1 > 0) {
    g.globalAlpha = a1;
    text(g, 'MORGENSHTERN', 540, 930, font(500, 30, 'JetBrains Mono'), 'rgba(255,255,255,0.7)', 'center', 14);
    glowText(g, 'ДОМ', 540, 1030, font(800, 76, 'Inter Display'), C.white, hexA(C.cyan, .7), 30, 'center', 34);
    g.globalAlpha = 1;
  }
  const ca = eOC(inv(2.7, 3.6, t)); if (ca <= 0) return;
  g.globalAlpha = ca; g.translate(0, (1 - ca) * 50);
  const { x, y, w, h } = CARD;
  card(g, x, y, w, h, { accent: C.cyan, title: 'ЧАСОВЫЕ ПОЯСА', right: 'сейчас', label: 'Часы' });
  // analog clock
  const cx = 540, cy = y + 250, R = 125, base = 23 * 3600 + 58 * 60 + 12 + t;
  g.strokeStyle = 'rgba(255,255,255,0.12)'; g.lineWidth = 2; g.beginPath(); g.arc(cx, cy, R, 0, 7); g.stroke();
  g.save(); g.shadowColor = C.cyan; g.shadowBlur = 20; g.strokeStyle = hexA(C.cyan, .9); g.lineWidth = 4;
  g.beginPath(); g.arc(cx, cy, R, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * ((base % 60) / 60)); g.stroke(); g.restore();
  for (let i = 0; i < 60; i++) { const a = i / 60 * Math.PI * 2, l = i % 5 ? 8 : 18; g.strokeStyle = i % 5 ? 'rgba(255,255,255,0.18)' : 'rgba(255,255,255,0.5)'; g.lineWidth = i % 5 ? 2 : 3; g.beginPath(); g.moveTo(cx + Math.cos(a) * (R - 14), cy + Math.sin(a) * (R - 14)); g.lineTo(cx + Math.cos(a) * (R - 14 - l), cy + Math.sin(a) * (R - 14 - l)); g.stroke(); }
  const sec = Math.floor(base) % 60 + eOB(clamp((base % 1) * 5)) - 1;
  const hand = (ang, len, wd, col) => { g.strokeStyle = col; g.lineWidth = wd; g.lineCap = 'round'; g.beginPath(); g.moveTo(cx, cy); g.lineTo(cx + Math.sin(ang) * len, cy - Math.cos(ang) * len); g.stroke(); };
  hand((base / 43200) * Math.PI * 2, 60, 8, C.white); hand((base / 3600) * Math.PI * 2, 92, 5, C.white); hand(((Math.floor(base / 60) * 60 + sec + 1) / 60) * Math.PI * 2, 104, 2.5, C.cyan);
  g.fillStyle = C.cyan; g.beginPath(); g.arc(cx, cy, 7, 0, 7); g.fill();
  const rows = [['ЛОНДОН', 0], ['ПРАГА', 1], ['НИЦЦА', 1], ['ДУБАЙ', 4], ['БАНГКОК', 7], ['ДОМ', null]];
  rows.forEach((r, i) => {
    const ta = 3.4 + i * BEAT * 2, k = eOC(inv(ta, ta + .5, t)); if (k <= 0) return;
    const ry = y + 450 + i * 74;
    g.save(); g.globalAlpha *= k; g.translate((1 - k) * 40, 0);
    g.strokeStyle = 'rgba(255,255,255,0.07)'; g.lineWidth = 2; g.beginPath(); g.moveTo(x + 50, ry + 26); g.lineTo(x + w - 50, ry + 26); g.stroke();
    const home = r[1] === null;
    text(g, r[0], x + 54, ry, font(600, 38), home ? 'rgba(255,255,255,0.45)' : C.white, 'left');
    text(g, home ? 'часовой пояс не найден' : `GMT+${r[1]}`, x + 250 + (home ? 0 : 0), ry - 4, font(500, 21, 'JetBrains Mono'), home ? hexA(C.red, .8) : 'rgba(255,255,255,0.4)', 'left', 1);
    let ts = '--:--:--';
    if (!home) { const s2 = (Math.floor(base) + r[1] * 3600) % 86400; ts = [s2 / 3600 | 0, (s2 / 60 | 0) % 60, s2 % 60].map(v => String(v).padStart(2, '0')).join(':'); }
    const blink = home ? .45 + .4 * (Math.sin(t * 6) > 0) : 1;
    text(g, ts, x + w - 54, ry, font(500, 38, 'JetBrains Mono'), home ? hexA(C.red, blink) : C.white, 'right');
    g.restore();
  });
}

// ---------------- ДОМ word -> particles, empty apartment -> dream ----------------
const domGlyphs = lazy(() => {
  const f = font(800, 330, 'Inter Display'), c = mk(W, H), g = cx2(c);
  g.font = f; g.letterSpacing = '0px';
  const chars = ['Д', 'О', 'М'], ws = chars.map(ch => g.measureText(ch).width), gap = 18, tot = ws.reduce((a, b) => a + b) + gap * 2;
  let x = W / 2 - tot / 2; const y = 1080; const glyphs = [];
  chars.forEach((ch, i) => {
    const gc = mk(ws[i] + 160, 460), gg = cx2(gc);
    gg.font = f; gg.textBaseline = 'alphabetic'; gg.shadowColor = hexA(C.amber, .9); gg.shadowBlur = 50;
    gg.fillStyle = '#fff3df'; gg.fillText(ch, 80, 380); gg.shadowBlur = 0; gg.fillText(ch, 80, 380);
    glyphs.push({ c: gc, x: x - 80, y: y - 380, w: ws[i] });
    g.fillStyle = '#fff'; g.font = f; g.fillText(ch, x, y); x += ws[i] + gap;
  });
  const id = g.getImageData(0, 0, W, H).data, pts = []; let minx = W, maxx = 0;
  for (let yy = 600; yy < 1160; yy += 5) for (let xx = 0; xx < W; xx += 5) if (id[(yy * W + xx) * 4 + 3] > 128) { pts.push([xx, yy, hash(xx * 3.1 + yy), hash(yy * 1.7 + xx * .3)]); minx = Math.min(minx, xx); maxx = Math.max(maxx, xx); }
  return { glyphs, pts, minx, maxx };
});
function scDom(g, t) {
  const D = domGlyphs();
  // apartment
  const aa = sstep(15.3, 17.0, t) * (1 - sstep(21.6, 22.95, t)), dream = inv(19.55, 22.4, t);
  if (aa > 0) {
    const sc = 1 + .04 * inv(14.5, 23, t) + .12 * eIC(dream);
    const al = clr(scratch[0]); al.translate(540, 960); al.scale(sc, sc); al.translate(-540, -960); al.drawImage(ART.apt, 0, 0);
    drawBlurred(g, scratch[0], dream * 22, aa * (1 - dream * .35));
    if (dream > 0) { g.save(); g.translate(26 * Math.sin(t * 1.3) * dream, -18 * dream); drawBlurred(g, scratch[0], 8 + dream * 30, aa * .4 * Math.sin(Math.PI * dream)); g.restore(); }
  }
  // letters
  const sweep0 = 18.35, sweep1 = 19.55, sw = eIOC(inv(sweep0, sweep1, t)), sx = lerp(D.minx - 30, D.maxx + 30, sw);
  D.glyphs.forEach((gl, i) => {
    const ta = 14.78 + i * .11, k = eOC(inv(ta, ta + .45, t)); if (k <= 0) return;
    g.save();
    if (sw > 0) { g.beginPath(); g.rect(sx, 0, W, H); g.clip(); }
    g.globalAlpha = k * (1 - .25 * sstep(17.5, 18.3, t)); const s = lerp(1.3, 1, k);
    g.translate(gl.x + gl.c.width / 2, gl.y + 380 - 120); g.scale(s, s); g.drawImage(gl.c, -gl.c.width / 2, -380 + 120);
    g.restore();
  });
  if (t > sweep0) {
    g.fillStyle = '#ffe2b8';
    for (const p of D.pts) {
      const ta = sweep0 + (p[0] - D.minx) / (D.maxx - D.minx + 1) * (sweep1 - sweep0), age = t - ta;
      if (age < 0 || age > 2.6) continue;
      const x = p[0] + age * (50 + 120 * p[2]) + Math.sin(age * 3 + p[3] * 9) * 14 * age, y = p[1] - age * (90 + 300 * p[3]) - age * age * 40;
      g.globalAlpha = (1 - age / 2.6) * .9; const s = 3.4 * (1 - age / 3.2);
      g.fillRect(x, y, s, s);
    }
    g.globalAlpha = 1;
  }
}

// ---------------- globe ----------------
function drawGlobe(g, cx, cy, R, lon, lat, o = {}) {
  const proj = d3.geoOrthographic().scale(R).translate([cx, cy]).rotate([-lon, -lat]).clipAngle(90).precision(.5);
  const path = d3.geoPath(proj, g);
  const atm = g.createRadialGradient(cx, cy, R * .9, cx, cy, R * 1.35);
  atm.addColorStop(0, hexA(o.acc || C.cyan, .35)); atm.addColorStop(.25, hexA(o.acc || C.cyan, .12)); atm.addColorStop(1, hexA(o.acc || C.cyan, 0));
  g.fillStyle = atm; g.fillRect(cx - R * 1.4, cy - R * 1.4, R * 2.8, R * 2.8);
  const sp = g.createRadialGradient(cx - R * .4, cy - R * .5, R * .1, cx, cy, R);
  sp.addColorStop(0, '#13264a'); sp.addColorStop(1, '#03060f');
  g.beginPath(); path({ type: 'Sphere' }); g.fillStyle = sp; g.fill();
  g.beginPath(); path(WORLD.graticule); g.strokeStyle = 'rgba(90,150,255,0.09)'; g.lineWidth = 1; g.stroke();
  g.beginPath(); path(WORLD.land110); g.fillStyle = hexA('#3d6fd0', o.landA ?? .26); g.fill(); g.strokeStyle = hexA('#8fc6ff', .55); g.lineWidth = 1.4; g.stroke();
  g.beginPath(); path({ type: 'Sphere' }); g.strokeStyle = hexA(o.acc || C.cyan, .5); g.lineWidth = 2; g.stroke();
  return proj;
}
function liftPoint(lon, lat, R, cx, cy, h, ll) {
  const p = d3.geoOrthographic().scale(1).translate([0, 0]).rotate([-lon, -lat])(ll);
  const vis = d3.geoDistance(ll, [lon, lat]) < Math.PI / 2 + h * 1.2;
  return [cx + p[0] * R * (1 + h), cy + p[1] * R * (1 + h), vis];
}
const GLOBE_CHAIN = ['lisbon', 'london', 'prague', 'belgrade', 'istanbul', 'tbilisi', 'dubai', 'bangkok', 'bali'];
const CITY_RU = { lisbon: 'ЛИССАБОН', london: 'ЛОНДОН', prague: 'ПРАГА', belgrade: 'БЕЛГРАД', istanbul: 'СТАМБУЛ', tbilisi: 'ТБИЛИСИ', dubai: 'ДУБАЙ', bangkok: 'БАНГКОК', bali: 'БАЛИ', nice: 'НИЦЦА', yerevan: 'ЕРЕВАН', newyork: 'НЬЮ-ЙОРК' };
function scGlobe(g, t) {
  const u = inv(22.95, 26.8, t), k = eOC(inv(22.95, 23.8, t));
  const lon = lerp(-8, 82, eIOC(u) * .85 + u * .15), lat = lerp(38, 18, u), R = 400 * lerp(.82, 1, k), cx = 540, cy = 1000;
  drawGlobe(g, cx, cy, R, lon, lat);
  const legT = 23.24, step = BEAT;
  for (let i = 0; i < GLOBE_CHAIN.length - 1; i++) {
    const a = CITY[GLOBE_CHAIN[i]], b = CITY[GLOBE_CHAIN[i + 1]], ts = legT + i * step, p = eIOC(inv(ts, ts + .7, t));
    if (p <= 0) continue;
    const ip = d3.geoInterpolate(a, b), N = 40, pts = [];
    for (let j = 0; j <= N * p; j++) { const uu = j / N; pts.push(liftPoint(lon, lat, R, cx, cy, .12 * Math.sin(Math.PI * uu) * Math.min(1, d3.geoDistance(a, b) * 1.5), ip(uu))); }
    for (const [lw, al] of [[10, .14], [3, .95]]) {
      g.strokeStyle = hexA(C.cyan, al); g.lineWidth = lw; g.lineCap = 'round'; g.beginPath(); let pen = false;
      for (const q of pts) { if (!q[2]) { pen = false; continue; } pen ? g.lineTo(q[0], q[1]) : g.moveTo(q[0], q[1]); pen = true; } g.stroke();
    }
    const hd = pts[pts.length - 1]; if (hd && hd[2] && p < 1) glowDot(g, hd[0], hd[1], 30, C.white, 1);
  }
  GLOBE_CHAIN.forEach((n, i) => {
    const ts = legT + (i - 1) * step + .7; const kk = i === 0 ? k : eOB(inv(ts, ts + .3, t)); if (kk <= 0) return;
    const q = liftPoint(lon, lat, R, cx, cy, 0, CITY[n]); if (!q[2]) return;
    glowDot(g, q[0], q[1], 26 * kk, C.cyan, 1); g.fillStyle = '#fff'; g.beginPath(); g.arc(q[0], q[1], 5 * kk, 0, 7); g.fill();
    g.globalAlpha = clamp(kk); text(g, CITY_RU[n], q[0] + 14, q[1] - 12, font(600, 20, 'JetBrains Mono'), 'rgba(255,255,255,0.75)', 'left', 2); g.globalAlpha = 1;
  });
}

// ---------------- airport: alone among the crowd ----------------
const crowd = lazy(() => Array.from({ length: 28 }, (_, i) => ({ z: .3 + Math.pow(hash(i * 7.3), .8) * 1.5, x0: hash(i * 3.7) * 1700, dir: hash(i * 9.1) < .5 ? -1 : 1, sp: 70 + hash(i * 2.3) * 90, ph: hash(i) * 6, bag: hash(i * 5.5) < .35, hh: .85 + hash(i * 4.4) * .25 })).sort((a, b) => a.z - b.z));
const lowres = { a: mk(W / 3, H / 3), b: mk(W / 8, H / 8) };
function scAirport(g, t) {
  const sc = 1 + .07 * inv(26.4, 30.1, t);
  g.save(); g.translate(540, 1000); g.scale(sc, sc); g.translate(-540, -1000);
  g.drawImage(ART.airport, 0, 0);
  // plane taking off outside
  const pu = inv(26.4, 30.2, t); g.save(); g.beginPath(); g.rect(180, 640, 720, 550); g.clip();
  g.globalAlpha = .9; g.drawImage(ART.plane, lerp(60, 640, pu), lerp(1060, 940, eIC(pu)), 300, 112); g.restore();
  // spotlight on the lone figure
  g.fillStyle = lingrad(g, 0, 300, 0, 1500, [[0, 'rgba(160,200,255,0)'], [1, 'rgba(160,200,255,0.10)']]);
  g.beginPath(); g.moveTo(500, 300); g.lineTo(580, 300); g.lineTo(700, 1500); g.lineTo(380, 1500); g.fill();
  radial(g, 540, 1490, 200, '#9fc4ff', .18);
  const P = crowd(), feet = z => 1190 + (z - .3) * 470;
  const drawSet = (gg, f, filter) => {
    gg.save(); gg.scale(f, f);
    for (const p of P) if (filter(p.z)) {
      const span = 1700, x = ((p.x0 + p.dir * p.sp * p.z * t) % span + span) % span - 310;
      const shade = Math.round(lerp(26, 4, clamp((p.z - .3) / 1.4)));
      person(gg, x, feet(p.z), 300 * p.z * p.hh, t * 7 + p.ph, `rgb(${shade},${shade + 3},${shade + 10})`, p.bag);
    }
    gg.restore();
  };
  drawSet(g, 1, z => z < .7);
  const la = clr(lowres.a); drawSet(la, 1 / 3, z => z >= .7 && z < 1.3); g.imageSmoothingQuality = 'high'; g.drawImage(lowres.a, 0, 0, W, H);
  // lone figure (still), rim-lit
  const br = Math.sin(t * 1.6) * 3;
  radial(g, 540, 1300, 420, '#9fc4ff', .16);
  g.save(); g.shadowColor = hexA('#b8d4ff', .9); g.shadowBlur = 40; person(g, 540, 1600, 560 + br, Math.PI, '#020308', true); g.restore();
  const lb = clr(lowres.b); drawSet(lb, 1 / 8, z => z >= 1.3); g.globalAlpha = .8; g.drawImage(lowres.b, 0, 0, W, H); g.globalAlpha = 1;
  g.restore();
}

// ---------------- airplane window over a night city ----------------
const groundLights = lazy(() => {
  const r = rng(808), L = [];
  for (let c = 0; c < 26; c++) {
    const cx = (r() - .5) * 90, cz = 4 + r() * 80, n = 40 + r() * 120 | 0, gs = .6 + r() * .8;
    for (let i = 0; i < n; i++) { const ax = Math.round((r() - .5) * 14) * gs, az = Math.round((r() - .5) * 14) * gs; L.push([cx + ax + (r() < .5 ? r() * gs : 0), cz + az, r() < .82 ? 0 : r() < .5 ? 1 : 2, r()]); }
  }
  for (let h = 0; h < 6; h++) { const x0 = (r() - .5) * 80, dx = (r() - .5) * .8; for (let z = 0; z < 84; z += .45) L.push([x0 + dx * z + Math.sin(z * .1 + h) * 3, z + 3, 3, r()]); }
  return L;
});
function scWindow(g, t) {
  g.fillStyle = lingrad(g, 0, 0, W, H, [[0, '#161922'], [.5, '#0d0f15'], [1, '#07080c']]); g.fillRect(0, 0, W, H);
  g.strokeStyle = 'rgba(255,255,255,0.04)'; g.lineWidth = 3; for (const y of [380, 1560]) { g.beginPath(); g.moveTo(0, y); g.lineTo(W, y); g.stroke(); }
  const cx = 540 + Math.sin(t * .7) * 6, cy = 960 + Math.sin(t * .9) * 8, ww = 580, wh = 800, rad = 290;
  // bezel
  g.save(); g.shadowColor = 'rgba(0,0,0,0.8)'; g.shadowBlur = 50; rr(g, cx - ww / 2 - 60, cy - wh / 2 - 60, ww + 120, wh + 120, rad + 60); g.fillStyle = '#1c1f29'; g.fill(); g.restore();
  rr(g, cx - ww / 2 - 60, cy - wh / 2 - 60, ww + 120, wh + 120, rad + 60); g.fillStyle = lingrad(g, 0, cy - wh / 2 - 60, 0, cy + wh / 2 + 60, [[0, '#2a2e3b'], [1, '#12141b']]); g.fill();
  rr(g, cx - ww / 2 - 18, cy - wh / 2 - 18, ww + 36, wh + 36, rad + 18); g.fillStyle = '#07080c'; g.fill();
  g.save(); rr(g, cx - ww / 2, cy - wh / 2, ww, wh, rad); g.clip();
  const hy = cy - 170;
  g.fillStyle = lingrad(g, 0, cy - wh / 2, 0, hy + 40, [[0, '#03060f'], [.7, '#121c3a'], [1, '#3a2c3a']]); g.fillRect(cx - ww / 2, cy - wh / 2, ww, hy + 40 - (cy - wh / 2));
  stars(g, 3, 40, cx - ww / 2, cy - wh / 2, ww, 180, .6);
  g.fillStyle = lingrad(g, 0, hy, 0, cy + wh / 2, [[0, '#1d1622'], [.2, '#0a0b14'], [1, '#040508']]); g.fillRect(cx - ww / 2, hy, ww, cy + wh / 2 - hy);
  const GL = groundLights(), v = 3.2, drift = Math.sin(t * .3) * 4;
  const cols = ['255,190,110', '255,240,220', '150,210,255', '255,170,80'];
  for (const p of GL) {
    const z = ((p[1] - v * t) % 84 + 84) % 84 + 2.2; if (z < 2.4) continue;
    const sx = cx + (p[0] + drift) * 520 / z, sy = hy + 2400 / z; if (sy > cy + wh / 2 + 10 || sx < cx - ww / 2 - 10 || sx > cx + ww / 2 + 10) continue;
    const s = Math.max(1.4, 9 / z), a = clamp(1.2 - z / 90) * (.5 + .5 * p[3]) * (p[2] === 3 ? .9 : 1);
    g.fillStyle = `rgba(${cols[p[2]]},${a})`; g.fillRect(sx - s / 2, sy - s / 2, s, s);
    if (z < 14 && p[3] > .7) glowDot(g, sx, sy, s * 4, '#ffb860', .25);
  }
  g.fillStyle = lingrad(g, 0, hy - 30, 0, hy + 140, [[0, 'rgba(255,150,90,0)'], [.3, 'rgba(255,150,90,0.16)'], [1, 'rgba(255,150,90,0)']]); g.fillRect(cx - ww / 2, hy - 30, ww, 170);
  // cloud wisps
  const cw = (t * 260) % 2400 - 900; g.globalAlpha = .35; g.drawImage(ART.cloud[0], 0, 200, 1400, 400, cx + 600 - cw, cy - 60, 1400, 400); g.globalAlpha = 1;
  // wing
  g.fillStyle = '#06070b'; g.beginPath(); g.moveTo(cx - ww / 2 - 10, cy + 190); g.lineTo(cx + 120, cy + 300); g.lineTo(cx + 170, cy + 318); g.lineTo(cx + 150, cy + 334); g.lineTo(cx - ww / 2 - 10, cy + 380); g.fill();
  g.strokeStyle = 'rgba(160,190,255,0.25)'; g.lineWidth = 2; g.beginPath(); g.moveTo(cx - ww / 2 - 10, cy + 190); g.lineTo(cx + 120, cy + 300); g.stroke();
  if ((t * 1.1) % 1 < .14) glowDot(g, cx + 166, cy + 322, 70, C.red, 1);
  g.restore();
  // glass reflection
  g.save(); rr(g, cx - ww / 2, cy - wh / 2, ww, wh, rad); g.clip(); g.fillStyle = 'rgba(255,255,255,0.05)';
  g.beginPath(); g.moveTo(cx - ww / 2, cy - 120); g.lineTo(cx + ww / 2, cy - wh / 2 - 80); g.lineTo(cx + ww / 2, cy - wh / 2 + 40); g.lineTo(cx - ww / 2, cy); g.fill(); g.restore();
  g.lineWidth = 3; g.strokeStyle = 'rgba(255,255,255,0.08)'; rr(g, cx - ww / 2, cy - wh / 2, ww, wh, rad); g.stroke();
}

// ---------------- unknown cities flashing ----------------
const RU_ALPH = 'АБВГДЕЖЗИКЛМНОПРСТУФХЦЧШЭЮЯ';
function scramble(str, settle, t, seed) {
  return str.split('').map((ch, i) => (t >= settle + i * .045 || ch === ' ') ? ch : RU_ALPH[Math.floor(hash(seed + i * 13 + Math.floor(t * 24)) * RU_ALPH.length)]).join('');
}
function scUnknown(g, t) {
  const cuts = [33.9, 34.74, 35.4, 36.28], names = ['БЕРЛИН', 'ДУБАЙ', 'СТАМБУЛ', 'ТБИЛИСИ'], coords = ['52.52° N · 13.40° E', '25.20° N · 55.27° E', '41.01° N · 28.98° E', '41.72° N · 44.79° E'];
  let k = 0; for (let i = 0; i < cuts.length; i++) if (t >= cuts[i]) k = i;
  const lt = t - cuts[k], z = 1.12 - .12 * eOQ(lt / .6) + lt * .02;
  g.save(); g.translate(540, 960); g.scale(z, z); g.translate(-540 + lt * (k % 2 ? 30 : -30), -960); g.drawImage(ART.sky[k], 0, 0); g.restore();
  const last = k === 3, nm = last ? scramble(names[k], 99, t, k * 50) : scramble(names[k], cuts[k] + .1, t, k * 50);
  const a = last ? (1 - sstep(36.9, 37.5, t)) * (.6 + .4 * (hash(Math.floor(t * 20)) > .3)) : 1;
  g.globalAlpha = a;
  const f = font(800, 150, 'Inter Display');
  const glitch = Math.exp(-lt * 9) + (last ? .4 : 0);
  if (glitch > .05) { g.save(); g.globalCompositeOperation = 'lighter'; text(g, nm, 540 + 14 * glitch, 760, f, hexA(C.red, .7 * glitch), 'center', 6); text(g, nm, 540 - 14 * glitch, 760, f, hexA(C.cyan, .7 * glitch), 'center', 6); g.restore(); }
  glowText(g, nm, 540, 760, f, C.white, hexA(C.violet, .8), 40, 'center', 6);
  text(g, last ? '??.??° N · ??.??° E' : coords[k], 540, 830, font(500, 26, 'JetBrains Mono'), 'rgba(255,255,255,0.6)', 'center', 4);
  g.globalAlpha = 1;
  g.fillStyle = `rgba(255,255,255,${.22 * Math.exp(-lt * 12)})`; g.fillRect(0, 0, W, H);
}

// ---------------- departures board ----------------
const BOARD_SETS = [
  [37.75, .12, [['23:40', 'ЛОНДОН', 'ВЫЛЕТЕЛ'], ['23:55', 'ПРАГА', 'ВЫЛЕТЕЛ'], ['00:10', 'НИЦЦА', 'ПО РАСП'], ['00:25', 'ДУБАЙ', 'ПО РАСП'], ['00:40', 'СТАМБУЛ', 'ПО РАСП'], ['01:05', 'ТБИЛИСИ', 'ЗАДЕРЖАН']]],
  [40.45, .07, [['00:10', 'НИЦЦА', 'ПОСАДКА'], ['00:25', 'ДУБАЙ', 'ПО РАСП'], ['00:40', 'СТАМБУЛ', 'ПО РАСП'], ['01:05', 'ТБИЛИСИ', 'ЗАДЕРЖАН'], ['01:30', 'ЛИССАБОН', 'ПО РАСП'], ['02:15', 'БАНГКОК', 'ПО РАСП']]],
  [41.35, .04, [['00:25', 'ДУБАЙ', 'ПОСАДКА'], ['00:40', 'СТАМБУЛ', 'ПОСАДКА'], ['01:05', 'ТБИЛИСИ', 'ПОСАДКА'], ['01:30', 'ЛИССАБОН', 'ПОСАДКА'], ['02:15', 'БАНГКОК', 'ПОСАДКА'], ['02:40', 'БАЛИ', 'ПОСАДКА']]],
  [41.8, .02, [['00:40', 'ЕРЕВАН', 'ПОСАДКА'], ['01:05', 'БЕЛГРАД', 'ПОСАДКА'], ['01:30', 'ЛОНДОН', 'ПОСАДКА'], ['02:15', 'ПРАГА', 'ПОСАДКА'], ['02:40', 'НИЦЦА', 'ПОСАДКА'], ['03:00', 'ДУБАЙ', 'ПОСАДКА']]],
  [42.12, .01, [['01:05', 'БАЛИ', 'ПОСАДКА'], ['01:30', 'ЛИССАБОН', 'ПОСАДКА'], ['02:15', 'ТБИЛИСИ', 'ПОСАДКА'], ['02:40', 'СТАМБУЛ', 'ПОСАДКА'], ['03:00', 'ЛОНДОН', 'ПОСАДКА'], ['03:20', 'ПРАГА', 'ПОСАДКА']]],
];
function flapRow(g, str, x, y, cw, chh, settle, t, col, seed) {
  for (let i = 0; i < str.length; i++) {
    const ts = settle + i * .025, ch = str[i];
    let c = ch; const flipping = t < ts && ch !== ' ';
    if (flipping) c = (RU_ALPH + '0123456789')[Math.floor(hash(seed + i * 7 + Math.floor(t * 28)) * 37)];
    const xx = x + i * cw;
    rr(g, xx, y, cw - 4, chh, 6); g.fillStyle = '#16140f'; g.fill();
    g.fillStyle = 'rgba(0,0,0,0.6)'; g.fillRect(xx, y + chh / 2 - 1, cw - 4, 2);
    if (c !== ' ') text(g, c, xx + (cw - 4) / 2, y + chh * .72, font(700, 34, 'JetBrains Mono'), flipping ? hexA(col, .55) : col, 'center');
    if (flipping) { g.fillStyle = 'rgba(255,255,255,0.05)'; g.fillRect(xx, y + (t * 28 % 1) * chh / 2, cw - 4, chh / 2); }
  }
}
function scBoard(g, t) {
  const zoom = 1 + .32 * eIC(inv(41.0, 42.5, t));
  g.translate(540, 1010); g.scale(zoom, zoom); g.translate(-540, -1010);
  const { x, y, w, h } = CARD;
  const T = 23 * 3600 + 59 * 60 + 2 + (t - 37.6) * (1 + 6 * eIC(inv(40.5, 42.5, t)));
  const clock = [T / 3600 % 24 | 0, (T / 60 | 0) % 60, T % 60 | 0].map(v => String(v).padStart(2, '0')).join(':');
  card(g, x, y, w, h, { accent: C.amber, title: 'ОТПРАВЛЕНИЕ', label: 'Аэропорт · табло' });
  text(g, clock, x + w - 46, y + 67, font(700, 28, 'JetBrains Mono'), C.amber, 'right', 2);
  g.strokeStyle = hexA(C.amber, .3); g.lineWidth = 2; g.beginPath(); g.moveTo(x + 46, y + 100); g.lineTo(x + w - 46, y + 100); g.stroke();
  const hdr = ['ВРЕМЯ', 'НАПРАВЛЕНИЕ', 'СТАТУС'], cw = 32, cx0 = x + 60;
  [0, 6, 17].forEach((c, i) => text(g, hdr[i], cx0 + c * cw, y + 150, font(600, 20, 'JetBrains Mono'), hexA(C.amber, .55), 'left', 2));
  let si = 0; for (let i = 0; i < BOARD_SETS.length; i++) if (t >= BOARD_SETS[i][0]) si = i;
  const [st, stag, rows] = BOARD_SETS[si];
  rows.forEach((r, ri) => {
    const ry = y + 180 + ri * 92, settle = st + ri * stag;
    const line = r[0].padEnd(5) + ' ' + r[1].padEnd(10) + ' ' + r[2].padEnd(8);
    const hot = r[2] === 'ПОСАДКА' && t > settle + .5;
    if (hot) { const bl = .5 + .5 * Math.sin(t * 14); g.fillStyle = hexA(C.amber, .06 + .08 * bl); rr(g, x + 40, ry - 10, w - 80, 72, 12); g.fill(); }
    flapRow(g, line, cx0, ry, cw, 52, settle, t, hot && Math.sin(t * 14) > 0 ? '#ffe2a8' : C.amber, ri * 100 + si * 1000);
  });
  text(g, 'ЗАЛ ОЖИДАНИЯ', x + 54, y + h - 46, font(600, 20, 'JetBrains Mono'), 'rgba(255,255,255,0.3)', 'left', 3);
  text(g, 'ВЫХОД 23', x + w - 54, y + h - 46, font(600, 20, 'JetBrains Mono'), 'rgba(255,255,255,0.3)', 'right', 3);
}

// ---------------- city posters (chorus) ----------------
const CITY_INFO = {
  london: { name: 'ЛОНДОН', co: '51.5072° N · 0.1276° W', tz: 'GMT+0', acc: C.cyan },
  prague: { name: 'ПРАГА', co: '50.0755° N · 14.4378° E', tz: 'GMT+1', acc: C.amber },
  nice: { name: 'НИЦЦА', co: '43.7102° N · 7.2620° E', tz: 'GMT+1', acc: C.pink },
};
function drawCityPoster(g, t, key, t0, v) {
  const A = ART[key], lt = t - t0, info = CITY_INFO[key];
  const z = (v ? 1.18 : 1.1) - .1 * eOQ(lt / .5) + lt * .015, px = (v ? -1 : 1) * lt * 22;
  const lay = (img, f, dy = 0) => { g.save(); g.translate(540, 960); g.scale(z, z); g.translate(-540 + px * f, -960 + dy); g.drawImage(img, 0, 0); g.restore(); };
  lay(A.sky, .2); if (A.far) lay(A.far, .5); if (A.mid) lay(A.mid, .8);
  if (key === 'nice') { lay(A.water, .5); g.save(); g.translate(540, 960); g.scale(z, z); g.translate(-540 + px * .5, -960); for (let i = 0; i < 70; i++) { const yy = A.hz + 6 + Math.pow(i / 70, 1.6) * 700, w2 = 20 + i * 1.6 + Math.sin(t * 3 + i) * 10, xx = 200 + Math.sin(i * 2.3 + t * 1.7) * (8 + i * .6); g.fillStyle = `rgba(230,240,255,${.5 * (1 - i / 80)})`; g.fillRect(xx - w2 / 2, yy, w2, 2.5); } g.restore(); }
  else { g.save(); g.translate(Math.sin(t * 2.2) * 3, 0); lay(A.water, .8); g.restore(); }
  lay(A.near, 1.25);
  // readability shade
  g.fillStyle = lingrad(g, 0, 0, 0, 1000, [[0, 'rgba(3,4,8,0.75)'], [.6, 'rgba(3,4,8,0.25)'], [1, 'rgba(3,4,8,0)']]); g.fillRect(0, 0, W, 1000);
  // typography
  const rv = eOE(inv(t0, t0 + .35, t)), ls = lerp(40, 10, rv), ny = 690;
  g.save(); g.beginPath(); g.rect(0, ny - 170 + (1 - rv) * 170, W, 230); g.clip();
  glowText(g, info.name, 540, ny + (1 - rv) * 60, font(900, 172, 'Inter Display'), C.white, hexA(info.acc, .9), 50, 'center', ls);
  g.restore();
  g.globalAlpha = eOC(inv(t0 + .1, t0 + .4, t));
  text(g, info.co, 540, ny - 170, font(500, 24, 'JetBrains Mono'), hexA(info.acc, .95), 'center', 4);
  text(g, `${info.tz}  ·  ВЫ ЗДЕСЬ`, 540, ny + 66, font(500, 24, 'JetBrains Mono'), 'rgba(255,255,255,0.65)', 'center', 4);
  g.globalAlpha = 1;
  g.fillStyle = `rgba(255,255,255,${.3 * Math.exp(-lt * 14)})`; g.fillRect(0, 0, W, H);
}
function scCities(times, v) {
  const keys = ['london', 'prague', 'nice'];
  return (g, t) => { let k = 0; for (let i = 0; i < 3; i++) if (t >= times[i]) k = i; drawCityPoster(g, t, keys[k], times[k], v); };
}

// ---------------- passport + stamps ----------------
const STAMP_POS = [ // page(0 left,1 right), x,y (page coords), rot, stampIdx
  [1, 110, 140, -.25, 0], [1, 300, 210, .18, 1], [0, -300, 160, .12, 2], [1, 140, 400, .3, 3], [0, -130, 330, -.2, 4], [1, 320, 470, -.12, 5],
  [0, -320, 470, .22, 6], [1, 210, 300, -.4, 7], [0, -170, 120, -.08, 8], [1, 330, 90, .1, 10], [0, -250, 280, .35, 11], [1, 200, 540, .05, 9]];
function drawPassport(g, t, t0, stampTimes, v) {
  const pw = 400, ph = 580, open = eIOC(inv(t0 - .05, t0 + .5, t));
  const intro = eOB(inv(t0 - .45, t0 - .05, t));
  let shake = 0; stampTimes.forEach(ts => { if (t > ts) shake += Math.exp(-(t - ts) * 16) * 12; });
  g.save();
  radial(g, 540, 980, 720, C.red, .08);
  g.translate(540 - pw / 2 * (1 - open) + (hash(Math.floor(t * 60)) - .5) * shake, 1000 + (1 - intro) * 300 + (hash(Math.floor(t * 60) + 9) - .5) * shake);
  const zz = (v ? 1.18 : 1.08) + .08 * inv(t0, t0 + 4.5, t); g.scale(zz, zz); g.rotate(v ? .06 : -.05);
  g.globalAlpha = clamp(intro * 1.4);
  // shadow
  g.save(); g.shadowColor = 'rgba(0,0,0,0.7)'; g.shadowBlur = 60; g.shadowOffsetY = 30; g.fillStyle = '#000'; g.fillRect(-pw * open, -ph / 2, pw * (1 + open), ph); g.restore();
  const page = (x0, isLeft) => {
    g.fillStyle = lingrad(g, x0, 0, x0 + pw, 0, isLeft ? [[0, '#cfc7b4'], [.85, '#d8d1c0'], [1, '#a9a290']] : [[0, '#a9a290'], [.12, '#d8d1c0'], [1, '#cfc7b4']]);
    g.fillRect(x0, -ph / 2, pw, ph);
    g.strokeStyle = 'rgba(40,120,130,0.18)'; g.lineWidth = 1.5;
    for (let k = 0; k < 18; k++) { g.beginPath(); for (let xx = 0; xx <= pw; xx += 8) { const yy = -ph / 2 + 30 + k * 30 + Math.sin(xx / 30 + k * .7) * 8; xx ? g.lineTo(x0 + xx, yy) : g.moveTo(x0 + xx, yy); } g.stroke(); }
    text(g, 'ВИЗЫ / VISAS', x0 + pw / 2, -ph / 2 + 36, font(600, 16, 'JetBrains Mono'), 'rgba(40,60,80,0.55)', 'center', 4);
    text(g, isLeft ? '14' : '15', x0 + pw / 2, ph / 2 - 18, font(500, 16, 'JetBrains Mono'), 'rgba(40,60,80,0.5)', 'center');
  };
  page(0, false);
  const drawStamps = left => STAMP_POS.forEach((sp, i) => {
    if ((sp[0] === 0) !== left || i >= stampTimes.length) return;
    const ts = stampTimes[i], k = inv(ts - .1, ts, t); if (k <= 0) return;
    const s = lerp(1.9, 1, eOC(k)), a = clamp(k * 1.2) * .88;
    g.save(); g.translate(left ? sp[1] + pw : sp[1], sp[2] - ph / 2); g.rotate(sp[3] + (v ? .3 : 0)); g.scale(s * .62, s * .62); g.globalAlpha = a; g.globalCompositeOperation = 'multiply';
    g.drawImage(ART.stamps[(sp[4] + (v ? 5 : 0)) % ART.stamps.length], -150, -150); g.restore();
    if (t > ts && t < ts + .35) { g.save(); g.translate(left ? sp[1] + pw : sp[1], sp[2] - ph / 2); g.strokeStyle = `rgba(255,255,255,${.6 * (1 - (t - ts) / .35)})`; g.lineWidth = 3; g.beginPath(); g.arc(0, 0, 90 + (t - ts) * 400, 0, 7); g.stroke(); g.restore(); }
  });
  drawStamps(false);
  // cover
  const sx = Math.cos(open * Math.PI);
  g.save();
  if (sx >= 0) {
    g.scale(sx, 1);
    g.fillStyle = lingrad(g, 0, -ph / 2, pw, ph / 2, [[0, '#1b3466'], [1, '#0c1a3a']]); rr(g, 0, -ph / 2, pw, ph, [0, 18, 18, 0]); g.fill();
    g.fillStyle = `rgba(0,0,0,${.5 * (1 - sx)})`; g.fillRect(0, -ph / 2, pw, ph);
    const gold = '#d9b56a';
    text(g, 'ПАСПОРТ', pw / 2, -150, font(700, 40), gold, 'center', 8);
    text(g, 'PASSPORT', pw / 2, -105, font(500, 22, 'JetBrains Mono'), gold, 'center', 8);
    g.strokeStyle = gold; g.lineWidth = 3; g.beginPath(); g.arc(pw / 2, 30, 70, 0, 7); g.stroke();
    g.beginPath(); g.ellipse(pw / 2, 30, 30, 70, 0, 0, 7); g.moveTo(pw / 2 - 70, 30); g.lineTo(pw / 2 + 70, 30); g.moveTo(pw / 2 - 62, -2); g.lineTo(pw / 2 + 62, -2); g.moveTo(pw / 2 - 62, 62); g.lineTo(pw / 2 + 62, 62); g.stroke();
    rr(g, pw / 2 - 30, 200, 60, 40, 8); g.stroke(); g.beginPath(); g.arc(pw / 2, 220, 9, 0, 7); g.stroke();
  } else {
    g.scale(sx, 1); g.translate(pw, 0); g.scale(-1, 1); // inside of the cover -> left page, un-mirrored
    page(0, true);
    drawStamps(true);
    g.fillStyle = `rgba(0,0,0,${.4 * (1 + sx)})`; g.fillRect(0, -ph / 2, pw, ph);
  }
  g.restore();
  g.restore();
}
function scPassport(t0, stampTimes, v) { return (g, t) => drawPassport(g, t, t0, stampTimes, v); }

// ---------------- europe map race ----------------
const europeExtra = lazy(() => {
  const all = new Path2D(); ART.europe.paths.forEach(p => all.addPath(p));
  const grat = new Path2D(d3.geoPath(ART.europe.proj)(d3.geoGraticule().step([5, 5])()));
  return { all, grat };
});
function drawEurope(g, t, t0, t1, R, acc, v) {
  const E = ART.europe, X = europeExtra(), N = R.pts.length - 1;
  const u = clamp((t - t0) / (t1 - t0)), pu = sstep(0, 1, u) * .7 + u * .3, idx = Math.min(N, Math.floor(pu * N));
  const lagI = Math.max(0, Math.min(N, Math.floor(clamp(sstep(0, 1, clamp((t - t0 - .25) / (t1 - t0))) * .7 + clamp((t - t0 - .25) / (t1 - t0)) * .3) * N)));
  const cam = R.pts[lagI], z = lerp(v ? 1.15 : 1.35, v ? .95 : 1.05, u) + .03 * pulse(t);
  g.fillStyle = '#04060c'; g.fillRect(0, 0, W, H);
  g.save(); g.translate(540, 1010); g.scale(z, z); g.translate(-cam[0], -cam[1]);
  g.strokeStyle = 'rgba(90,140,255,0.07)'; g.lineWidth = 1 / z; g.stroke(X.grat);
  g.fillStyle = '#0e1526'; g.fill(X.all);
  // visited countries
  const seen = new Map(); for (let i = 0; i <= idx; i++) { const c = R.cidx[i]; if (c >= 0 && !seen.has(c)) seen.set(c, i); }
  const cur = R.cidx[idx];
  for (const [c, i0] of seen) { const age = (idx - i0) / N * (t1 - t0); g.fillStyle = hexA(acc, c === cur ? .22 : .07 + .2 * Math.exp(-age * 3)); g.fill(E.paths[c]); }
  g.strokeStyle = 'rgba(150,180,255,0.3)'; g.lineWidth = 1.4 / z; g.stroke(E.borders);
  if (cur >= 0) { g.save(); g.shadowColor = acc; g.shadowBlur = 20; g.strokeStyle = hexA(acc, .95); g.lineWidth = 3 / z; g.stroke(E.paths[cur]); g.restore(); }
  // trail
  g.lineCap = 'round'; g.lineJoin = 'round';
  const seg = 12;
  for (let s = 0; s < idx; s += seg) {
    const e = Math.min(idx, s + seg + 1), a = .25 + .75 * (s / Math.max(1, idx));
    g.beginPath(); for (let i = s; i <= e; i++) i === s ? g.moveTo(R.pts[i][0], R.pts[i][1]) : g.lineTo(R.pts[i][0], R.pts[i][1]);
    g.strokeStyle = hexA(acc, .18 * a); g.lineWidth = 14 / z; g.stroke(); g.strokeStyle = hexA('#ffffff', .95 * a); g.lineWidth = 3.5 / z; g.stroke();
  }
  R.cityAt.forEach((c, i) => {
    if (c.i > idx + 2) return; const age = (idx - c.i) / N * (t1 - t0);
    glowDot(g, c.p[0], c.p[1], (22 + 30 * Math.exp(-age * 6)) / z, acc, 1); g.fillStyle = '#fff'; g.beginPath(); g.arc(c.p[0], c.p[1], 4.5 / z, 0, 7); g.fill();
    text(g, CITY_RU[c.n] || ({ paris: 'ПАРИЖ', frankfurt: 'ФРАНКФУРТ', vienna: 'ВЕНА', munich: 'МЮНХЕН', zurich: 'ЦЮРИХ', milan: 'МИЛАН', barcelona: 'БАРСЕЛОНА', madrid: 'МАДРИД', amsterdam: 'АМСТЕРДАМ', berlin: 'БЕРЛИН' })[c.n], c.p[0] + 12 / z, c.p[1] - 12 / z, font(600, Math.round(20 / z), 'JetBrains Mono'), 'rgba(255,255,255,0.8)', 'left', 2);
  });
  const hd = R.pts[idx]; glowDot(g, hd[0], hd[1], 50 / z, acc, 1); glowDot(g, hd[0], hd[1], 16 / z, '#ffffff', 1);
  g.restore();
  // HUD
  let crossings = 0, prev = R.cidx[0]; for (let i = 1; i <= idx; i++) if (R.cidx[i] >= 0 && R.cidx[i] !== prev) { crossings++; prev = R.cidx[i]; }
  const hud = (lbl, val, x, al) => { text(g, lbl, x, 1440, font(600, 20, 'JetBrains Mono'), 'rgba(255,255,255,0.45)', al, 3); text(g, val, x, 1492, font(700, 44, 'JetBrains Mono'), C.white, al); };
  hud('ГРАНИЦ ПЕРЕСЕЧЕНО', String(crossings).padStart(2, '0'), 90, 'left');
  hud('СКОРОСТЬ', `${Math.round(880 + 90 * Math.sin(t * 3))} КМ/Ч`, 990, 'right');
}
function scEurope(t0, t1, R, v) { return (g, t) => drawEurope(g, t, t0, t1, R, C.cyan, v); }

// ---------------- suitcase ----------------
function drawShirt(g, x, y, w, h, col, stripe) { rr(g, x, y, w, h, 14); g.fillStyle = col; g.fill(); g.strokeStyle = 'rgba(0,0,0,0.25)'; g.lineWidth = 2; g.stroke(); if (stripe) { g.fillStyle = stripe; for (let k = 1; k < 6; k++) g.fillRect(x + 6, y + k * h / 6, w - 12, 5); } g.fillStyle = 'rgba(255,255,255,0.12)'; g.beginPath(); g.moveTo(x + w / 2 - 40, y); g.lineTo(x + w / 2, y + 30); g.lineTo(x + w / 2 + 40, y); g.fill(); }
function drawTicket(g, x, y, rot, label) {
  g.save(); g.translate(x, y); g.rotate(rot); rr(g, -150, -55, 300, 110, 12); g.fillStyle = '#e9eef6'; g.fill();
  g.fillStyle = C.cyan; g.fillRect(-150, -55, 300, 26);
  text(g, 'BOARDING PASS', -136, -36, font(700, 14, 'JetBrains Mono'), '#06223a', 'left', 2);
  text(g, label, -136, 18, font(800, 36), '#0b1a2c', 'left', 1);
  g.fillStyle = '#0b1a2c'; for (let k = 0; k < 26; k++) g.fillRect(40 + k * 4, -16, (k * 7 % 3) + 1, 52);
  g.restore();
}
function drawSuitcase(g, t, t0, v) {
  const cx = 540, hy = 1010, w = 720, h = 470, bx = cx - w / 2;
  const intro = eOB(inv(t0 - .5, t0 + .05, t)), open = eIOC(inv(t0 + .5, t0 + 1.15, t));
  g.save(); g.translate(0, (1 - intro) * 700 + Math.sin(t * 2) * 4);
  radial(g, cx, hy + 120, 700, C.violet, .14);
  g.save(); g.shadowColor = 'rgba(0,0,0,0.7)'; g.shadowBlur = 60; g.shadowOffsetY = 30; rr(g, bx, hy, w, h, 40); g.fillStyle = '#0b0c12'; g.fill(); g.restore();
  // base interior
  rr(g, bx, hy, w, h, 40); g.fillStyle = '#2a2f45'; g.fill();
  rr(g, bx + 18, hy + 18, w - 36, h - 36, 28); g.fillStyle = lingrad(g, 0, hy, 0, hy + h, [[0, '#191b28'], [1, '#22263a']]); g.fill();
  g.setLineDash([10, 8]); g.strokeStyle = 'rgba(255,255,255,0.12)'; g.lineWidth = 2; rr(g, bx + 30, hy + 30, w - 60, h - 60, 22); g.stroke(); g.setLineDash([]);
  const items = [
    gg => { drawShirt(gg, bx + 60, hy + 60, 290, 170, '#2d3b66', 'rgba(255,255,255,0.08)'); drawShirt(gg, bx + 72, hy + 120, 290, 170, '#4b4f5e'); drawShirt(gg, bx + 84, hy + 180, 270, 160, '#d8d2c4', 'rgba(60,80,140,0.25)'); },
    gg => { gg.save(); gg.translate(bx + 470, hy + 150); gg.rotate(-.12); rr(gg, -70, -95, 140, 190, 10); gg.fillStyle = '#1b3466'; gg.fill(); gg.strokeStyle = '#d9b56a'; gg.lineWidth = 2; gg.beginPath(); gg.arc(0, -5, 32, 0, 7); gg.stroke(); text(gg, 'ПАСПОРТ', 0, -60, font(700, 16), '#d9b56a', 'center', 3); gg.restore(); },
    gg => { drawTicket(gg, bx + 520, hy + 330, .1, 'NCE → ???'); drawTicket(gg, bx + 500, hy + 380, -.06, 'LHR → PRG'); },
    gg => { gg.save(); gg.translate(bx + 170, hy + 380); gg.strokeStyle = '#0d0f17'; gg.lineWidth = 16; gg.beginPath(); gg.arc(0, 0, 70, Math.PI * 1.05, Math.PI * 1.95); gg.stroke(); gg.fillStyle = '#0d0f17'; rr(gg, -92, -20, 40, 60, 14); gg.fill(); rr(gg, 52, -20, 40, 60, 14); gg.fill(); gg.fillStyle = C.violet; gg.fillRect(-80, 0, 16, 4); gg.restore(); },
    gg => { gg.save(); gg.translate(bx + 640, hy + 70); gg.rotate(.5); gg.fillStyle = '#05060a'; gg.beginPath(); gg.ellipse(-28, 0, 24, 18, 0, 0, 7); gg.ellipse(28, 0, 24, 18, 0, 0, 7); gg.fill(); gg.fillRect(-6, -3, 12, 4); gg.restore(); },
  ];
  items.forEach((it, i) => { const ta = t0 + 1.0 + i * BEAT * .5, k = eOB(inv(ta, ta + .3, t)); if (k <= 0) return; g.save(); g.translate(cx, hy + h / 2); g.scale(k, k); g.translate(-cx, -(hy + h / 2)); g.globalAlpha = clamp(k); it(g); g.restore(); });
  // lid
  const sy = Math.cos(open * Math.PI);
  g.save(); g.translate(0, hy);
  if (sy >= 0) {
    g.scale(1, Math.max(.001, sy));
    rr(g, bx, 0, w, h, 40); g.fillStyle = lingrad(g, 0, 0, 0, h, [[0, '#3b4262'], [1, '#262b40']]); g.fill();
    g.strokeStyle = 'rgba(255,255,255,0.08)'; g.lineWidth = 6; for (let k = 1; k < 8; k++) { g.beginPath(); g.moveTo(bx + k * w / 8, 30); g.lineTo(bx + k * w / 8, h - 30); g.stroke(); }
    g.fillStyle = '#15182a'; rr(g, cx - 90, h - 46, 180, 30, 12); g.fill();
    // stickers
    g.save(); g.translate(bx + 150, 150); g.rotate(-.2); g.fillStyle = C.cyan; g.beginPath(); g.arc(0, 0, 62, 0, 7); g.fill(); text(g, 'LONDON', 0, 8, font(800, 22), '#05121e', 'center', 1); g.restore();
    g.save(); g.translate(bx + 520, 300); g.rotate(.15); rr(g, -90, -40, 180, 80, 10); g.fillStyle = C.amber; g.fill(); text(g, 'PRAHA', 0, 12, font(800, 32), '#1c1205', 'center', 2); g.restore();
    g.save(); g.translate(bx + 300, 330); g.rotate(-.05); rr(g, -70, -30, 140, 60, 30); g.fillStyle = C.pink; g.fill(); text(g, 'NICE', 0, 11, font(800, 28), '#24060f', 'center', 2); g.restore();
    g.fillStyle = `rgba(0,0,0,${.6 * (1 - sy)})`; rr(g, bx, 0, w, h, 40); g.fill();
  } else {
    g.scale(1, -sy);
    rr(g, bx, -h, w, h, 40); g.fillStyle = '#2a2f45'; g.fill();
    rr(g, bx + 18, -h + 18, w - 36, h - 36, 28); g.fillStyle = '#1b1e2c'; g.fill();
    g.strokeStyle = 'rgba(255,255,255,0.08)'; g.lineWidth = 1.5; for (let k = 0; k < 40; k++) { g.beginPath(); g.moveTo(bx + 40 + k * 16, -h + 60); g.lineTo(bx + 40 + k * 16, -60); g.stroke(); }
    [[C.cyan, 'LONDON'], [C.amber, 'PRAHA'], [C.pink, 'NICE']].forEach(([c, n], i) => { g.save(); g.translate(bx + 170 + i * 190, -h / 2); g.rotate((i - 1) * .12); rr(g, -80, -110, 160, 220, 8); g.fillStyle = '#e9e4d8'; g.fill(); g.fillStyle = lingrad(g, 0, -100, 0, 60, [[0, hexA(c, .9)], [1, '#0b1020']]); g.fillRect(-70, -100, 140, 160); text(g, n, 0, 92, font(700, 18, 'JetBrains Mono'), '#222', 'center', 2); g.restore(); });
    g.fillStyle = `rgba(0,0,0,${.5 * (1 + sy)})`; rr(g, bx, -h, w, h, 40); g.fill();
  }
  g.restore();
  // hinge highlight
  g.fillStyle = '#11131c'; g.fillRect(bx + 40, hy - 6, w - 80, 12);
  g.restore();
}
function scSuitcase(t0, v) { return (g, t) => drawSuitcase(g, t, t0, v); }

// ---------------- flight over clouds -> bird ----------------
function drawSky(g, t, rise, v) {
  g.fillStyle = lingrad(g, 0, 0, 0, H, [[0, '#02030a'], [.45, v ? '#0a1230' : '#0c1636'], [.7, v ? '#2a2550' : '#3a2c5c'], [1, '#120f22']]); g.fillRect(0, 0, W, H);
  g.save(); g.globalAlpha = .6 + rise * .4; stars(g, 909, 220, 0, 0, W, 1000, .7); g.restore();
  radial(g, 860, 560 + rise * 120, 300, '#cdd8ff', .12); g.fillStyle = '#eef2ff'; g.beginPath(); g.arc(860, 560 + rise * 120, 38, 0, 7); g.fill();
  const hz = lerp(1100, 1480, rise);
  radial(g, 540, hz, 900, '#7a5aa8', .25);
  const speeds = [60, 140, 300], dy = [-40, 120, 320], rf = [140, 260, 460];
  ART.cloud.forEach((c, i) => { const y = hz + dy[i] + rise * rf[i] - c.height * .5, x = -((t * speeds[i]) % 2160); g.globalAlpha = .9; g.drawImage(c, x, y); g.drawImage(c, x + 2160, y); });
  g.globalAlpha = 1;
  return hz;
}
function scFlight(t0, morphT, flockT, t1, v) {
  return (g, t) => {
    const rise = eIOC(inv(t0, t1 + 2, t));
    drawSky(g, t, rise, v);
    const pu = inv(t0, morphT + .3, t), px = lerp(v ? 260 : 120, 560, eOC(pu)), py = 900 + Math.sin(t * 1.4) * 12 - rise * 60;
    const m = inv(morphT - .05, morphT + .45, t);
    // contrail
    if (m < 1) { g.fillStyle = lingrad(g, px - 520, 0, px - 40, 0, [[0, 'rgba(220,230,255,0)'], [1, `rgba(220,230,255,${.28 * (1 - m)})`]]); g.fillRect(px - 520, py + 8, 480, 8); }
    if (m < 1) {
      g.save(); g.translate(px, py); g.rotate(-.04); const s = .95 * (1 - .5 * eIC(m)); g.scale(s, s); g.globalAlpha = 1 - eIC(m);
      g.drawImage(ART.plane, -350, -130);
      if ((t * 1.2) % 1 < .1) glowDot(g, -330, -100, 40, '#ffffff', 1);
      glowDot(g, 0, 70, 22, (t * 2) % 1 < .5 ? C.red : C.green, .9);
      g.restore();
    }
    if (m > 0 && m < 1) { glowDot(g, px, py, 260 * Math.sin(Math.PI * m), '#ffffff', .9); }
    if (m > 0) {
      // feathers
      for (let i = 0; i < 26; i++) { const a = t - morphT; if (a < 0 || a > 2) continue; const ang = hash(i) * 6.28, d = a * (80 + 200 * hash(i + 3)); g.fillStyle = `rgba(255,255,255,${.6 * (1 - a / 2)})`; g.beginPath(); g.ellipse(px + Math.cos(ang) * d, py + Math.sin(ang) * d + a * a * 40, 7, 2.5, ang + a * 3, 0, 7); g.fill(); }
      const bs = 2.4 * eOB(m), bx = px + (t - morphT) * 60;
      bird(g, bx, py - (t - morphT) * 30, bs, t * 9, '#06070c', 1);
      g.save(); g.globalCompositeOperation = 'lighter'; glowDot(g, bx, py, 90, '#9fb8ff', .25); g.restore();
      // flock
      for (let i = 0; i < 8; i++) {
        const ta = flockT + i * .12, k = eOC(inv(ta, ta + 1.1, t)); if (k <= 0) continue;
        const side = i % 2 ? 1 : -1, row = (i >> 1) + 1;
        const tx = bx - row * 120, ty = py - (t - morphT) * 30 + side * row * 70;
        const sx = side < 0 ? -200 : 1280, sy2 = side < 0 ? 400 : 1500;
        bird(g, lerp(sx, tx, k), lerp(sy2, ty, k), (1.1 + .3 * hash(i)) * (.6 + .4 * k), t * 9 + i * 1.3, '#06070c', 1);
      }
    }
  };
}

// ---------------- birds return home ----------------
function scHome(t0, domT, final) {
  return (g, t) => {
    const L = ART.land, [hx, hy] = L.house;
    const lt = t - t0;
    let z = final ? lerp(1.55, 1.0, eIOC(inv(t0 + 2.2, t0 + 9.5, t))) : lerp(1.32, 1.22, inv(t0, t0 + 6, t));
    const fy = hy - 140;
    const lay = (img, f) => { g.save(); g.translate(540, fy); g.scale(1 + (z - 1) * f, 1 + (z - 1) * f); g.translate(-540, -fy); g.drawImage(img, 0, 0); g.restore(); };
    lay(L.sky, .3); lay(L.h1, .6); lay(L.h2, .8);
    g.save(); g.translate(540, fy); g.scale(z, z); g.translate(-540, -fy);
    g.drawImage(L.near, 0, 0);
    const fadeOut = final ? 1 - sstep(151.2, 152.8, t) * .85 : 1;
    houseWindows(g, hx, hy, (.85 + .15 * Math.sin(t * 2.3)) * fadeOut, .7 + .3 * noise1(t * 3));
    for (let i = 0; i < 6; i++) { const a = ((t * .35 + i / 6) % 1); g.fillStyle = `rgba(200,210,230,${.045 * Math.sin(Math.PI * a)})`; g.beginPath(); g.arc(hx + 53 + a * 40 + Math.sin(a * 6 + i) * 10, hy - 230 - a * 200, 16 + a * 40, 0, 7); g.fill(); }
    g.restore();
    // birds flying to the house
    const target = [540 + (hx - 540) * z, fy + (hy - 250 - fy) * z];
    for (let i = 0; i < 9; i++) {
      const ta = t0 - .2 + i * .16, u = inv(ta, ta + 3.6, t); if (u <= 0 || u >= 1) continue;
      const e = eIOC(u), side = i % 2 ? 1 : -1;
      const p0 = [540 + side * (380 + 120 * hash(i)), 1700 + 200 * hash(i + 1)], p1 = [540 + side * (280 + 80 * hash(i + 2)), 900 - 120 * hash(i + 4)];
      const x = (1 - e) * (1 - e) * p0[0] + 2 * (1 - e) * e * p1[0] + e * e * (target[0] + side * 30 * (1 - e));
      const y = (1 - e) * (1 - e) * p0[1] + 2 * (1 - e) * e * p1[1] + e * e * target[1];
      const s = lerp(3.4, .22, Math.pow(e, .6));
      g.save(); g.translate(x, y); if (side < 0) g.scale(-1, 1); bird(g, 0, 0, s, t * 10 + i, '#05060b', clamp((1 - u) * 5)); g.restore();
    }
    // ДОМ
    const dk = eOC(inv(domT, domT + 1.4, t)) * (final ? 1 - sstep(150.6, 151.8, t) : 1 - sstep(72.6, 73.5, t));
    if (dk > 0) { g.globalAlpha = dk; glowText(g, 'ДОМ', 540, 900 - 30 * dk, font(300, 150, 'Inter Display'), '#fff3df', hexA(C.warm, .9), 50, 'center', lerp(80, 50, dk)); g.globalAlpha = 1; }
    if (final) {
      const ek = sstep(151.4, 152.3, t) * (1 - sstep(153.1, 153.6, t));
      g.fillStyle = `rgba(0,0,0,${.85 * sstep(151.0, 152.0, t)})`; g.fillRect(0, 0, W, H);
      if (ek > 0) { g.globalAlpha = ek; text(g, 'MORGENSHTERN', 540, 940, font(500, 30, 'JetBrains Mono'), 'rgba(255,255,255,0.75)', 'center', 14); glowText(g, 'ДОМ', 540, 1040, font(800, 76, 'Inter Display'), C.white, hexA(C.warm, .7), 30, 'center', 34); g.globalAlpha = 1; }
    }
  };
}

// ---------------- instrumental: flight tracker ----------------
function scTracker(g, t) {
  const { x, y, w, h } = CARD;
  card(g, x, y, w, h, { accent: C.cyan, title: 'РЕЙС DM 0153', right: 'в полёте', label: 'Рейсы' });
  const mx = x + 40, my = y + 110, mw = w - 80, mh = 430;
  g.save(); rr(g, mx, my, mw, mh, 26); g.clip(); g.fillStyle = '#070b16'; g.fillRect(mx, my, mw, mh);
  const pan = inv(73.4, 80, t);
  const proj = d3.geoEquirectangular().scale(200).center([lerp(40, 75, pan), 22]).translate([mx + mw / 2, my + mh / 2]);
  const path = d3.geoPath(proj, g);
  g.beginPath(); path(d3.geoGraticule().step([15, 15])()); g.strokeStyle = 'rgba(80,140,255,0.08)'; g.lineWidth = 1; g.stroke();
  g.beginPath(); path(WORLD.land110); g.fillStyle = '#121c33'; g.fill(); g.strokeStyle = 'rgba(120,180,255,0.3)'; g.stroke();
  const a = CITY.nice, b = CITY.bali, ip = d3.geoInterpolate(a, b), u = lerp(.08, .62, inv(73.4, 80, t));
  g.setLineDash([8, 10]); g.beginPath(); for (let i = 0; i <= 60; i++) { const p = proj(ip(i / 60)); i ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1]); } g.strokeStyle = 'rgba(255,255,255,0.35)'; g.lineWidth = 2; g.stroke(); g.setLineDash([]);
  g.beginPath(); for (let i = 0; i <= 60 * u; i++) { const p = proj(ip(i / 60)); i ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1]); } g.strokeStyle = C.cyan; g.lineWidth = 4; g.stroke();
  const pp = proj(ip(u)), pn = proj(ip(u + .01)), ang = Math.atan2(pn[1] - pp[1], pn[0] - pp[0]);
  glowDot(g, pp[0], pp[1], 50, C.cyan, .8);
  g.save(); g.translate(pp[0], pp[1]); g.rotate(ang); g.fillStyle = '#fff'; g.beginPath(); g.moveTo(18, 0); g.lineTo(-10, -14); g.lineTo(-4, 0); g.lineTo(-10, 14); g.closePath(); g.fill(); g.restore();
  for (const c of [a, b]) { const p = proj(c); g.fillStyle = '#fff'; g.beginPath(); g.arc(p[0], p[1], 6, 0, 7); g.fill(); }
  g.restore();
  const el = 13 * 3600 + 42 * 60 + (t - 73.4) * 37;
  const stats = [['ВЫСОТА', `${(11278 + Math.round(Math.sin(t * 2) * 6)).toLocaleString('ru-RU')} м`], ['СКОРОСТЬ', `${894 + Math.round(Math.sin(t * 1.3) * 4)} км/ч`], ['В ПУТИ', [el / 3600 | 0, (el / 60 | 0) % 60, el % 60 | 0].map(v => String(v).padStart(2, '0')).join(':')], ['ДО ДОМА', '—']];
  stats.forEach((s, i) => {
    const k = eOC(inv(73.6 + i * BEAT, 74.1 + i * BEAT, t)); g.save(); g.globalAlpha *= k;
    const bx = x + 40 + (i % 2) * 430, by = y + 570 + (i >> 1) * 140;
    rr(g, bx, by, 410, 120, 22); g.fillStyle = 'rgba(255,255,255,0.04)'; g.fill();
    text(g, s[0], bx + 28, by + 44, font(600, 20, 'JetBrains Mono'), 'rgba(255,255,255,0.45)', 'left', 3);
    text(g, s[1], bx + 28, by + 96, font(700, 40, 'JetBrains Mono'), i === 3 ? C.cyan : C.white, 'left');
    g.restore();
  });
}

// ---------------- instrumental: memories gallery ----------------
const galleryTiles = lazy(() => {
  const names = ['ЛОНДОН', 'ПРАГА', 'НИЦЦА', 'ДУБАЙ', 'СТАМБУЛ', 'БАЛИ', 'ТБИЛИСИ', 'ЕРЕВАН', 'БЕЛГРАД', 'ЛИССАБОН', 'ДОМ', 'БАНГКОК', 'МИЛАН', 'ВЕНА', 'БЕРЛИН', 'ПАРИЖ', 'ЦЮРИХ', 'РИМ'];
  const cols = [C.cyan, C.amber, C.pink, C.violet, C.teal, C.blue, C.green, C.red];
  return names.map((n, i) => {
    const c = mk(250, 250), g = cx2(c), r = rng(i * 13 + 1);
    if (n === 'ДОМ') { g.setLineDash([10, 8]); g.strokeStyle = hexA(C.pink, .8); g.lineWidth = 3; rr(g, 3, 3, 244, 244, 20); g.stroke(); text(g, 'нет фото', 125, 135, font(500, 22, 'JetBrains Mono'), 'rgba(255,255,255,0.4)', 'center', 1); }
    else {
      g.save(); rr(g, 0, 0, 250, 250, 20); g.clip();
      const col = cols[i % cols.length];
      g.fillStyle = lingrad(g, 0, 0, 0, 250, [[0, '#060812'], [.7, hexA(col, .55)], [1, '#05060a']]); g.fillRect(0, 0, 250, 250);
      let xx = 0; while (xx < 250) { const bw = 12 + r() * 30, bh = 30 + r() * 110; g.fillStyle = '#05070d'; g.fillRect(xx, 200 - bh, bw, bh + 60); for (let k = 0; k < 8; k++) { g.fillStyle = hexA(C.warm, r() * .8); g.fillRect(xx + 3 + r() * (bw - 6), 200 - bh + r() * bh, 2, 2); } xx += bw + 2; }
      g.fillStyle = 'rgba(255,255,255,0.8)'; g.beginPath(); g.arc(40 + r() * 170, 40 + r() * 50, 6 + r() * 8, 0, 7); g.fill();
      g.restore();
    }
    text(g, n, 16, 236, font(700, 18, 'JetBrains Mono'), 'rgba(255,255,255,0.85)', 'left', 2);
    return c;
  });
});
function scGallery(g, t) {
  const { x, y, w, h } = CARD;
  card(g, x, y, w, h, { accent: C.pink, title: 'ВОСПОМИНАНИЯ', right: '47 городов', label: 'Фото' });
  const T = galleryTiles(), scroll = eIOC(inv(80.4, 85.8, t)) * 690;
  g.save(); rr(g, x + 20, y + 100, w - 40, h - 130, 26); g.clip();
  T.forEach((c, i) => {
    const col = i % 3, row = i / 3 | 0, tx = x + 50 + col * 280, ty = y + 120 + row * 280 - scroll;
    if (ty > y + h || ty < y - 260) return;
    const ta = 79.9 + i * .07, k = eOC(inv(ta, ta + .5, t)); g.save(); g.globalAlpha *= k; g.translate(tx + 125, ty + 125); g.scale(lerp(.85, 1, k), lerp(.85, 1, k));
    if (i === 10) { const p = .5 + .5 * Math.sin(t * 5); g.shadowColor = C.pink; g.shadowBlur = 30 * p; }
    g.drawImage(c, -125, -125); g.restore();
  });
  g.restore();
  g.fillStyle = lingrad(g, 0, y + h - 140, 0, y + h - 20, [[0, 'rgba(15,17,23,0)'], [1, 'rgba(15,17,23,0.95)']]); g.fillRect(x + 20, y + h - 140, w - 40, 120);
}

// ---------------- verse 2: maps / pin ----------------
function scMap(g, t) {
  const { x, y, w, h } = CARD;
  card(g, x, y, w, h, { accent: C.green, title: 'МЕСТО ЖИТЕЛЬСТВА', right: 'поиск', label: 'Карты' });
  const mx = x + 50, my = y + 110, mw = 820, mh = 470;
  g.save(); rr(g, mx, my, mw, mh, 26); g.clip(); const pan = (t - 86.3) * 6;
  g.drawImage(ART.street, -pan * .5, -pan * .3, mw + 40, mh + 30, mx, my, mw + 40, mh + 30);
  const px = mx + mw / 2, py = my + mh / 2 + 30, drop = eOB(inv(88.94, 89.4, t));
  if (t > 88.94) {
    for (let k = 0; k < 3; k++) { const a = ((t - 89.3) * .7 + k / 3) % 1; if (t < 89.3) break; g.strokeStyle = hexA(C.green, .5 * (1 - a)); g.lineWidth = 3; g.beginPath(); g.ellipse(px, py, 30 + a * 160, (30 + a * 160) * .45, 0, 0, 7); g.stroke(); }
    g.fillStyle = 'rgba(0,0,0,0.4)'; g.beginPath(); g.ellipse(px, py, 22 * drop, 9 * drop, 0, 0, 7); g.fill();
    g.save(); g.translate(px, py - (1 - drop) * 300); g.shadowColor = C.green; g.shadowBlur = 30; g.fillStyle = C.green;
    g.beginPath(); g.moveTo(0, 0); g.bezierCurveTo(-10, -20, -38, -40, -38, -70); g.arc(0, -70, 38, Math.PI, 0); g.bezierCurveTo(38, -40, 10, -20, 0, 0); g.fill();
    g.fillStyle = '#062016'; g.beginPath(); g.moveTo(-14, -66); g.lineTo(0, -82); g.lineTo(14, -66); g.lineTo(14, -54); g.lineTo(-14, -54); g.fill(); g.restore();
  }
  g.restore();
  // search bar
  rr(g, mx + 24, my + 22, 420, 64, 32); g.fillStyle = 'rgba(10,14,12,0.85)'; g.fill(); g.strokeStyle = 'rgba(255,255,255,0.08)'; g.lineWidth = 2; g.stroke();
  const q = 'дом'.slice(0, Math.floor(inv(86.5, 87.4, t) * 3 + .001));
  text(g, '⌕', mx + 56, my + 66, font(600, 30), 'rgba(255,255,255,0.5)', 'center');
  text(g, q + ((t * 2) % 1 < .5 ? '|' : ''), mx + 84, my + 64, font(500, 28), C.white, 'left');
  if (t > 87.6) text(g, 'ничего не найдено', mx + 430, my + 64, font(500, 20, 'JetBrains Mono'), 'rgba(255,255,255,0.4)', 'right', 1);
  // belonging meter
  const pct = 4 * eOC(inv(89.58, 92.3, t));
  text(g, 'СТАТЬ СВОИМ', x + 54, y + 660, font(600, 22, 'JetBrains Mono'), 'rgba(255,255,255,0.5)', 'left', 3);
  text(g, `${pct.toFixed(0)}%`, x + w - 54, y + 680, font(800, 72, 'Inter Display'), C.green, 'right');
  rr(g, x + 54, y + 730, w - 108, 14, 7); g.fillStyle = 'rgba(255,255,255,0.08)'; g.fill();
  rr(g, x + 54, y + 730, (w - 108) * pct / 100 + 6, 14, 7); g.fillStyle = C.green; g.fill();
  text(g, 'чуть-чуть', x + 54, y + 800, font(500, 22, 'JetBrains Mono'), hexA(C.green, sstep(91.4, 91.9, t) * .8), 'left', 2);
}

// ---------------- verse 2: ban ----------------
function scBan(g, t) {
  let sh = t > 95.26 ? Math.exp(-(t - 95.26) * 10) * 16 : 0;
  g.translate((hash(Math.floor(t * 60)) - .5) * sh, (hash(Math.floor(t * 60) + 3) - .5) * sh);
  const { x, y, w, h } = CARD;
  card(g, x, y, w, h, { accent: C.red, title: 'СТАТУС ВЪЕЗДА', right: 'проверка', label: 'Документы', glow: 1 + 2 * Math.exp(-Math.max(0, t - 95.26) * 4) * (t > 95.26) });
  const ik = eOB(inv(93.36, 93.8, t)), cx = 540, cy = y + 270;
  g.save(); g.translate(cx, cy); g.scale(ik, ik); g.shadowColor = C.red; g.shadowBlur = 40; g.strokeStyle = C.red; g.lineWidth = 16;
  g.beginPath(); g.arc(0, 0, 110, 0, 7); g.stroke(); g.beginPath(); g.moveTo(-78, 78); g.lineTo(78, -78); g.stroke(); g.restore();
  const rows = [['Виза', 94.44], ['Вид на жительство', 94.9], ['Въезд', 95.26]];
  rows.forEach(([n, ts], i) => {
    const ry = y + 500 + i * 100;
    g.strokeStyle = 'rgba(255,255,255,0.07)'; g.lineWidth = 2; g.beginPath(); g.moveTo(x + 50, ry + 34); g.lineTo(x + w - 50, ry + 34); g.stroke();
    text(g, n, x + 54, ry, font(600, 36), C.white, 'left');
    const den = t >= ts, k = eOB(inv(ts, ts + .25, t));
    const lbl = den ? 'отказ' : 'на рассмотрении', fw = den ? 120 : 250;
    g.save(); g.translate(x + w - 54 - fw / 2, ry - 12); if (den) g.scale(k, k);
    rr(g, -fw / 2, -24, fw, 48, 24); g.fillStyle = den ? hexA(C.red, .9) : 'rgba(255,255,255,0.08)'; g.fill();
    text(g, lbl, 0, 9, font(600, 24), den ? '#fff' : 'rgba(255,255,255,0.5)', 'center'); g.restore();
  });
  if (t > 95.26) {
    const k = inv(95.26, 95.38, t); g.save(); g.translate(540, y + 470); g.rotate(-.2); g.scale(lerp(2.2, 1.45, eOC(k)), lerp(2.2, 1.45, eOC(k))); g.globalAlpha = clamp(k * 1.5) * .95;
    g.drawImage(ART.ban, -150, -150); g.restore();
    g.fillStyle = `rgba(255,60,80,${.25 * Math.exp(-(t - 95.26) * 6)})`; g.fillRect(-50, -50, W + 100, H + 100);
  }
}

// ---------------- verse 2: boarding pass, back on the road ----------------
function scTicket(g, t) {
  const { x, y, w, h } = CARD;
  card(g, x, y, w, h, { accent: C.cyan, title: 'ПОСАДОЧНЫЙ ТАЛОН', right: 'снова', label: 'Билеты' });
  const slotY = y + 130; g.fillStyle = '#05060a'; rr(g, x + 60, slotY - 8, w - 120, 16, 8); g.fill();
  const pr = eOC(inv(96.4, 97.6, t)), th = 520, ty = slotY - th + th * pr;
  g.save(); g.beginPath(); g.rect(x, slotY, w, h); g.clip();
  g.save(); g.translate(0, ty);
  rr(g, x + 80, 0, w - 160, th, 22); g.fillStyle = '#e9eef6'; g.fill();
  g.fillStyle = C.cyan; g.fillRect(x + 80, 0, w - 160, 8);
  text(g, 'ОТКУДА', x + 120, 70, font(600, 18, 'JetBrains Mono'), '#5a6a80', 'left', 3); text(g, 'КУДА', x + w - 120, 70, font(600, 18, 'JetBrains Mono'), '#5a6a80', 'right', 3);
  text(g, 'NCE', x + 120, 150, font(800, 84, 'Inter Display'), '#0b1a2c', 'left', 2);
  text(g, (t * 6 % 1 < .5 && t < 98.9) ? '???' : '— — —', x + w - 120, 150, font(800, 84, 'Inter Display'), '#0b1a2c', 'right', 2);
  text(g, '✈', 540, 140, font(700, 50), C.cyan, 'center');
  const f = [['РЕЙС', 'DM 0153'], ['ВЫХОД', '23'], ['МЕСТО', '14A'], ['ПОСАДКА', '23:59']];
  f.forEach((q, i) => { const fx = x + 120 + i * 175; text(g, q[0], fx, 230, font(600, 16, 'JetBrains Mono'), '#5a6a80', 'left', 3); text(g, q[1], fx, 272, font(700, 32), '#0b1a2c', 'left'); });
  g.setLineDash([10, 10]); g.strokeStyle = '#a0abbc'; g.lineWidth = 2; g.beginPath(); g.moveTo(x + 100, 320); g.lineTo(x + w - 100, 320); g.stroke(); g.setLineDash([]);
  const r = rng(77); let bx = x + 130; while (bx < x + w - 130) { const bw = 2 + r() * 6 | 0; g.fillStyle = '#0b1a2c'; g.fillRect(bx, 360, bw, 120); bx += bw + 2 + r() * 5; }
  g.restore(); g.restore();
  // dashed route + plane leaving
  const ry = y + h - 100, rk = inv(98.94, 100.2, t);
  g.setLineDash([12, 12]); g.strokeStyle = 'rgba(255,255,255,0.25)'; g.lineWidth = 3; g.beginPath(); g.moveTo(x + 60, ry); g.lineTo(x + w - 60, ry); g.stroke(); g.setLineDash([]);
  const pxx = lerp(x + 60, x + w + 120, eIC(rk));
  g.strokeStyle = C.cyan; g.lineWidth = 4; g.beginPath(); g.moveTo(x + 60, ry); g.lineTo(Math.min(pxx, x + w - 60), ry); g.stroke();
  g.save(); g.translate(pxx, ry); g.fillStyle = '#fff'; g.beginPath(); g.moveTo(22, 0); g.lineTo(-12, -18); g.lineTo(-5, 0); g.lineTo(-12, 18); g.closePath(); g.fill(); g.restore();
  glowDot(g, pxx, ry, 60, C.cyan, .7);
}

// ---------------- verse 2: family photos ----------------
function polaroid(g, x, y, rot, k, fade, seed, fig) {
  g.save(); g.translate(x, y); g.rotate(rot); g.scale(lerp(1.3, 1, k), lerp(1.3, 1, k)); g.globalAlpha *= clamp(k * 1.5);
  g.shadowColor = 'rgba(0,0,0,0.6)'; g.shadowBlur = 40; g.shadowOffsetY = 16; g.fillStyle = '#ece6da'; g.fillRect(-150, -180, 300, 360); g.shadowBlur = 0; g.shadowOffsetY = 0;
  g.fillStyle = lingrad(g, 0, -160, 0, 100, [[0, '#ffcf86'], [.6, '#c46a3a'], [1, '#3a1d18']]); g.fillRect(-130, -160, 260, 260);
  g.save(); g.beginPath(); g.rect(-130, -160, 260, 260); g.clip(); radial(g, 60, -90, 120, '#fff2c8', .6);
  fig.forEach(([fx, fh]) => person(g, fx, 100, fh, Math.PI, '#2a140f', false)); g.restore();
  g.fillStyle = `rgba(30,32,40,${.75 * fade})`; g.fillRect(-130, -160, 260, 260);
  g.restore();
}
function scFamily(g, t) {
  const { x, y, w, h } = CARD;
  card(g, x, y, w, h, { accent: C.amber, title: 'СЕМЬЯ', right: 'последнее фото', label: 'Галерея' });
  const fade = sstep(103.6, 106.8, t);
  polaroid(g, 330, y + 360, -.14, eOC(inv(101.52, 101.95, t)), fade, 1, [[-60, 240], [10, 220], [70, 140]]);
  polaroid(g, 750, y + 340, .12, eOC(inv(102.54, 102.97, t)), fade, 2, [[-40, 230], [40, 230]]);
  polaroid(g, 540, y + 400, .02, eOC(inv(103.0, 103.4, t)), fade * .8, 3, [[-50, 150], [0, 250], [50, 130]]);
  const days = Math.round(2190 * eIOC(inv(104.2, 106.4, t)));
  const k = eOC(inv(103.64, 104.1, t)); g.save(); g.globalAlpha *= k;
  text(g, 'НЕ ВИДЕЛИСЬ', x + 54, y + 690, font(600, 22, 'JetBrains Mono'), 'rgba(255,255,255,0.5)', 'left', 3);
  text(g, `${days.toLocaleString('ru-RU')}`, x + 54, y + 800, font(800, 110, 'Inter Display'), C.amber, 'left');
  text(g, 'дней', x + w - 54, y + 800, font(500, 40), 'rgba(255,255,255,0.6)', 'right');
  g.restore();
}

// ---------------- verse 2: seat map -> no place on earth ----------------
function scSeats(g, t) {
  const { x, y, w, h } = CARD, sw = t >= 110.92, sk = eOC(inv(110.92, 111.3, t));
  card(g, x, y, w, h, { accent: sw ? C.red : C.blue, title: 'ВЫБОР МЕСТА', right: 'DM 0153', label: 'Места' });
  // tabs
  rr(g, x + 220, y + 110, 480, 66, 33); g.fillStyle = 'rgba(255,255,255,0.06)'; g.fill();
  rr(g, lerp(x + 226, x + 464, sk), y + 116, 230, 54, 27); g.fillStyle = sw ? hexA(C.red, .85) : hexA(C.blue, .85); g.fill();
  text(g, 'НЕБО', x + 341, y + 153, font(700, 24, 'JetBrains Mono'), C.white, 'center', 3); text(g, 'ЗЕМЛЯ', x + 579, y + 153, font(700, 24, 'JetBrains Mono'), C.white, 'center', 3);
  g.save(); rr(g, x + 40, y + 200, w - 80, h - 240, 26); g.clip();
  const scroll = (t - 107.3) * 50, cx = 540;
  if (!sw || sk < 1) {
    g.save(); g.globalAlpha *= 1 - sk;
    g.strokeStyle = 'rgba(150,180,255,0.25)'; g.lineWidth = 4; rr(g, cx - 250, y + 120 - scroll, 500, 1600, 240); g.stroke();
    for (let r2 = 0; r2 < 18; r2++) for (let c = 0; c < 6; c++) {
      const sx = cx - 205 + c * 64 + (c > 2 ? 30 : 0), sy = y + 360 + r2 * 74 - scroll; if (sy < y + 180 || sy > y + h) continue;
      const mine = r2 === 4 && c === 0; rr(g, sx, sy, 50, 54, 12);
      g.fillStyle = mine ? C.blue : hash(r2 * 6 + c) < .7 ? 'rgba(255,255,255,0.10)' : 'rgba(255,255,255,0.03)'; g.fill();
      if (mine) { glowDot(g, sx + 25, sy + 27, 80, C.blue, .6); text(g, '14A', sx + 25, sy + 36, font(700, 18, 'JetBrains Mono'), '#fff', 'center'); }
    }
    g.restore();
  }
  if (sk > 0) {
    g.save(); g.globalAlpha *= sk;
    for (let r2 = 0; r2 < 9; r2++) for (let c = 0; c < 10; c++) {
      const sx = x + 80 + c * 78, sy = y + 230 + r2 * 72, ap = eOB(inv(110.95 + (r2 * 10 + c) * .006, 111.3 + (r2 * 10 + c) * .006, t));
      g.save(); g.translate(sx + 27, sy + 27); g.scale(ap, ap); rr(g, -27, -27, 54, 54, 12); g.fillStyle = 'rgba(255,255,255,0.07)'; g.fill();
      g.strokeStyle = hexA(C.red, .7); g.lineWidth = 4; g.beginPath(); g.moveTo(-10, -10); g.lineTo(10, 10); g.moveTo(10, -10); g.lineTo(-10, 10); g.stroke(); g.restore();
    }
    g.fillStyle = 'rgba(15,17,23,0.75)'; rr(g, x + 120, y + 420, w - 240, 220, 30); g.fill();
    const zk = eOB(inv(111.64, 112.0, t));
    text(g, 'СВОБОДНЫХ МЕСТ', 540, y + 490, font(600, 24, 'JetBrains Mono'), 'rgba(255,255,255,0.55)', 'center', 4);
    g.save(); g.translate(540, y + 590); g.scale(zk, zk); glowText(g, '0', 0, 0, font(800, 120, 'Inter Display'), C.red, hexA(C.red, .8), 30); g.restore();
    g.restore();
  }
  g.restore();
}

// ---------------- verse 2: empty globe ----------------
function scGlobeEmpty(g, t) {
  const u = inv(114.1, 118.8, t), R = lerp(430, 250, eIOC(u)), lon = lerp(10, 60, u), lat = 30;
  drawGlobe(g, 540, 1000, R, lon, lat, { acc: C.blue, landA: .2 });
  const list = ['london', 'prague', 'nice', 'istanbul', 'dubai', 'tbilisi', 'yerevan', 'belgrade', 'lisbon'];
  list.forEach((n, i) => {
    const off = 114.3 + i * BEAT * .9, a = 1 - inv(off, off + .25, t); if (a <= 0) return;
    const q = liftPoint(lon, lat, R, 540, 1000, 0, CITY[n]); if (!q[2]) return;
    glowDot(g, q[0], q[1], 26, C.white, a); if (t > off && t < off + .25) glowDot(g, q[0], q[1], 60, C.red, (1 - a));
  });
}

// ---------------- timeline ----------------
function buildTimeline() {
  S(0, 14.9, scIntro, { tin: 0, fin: 'cut', tout: .45, fout: 'blur', acc: C.cyan });
  S(14.55, 23.15, scDom, { tin: .1, fin: 'fade', tout: .3, acc: C.amber });
  S(22.95, 26.75, scGlobe, { tin: .45, fin: 'zoomin', tout: .3, fout: 'zoom', acc: C.cyan });
  S(26.45, 29.95, scAirport, { tin: .3, fin: 'blur', tout: .3, acc: C.blue });
  S(29.65, 34.05, scWindow, { tin: .3, tout: .2, fout: 'zoom', acc: C.warm });
  S(33.85, 37.8, scUnknown, { tin: .05, fin: 'fade', tout: .25, acc: C.violet });
  S(37.55, 42.6, scBoard, { tin: .3, tout: .15, fout: 'fade', acc: C.amber });
  // chorus 1
  S(43.55, 46.15, scCities([43.55, 44.64, 45.16], 0), { tin: 0, fin: 'cut', tout: .12, fout: 'whip', acc: C.cyan, shake: 1, accFn: t => t < 44.64 ? C.cyan : t < 45.16 ? C.amber : C.pink });
  S(46.03, 50.75, scPassport(46.12, [47.0, 47.0 + BEAT, 47.0 + 2 * BEAT, 47.0 + 3 * BEAT, 48.64, 48.64 + BEAT, 48.64 + 2 * BEAT, 48.64 + 3 * BEAT, 48.64 + 4 * BEAT, 48.64 + 5 * BEAT, 48.64 + 6 * BEAT], 0), { tin: .12, fin: 'whip', tout: .2, fout: 'zoom', acc: C.red, shake: 1 });
  S(50.55, 53.6, scEurope(50.68, 53.4, ART.route1, 0), { tin: .2, fin: 'zoomin', tout: .2, fout: 'blur', acc: C.cyan, shake: 1 });
  S(53.4, 57.92, scSuitcase(53.5, 0), { tin: .2, fin: 'blur', tout: .12, fout: 'whip', acc: C.violet, shake: 1 });
  S(57.8, 60.85, scCities([57.82, 58.96, 59.78], 1), { tin: .12, fin: 'whip', tout: .3, fout: 'blur', acc: C.cyan, shake: 1, accFn: t => t < 58.96 ? C.cyan : t < 59.78 ? C.amber : C.pink });
  S(60.6, 68.2, scFlight(60.78, 65.16, 66.0, 68.0, 0), { tin: .3, tout: .5, acc: C.blue });
  S(67.85, 73.9, scHome(68.0, 71.54, false), { tin: .5, tout: .5, acc: C.warm });
  // instrumental
  S(73.5, 80.0, scTracker, { tin: .5, tout: .4, acc: C.cyan });
  S(79.7, 86.5, scGallery, { tin: .4, tout: .4, acc: C.pink });
  // verse 2
  S(86.25, 93.1, scMap, { tin: .4, tout: .35, acc: C.green });
  S(92.95, 96.55, scBan, { tin: .3, tout: .3, acc: C.red });
  S(96.3, 100.4, scTicket, { tin: .3, tout: .4, acc: C.cyan });
  S(100.15, 107.45, scFamily, { tin: .4, tout: .4, acc: C.amber });
  S(107.3, 114.35, scSeats, { tin: .4, tout: .4, acc: C.blue, accFn: t => t < 110.92 ? C.blue : C.red });
  S(114.1, 118.85, scGlobeEmpty, { tin: .4, tout: .5, fout: 'fade', acc: C.blue });
  // chorus 2
  S(118.8, 121.7, scCities([118.8, 119.8, 120.6], 1), { tin: 0, fin: 'cut', tout: .12, fout: 'whip', acc: C.cyan, shake: 1, accFn: t => t < 119.8 ? C.cyan : t < 120.6 ? C.amber : C.pink });
  S(121.58, 126.0, scPassport(121.64, [122.22, 122.22 + BEAT, 122.22 + 2 * BEAT, 122.22 + 3 * BEAT, 123.88, 123.88 + BEAT, 123.88 + 2 * BEAT, 123.88 + 3 * BEAT, 123.88 + 4 * BEAT, 123.88 + 5 * BEAT, 123.88 + 6 * BEAT, 123.88 + 7 * BEAT], 1), { tin: .12, fin: 'whip', tout: .2, fout: 'zoom', acc: C.red, shake: 1 });
  S(125.8, 128.95, scEurope(125.88, 128.7, ART.route2, 1), { tin: .2, fin: 'zoomin', tout: .2, fout: 'blur', acc: C.cyan, shake: 1 });
  S(128.75, 133.05, scSuitcase(128.84, 1), { tin: .2, fin: 'blur', tout: .12, fout: 'whip', acc: C.violet, shake: 1 });
  S(132.94, 136.1, scCities([132.96, 134.14, 135.02], 0), { tin: .12, fin: 'whip', tout: .3, fout: 'blur', acc: C.cyan, shake: 1, accFn: t => t < 134.14 ? C.cyan : t < 135.02 ? C.amber : C.pink });
  S(135.85, 143.4, scFlight(136.02, 140.36, 141.5, 143.2, 1), { tin: .3, tout: .5, acc: C.blue });
  S(143.05, DUR, scHome(143.18, 146.74, true), { tin: .5, fin: 'blur', tout: 0, acc: C.warm });
}
