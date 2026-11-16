'use strict';
// ======== pre-rendered illustrations (built once at init) ========
const ART = {};

function stars(g, seed, n, x0, y0, w, h, amax = .8) {
  const r = rng(seed);
  for (let i = 0; i < n; i++) {
    const x = x0 + r() * w, y = y0 + Math.pow(r(), 1.4) * h, s = r();
    g.fillStyle = `rgba(255,255,255,${(.15 + s * amax) * (1 - (y - y0) / h * .6)})`;
    const sz = s > .96 ? 2.6 : s > .8 ? 1.8 : 1.2; g.fillRect(x, y, sz, sz);
  }
}
function litWindows(g, x, y, w, h, seed, dens = .35, col = '#ffcf86', cw = 6, chh = 8, gx = 12, gy = 16) {
  const r = rng(seed);
  for (let yy = y + 8; yy < y + h - chh; yy += gy) for (let xx = x + 5; xx < x + w - cw - 2; xx += gx) {
    if (r() < dens) { g.fillStyle = hexA(col, .35 + r() * .6); g.fillRect(xx, yy, cw, chh); }
  }
}
function skyGrad(g, w, h, stops) { g.fillStyle = lingrad(g, 0, 0, 0, h, stops); g.fillRect(0, 0, w, h); }

// reflection: mirror a layer below a horizon line with ripple strips
function reflect(dst, src, horizon, alpha, seed, squash = .85) {
  const r = rng(seed), g = dst;
  for (let y = 0; y < H - horizon; y += 3) {
    const sy = horizon - y / squash; if (sy < 0) break;
    const dx = Math.sin(y * .09 + r() * 2) * (2 + y * .02);
    g.globalAlpha = alpha * (1 - y / (H - horizon)) * (.6 + r() * .4);
    g.drawImage(src, 0, sy, W, 3 / squash, dx, horizon + y, W, 3);
  }
  g.globalAlpha = 1;
}

// ---- generic building silhouette ----
function bldg(g, x, base, w, h, col, seed, wcol, dens) {
  g.fillStyle = col; g.fillRect(x, base - h, w, h);
  if (wcol) litWindows(g, x, base - h, w, h, seed, dens, wcol);
}

// ---------------- LONDON ----------------
function paintLondon() {
  const HZ = 1250, L = {};
  // sky
  let c = mk(W, H), g = cx2(c);
  skyGrad(g, W, H, [[0, '#03060f'], [.45, '#0a1630'], [.66, '#1b2a55'], [1, '#05070d']]);
  stars(g, 11, 160, 0, 0, W, 900, .5);
  radial(g, 940, 470, 260, '#9fb8ff', .12); // moon halo
  g.fillStyle = '#e8eeff'; g.beginPath(); g.arc(940, 470, 40, 0, 7); g.fill();
  radial(g, 540, HZ, 700, '#3b57a8', .35);
  L.sky = c;
  // far: shard + skyline
  c = mk(W, H); g = cx2(c);
  const r = rng(5); let x = -10;
  while (x < W) { const w = 30 + r() * 60, h = 60 + r() * 160; bldg(g, x, HZ, w, h, '#0c1328', 77 + x | 0, '#7fa2ff', .12); x += w + 2; }
  g.fillStyle = '#0e1630'; g.beginPath(); g.moveTo(880, HZ); g.lineTo(950, 520); g.lineTo(1020, HZ); g.fill();
  litWindows(g, 900, 700, 100, 540, 9, .12, '#9fc0ff', 4, 4, 9, 10);
  glowDot(g, 950, 520, 30, C.white, .9);
  L.far = c;
  // mid: london eye + westminster + big ben
  c = mk(W, H); g = cx2(c);
  const ex = 250, ey = 930, er = 300;
  g.strokeStyle = hexA(C.cyan, .35); g.lineWidth = 2;
  for (let i = 0; i < 32; i++) { const a = i / 32 * Math.PI * 2; g.beginPath(); g.moveTo(ex, ey); g.lineTo(ex + Math.cos(a) * er, ey + Math.sin(a) * er); g.stroke(); }
  g.save(); g.shadowColor = C.cyan; g.shadowBlur = 25; g.strokeStyle = hexA(C.cyan, .95); g.lineWidth = 6;
  g.beginPath(); g.arc(ex, ey, er, 0, 7); g.stroke(); g.lineWidth = 3; g.beginPath(); g.arc(ex, ey, er - 22, 0, 7); g.stroke(); g.restore();
  for (let i = 0; i < 32; i++) { const a = i / 32 * Math.PI * 2; g.fillStyle = '#bff0ff'; g.beginPath(); g.ellipse(ex + Math.cos(a) * (er + 10), ey + Math.sin(a) * (er + 10), 9, 7, 0, 0, 7); g.fill(); }
  g.strokeStyle = '#0d1530'; g.lineWidth = 10; g.beginPath(); g.moveTo(ex - 130, HZ); g.lineTo(ex, ey); g.lineTo(ex + 130, HZ); g.stroke();
  // westminster palace
  const pc = '#0a0f20';
  g.fillStyle = pc; g.fillRect(-20, HZ - 170, 640, 170);
  for (let px = -10; px < 620; px += 26) { g.beginPath(); g.moveTo(px, HZ - 170); g.lineTo(px + 6, HZ - 205); g.lineTo(px + 12, HZ - 170); g.fill(); }
  litWindows(g, -20, HZ - 160, 640, 150, 21, .55, C.warm, 5, 12, 13, 22);
  g.fillStyle = pc; g.fillRect(40, HZ - 430, 120, 430); // victoria tower
  for (let k = 0; k < 4; k++) { g.beginPath(); g.moveTo(40 + k * 36, HZ - 430); g.lineTo(46 + k * 36, HZ - 480); g.lineTo(52 + k * 36, HZ - 430); g.fill(); }
  litWindows(g, 40, HZ - 420, 120, 400, 33, .4, C.warm, 5, 14, 14, 26);
  // big ben (elizabeth tower), floodlit warm
  const bx = 640, bw = 104;
  const bg = lingrad(g, bx, 0, bx + bw, 0, [[0, '#3a2a12'], [.5, '#8a6a32'], [1, '#2a1e0e']]);
  g.fillStyle = bg; g.fillRect(bx, HZ - 640, bw, 640);
  g.strokeStyle = 'rgba(255,220,150,0.35)'; g.lineWidth = 2;
  for (let k = 1; k < 6; k++) { g.beginPath(); g.moveTo(bx + k * bw / 6, HZ - 630); g.lineTo(bx + k * bw / 6, HZ); g.stroke(); }
  g.fillStyle = bg; g.fillRect(bx - 12, HZ - 790, bw + 24, 150);
  g.save(); g.shadowColor = '#ffd890'; g.shadowBlur = 40; g.fillStyle = '#ffe7b0'; g.beginPath(); g.arc(bx + bw / 2, HZ - 715, 50, 0, 7); g.fill(); g.restore();
  g.strokeStyle = '#3a2a12'; g.lineWidth = 4; g.beginPath(); g.moveTo(bx + bw / 2, HZ - 715); g.lineTo(bx + bw / 2, HZ - 752); g.moveTo(bx + bw / 2, HZ - 715); g.lineTo(bx + bw / 2 + 26, HZ - 712); g.stroke();
  g.fillStyle = '#5a4420'; g.fillRect(bx - 2, HZ - 870, bw + 4, 80);
  g.fillStyle = 'rgba(255,214,140,0.7)'; for (let k = 0; k < 4; k++) g.fillRect(bx + 10 + k * 24, HZ - 860, 12, 56);
  g.fillStyle = '#2a1e0e'; g.beginPath(); g.moveTo(bx - 6, HZ - 870); g.lineTo(bx + bw / 2, HZ - 1060); g.lineTo(bx + bw + 6, HZ - 870); g.fill();
  g.fillRect(bx + bw / 2 - 3, HZ - 1120, 6, 70);
  // bridge
  g.fillStyle = '#0b1226'; g.fillRect(-20, HZ - 20, W + 40, 34);
  g.fillStyle = hexA(C.green, .55); for (let k = 0; k < 14; k++) g.fillRect(k * 80 + 20, HZ - 26, 40, 5);
  L.mid = c;
  // water
  c = mk(W, H); g = cx2(c);
  g.fillStyle = lingrad(g, 0, HZ, 0, H, [[0, '#0b1734'], [1, '#03050b']]); g.fillRect(0, HZ, W, H - HZ);
  const tmp = mk(W, H), tg = cx2(tmp); tg.drawImage(L.far, 0, 0); tg.drawImage(L.mid, 0, 0);
  reflect(g, tmp, HZ + 14, .42, 3);
  L.water = c;
  // near: embankment lamps
  c = mk(W, H); g = cx2(c);
  g.fillStyle = '#05070e'; g.fillRect(0, 1560, W, H - 1560);
  g.fillStyle = '#080c18'; g.fillRect(0, 1540, W, 28);
  for (let k = 0; k < 5; k++) {
    const lx = 60 + k * 240;
    g.fillStyle = '#05070e'; g.fillRect(lx - 5, 1330, 10, 220); g.fillRect(lx - 30, 1335, 60, 8);
    glowDot(g, lx - 26, 1322, 40, C.warm, .9); glowDot(g, lx + 26, 1322, 40, C.warm, .9);
    g.fillStyle = '#fff3d8'; g.beginPath(); g.arc(lx - 26, 1322, 9, 0, 7); g.arc(lx + 26, 1322, 9, 0, 7); g.fill();
  }
  L.near = c; L.hz = HZ;
  return L;
}

// ---------------- PRAGUE ----------------
function spire(g, x, base, w, h, col) { g.fillStyle = col; g.beginPath(); g.moveTo(x - w / 2, base); g.lineTo(x, base - h); g.lineTo(x + w / 2, base); g.fill(); }
function paintPrague() {
  const HZ = 1270, L = {};
  let c = mk(W, H), g = cx2(c);
  skyGrad(g, W, H, [[0, '#07040f'], [.4, '#170c2a'], [.64, '#3a1d44'], [1, '#05040a']]);
  stars(g, 21, 140, 0, 0, W, 900, .5);
  radial(g, 140, 480, 220, '#ffd9a8', .1); g.fillStyle = '#fff1d8'; g.beginPath(); g.arc(140, 480, 34, 0, 7); g.fill();
  radial(g, 540, HZ - 100, 700, '#8a4a5a', .3);
  L.sky = c;
  // far: castle hill + st vitus, floodlit gold
  c = mk(W, H); g = cx2(c);
  g.fillStyle = '#0d0818'; g.beginPath(); g.moveTo(-20, HZ); g.bezierCurveTo(100, 1020, 350, 990, 760, 1060); g.lineTo(760, HZ); g.fill();
  litWindows(g, 20, 1060, 700, 180, 41, .12, C.warm, 4, 4, 11, 12);
  const gold = lingrad(g, 0, 700, 0, 1060, [[0, '#ffd27a'], [1, '#a46a22']]);
  g.fillStyle = gold; g.fillRect(90, 975, 520, 70); // castle
  g.fillStyle = 'rgba(80,40,10,0.7)'; for (let k = 0; k < 26; k++) g.fillRect(100 + k * 20, 990, 8, 14), g.fillRect(100 + k * 20, 1018, 8, 14);
  g.fillStyle = gold; g.fillRect(330, 800, 170, 180); g.fillRect(470, 660, 60, 320);
  spire(g, 360, 800, 44, 170, '#e3ae55'); spire(g, 470, 800, 44, 170, '#e3ae55'); spire(g, 500, 660, 70, 150, '#c9913f');
  g.fillStyle = '#ffeab8'; g.beginPath(); g.arc(415, 870, 26, 0, 7); g.fill();
  g.save(); g.globalCompositeOperation = 'lighter'; radial(g, 420, 870, 380, '#ffb547', .25); g.restore();
  L.far = c;
  // mid: tyn church + old town roofs
  c = mk(W, H); g = cx2(c);
  const mc = '#0a0612';
  let x = -10; const r = rng(17);
  while (x < W + 20) { const w = 50 + r() * 50, h = 90 + r() * 70; g.fillStyle = mc; g.fillRect(x, HZ - h, w, h); g.beginPath(); g.moveTo(x - 4, HZ - h); g.lineTo(x + w / 2, HZ - h - 50); g.lineTo(x + w + 4, HZ - h); g.fill(); litWindows(g, x, HZ - h, w, h, x | 0, .5, C.warm, 6, 9, 14, 20); x += w + 4; }
  for (const tx of [760, 900]) {
    g.fillStyle = mc; g.fillRect(tx, 900, 90, 380);
    g.beginPath(); g.moveTo(tx - 6, 900); g.lineTo(tx + 45, 700); g.lineTo(tx + 96, 900); g.fill();
    for (const sx of [tx + 2, tx + 30, tx + 60, tx + 88]) spire(g, sx, 900, 16, 90, mc);
    for (const sx of [tx + 2, tx + 30, tx + 60, tx + 88, tx + 45]) glowDot(g, sx, sx === tx + 45 ? 700 : 810, 14, '#ffd27a', .9);
    litWindows(g, tx + 10, 940, 70, 300, tx, .3, C.warm, 6, 14, 18, 30);
  }
  g.fillStyle = mc; g.fillRect(780, 1000, 220, 280);
  L.mid = c;
  // water
  c = mk(W, H); g = cx2(c);
  g.fillStyle = lingrad(g, 0, HZ, 0, H, [[0, '#1d1028'], [1, '#040208']]); g.fillRect(0, HZ, W, H - HZ);
  const tmp = mk(W, H), tg = cx2(tmp); tg.drawImage(L.far, 0, 0); tg.drawImage(L.mid, 0, 0);
  reflect(g, tmp, HZ + 6, .45, 8);
  L.water = c;
  // near: charles bridge
  c = mk(W, H); g = cx2(c);
  const by = 1420, bc = '#07040c';
  g.fillStyle = bc; g.fillRect(-20, by, W + 40, 70);
  for (let k = 0; k < 5; k++) { g.beginPath(); g.moveTo(k * 260 - 40, by + 70); g.lineTo(k * 260 - 40, H); g.lineTo(k * 260 + 40, H); g.lineTo(k * 260 + 40, by + 70); g.fill(); }
  g.fillStyle = bc; g.fillRect(0, by + 70, W, 70);
  g.save(); g.globalCompositeOperation = 'destination-out';
  for (let k = 0; k < 4; k++) { g.beginPath(); g.ellipse(k * 260 + 130, by + 140, 90, 70, 0, Math.PI, 0); g.lineTo(k * 260 + 220, by + 141); g.fill(); }
  g.restore();
  for (let k = 0; k < 12; k++) { // statues + lamps
    const sx = 20 + k * 92;
    g.fillStyle = bc;
    if (k % 2) { g.fillRect(sx - 9, by - 70, 18, 70); g.beginPath(); g.arc(sx, by - 82, 12, 0, 7); g.fill(); g.fillRect(sx - 16, by - 64, 32, 14); }
    else { g.fillRect(sx - 3, by - 120, 6, 120); glowDot(g, sx, by - 128, 46, C.amber, .95); g.fillStyle = '#fff0c8'; g.beginPath(); g.arc(sx, by - 128, 8, 0, 7); g.fill(); }
  }
  // old town bridge tower on left
  g.fillStyle = bc; g.fillRect(-20, 1080, 170, 420); g.beginPath(); g.moveTo(-26, 1080); g.lineTo(65, 900); g.lineTo(156, 1080); g.fill();
  spire(g, 0, 1080, 18, 80, bc); spire(g, 130, 1080, 18, 80, bc);
  litWindows(g, 10, 1120, 120, 200, 61, .35, C.amber, 8, 16, 22, 34);
  L.near = c; L.hz = HZ;
  return L;
}

// ---------------- NICE ----------------
function palm(g, x, base, h, lean, col) {
  g.strokeStyle = col; g.lineCap = 'round';
  const tx = x + lean, ty = base - h;
  g.lineWidth = 16; g.beginPath(); g.moveTo(x, base); g.quadraticCurveTo(x + lean * .2, base - h * .5, tx, ty); g.stroke();
  g.lineWidth = 7;
  for (let k = 0; k < 9; k++) {
    const a = -Math.PI / 2 + (k - 4) * .42 + (k > 4 ? .3 : -.3), L = 150 + (k % 3) * 30;
    const ex = tx + Math.cos(a) * L, ey = ty + Math.sin(a) * L * .55 + L * .45;
    const mx = tx + Math.cos(a) * L * .5, my = ty + Math.sin(a) * L * .6 - 20;
    g.beginPath(); g.moveTo(tx, ty); g.quadraticCurveTo(mx, my, ex, ey); g.stroke();
    for (let j = 1; j < 8; j++) { const u = j / 8, px = (1 - u) * (1 - u) * tx + 2 * (1 - u) * u * mx + u * u * ex, py = (1 - u) * (1 - u) * ty + 2 * (1 - u) * u * my + u * u * ey; g.lineWidth = 3; g.beginPath(); g.moveTo(px, py); g.lineTo(px + Math.cos(a + 1.2) * 26 * (1 - u * .5), py + 26); g.moveTo(px, py); g.lineTo(px + Math.cos(a - 1.2) * 26 * (1 - u * .5), py + 22); g.stroke(); }
    g.lineWidth = 7;
  }
}
function paintNice() {
  const HZ = 1020, L = {};
  let c = mk(W, H), g = cx2(c);
  skyGrad(g, W, HZ, [[0, '#020611'], [.55, '#0a1c38'], [1, '#2f3f6a']]);
  stars(g, 31, 180, 0, 0, W, 760, .55);
  radial(g, 200, 480, 300, '#cfe0ff', .13); g.fillStyle = '#f2f6ff'; g.beginPath(); g.arc(200, 480, 48, 0, 7); g.fill();
  radial(g, 760, HZ, 520, '#ff7aa8', .22);
  L.sky = c;
  // far: hills with lights
  c = mk(W, H); g = cx2(c);
  g.fillStyle = '#0a0e1e'; g.beginPath(); g.moveTo(560, HZ + 4); g.bezierCurveTo(700, 900, 820, 780, 1100, 760); g.lineTo(1100, HZ + 4); g.fill();
  g.fillStyle = '#070a16'; g.beginPath(); g.moveTo(760, HZ + 4); g.bezierCurveTo(860, 900, 960, 880, 1100, 870); g.lineTo(1100, HZ + 4); g.fill();
  const r = rng(51);
  for (let i = 0; i < 260; i++) { const x = 600 + r() * 480, y = 780 + r() * 240; const top = x < 820 ? lerp(HZ, 830, (x - 600) / 220) : 780 + (1 - (x - 820) / 260) * 40; if (y > top + 8 && y < HZ) { g.fillStyle = hexA(r() < .8 ? C.warm : '#bfe0ff', .4 + r() * .6); g.fillRect(x, y, 3, 3); } }
  L.far = c;
  // water
  c = mk(W, H); g = cx2(c);
  g.fillStyle = lingrad(g, 0, HZ, 0, H, [[0, '#13284a'], [.4, '#071530'], [1, '#02060e']]); g.fillRect(0, HZ, W, H - HZ);
  L.water = c;
  // near: promenade curve + palms + beach
  c = mk(W, H); g = cx2(c);
  g.fillStyle = '#0c0f19'; g.beginPath(); g.moveTo(-50, H); g.lineTo(-50, 1520); g.bezierCurveTo(300, 1330, 650, 1130, 1100, 1060); g.lineTo(1100, H); g.fill();
  g.fillStyle = '#05070d'; g.beginPath(); g.moveTo(-50, H); g.lineTo(-50, 1600); g.bezierCurveTo(330, 1410, 700, 1190, 1100, 1110); g.lineTo(1100, H); g.fill();
  for (let i = 0; i < 26; i++) { // lamps along promenade
    const u = i / 25, e = Math.pow(u, .7);
    const x = lerp(-40, 1090, e), y = (1 - e) ** 3 * 1520 + 3 * (1 - e) ** 2 * e * 1330 + 3 * (1 - e) * e * e * 1130 + e ** 3 * 1060 - 10;
    const s = lerp(1.6, .35, e);
    g.fillStyle = '#05070d'; g.fillRect(x - 2 * s, y - 70 * s, 4 * s, 70 * s);
    glowDot(g, x, y - 72 * s, 38 * s, C.warm, .9); g.fillStyle = '#fff4dc'; g.beginPath(); g.arc(x, y - 72 * s, 5 * s, 0, 7); g.fill();
  }
  palm(g, 110, H + 20, 760, 60, '#04060b'); palm(g, 1010, H + 20, 640, -70, '#04060b'); palm(g, 880, H + 40, 420, 40, '#04060b');
  L.near = c; L.hz = HZ;
  return L;
}

// ---------------- generic skylines ("не помню, что это за город") ----------------
function paintSkyline(seed, tint, landmark) {
  const c = mk(W, H), g = cx2(c), r = rng(seed), HZ = 1300;
  skyGrad(g, W, H, [[0, '#03050b'], [.5, hexA(tint, .12)], [.68, hexA(tint, .32)], [1, '#020306']]);
  g.fillStyle = 'rgba(0,0,0,0.55)'; g.fillRect(0, 0, W, 300);
  stars(g, seed, 90, 0, 0, W, 900, .4);
  radial(g, 540, HZ, 800, tint, .25);
  let x = -20;
  while (x < W) { const w = 40 + r() * 90, h = 120 + r() * 380; bldg(g, x, HZ, w, h, '#070a12', x * 7 + seed | 0, tint, .22); x += w + 3; }
  g.fillStyle = '#05070d';
  if (landmark === 'needle') { g.fillRect(525, 520, 30, 780); g.beginPath(); g.arc(540, 700, 70, 0, 7); g.fill(); g.fillRect(535, 330, 10, 200); glowDot(g, 540, 330, 26, C.red, 1); litWindows(g, 480, 690, 120, 18, 3, .9, tint, 6, 6, 10, 10); }
  if (landmark === 'spire') { g.beginPath(); g.moveTo(470, HZ); g.lineTo(500, 700); g.lineTo(525, 520); g.lineTo(538, 260); g.lineTo(552, 520); g.lineTo(580, 700); g.lineTo(610, HZ); g.fill(); litWindows(g, 490, 720, 100, 560, 5, .45, tint, 4, 6, 9, 11); glowDot(g, 538, 262, 26, C.white, 1); }
  if (landmark === 'domes') { for (const [dx, rr2] of [[540, 150], [380, 90], [700, 90]]) { g.beginPath(); g.arc(dx, HZ - 220, rr2, Math.PI, 0); g.fill(); g.fillRect(dx - rr2, HZ - 220, rr2 * 2, 220); } for (const mx of [220, 860, 300, 780]) { g.fillRect(mx - 9, 620, 18, 680); spire(g, mx, 620, 22, 90, '#05070d'); glowDot(g, mx, 700, 16, tint, .9); } }
  if (landmark === 'bridge') { g.strokeStyle = '#0a0e18'; g.lineWidth = 6; for (const px of [300, 780]) { g.fillRect(px - 14, 760, 28, 560); } g.beginPath(); g.moveTo(0, 1180); g.quadraticCurveTo(300, 760, 540, 1150); g.quadraticCurveTo(780, 760, 1080, 1180); g.stroke(); for (let i = 0; i < 30; i++) glowDot(g, i * 37, 1190, 12, tint, .8); }
  g.fillStyle = lingrad(g, 0, HZ, 0, H, [[0, '#04060c'], [1, '#010204']]); g.fillRect(0, HZ, W, H - HZ);
  for (let i = 0; i < 160; i++) { g.fillStyle = hexA(tint, r() * .5); g.fillRect(r() * W, HZ + 10 + Math.pow(r(), 2) * 500, 2 + r() * 30, 2); }
  return c;
}

// ---------------- empty apartment (line art) ----------------
function paintApartment() {
  const c = mk(W, H), g = cx2(c);
  const col = 'rgba(255,214,160,', vp = [540, 900];
  const back = [230, 640, 850, 1250]; // x0,y0,x1,y1
  const line = (pts, a = .55, w = 3) => {
    for (const [lw, la] of [[w * 6, a * .12], [w, a]]) { g.lineWidth = lw; g.strokeStyle = col + la + ')'; g.beginPath(); pts.forEach((p, i) => i ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1])); g.stroke(); }
  };
  g.lineCap = 'round'; g.lineJoin = 'round';
  // back wall + room edges
  line([[back[0], back[1]], [back[2], back[1]], [back[2], back[3]], [back[0], back[3]], [back[0], back[1]]], .5);
  line([[back[0], back[1]], [-40, 160]], .35); line([[back[2], back[1]], [1120, 160]], .35);
  line([[back[0], back[3]], [-40, 1820]], .35); line([[back[2], back[3]], [1120, 1820]], .35);
  // window with city glow
  const wx = 520, wy = 720, ww = 270, wh = 330;
  const gr = g.createLinearGradient(0, wy, 0, wy + wh); gr.addColorStop(0, 'rgba(40,60,120,0.25)'); gr.addColorStop(1, 'rgba(255,170,90,0.22)');
  g.fillStyle = gr; g.fillRect(wx, wy, ww, wh);
  const r = rng(99); for (let i = 0; i < 70; i++) { g.fillStyle = `rgba(255,${180 + r() * 60 | 0},120,${.2 + r() * .5})`; g.fillRect(wx + 8 + r() * (ww - 16), wy + wh * .55 + r() * wh * .42, 3, 3); }
  line([[wx, wy], [wx + ww, wy], [wx + ww, wy + wh], [wx, wy + wh], [wx, wy]], .7, 4);
  line([[wx + ww / 2, wy], [wx + ww / 2, wy + wh]], .6); line([[wx, wy + wh * .42], [wx + ww, wy + wh * .42]], .6);
  line([[wx - 20, wy + wh + 12], [wx + ww + 20, wy + wh + 12]], .5);
  // door on left wall (perspective)
  line([[95, 1500], [95, 880], [190, 820], [190, 1340]], .45);
  // hanging bulb
  line([[400, 160], [400, 690]], .4, 2);
  g.beginPath(); g.arc(400, 712, 22, 0, 7); g.strokeStyle = col + '.7)'; g.lineWidth = 3; g.stroke();
  // empty chair
  line([[620, 1390], [620, 1250], [700, 1250], [700, 1390]], .55); line([[620, 1250], [612, 1120], [692, 1120], [700, 1250]], .55);
  line([[612, 1305], [708, 1305]], .4);
  // empty frame on right wall
  line([[930, 760], [1030, 700], [1030, 940], [930, 980], [930, 760]], .45);
  // floor boards
  for (let k = 1; k < 6; k++) line([[back[0] + (back[2] - back[0]) * k / 6, back[3]], [lerp(-40, 1120, k / 6), 1820]], .12, 2);
  // a box (moving) on floor
  line([[300, 1420], [440, 1420], [440, 1320], [300, 1320], [300, 1420]], .45); line([[300, 1320], [340, 1290], [480, 1290], [440, 1320]], .45); line([[480, 1290], [480, 1390], [440, 1420]], .45);
  return c;
}

// ---------------- airport hall (static) ----------------
function paintAirport() {
  const c = mk(W, H), g = cx2(c), VPX = 540, VPY = 980;
  g.fillStyle = '#05070d'; g.fillRect(0, 0, W, H);
  // big window at the end
  const wx0 = 180, wx1 = 900, wy0 = 640, wy1 = 1190;
  g.fillStyle = lingrad(g, 0, wy0, 0, wy1, [[0, '#060c1c'], [.6, '#16264d'], [1, '#2c3c6c']]); g.fillRect(wx0, wy0, wx1 - wx0, wy1 - wy0);
  stars(g, 5, 60, wx0, wy0, wx1 - wx0, 300, .4);
  const r = rng(12); for (let i = 0; i < 40; i++) glowDot(g, wx0 + r() * (wx1 - wx0), 1150 + r() * 30, 8, r() < .5 ? C.warm : C.cyan, .8);
  g.strokeStyle = 'rgba(160,190,255,0.18)'; g.lineWidth = 6;
  for (let k = 0; k <= 6; k++) { const x = lerp(wx0, wx1, k / 6); g.beginPath(); g.moveTo(x, wy0); g.lineTo(x, wy1); g.stroke(); }
  for (let k = 0; k <= 3; k++) { const y = lerp(wy0, wy1, k / 3); g.beginPath(); g.moveTo(wx0, y); g.lineTo(wx1, y); g.stroke(); }
  // ceiling & walls (perspective planes)
  g.fillStyle = '#0a0e18'; g.beginPath(); g.moveTo(-200, 0); g.lineTo(1280, 0); g.lineTo(wx1, wy0); g.lineTo(wx0, wy0); g.fill();
  g.fillStyle = '#080b14'; g.beginPath(); g.moveTo(-200, 0); g.lineTo(wx0, wy0); g.lineTo(wx0, wy1); g.lineTo(-200, H); g.fill();
  g.beginPath(); g.moveTo(1280, 0); g.lineTo(wx1, wy0); g.lineTo(wx1, wy1); g.lineTo(1280, H); g.fill();
  // ceiling light rows
  for (let row = -3; row <= 3; row++) for (let k = 0; k < 14; k++) {
    const z = Math.pow(k / 14, 1.6), x = lerp(VPX + row * 260, lerp(wx0, wx1, (row + 3) / 6), z), y = lerp(10, wy0 - 6, z);
    glowDot(g, x, y, lerp(34, 8, z), '#cfe2ff', .5);
  }
  // floor (polished) + window reflection
  g.fillStyle = lingrad(g, 0, wy1, 0, H, [[0, '#121a2e'], [1, '#04060c']]); g.beginPath(); g.moveTo(wx0, wy1); g.lineTo(wx1, wy1); g.lineTo(1280, H); g.lineTo(-200, H); g.fill();
  g.save(); g.globalAlpha = .28; g.translate(0, wy1 * 2); g.scale(1, -1); g.drawImage(c, wx0, wy0, wx1 - wx0, wy1 - wy0, wx0, wy0, wx1 - wx0, wy1 - wy0); g.restore();
  g.strokeStyle = 'rgba(150,180,255,0.07)'; g.lineWidth = 2;
  for (let k = -8; k <= 8; k++) { g.beginPath(); g.moveTo(VPX + k * 40, wy1); g.lineTo(VPX + k * 260, H); g.stroke(); }
  // gate sign
  g.save(); g.translate(540, 520);
  rr(g, -150, -40, 300, 80, 10); g.fillStyle = '#0d1424'; g.fill(); g.strokeStyle = hexA(C.amber, .5); g.lineWidth = 2; g.stroke();
  text(g, 'ВЫХОД  23', 0, 14, font(700, 36, 'JetBrains Mono'), C.amber, 'center', 4); g.restore();
  g.fillStyle = '#05070d'; g.fillRect(538, 440, 4, 40);
  return c;
}

function person(g, x, feet, h, phase, col, bag) {
  const s = h / 300, sw = Math.sin(phase) * 22 * s;
  g.fillStyle = col;
  g.beginPath(); g.ellipse(x, feet - 270 * s, 22 * s, 27 * s, 0, 0, 7); g.fill();
  rr(g, x - 34 * s, feet - 240 * s, 68 * s, 120 * s, 22 * s); g.fill();
  g.lineCap = 'round'; g.strokeStyle = col; g.lineWidth = 22 * s;
  g.beginPath(); g.moveTo(x - 12 * s, feet - 130 * s); g.lineTo(x - 12 * s + sw, feet - 6 * s); g.moveTo(x + 12 * s, feet - 130 * s); g.lineTo(x + 12 * s - sw, feet - 6 * s); g.stroke();
  g.lineWidth = 16 * s; g.beginPath(); g.moveTo(x - 30 * s, feet - 225 * s); g.lineTo(x - 36 * s - sw * .5, feet - 130 * s); g.moveTo(x + 30 * s, feet - 225 * s); g.lineTo(x + 36 * s + sw * .5, feet - 130 * s); g.stroke();
  if (bag) { rr(g, x + 46 * s, feet - 110 * s, 54 * s, 100 * s, 8 * s); g.fill(); g.lineWidth = 5 * s; g.beginPath(); g.moveTo(x + 73 * s, feet - 110 * s); g.lineTo(x + 50 * s, feet - 160 * s); g.stroke(); }
}

// ---------------- clouds ----------------
function paintCloudLayer(seed, w, h, density, light, dark) {
  const c = mk(w, h), g = cx2(c), r = rng(seed);
  for (let i = 0; i < density * 4; i++) {
    const x = r() * w, y = h * .3 + Math.pow(r(), 1.3) * h * .65, rad = 40 + r() * 140, fy = .45;
    for (const dx of [-w, 0, w]) {
      if (x + dx + rad < 0 || x + dx - rad > w) continue;
      g.save(); g.translate(x + dx, y); g.scale(1, fy);
      const gr = g.createRadialGradient(0, -rad * .25, 0, 0, 0, rad);
      gr.addColorStop(0, hexA(light, .17)); gr.addColorStop(.5, hexA(dark, .11)); gr.addColorStop(1, hexA(dark, 0));
      g.fillStyle = gr; g.fillRect(-rad, -rad, rad * 2, rad * 2); g.restore();
    }
  }
  g.fillStyle = lingrad(g, 0, 0, 0, h, [[0, 'rgba(0,0,0,0)'], [.6, hexA(dark, .35)], [1, hexA(dark, .85)]]); g.globalCompositeOperation = 'source-atop'; g.fillRect(0, 0, w, h);
  return c;
}

// ---------------- airplane (side silhouette, facing right) ----------------
function paintPlane() {
  const c = mk(700, 260), g = cx2(c);
  g.translate(20, 40);
  const body = '#0b0f1b';
  g.fillStyle = body;
  g.beginPath(); g.moveTo(20, 120); g.bezierCurveTo(60, 92, 520, 92, 600, 104); g.bezierCurveTo(650, 110, 666, 128, 640, 140); g.bezierCurveTo(560, 150, 100, 152, 40, 140); g.closePath(); g.fill();
  g.beginPath(); g.moveTo(30, 122); g.lineTo(0, 10); g.lineTo(46, 10); g.lineTo(130, 106); g.fill(); // tail fin
  g.beginPath(); g.moveTo(40, 128); g.lineTo(-10, 150); g.lineTo(20, 156); g.lineTo(110, 136); g.fill(); // stabilizer
  g.beginPath(); g.moveTo(250, 136); g.lineTo(150, 196); g.lineTo(190, 200); g.lineTo(380, 140); g.fill(); // wing
  rr(g, 260, 146, 90, 30, 14); g.fill(); // engine
  g.fillStyle = 'rgba(255,214,150,0.85)'; for (let k = 0; k < 26; k++) g.fillRect(130 + k * 17, 112, 7, 7);
  g.strokeStyle = 'rgba(160,190,255,0.35)'; g.lineWidth = 2; g.beginPath(); g.moveTo(60, 100); g.bezierCurveTo(200, 92, 520, 92, 600, 104); g.stroke();
  return c;
}

// bird silhouette (gull-like "M"), flapping
function bird(g, x, y, s, flap, col, a = 1) {
  const up = Math.sin(flap), tipY = -34 * up - 4, elY = -12 * up - 2;
  g.save(); g.translate(x, y); g.scale(s, s); g.globalAlpha *= a; g.fillStyle = col;
  for (const sd of [-1, 1]) {
    g.beginPath(); g.moveTo(0, -3); g.quadraticCurveTo(sd * 10, elY - 6, sd * 20, elY);
    g.quadraticCurveTo(sd * 34, elY + (tipY - elY) * .4 - 4, sd * 50, tipY);
    g.quadraticCurveTo(sd * 30, elY + 6, sd * 18, elY + 7); g.quadraticCurveTo(sd * 8, 4, 0, 5); g.fill();
  }
  g.beginPath(); g.ellipse(0, 2, 6, 9, 0, 0, 7); g.fill(); g.beginPath(); g.arc(0, -6, 4.5, 0, 7); g.fill();
  g.restore();
}

// ---------------- night landscape with lonely house ----------------
function paintHouseLand() {
  const L = {};
  let c = mk(W, H), g = cx2(c);
  skyGrad(g, W, H, [[0, '#02040a'], [.5, '#0a1430'], [.68, '#24294d'], [.72, '#3a2c44'], [1, '#05060b']]);
  stars(g, 77, 320, 0, 0, W, 1100, .75);
  radial(g, 880, 600, 260, '#c8d6ff', .12); g.fillStyle = '#eef2ff'; g.beginPath(); g.arc(880, 600, 32, 0, 7); g.fill();
  L.sky = c;
  const hill = (y0, amp, seed, col) => { const c2 = mk(W, H), g2 = cx2(c2); g2.fillStyle = col; g2.beginPath(); g2.moveTo(-20, H); for (let x = -20; x <= W + 20; x += 10) g2.lineTo(x, y0 - (noise1(x / 260 + seed) - .5) * amp - (noise1(x / 90 + seed * 3) - .5) * amp * .25); g2.lineTo(W + 20, H); g2.fill(); return c2; };
  L.h1 = hill(1180, 160, 3, '#0b1022');
  L.h2 = hill(1290, 120, 7, '#070a17');
  // near hill with house
  c = mk(W, H); g = cx2(c);
  g.fillStyle = '#04060d'; g.beginPath(); g.moveTo(-20, H); g.lineTo(-20, 1470); g.bezierCurveTo(250, 1400, 400, 1352, 540, 1350); g.bezierCurveTo(700, 1350, 860, 1400, 1100, 1450); g.lineTo(1100, H); g.fill();
  // house
  const hx = 540, hy = 1356;
  g.fillStyle = '#04060d'; g.fillRect(hx - 90, hy - 130, 180, 130);
  g.beginPath(); g.moveTo(hx - 112, hy - 126); g.lineTo(hx, hy - 220); g.lineTo(hx + 112, hy - 126); g.fill();
  g.fillRect(hx + 40, hy - 222, 26, 70);
  // tree
  g.fillRect(hx + 168, hy - 110, 10, 110);
  for (let k = 0; k < 7; k++) { g.beginPath(); g.ellipse(hx + 173 + Math.sin(k * 2.1) * 26, hy - 130 - k * 18, 54 - k * 6, 30, 0, 0, 7); g.fill(); }
  // fence
  g.strokeStyle = '#04060d'; g.lineWidth = 4; g.beginPath(); g.moveTo(hx - 300, hy + 14); g.lineTo(hx - 110, hy + 4); g.stroke();
  for (let k = 0; k < 9; k++) { const fx = hx - 300 + k * 24; g.fillRect(fx, hy - 2 - (9 - k) * .9, 4, 26); }
  L.near = c; L.house = [hx, hy];
  return L;
}
function houseWindows(g, hx, hy, a, flick) {
  const wins = [[-62, -100, 40, 46], [22, -100, 40, 46], [-14, -190, 28, 30]];
  g.save();
  radial(g, hx, hy - 80, 360, C.warm, .16 * a);
  wins.forEach((w, i) => {
    const aa = a * (i === 2 ? flick : 1);
    g.fillStyle = hexA('#ffd28a', .95 * aa); g.fillRect(hx + w[0], hy + w[1], w[2], w[3]);
    g.fillStyle = hexA('#5a3410', .8 * aa); g.fillRect(hx + w[0] + w[2] / 2 - 2, hy + w[1], 4, w[3]); g.fillRect(hx + w[0], hy + w[1] + w[3] / 2 - 2, w[2], 4);
    glowDot(g, hx + w[0] + w[2] / 2, hy + w[1] + w[3] / 2, 90, '#ffb860', .5 * aa);
  });
  // spill light on the ground
  g.fillStyle = hexA('#ffb860', .1 * a); g.beginPath(); g.moveTo(hx - 70, hy); g.lineTo(hx - 150, hy + 90); g.lineTo(hx + 150, hy + 90); g.lineTo(hx + 70, hy); g.fill();
  g.restore();
}

// ---------------- passport stamps (pre-rendered with ink erosion) ----------------
function paintStamp(kind, col, l1, l2, l3, seed) {
  const S = 300, c = mk(S, S), g = cx2(c), m = S / 2;
  g.strokeStyle = col; g.fillStyle = col; g.lineWidth = 7;
  g.textAlign = 'center';
  if (kind === 'circle') {
    g.beginPath(); g.arc(m, m, 128, 0, 7); g.stroke(); g.lineWidth = 3; g.beginPath(); g.arc(m, m, 108, 0, 7); g.stroke();
  } else if (kind === 'rect') { g.lineWidth = 7; rr(g, 26, 66, 248, 168, 18); g.stroke(); g.lineWidth = 3; rr(g, 40, 80, 220, 140, 10); g.stroke(); }
  else if (kind === 'oct') { g.beginPath(); for (let i = 0; i < 8; i++) { const a = i / 8 * Math.PI * 2 + Math.PI / 8; g.lineTo(m + Math.cos(a) * 128, m + Math.sin(a) * 128); } g.closePath(); g.stroke(); }
  else if (kind === 'tri') { g.beginPath(); g.moveTo(m, 20); g.lineTo(282, 262); g.lineTo(18, 262); g.closePath(); g.stroke(); }
  else if (kind === 'ban') { g.lineWidth = 10; rr(g, 10, 90, 280, 120, 12); g.stroke(); }
  const yo = kind === 'tri' ? 40 : 0;
  g.font = font(700, 22, 'JetBrains Mono'); g.letterSpacing = '3px'; g.fillText(l1, m, m - 38 + yo);
  g.font = font(800, kind === 'ban' ? 46 : 40, 'Inter'); g.letterSpacing = '1px'; g.fillText(l2, m, m + 14 + yo);
  g.font = font(600, 22, 'JetBrains Mono'); g.letterSpacing = '2px'; g.fillText(l3, m, m + 50 + yo);
  if (kind !== 'ban') { g.font = font(700, 30, 'Inter'); g.fillText('✈', m, m - 70 + yo); }
  // ink erosion
  const r = rng(seed); g.globalCompositeOperation = 'destination-out';
  for (let i = 0; i < 900; i++) { g.fillStyle = `rgba(0,0,0,${.2 + r() * .8})`; const s = 1 + r() * 4; g.fillRect(r() * S, r() * S, s, s); }
  for (let i = 0; i < 6; i++) { g.fillStyle = 'rgba(0,0,0,0.35)'; g.beginPath(); g.ellipse(r() * S, r() * S, 20 + r() * 60, 8 + r() * 20, r() * 3, 0, 7); g.fill(); }
  return c;
}

// ---------------- europe map (paths in base projection) ----------------
function buildEurope() {
  const proj = d3.geoConicConformal().parallels([40, 60]).rotate([-10, 0]).center([0, 47.5]).scale(2300).translate([540, 960]);
  const paths = WORLD.c50.map(f => { const p = new Path2D(d3.geoPath(proj)(f) || ''); return p; });
  const borders = new Path2D(d3.geoPath(proj)(WORLD.borders50));
  return { proj, paths, borders };
}
function buildRoute(proj, names, samples = 500) {
  const pts = names.map(n => proj(CITY[n]));
  // catmull-rom through points
  const out = [];
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[Math.max(0, i - 1)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(pts.length - 1, i + 2)];
    for (let k = 0; k < 40; k++) {
      const t = k / 40, t2 = t * t, t3 = t2 * t;
      out.push([0, 1].map(j => .5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3)));
    }
  }
  out.push(pts[pts.length - 1]);
  const len = [0]; for (let i = 1; i < out.length; i++) len.push(len[i - 1] + Math.hypot(out[i][0] - out[i - 1][0], out[i][1] - out[i - 1][1]));
  const total = len[len.length - 1];
  // resample uniformly
  const res = []; let j = 0;
  for (let s = 0; s <= samples; s++) { const d = total * s / samples; while (j < len.length - 2 && len[j + 1] < d) j++; const u = (d - len[j]) / (len[j + 1] - len[j] || 1); res.push([lerp(out[j][0], out[j + 1][0], u), lerp(out[j][1], out[j + 1][1], u)]); }
  // which country each sample is in
  const cidx = res.map(p => { const ll = proj.invert(p); for (let i = 0; i < WORLD.c50.length; i++) if (d3.geoContains(WORLD.c50[i], ll)) return i; return -1; });
  const cityAt = names.map(n => { const p = proj(CITY[n]); let best = 0, bd = 1e9; res.forEach((q, i) => { const d = Math.hypot(q[0] - p[0], q[1] - p[1]); if (d < bd) { bd = d; best = i; } }); return { n, i: best, p }; });
  return { pts: res, cidx, cityAt };
}

// ---------------- street map for verse 2 ----------------
function paintStreetMap(w, h) {
  const c = mk(w, h), g = cx2(c), r = rng(404);
  g.fillStyle = '#0b1210'; g.fillRect(0, 0, w, h);
  g.fillStyle = '#0f1d17'; g.beginPath(); g.ellipse(w * .78, h * .3, 120, 80, .4, 0, 7); g.fill(); // park
  g.fillStyle = '#0a1a26'; g.beginPath(); g.moveTo(0, h * .82); g.bezierCurveTo(w * .3, h * .7, w * .6, h * .95, w, h * .78); g.lineTo(w, h * .9); g.bezierCurveTo(w * .6, h * 1.05, w * .3, h * .8, 0, h * .92); g.fill();
  g.strokeStyle = 'rgba(160,255,210,0.14)'; g.lineWidth = 3;
  g.save(); g.translate(w / 2, h / 2); g.rotate(-.18);
  for (let x = -w; x < w; x += 46 + r() * 30) { g.lineWidth = r() < .2 ? 7 : 3; g.beginPath(); g.moveTo(x, -h); g.lineTo(x + 20, h); g.stroke(); }
  for (let y = -h; y < h; y += 46 + r() * 30) { g.lineWidth = r() < .2 ? 7 : 3; g.beginPath(); g.moveTo(-w, y); g.lineTo(w, y + 10); g.stroke(); }
  g.restore();
  g.strokeStyle = 'rgba(160,255,210,0.28)'; g.lineWidth = 9; g.beginPath(); g.moveTo(0, h * .2); g.bezierCurveTo(w * .4, h * .35, w * .5, h * .1, w, h * .45); g.stroke();
  return c;
}

function initArt() {
  ART.london = paintLondon(); ART.prague = paintPrague(); ART.nice = paintNice();
  ART.sky = [paintSkyline(101, C.violet, 'needle'), paintSkyline(202, C.amber, 'spire'), paintSkyline(303, C.cyan, 'domes'), paintSkyline(404, C.pink, 'bridge')];
  ART.apt = paintApartment();
  ART.airport = paintAirport();
  ART.cloud = [paintCloudLayer(1, 2160, 700, 70, '#c9d6ff', '#1a2244'), paintCloudLayer(2, 2160, 800, 60, '#dfe6ff', '#141b38'), paintCloudLayer(3, 2160, 900, 45, '#eef2ff', '#0e1430')];
  ART.plane = paintPlane();
  ART.land = paintHouseLand();
  ART.street = paintStreetMap(820, 470);
  const st = [
    ['circle', '#e0465a', 'ENTRY', 'LONDON', '12.03.25'], ['rect', '#3a7bff', 'ARRIVAL', 'PRAHA', '02.04.25'], ['oct', '#1f9e6e', 'ENTRÉE', 'NICE', '19.05.25'],
    ['tri', '#9b5cff', 'DEPART', 'DUBAI', '01.06.25'], ['circle', '#e08a1e', 'ARRIVAL', 'İSTANBUL', '14.07.25'], ['rect', '#d0345a', 'ENTRY', 'TBILISI', '30.07.25'],
    ['oct', '#2a8fd6', 'VISA', 'BEOGRAD', '11.08.25'], ['circle', '#3a7bff', 'ENTRY', 'BALI', '05.09.25'], ['rect', '#1f9e6e', 'ARRIVAL', 'LISBOA', '21.10.25'],
    ['circle', '#e0465a', 'DEPART', 'NICE', '02.11.25'], ['tri', '#e08a1e', 'ENTRY', 'BANGKOK', '09.11.25'], ['oct', '#9b5cff', 'ENTRY', 'YEREVAN', '15.11.25']
  ];
  ART.stamps = st.map((s, i) => paintStamp(s[0], s[1], s[2], s[3], s[4], i * 31 + 7));
  ART.ban = paintStamp('ban', '#ff3b52', 'ВЪЕЗД', 'ЗАПРЕЩЁН', '', 991);
  ART.europe = buildEurope();
  ART.route1 = buildRoute(ART.europe.proj, ['london', 'paris', 'frankfurt', 'prague', 'vienna', 'munich', 'zurich', 'milan', 'nice']);
  ART.route2 = buildRoute(ART.europe.proj, ['nice', 'barcelona', 'madrid', 'lisbon', 'paris', 'amsterdam', 'berlin', 'prague', 'london']);
  // noise grain
  ART.grain = [0, 1, 2].map(k => { const c = mk(540, 960), g = cx2(c), id = g.createImageData(540, 960), r = rng(k + 5); for (let i = 0; i < id.data.length; i += 4) { const v = r() * 255; id.data[i] = id.data[i + 1] = id.data[i + 2] = v; id.data[i + 3] = 255; } g.putImageData(id, 0, 0); return c; });
  ART.vignette = (() => { const c = mk(W, H), g = cx2(c), gr = g.createRadialGradient(W / 2, H * .48, H * .25, W / 2, H * .48, H * .75); gr.addColorStop(0, 'rgba(0,0,0,0)'); gr.addColorStop(1, 'rgba(0,0,0,0.8)'); g.fillStyle = gr; g.fillRect(0, 0, W, H); return c; })();
}
