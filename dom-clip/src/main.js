'use strict';
// =================== frame compositor ===================
const canvas = document.getElementById('c'); canvas.width = W; canvas.height = H;
const ctx = canvas.getContext('2d');
const LAYER = mk(W, H), LG = cx2(LAYER);

function trans(s, t) {
  let alpha = 1, blur = 0, scale = 1, dx = 0, dy = 0;
  const pi = s.tin > 0 ? inv(s.a, s.a + s.tin, t) : 1, po = s.tout > 0 ? inv(s.b - s.tout, s.b, t) : 0;
  const apply = (type, k, dir) => {
    if (k <= 0) return;
    switch (type) {
      case 'fade': alpha *= 1 - k; break;
      case 'blur': alpha *= 1 - k; blur += 30 * k; scale *= dir < 0 ? 1 + .05 * k : 1 - .04 * k; dy += dir < 0 ? 30 * k : -20 * k; break;
      case 'zoom': alpha *= 1 - k * k; blur += 40 * k; scale *= dir < 0 ? 1 - .2 * k : 1 + .7 * k; break;
      case 'zoomin': alpha *= 1 - k; blur += 30 * k; scale *= dir < 0 ? 1.6 - .6 * (1 - k) : 1; break;
      case 'whip': dx += (dir < 0 ? 1 : -1) * W * .9 * k; blur += 36 * Math.sin(Math.PI * Math.min(1, k * 1.2)) + 8 * k; alpha *= 1 - .3 * k; break;
      case 'cut': break;
    }
  };
  if (pi < 1) apply(s.fin, 1 - eOC(pi), -1);
  if (po > 0) apply(s.fout, eIC(po), 1);
  return { alpha, blur, scale, dx, dy };
}

const dust = Array.from({ length: 150 }, (_, i) => ({ x: hash(i * 1.3) * W, y: hash(i * 2.9) * H, d: .25 + hash(i * 5.7) * 1.2, tw: hash(i * 8.1) * 6, v: hash(i * 3.3) }));
function drawDust(g, t, e) {
  for (const p of dust) {
    const y = ((p.y - t * (10 + 26 * p.d) * (1 + e * .8)) % H + H) % H, x = p.x + Math.sin(t * .3 + p.tw) * 30 * p.d;
    const a = (.12 + .35 * (.5 + .5 * Math.sin(t * 2 + p.tw))) * (p.d > 1.1 ? .5 : 1);
    if (p.d > 1.1) glowDot(g, x, y, 10 * p.d, '#cfe0ff', a * .6);
    else { g.fillStyle = `rgba(220,230,255,${a})`; g.fillRect(x, y, 1.2 + p.d * 1.6, 1.2 + p.d * 1.6); }
  }
}

function renderFrame(t) {
  const g = ctx;
  g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1; g.globalCompositeOperation = 'source-over'; g.filter = 'none';
  g.fillStyle = lingrad(g, 0, 0, 0, H, [[0, '#060912'], [.5, '#080c18'], [1, '#04050a']]); g.fillRect(0, 0, W, H);
  const act = []; for (const s of SC) if (t >= s.a && t <= s.b) act.push([s, trans(s, t)]);
  // accent colour (weighted)
  let acc = [0, 0, 0], wsum = 0;
  for (const [s, v] of act) { const c = hexRGB(s.accFn ? s.accFn(t) : s.acc); acc = acc.map((q, i) => q + c[i] * v.alpha); wsum += v.alpha; }
  acc = wsum > 0 ? acc.map(q => q / wsum) : [70, 110, 200];
  const e = energy(t), pl = pulse(t, 5) * (isChorus(t) ? 1 : .35), bp = barPulse(t, 3) * (isChorus(t) ? 1 : .3);
  // bloom behind content
  const bloomA = (.22 + .22 * e + .18 * pl) * clamp(wsum);
  const bx = 540 + Math.sin(t * .4) * 60, by = 1000 + Math.cos(t * .3) * 50;
  g.save(); g.translate(bx, by); g.scale(1, 1.3);
  const gr = g.createRadialGradient(0, 0, 0, 0, 0, 640 + 80 * bp);
  gr.addColorStop(0, rgbA(acc, bloomA)); gr.addColorStop(.55, rgbA(acc, bloomA * .35)); gr.addColorStop(1, rgbA(acc, 0));
  g.fillStyle = gr; g.fillRect(-900, -900, 1800, 1800); g.restore();
  drawDust(g, t, e);
  // scenes
  for (const [s, v] of act) {
    if (v.alpha <= .002) continue;
    const lg = LG; lg.setTransform(1, 0, 0, 1, 0, 0); lg.globalAlpha = 1; lg.globalCompositeOperation = 'source-over'; lg.clearRect(0, 0, W, H);
    lg.save(); s.draw(lg, t); lg.restore();
    let dx = v.dx, dy = v.dy, sc = v.scale;
    if (s.shake) { dx += (noise1(t * 30) - .5) * 14 * bp; dy += (noise1(t * 30 + 50) - .5) * 14 * bp; sc *= 1 + .012 * pl; }
    g.save(); g.setTransform(sc, 0, 0, sc, W / 2 * (1 - sc) + dx, H / 2 * (1 - sc) + dy);
    drawBlurred(g, LAYER, v.blur, v.alpha);
    g.restore();
  }
  g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1;
  // readability shades + HUD
  g.fillStyle = lingrad(g, 0, 0, 0, 470, [[0, 'rgba(3,4,8,0.85)'], [1, 'rgba(3,4,8,0)']]); g.fillRect(0, 0, W, 470);
  g.fillStyle = lingrad(g, 0, 1560, 0, H, [[0, 'rgba(3,4,8,0)'], [1, 'rgba(3,4,8,0.92)']]); g.fillRect(0, 1560, W, H - 1560);
  g.drawImage(ART.vignette, 0, 0);
  drawLyrics(g, t);
  const hudA = sstep(.6, 2.0, t) * (1 - sstep(150.8, 151.8, t));
  if (hudA > 0) { g.globalAlpha = hudA; drawPlayer(g, t); g.globalAlpha = 1; }
  // grain
  g.save(); g.globalAlpha = .07; g.globalCompositeOperation = 'overlay'; g.drawImage(ART.grain[Math.floor(t * FPS) % 3], 0, 0, W, H); g.restore();
  // global fades
  const fade = Math.max(1 - sstep(0, .9, t), sstep(DUR - .5, DUR, t));
  if (fade > 0) { g.fillStyle = `rgba(0,0,0,${fade})`; g.fillRect(0, 0, W, H); }
}

async function init() {
  await Promise.all(['400 40px "Inter"', '500 40px "Inter"', '600 40px "Inter"', '700 40px "Inter"', '800 40px "Inter"', '300 40px "Inter Display"', '800 40px "Inter Display"', '900 40px "Inter Display"', '500 40px "JetBrains Mono"', '600 40px "JetBrains Mono"', '700 40px "JetBrains Mono"'].map(f => document.fonts.load(f, 'ДОМAa0')));
  initWorld(); initArt(); buildTimeline();
  window.READY = true;
}
window.renderFrame = renderFrame;
window.grab = (t, q = .93) => { renderFrame(t); return canvas.toDataURL('image/jpeg', q); };
init().catch(e => { window.INIT_ERR = String(e && e.stack || e); });
