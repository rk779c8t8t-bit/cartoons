// «Гикаю» — kinetic typography visualizer.
// Every frame is a pure function of song time T, so frames can be rendered
// in any order (and in parallel) and always match the audio exactly.
import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { FullScreenQuad } from 'three/addons/postprocessing/Pass.js';
import { TextGeometry } from 'three/addons/geometries/TextGeometry.js';
import { Font } from 'three/addons/loaders/FontLoader.js';

const Q = new URLSearchParams(location.search);
const WIDTH = +(Q.get('w') ?? 1920), HEIGHT = +(Q.get('h') ?? 1080);
const SUB = +(Q.get('sub') ?? 1);          // motion blur subframes
const FPS = +(Q.get('fps') ?? 30);
const SHUTTER = 0.55 / FPS;                // ~200° shutter

const timing = await (await fetch('./timing.json')).json();
const CLIP0 = timing.clip.start, CLIP1 = timing.clip.end;
const BEAT = 60 / timing.bpm;
const WT = timing.lines.map(l => l.words.map(w => w[1]));   // word times per line

// ───────────────────────── math helpers ─────────────────────────
const clamp = (x, a, b) => Math.min(b, Math.max(a, x));
const sat = x => clamp(x, 0, 1);
const lerp = (a, b, t) => a + (b - a) * t;
const ap = (T, a, d) => sat((T - a) / d);                  // progress of an animation that starts at a, lasts d
const inW = (T, a, b) => T >= a && T < b;
const oCubic = t => 1 - Math.pow(1 - t, 3);
const iCubic = t => t * t * t;
const ioCubic = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
const oExpo = t => t >= 1 ? 1 : 1 - Math.pow(2, -10 * t);
const iExpo = t => t <= 0 ? 0 : Math.pow(2, 10 * t - 10);
const oBack = (t, s = 1.9) => 1 + (s + 1) * Math.pow(t - 1, 3) + s * Math.pow(t - 1, 2);
const oElastic = t => t <= 0 ? 0 : t >= 1 ? 1 : Math.pow(2, -10 * t) * Math.sin((t * 10 - .75) * (2 * Math.PI) / 3) + 1;
const decay = (T, t0, tau) => T >= t0 ? Math.exp(-(T - t0) / tau) : 0;
const fract = x => x - Math.floor(x);
const hash = n => fract(Math.sin(n * 127.1 + 311.7) * 43758.5453);
const vnoise = x => { const i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f); return lerp(hash(i), hash(i + 1), u) * 2 - 1; };
const frameOf = T => Math.floor(T * 30 + 1e-4);              // glitch randomness is quantized to 30 fps

// ───────────────────────── renderer / scene ─────────────────────────
const renderer = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(1);
renderer.setSize(WIDTH, HEIGHT);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;
document.body.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x030102);
const FOV = 40;
const camera = new THREE.PerspectiveCamera(FOV, WIDTH / HEIGHT, 0.1, 400);
const PIX = HEIGHT / (2 * Math.tan(THREE.MathUtils.degToRad(FOV / 2)));   // world→pixel factor at distance 1

scene.add(new THREE.AmbientLight(0xffe2c8, 0.35));
const key = new THREE.DirectionalLight(0xffffff, 1.7); key.position.set(-8, 12, 20); scene.add(key);
const rim = new THREE.PointLight(0xff5a10, 400, 120, 1.6); rim.position.set(10, -8, -6); scene.add(rim);
const fill = new THREE.PointLight(0xff9a40, 250, 120, 1.6); fill.position.set(-14, 6, 14); scene.add(fill);

// ───────────────────────── fonts & 3D words ─────────────────────────
const FONTS = {};
for (const [k, f] of [['ub', 'unbounded-900'], ['m9', 'montserrat-900'], ['m7', 'montserrat-700']])
  FONTS[k] = new Font(await (await fetch(`./assets/${f}.json`)).json());

const STYLES = {
  white:  { front: 0xfff6ee, fe: 0xfff0e0, fi: 0.16, side: 0xd2672a, se: 0x8a2c00, si: 0.55 },
  orange: { front: 0xffa040, fe: 0xff5a00, fi: 0.7, side: 0xb33a00, se: 0x5a1400, si: 0.6 },
  red:    { front: 0xff3c1c, fe: 0xe01000, fi: 0.6,  side: 0x7a0c00, se: 0x3a0400, si: 0.6 },
  hot:    { front: 0xffffff, fe: 0xffffff, fi: 0.4,  side: 0xffb070, se: 0xff7a20, si: 0.8 },
  ghost:  { front: 0x401608, fe: 0xff3a00, fi: 0.16, side: 0x2a0a00, se: 0x000000, si: 0 },
  dim:    { front: 0xffe6d0, fe: 0xffd2a0, fi: 0.3,  side: 0x6a3010, se: 0x200800, si: 0.2 },
};
const geoCache = new Map();
function glyphGeo(font, ch, depth) {
  const id = `${font}|${ch}|${depth}`;
  if (geoCache.has(id)) return geoCache.get(id);
  let g = null;
  if (ch.trim()) {
    g = new TextGeometry(ch, { font: FONTS[font], size: 1, depth, curveSegments: 6,
      bevelEnabled: true, bevelThickness: depth * 0.14, bevelSize: 0.02, bevelSegments: 2 });
    g.computeBoundingBox();
    const c = new THREE.Vector3(); g.boundingBox.getCenter(c);
    g.translate(-c.x, -c.y, -c.z);
    g.userData.c = c;
  }
  geoCache.set(id, g);
  return g;
}
const ALL = [];            // every animated object; hidden at the start of each frame
function mats(style) {
  const s = STYLES[style];
  const front = new THREE.MeshStandardMaterial({ color: s.front, emissive: s.fe, emissiveIntensity: s.fi, roughness: 0.32, metalness: 0.15, transparent: true });
  const side = new THREE.MeshStandardMaterial({ color: s.side, emissive: s.se, emissiveIntensity: s.si, roughness: 0.45, metalness: 0.25, transparent: true });
  front.userData.ei = s.fi; side.userData.ei = s.si;
  return [front, side];
}
// W(text, font, style, worldWidth, depth): a 3D word made of individually animatable letters.
function W(text, font = 'ub', style = 'white', width = 10, depth = 0.34) {
  const F = FONTS[font], res = F.data.resolution;
  const g = new THREE.Group(); scene.add(g);
  const capH = glyphGeo(font, 'Н', depth).boundingBox.max.y * 2;     // centred → max.y = h/2
  let pen = 0; const L = [];
  for (const ch of text) {
    const gl = F.data.glyphs[ch] ?? F.data.glyphs['?'];
    const adv = gl.ha / res;
    const geo = glyphGeo(font, ch, depth);
    if (geo) {
      const m = mats(style);
      const mesh = new THREE.Mesh(geo, m);
      const p = new THREE.Group(); p.add(mesh); g.add(p);
      const c = geo.userData.c;
      L.push({ p, mesh, m, bx: pen + c.x, by: c.y, ch, op: 1 });
    }
    pen += adv;
  }
  for (const l of L) { l.bx -= pen / 2; l.by -= capH / 2; }
  const w = { g, L, k: width / pen, nat: pen, capH, style, text };
  w.reset = () => { g.visible = false; for (const l of L) { l.p.position.set(l.bx, l.by, 0); l.p.rotation.set(0, 0, 0); l.p.scale.set(1, 1, 1); l.p.visible = true; l.op = 1; l.em = 1; } };
  w.height = () => capH * w.k;
  ALL.push(w);
  return w;
}
// show(): place a word in world space. s multiplies the fitted scale.
function show(w, o = {}) {
  const g = w.g; g.visible = true;
  g.position.set(o.x ?? 0, o.y ?? 0, o.z ?? 0);
  g.rotation.set(o.rx ?? 0, o.ry ?? 0, o.rz ?? 0);
  const s = (o.s ?? 1) * w.k;
  g.scale.set(s * (o.sx ?? 1), s * (o.sy ?? 1), s * (o.sz ?? 1));
  w.op = o.op ?? 1; w.em = o.em ?? 1;
  return w;
}
function finishWords() {           // apply per-word × per-letter opacity / emissive after scenes ran
  for (const w of ALL) {
    if (!w.L || !w.g.visible) continue;
    for (const l of w.L) {
      const op = sat(w.op * l.op);
      l.p.visible = op > 0.003;
      for (const m of l.m) { m.opacity = op; m.emissiveIntensity = m.userData.ei * w.em * l.em; m.depthWrite = op > 0.98; }
    }
  }
}
// letter helpers (offsets are in world units; converted to the word's local units)
function lOff(w, i, dx = 0, dy = 0, dz = 0) { const k = w.k, p = w.L[i].p.position; p.x += dx / k; p.y += dy / k; p.z += dz / k; }
function scatter(w, p, seed = 1, dist = 14, spin = 4) {      // letters fly apart
  if (p <= 0) return;
  const e = iCubic(p) * 0.6 + p * 0.4;
  w.L.forEach((l, i) => {
    const a = hash(seed * 31 + i) * Math.PI * 2, r = dist * (0.5 + hash(seed * 7 + i));
    lOff(w, i, Math.cos(a) * r * e, Math.sin(a) * r * e, (hash(seed + i * 3) * 2 - 0.4) * r * e);
    l.p.rotation.x += (hash(i + seed * 11) - .5) * spin * e; l.p.rotation.z += (hash(i + seed * 5) - .5) * spin * e;
    l.op *= 1 - sat(p * 1.4 - 0.3);
  });
}
function lettersIn(w, T, t0, stagger, dur, fn) {               // per-letter staged entrance
  w.L.forEach((l, i) => { fn(l, i, sat((T - t0 - i * stagger) / dur)); });
}

// ───────────────────────── emoji sprites ─────────────────────────
const texLoader = new THREE.TextureLoader();
const emojiTex = {};
async function loadEmoji(code) {
  if (!emojiTex[code]) { const t = await texLoader.loadAsync(`./assets/emoji/${code}.webp`); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; emojiTex[code] = t; }
  return emojiTex[code];
}
const EMOJI_CODES = ['1f3a7', '1f50a', '1f48b', '1f4f1', '1f36c', '1f60b', '2728', '1f4af', '1f30d', '1f4cd', '2708-fe0f', '1f913', '1f3ae', '1f4bb', '1f47e', '26a1', '1f525', '1f50b', '1faab', '1f4f4', '1f635', '1f4a5', '1f92f', '1f60e'];
await Promise.all(EMOJI_CODES.map(loadEmoji));
function E(code, size = 3) {
  const m = new THREE.MeshBasicMaterial({ map: emojiTex[code], transparent: true, depthWrite: false, toneMapped: false, color: 0xd8d8d8 });
  const mesh = new THREE.Mesh(new THREE.PlaneGeometry(size, size), m);
  scene.add(mesh);
  const e = { g: mesh, m, emoji: true };
  e.reset = () => { mesh.visible = false; };
  ALL.push(e);
  return e;
}
function showE(e, o = {}) {
  const g = e.g; g.visible = true;
  g.position.set(o.x ?? 0, o.y ?? 0, o.z ?? 0);
  g.rotation.set(o.rx ?? 0, o.ry ?? 0, o.rz ?? 0);
  g.scale.setScalar(o.s ?? 1);
  e.m.opacity = o.op ?? 1;
  e.g.visible = e.m.opacity > 0.003 && (o.s ?? 1) > 0.003;
}
// pop-in with elastic overshoot + idle float
function popE(e, T, t0, o = {}, tOut = 1e9, dOut = 0.2) {
  if (T < t0) return;
  const p = ap(T, t0, 0.45), q = ap(T, tOut, dOut);
  const fl = Math.sin((T - t0) * 3 + t0) * 0.25;
  showE(e, { ...o, y: (o.y ?? 0) + fl - q * 2, s: (o.s ?? 1) * oElastic(p) * (1 - q * 0.6), op: (o.op ?? 1) * sat(p * 4) * (1 - q), rz: (o.rz ?? 0) + Math.sin((T - t0) * 2.2) * 0.12 });
}

// ───────────────────────── generic meshes ─────────────────────────
function M(mesh) { scene.add(mesh); const o = { g: mesh }; o.reset = () => { mesh.visible = false; }; ALL.push(o); return o; }
function canvasTex(size, draw) {
  const c = document.createElement('canvas'); c.width = c.height = size;
  draw(c.getContext('2d'), size);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}
const glowTex = canvasTex(128, (x, s) => {
  const g = x.createRadialGradient(s / 2, s / 2, 0, s / 2, s / 2, s / 2);
  g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(0.25, 'rgba(255,255,255,.55)'); g.addColorStop(1, 'rgba(255,255,255,0)');
  x.fillStyle = g; x.fillRect(0, 0, s, s);
});

// Bluetooth 3D badge
function makeBluetooth() {
  const grp = new THREE.Group();
  const shape = new THREE.Shape(); const w = 3.2, h = 4.4, r = 1.1;
  shape.moveTo(-w / 2 + r, -h / 2); shape.lineTo(w / 2 - r, -h / 2); shape.quadraticCurveTo(w / 2, -h / 2, w / 2, -h / 2 + r);
  shape.lineTo(w / 2, h / 2 - r); shape.quadraticCurveTo(w / 2, h / 2, w / 2 - r, h / 2); shape.lineTo(-w / 2 + r, h / 2);
  shape.quadraticCurveTo(-w / 2, h / 2, -w / 2, h / 2 - r); shape.lineTo(-w / 2, -h / 2 + r); shape.quadraticCurveTo(-w / 2, -h / 2, -w / 2 + r, -h / 2);
  const bg = new THREE.ExtrudeGeometry(shape, { depth: 0.7, bevelEnabled: true, bevelThickness: 0.18, bevelSize: 0.16, bevelSegments: 4, curveSegments: 16 });
  bg.translate(0, 0, -0.35);
  const badgeM = [new THREE.MeshStandardMaterial({ color: 0xff6a1a, emissive: 0xff3a00, emissiveIntensity: 0.55, roughness: 0.3, metalness: 0.2, transparent: true }),
                  new THREE.MeshStandardMaterial({ color: 0xa02a00, emissive: 0x501000, emissiveIntensity: 0.5, roughness: 0.4, transparent: true })];
  grp.add(new THREE.Mesh(bg, badgeM));
  const runeM = new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: 0xffffff, emissiveIntensity: 1.1, roughness: 0.3, transparent: true });
  const P = [[-0.8, -0.75], [0.8, 0.75], [0, 1.55], [0, -1.55], [0.8, -0.75], [-0.8, 0.75]].map(([x, y]) => new THREE.Vector2(x, y));
  const th = 0.32;
  for (let i = 0; i < P.length - 1; i++) {
    const a = P[i], b = P[i + 1], d = b.clone().sub(a);
    const box = new THREE.Mesh(new THREE.BoxGeometry(d.length() + th * 0.5, th, 0.4), runeM);
    box.position.set((a.x + b.x) / 2, (a.y + b.y) / 2, 0.75); box.rotation.z = Math.atan2(d.y, d.x);
    grp.add(box);
  }
  for (const p of P.slice(1, 5)) { const s = new THREE.Mesh(new THREE.SphereGeometry(th * 0.62, 12, 8), runeM); s.position.set(p.x, p.y, 0.75); grp.add(s); }
  scene.add(grp);
  const o = { g: grp, mats: [...badgeM, runeM] };
  o.reset = () => { grp.visible = false; };
  o.set = (op, glow = 1) => { for (const m of o.mats) m.opacity = op; runeM.emissiveIntensity = 1.1 * glow; badgeM[0].emissiveIntensity = 0.55 * glow; };
  ALL.push(o);
  return o;
}
function makeWaves() {
  const arcs = [];
  for (let side = 0; side < 2; side++) for (let i = 0; i < 3; i++) {
    const m = new THREE.MeshBasicMaterial({ color: 0xffb070, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, toneMapped: false });
    const mesh = new THREE.Mesh(new THREE.TorusGeometry(1, 0.06, 8, 48, Math.PI * 0.55), m);
    mesh.rotation.z = side ? Math.PI - Math.PI * 0.275 : -Math.PI * 0.275;
    arcs.push({ mesh, m, i, side });
  }
  const grp = new THREE.Group(); arcs.forEach(a => grp.add(a.mesh)); scene.add(grp);
  const o = { g: grp, arcs }; o.reset = () => { grp.visible = false; }; ALL.push(o); return o;
}

// Lollipop
function makeLollipop() {
  const grp = new THREE.Group();
  const swirl = canvasTex(256, (x, s) => {
    const img = x.createImageData(s, s);
    for (let j = 0; j < s; j++) for (let i = 0; i < s; i++) {
      const dx = i - s / 2, dy = j - s / 2, r = Math.hypot(dx, dy) / (s / 2), a = Math.atan2(dy, dx);
      const v = fract((a / (Math.PI * 2)) * 3 + r * 2.2);
      const c = v < 0.33 ? [255, 40, 60] : v < 0.66 ? [255, 250, 245] : [255, 150, 30];
      const k = (j * s + i) * 4; const sh = 0.75 + 0.25 * (1 - r);
      img.data[k] = c[0] * sh; img.data[k + 1] = c[1] * sh; img.data[k + 2] = c[2] * sh; img.data[k + 3] = 255;
    }
    x.putImageData(img, 0, 0);
  });
  const cap = new THREE.MeshStandardMaterial({ map: swirl, roughness: 0.18, metalness: 0.05, emissive: 0xffffff, emissiveMap: swirl, emissiveIntensity: 0.35, transparent: true });
  const side = new THREE.MeshStandardMaterial({ color: 0xff5a40, roughness: 0.2, emissive: 0xff2a10, emissiveIntensity: 0.3, transparent: true });
  const disc = new THREE.Mesh(new THREE.CylinderGeometry(2.1, 2.1, 0.7, 64, 1), [side, cap, cap]);
  disc.rotation.x = Math.PI / 2; grp.add(disc);
  const stickM = new THREE.MeshStandardMaterial({ color: 0xfff0e0, roughness: 0.5, emissive: 0x403020, transparent: true });
  const stick = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.16, 4.6, 16), stickM);
  stick.position.y = -4.2; grp.add(stick);
  scene.add(grp);
  const o = { g: grp, mats: [cap, side, stickM] }; o.reset = () => { grp.visible = false; };
  o.set = op => o.mats.forEach(m => m.opacity = op);
  ALL.push(o); return o;
}

// ───────────────────────── particles ─────────────────────────
const PART_VS = `
  attribute vec3 dir; attribute vec4 rnd;
  uniform float uT, uSpeed, uLife, uGrav, uSize, uPix, uDrag, uMode;
  uniform vec3 uOrigin;
  varying float vA; varying float vHot; varying float vTw;
  void main(){
    vec3 p;
    float a;
    if (uMode < 0.5) {             // burst
      float lt = uLife * (0.45 + 0.55 * rnd.y);
      float t = min(uT, lt);
      float sp = uSpeed * (0.25 + 0.75 * rnd.x);
      p = uOrigin + dir * sp * (1.0 - exp(-uDrag * t)) / uDrag + vec3(0.0, -uGrav * t * t, 0.0);
      float k = clamp(uT / lt, 0.0, 1.0);
      a = (1.0 - k) * (1.0 - k) * step(uT, lt);
      vHot = 1.0 - k;
    } else {                        // ambient embers / dust
      p = dir;
      p.y = mod(dir.y + uT * (0.3 + rnd.x * 1.1) + 20.0, 40.0) - 20.0;
      p.x += sin(uT * (0.4 + rnd.x) + rnd.y * 6.28) * 1.5;
      p.z += cos(uT * 0.3 + rnd.y * 6.28) * 1.0;
      a = 0.35 + 0.65 * (0.5 + 0.5 * sin(uT * (1.5 + rnd.x * 4.0) + rnd.y * 30.0));
      vHot = rnd.w * 0.6;
    }
    vec4 mv = modelViewMatrix * vec4(p, 1.0);
    gl_Position = projectionMatrix * mv;
    gl_PointSize = max(1.0, uPix * uSize * (0.4 + rnd.z * 1.2) / -mv.z);
    vA = a;
  }`;
const PART_FS = `
  uniform vec3 uColor; uniform float uAmp;
  varying float vA; varying float vHot;
  void main(){
    float d = length(gl_PointCoord - 0.5);
    float s = smoothstep(0.5, 0.0, d);
    s = s * s;
    vec3 c = mix(uColor, vec3(1.0, 0.95, 0.85), vHot * 0.7);
    gl_FragColor = vec4(c * uAmp, s * vA);
  }`;
function partMat(color, extra = {}) {
  return new THREE.ShaderMaterial({
    vertexShader: PART_VS, fragmentShader: PART_FS, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    uniforms: { uT: { value: 0 }, uSpeed: { value: 10 }, uLife: { value: 1 }, uGrav: { value: 2 }, uSize: { value: 0.12 }, uPix: { value: PIX },
      uDrag: { value: 3 }, uMode: { value: 0 }, uOrigin: { value: new THREE.Vector3() }, uColor: { value: new THREE.Color(color) }, uAmp: { value: 1 }, ...extra },
  });
}
function rndAttrs(n, seed, ambient = false) {
  const dir = new Float32Array(n * 3), rnd = new Float32Array(n * 4);
  for (let i = 0; i < n; i++) {
    const h = k => hash(seed * 1000 + i * 13.37 + k);
    if (ambient) { dir[i * 3] = (h(1) - .5) * 70; dir[i * 3 + 1] = (h(2) - .5) * 40; dir[i * 3 + 2] = -45 + h(3) * 52; }
    else {
      const u = h(1) * 2 - 1, th = h(2) * Math.PI * 2, s = Math.sqrt(1 - u * u);
      dir[i * 3] = s * Math.cos(th); dir[i * 3 + 1] = s * Math.sin(th) * 0.9 + 0.15; dir[i * 3 + 2] = u * 0.8;
    }
    for (let k = 0; k < 4; k++) rnd[i * 4 + k] = h(10 + k);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(dir.slice(), 3));
  g.setAttribute('dir', new THREE.BufferAttribute(dir, 3));
  g.setAttribute('rnd', new THREE.BufferAttribute(rnd, 4));
  return g;
}
const ambient = new THREE.Points(rndAttrs(1400, 7, true), partMat(0xff7a2a, { uMode: { value: 1 }, uSize: { value: 0.09 } }));
ambient.frustumCulled = false; scene.add(ambient);

const BURSTS = [];
function burst(t0, x, y, z, o = {}) {
  const n = o.n ?? 160;
  const mat = partMat(o.color ?? 0xff7a20, { uSize: { value: o.size ?? 0.16 } });
  Object.assign(mat.uniforms, {});
  mat.uniforms.uSpeed.value = o.speed ?? 22; mat.uniforms.uLife.value = o.life ?? 1.1; mat.uniforms.uGrav.value = o.grav ?? 4;
  mat.uniforms.uDrag.value = o.drag ?? 2.6; mat.uniforms.uOrigin.value.set(x, y, z);
  const pts = new THREE.Points(rndAttrs(n, t0 * 10 + x), mat); pts.frustumCulled = false; scene.add(pts);
  BURSTS.push({ t0, pts, mat, life: o.life ?? 1.1 });
}
const RINGS = [];
const ringGeo = new THREE.RingGeometry(0.92, 1, 96);
function ring(t0, x, y, z, o = {}) {
  const m = new THREE.MeshBasicMaterial({ color: o.color ?? 0xffa060, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, toneMapped: false, side: THREE.DoubleSide });
  const mesh = new THREE.Mesh(ringGeo, m); mesh.position.set(x, y, z); scene.add(mesh);
  RINGS.push({ t0, mesh, m, r: o.r ?? 18, life: o.life ?? 0.55, op: o.op ?? 0.9 });
}

// smoke layers (procedural fbm texture)
const smokeTex = (() => {
  const s = 256, c = document.createElement('canvas'); c.width = c.height = s; const x = c.getContext('2d'); const img = x.createImageData(s, s);
  const n2 = (px, py) => { const ix = Math.floor(px), iy = Math.floor(py), fx = px - ix, fy = py - iy; const h = (a, b) => hash(((a % 16) + 16) % 16 * 57 + (((b % 16) + 16) % 16) * 131);
    const u = fx * fx * (3 - 2 * fx), v = fy * fy * (3 - 2 * fy);
    return lerp(lerp(h(ix, iy), h(ix + 1, iy), u), lerp(h(ix, iy + 1), h(ix + 1, iy + 1), u), v); };
  for (let j = 0; j < s; j++) for (let i = 0; i < s; i++) {
    let v = 0, a = 0.5, f = 16 / s;
    for (let o = 0; o < 5; o++) { v += a * n2(i * f * (1 << o), j * f * (1 << o)); a *= 0.5; }
    const r = Math.hypot(i - s / 2, j - s / 2) / (s / 2);
    const m = Math.max(0, v - 0.42) * 2.4 * Math.max(0, 1 - r * r);
    const k = (j * s + i) * 4; img.data[k] = 255; img.data[k + 1] = 255; img.data[k + 2] = 255; img.data[k + 3] = clamp(m * 255, 0, 255);
  }
  x.putImageData(img, 0, 0); const t = new THREE.CanvasTexture(c); return t;
})();
const smokes = [];
for (let i = 0; i < 7; i++) {
  const m = new THREE.MeshBasicMaterial({ map: smokeTex, color: i % 2 ? 0xff5a1a : 0xb8401a, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, opacity: 0.12 });
  const mesh = new THREE.Mesh(new THREE.PlaneGeometry(60, 60), m);
  scene.add(mesh); smokes.push({ mesh, m, i });
}

// anamorphic light streak
const streakMat = new THREE.MeshBasicMaterial({ map: glowTex, color: 0xff9a50, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false });
const streak = M(new THREE.Mesh(new THREE.PlaneGeometry(1, 1), streakMat));

// ───────────────────────── FX accumulation ─────────────────────────
const HITS = [];
function hit(t0, fx, tau = 0.25) { HITS.push({ t0, fx, tau }); }
const KICKS = [];
for (let i = 0; ; i++) { const t = timing.beatPhase + i * BEAT; if (t >= timing.drop - 0.01 && t <= 90.5) KICKS.push({ t, down: ((i - 143) % 4 + 4) % 4 === 0 }); if (t > 91) break; }
function kickEnv(T) { let v = 0; for (const k of KICKS) { if (k.t > T) break; v = Math.max(v, decay(T, k.t, 0.11) * (k.down ? 1 : 0.65)); } return v; }

// ───────────────────────── post processing ─────────────────────────
const MSAA = +(Q.get('msaa') ?? (SUB > 1 ? 0 : 4));
const rt = new THREE.WebGLRenderTarget(WIDTH, HEIGHT, { type: THREE.HalfFloatType, samples: MSAA });
const composer = new EffectComposer(renderer, rt);
composer.setPixelRatio(1); composer.setSize(WIDTH, HEIGHT);
composer.addPass(new RenderPass(scene, camera));
const bloom = new UnrealBloomPass(new THREE.Vector2(WIDTH, HEIGHT), 0.5, 0.42, 0.88);
if (Q.get('bloom') !== '0') composer.addPass(bloom);
composer.addPass(new OutputPass());
const VHS = new ShaderPass({
  uniforms: { tDiffuse: { value: null }, uFrame: { value: 0 }, uRGB: { value: 0 }, uGlitch: { value: 0 }, uBlocks: { value: 0 }, uFlash: { value: 0 },
    uCRT: { value: 0 }, uScan: { value: 0.12 }, uGrain: { value: 0.05 }, uSat: { value: 1 }, uDark: { value: 0 }, uAspect: { value: WIDTH / HEIGHT }, uJerk: { value: 0 } },
  vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
  fragmentShader: `
    uniform sampler2D tDiffuse; uniform float uFrame, uRGB, uGlitch, uBlocks, uFlash, uCRT, uScan, uGrain, uSat, uDark, uAspect, uJerk;
    varying vec2 vUv;
    float h(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
    vec3 samp(vec2 uv){ if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) return vec3(0.0); return texture2D(tDiffuse, uv).rgb; }
    void main(){
      vec2 uv = vUv;
      float crtLine = 0.0;
      if (uCRT > 0.0) {                       // old TV switching off
        float sy = max(1.0 - uCRT * 1.7, 0.003);
        float sx = uCRT > 0.55 ? max(1.0 - (uCRT - 0.55) * 2.4, 0.002) : 1.0;
        uv = (uv - 0.5) / vec2(sx, sy) + 0.5;
        crtLine = smoothstep(0.0, 0.6, uCRT);
      }
      uv.y += uJerk;
      float f = uFrame;
      // horizontal tearing slices
      float bands = mix(10.0, 46.0, h(vec2(f, 3.1)));
      float band = floor(uv.y * bands);
      float r = h(vec2(band, f));
      if (r < uGlitch * 0.55) uv.x += (h(vec2(band, f + 7.0)) - 0.5) * 0.22 * uGlitch;
      // digital block breakup
      vec2 blk = floor(uv * vec2(24.0, 13.5));
      float rb = h(blk + vec2(floor(f / 2.0), 9.0));
      bool hole = false;
      if (rb < uBlocks * 0.3) { uv += (vec2(h(blk + 3.0), h(blk + 5.0)) - 0.5) * 0.12 * uBlocks; }
      if (rb > 1.0 - uBlocks * 0.08) hole = true;
      // RGB split (radial-ish + horizontal)
      vec2 c = uv - 0.5;
      vec2 off = vec2(0.006 + length(c) * 0.01, 0.0) * uRGB + c * 0.004 * uRGB;
      vec3 col = vec3(samp(uv + off).r, samp(uv).g, samp(uv - off).b);
      if (r < uGlitch * 0.12) col = mix(col, col.brg, 0.5);
      if (hole) col = (h(blk + f) > 0.5) ? vec3(0.0) : col.grb * 1.2;
      // saturation
      float l = dot(col, vec3(0.299, 0.587, 0.114));
      col = mix(vec3(l), col, uSat);
      // scanlines, grain, vignette
      col *= 1.0 - uScan * (0.5 + 0.5 * sin(vUv.y * 1080.0 * 3.14159));
      col += (h(vUv * 1000.0 + f) - 0.5) * uGrain;
      vec2 v = (vUv - 0.5) * vec2(uAspect, 1.0);
      col *= 1.0 - smoothstep(0.55, 1.25, length(v)) * 0.75;
      col = mix(col, vec3(1.0, 0.97, 0.92), uFlash);
      if (uCRT > 0.0) col += vec3(1.0, 0.95, 0.9) * crtLine * 1.4 * step(abs(uv.y - 0.5), 0.5) * step(abs(uv.x - 0.5), 0.5);
      col *= 1.0 - uDark;
      gl_FragColor = vec4(max(col, 0.0), 1.0);
    }`,
});
composer.addPass(VHS);
composer.renderToScreen = false;

const accRT = new THREE.WebGLRenderTarget(WIDTH, HEIGHT, { type: THREE.HalfFloatType });
const accQuad = new FullScreenQuad(new THREE.ShaderMaterial({
  uniforms: { t: { value: null }, k: { value: 1 } }, transparent: true, blending: THREE.CustomBlending,
  blendSrc: THREE.OneFactor, blendDst: THREE.OneFactor, blendEquation: THREE.AddEquation, depthTest: false, depthWrite: false,
  vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }`,
  fragmentShader: `uniform sampler2D t; uniform float k; varying vec2 vUv; void main(){ gl_FragColor = vec4(texture2D(t, vUv).rgb * k, 1.0); }`,
}));
const blitQuad = new FullScreenQuad(new THREE.ShaderMaterial({
  uniforms: { t: { value: accRT.texture } }, depthTest: false, depthWrite: false,
  vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }`,
  fragmentShader: `uniform sampler2D t; varying vec2 vUv; void main(){ gl_FragColor = vec4(texture2D(t, vUv).rgb, 1.0); }`,
}));

// ═════════════════════════ SCENES ═════════════════════════
// Layout reference: camera at z=30, fov 40 → the z=0 plane shows x∈[-19.4,19.4], y∈[-10.9,10.9].
let fx, cam;

// ── Intro (54.80 → 56.93): darkness, embers, a slow light line builds tension
function intro(T) {
  if (T > 57.6) return;
  const p = ap(T, CLIP0, 2.1);
  fx.amb = lerp(0.15, 0.6, p);
  fx.smoke = lerp(0.2, 0.7, p);
  cam.z += lerp(4, 0, oCubic(ap(T, CLIP0, 2.6)));
  const s = ap(T, 55.6, 1.33);
  if (T < 57.2) {
    showStreak(0, 0, -6, lerp(0, 46, oCubic(s)), lerp(0.05, 0.5, s), sat(s * 3) * (1 - ap(T, 56.95, 0.25)) * 0.8);
  }
  fx.dark = 1 - oCubic(ap(T, CLIP0, 0.6));
}
function showStreak(x, y, z, w, h, op) { const g = streak.g; g.visible = op > 0.002; g.position.set(x, y, z); g.scale.set(w, h, 1); streakMat.opacity = op; }

// ── Scene 1: «Ты слушаешь ху*ню»
const S1 = { ty: W('ТЫ', 'm9', 'white', 4.2, 0.3), sl: W('СЛУШАЕШЬ', 'ub', 'white', 25, 0.34), hu: W('ХУ*НЮ', 'ub', 'orange', 31, 0.5),
  e1: E('1f3a7', 3.4), e2: E('1f50a', 3.0) };
{
  const t = WT[0][2];
  hit(t, { flash: 0.55, rgb: 1.6, glitch: 0.9, shake: 1.4, zoom: 2.5, bloom: 0.8 }, 0.22);
  hit(t, { blocks: 0.6 }, 0.08);
  burst(t, 0, -2.6, 1, { n: 320, speed: 34, life: 1.4, size: 0.2 });
  burst(t, 0, -2.6, 1, { n: 120, speed: 14, life: 0.9, size: 0.35, color: 0xffd0a0 });
  ring(t, 0, -2.6, 0, { r: 30, life: 0.6 });
  hit(58.9, { glitch: 0.6, rgb: 1.0 }, 0.12);
}
function scene1(T) {
  if (!inW(T, 56.8, 59.15)) return;
  const [tTy, tSl, tHu] = WT[0];
  const dE = oExpo(ap(T, tHu - 0.03, 0.22));
  const ex = ap(T, 58.86, 0.26);
  const kk = kickEnv(T);
  if (T >= tTy - 0.08) {
    const p = oCubic(ap(T, tTy - 0.08, 0.4));
    show(S1.ty, { y: lerp(2.9, 7.4, dE), z: lerp(-24, 0, p) - dE * 2, op: p, ry: (1 - p) * 0.8 });
    scatter(S1.ty, ex, 2);
  }
  if (T >= tSl - 0.08) {
    show(S1.sl, { y: lerp(-0.4, 3.6, dE), z: -dE * 2.5, s: lerp(1, 0.78, dE), ry: Math.sin(T * 1.3) * 0.06 * (1 - dE) });
    lettersIn(S1.sl, T, tSl - 0.08, 0.05, 0.35, (l, i, p) => {
      const e = oCubic(p); l.op = e; l.em = lerp(0, 1, sat(p * 1.5)); l.p.position.z += (1 - e) * -3; l.p.rotation.y = (1 - e) * 1.2;
    });
    scatter(S1.sl, ex, 3);
  }
  if (T >= tHu - 0.03) {
    const p = ap(T, tHu - 0.03, 0.2);
    show(S1.hu, { y: -3.0, z: lerp(28, 0, oExpo(p)), rz: (1 - oExpo(p)) * -0.25, s: 1 + 0.06 * kk, em: 1 + decay(T, tHu, 0.3) * 1.5 });
    S1.hu.L.forEach((l, i) => {      // letters tremble and kick outward with the bass
      const c = (i - (S1.hu.L.length - 1) / 2);
      lOff(S1.hu, i, c * 0.55 * kk + vnoise(T * 24 + i * 9) * 0.12, vnoise(T * 21 + i * 4) * 0.14 + kk * 0.35 * (i % 2 ? 1 : -1), 0);
      l.p.rotation.z += vnoise(T * 17 + i * 3) * 0.04 + kk * 0.06 * c;
    });
    scatter(S1.hu, ex, 4, 18);
  }
  popE(S1.e1, T, tSl + 0.05, { x: -14.6, y: 6.6, z: 1, s: 1 }, 58.86);
  popE(S1.e2, T, tHu + 0.08, { x: 14.6, y: 7.0, z: 1, s: 1, rz: -0.2 }, 58.86);
  fx.amb = lerp(0.6, 1, dE);
}

// ── Scene 2: «Детка, да, дай мне подключиться на Bluetooth»
const S2 = { de: W('ДЕТКА,', 'ub', 'white', 17), da: W('ДА,', 'ub', 'orange', 5.4), dai: W('ДАЙ', 'm9', 'white', 5.6), mne: W('МНЕ', 'm9', 'white', 5.6),
  pod: W('ПОДКЛЮЧИТЬСЯ', 'ub', 'orange', 23.5, 0.3), na: W('НА', 'm9', 'white', 2.6), bt: W('BLUETOOTH', 'ub', 'white', 19.5, 0.36),
  cg: W('CONNECTING...', 'm7', 'dim', 7.2, 0.08), cd: W('CONNECTED', 'm7', 'orange', 6.0, 0.08),
  icon: makeBluetooth(), waves: makeWaves(), e1: E('1f48b', 3), e2: E('1f4f1', 3.2),
  bar: M(new THREE.Mesh(new THREE.BoxGeometry(1, 1, 0.2), new THREE.MeshBasicMaterial({ color: 0xff7a20, toneMapped: false, transparent: true }))),
  barBg: M(new THREE.Mesh(new THREE.BoxGeometry(1, 1, 0.1), new THREE.MeshBasicMaterial({ color: 0x3a1a0a, transparent: true }))),
  ghosts: [0, 1, 2, 3, 4].map(i => W(i % 2 ? 'BLUETOOTH' : 'CONNECT', 'm7', 'ghost', 9 + i * 2, 0.1)) };
{
  const [tDe, tDa, , , tPod, , tBt] = WT[1];
  hit(tDa, { zoom: 0.8, rgb: 0.3 }, 0.15);
  hit(tPod, { glitch: 0.35, rgb: 0.6 }, 0.12);
  hit(tBt, { zoom: 1.4, shake: 0.6, rgb: 0.5 }, 0.2);
  hit(61.62, { flash: 0.28, bloom: 0.7, zoom: 1.6, shake: 0.5 }, 0.25);
  burst(61.62, -11.6, -0.3, 1, { n: 260, speed: 26, life: 1.2, color: 0xffb070 });
  ring(61.62, -11.6, -0.3, 0.5, { r: 22, life: 0.7, color: 0xffd0a0 });
  ring(61.72, -11.6, -0.3, 0.5, { r: 14, life: 0.6 });
  burst(tBt, 15, -3.2, 0, { n: 90, speed: 16, life: 0.7, size: 0.12 });
  hit(62.2, { glitch: 0.4, rgb: 0.8 }, 0.1);
}
function scene2(T) {
  if (!inW(T, 59.05, 62.42)) return;
  const [tDe, tDa, tDai, tMne, tPod, tNa, tBt] = WT[1];
  const A = ap(T, tPod - 0.22, 0.24);                  // phase A → B
  const ex = oExpo(ap(T, 62.14, 0.27));                 // fly-through exit toward camera
  const exO = { z: ex * 34 };
  // phase A
  if (T < tPod + 0.05) {
    const up = iCubic(A);
    const p = ioCubic(ap(T, tDe - 0.05, 0.55));
    show(S2.de, { x: -2.4, y: 3.4 + up * 9, s: lerp(0.35, 1, p), op: sat(p * 2) * (1 - up), rz: (1 - p) * 0.12, sy: 1 + up * 0.5 });
    if (T >= tDa) { const q = ap(T, tDa, 0.4); show(S2.da, { x: 10.6, y: 3.4 + up * 9, s: oElastic(q), op: 1 - up, rz: (1 - oCubic(q)) * 0.5 }); }
    [[S2.dai, tDai, -3.4], [S2.mne, tMne, 3.4]].forEach(([w, t, x]) => {
      if (T < t - 0.02) return; const q = ap(T, t - 0.02, 0.32);
      show(w, { x, y: -2.6 + (1 - oBack(q)) * 4 + up * 9, op: sat(q * 3) * (1 - up), rx: (1 - oCubic(q)) * -1.2 });
    });
    popE(S2.e1, T, tDe + 0.1, { x: -14.8, y: 7.3, s: 1, rz: 0.2 }, tPod - 0.22);
  }
  // phase B
  if (T >= tPod - 0.04) {
    // ПОДКЛЮЧИТЬСЯ: letters "connect" one by one, flickering on
    show(S2.pod, { x: 4.6, y: 3.0, ...exO, ry: -0.12 + Math.sin(T * 1.5) * 0.04, op: 1 - ex });
    lettersIn(S2.pod, T, tPod - 0.04, 0.034, 0.16, (l, i, p) => {
      const fl = p >= 1 ? 1 : (hash(frameOf(T) * 3 + i) > 0.45 ? p : 0.08);
      l.op = p > 0 ? fl : 0; l.p.position.y += (1 - oCubic(p)) * 0.4;
      l.em = 1 + decay(T, tPod - 0.04 + i * 0.034, 0.12) * 2;
    });
    // Bluetooth badge
    const ip = ap(T, tPod - 0.04, 0.5);
    const flashE = decay(T, 61.62, 0.25);
    const ic = S2.icon; ic.g.visible = true;
    ic.g.position.set(-11.6, -0.3, ex * 34);
    const sc = 1.55 * oBack(ip, 2.2) * (1 + 0.25 * flashE + 0.04 * kickEnv(T));
    ic.g.scale.setScalar(Math.max(sc, 0.001));
    ic.g.rotation.set(Math.sin(T * 1.7) * 0.15, (1 - oCubic(ip)) * Math.PI * 2 + Math.sin(T * 1.2) * 0.35, 0);
    ic.set(sat(ip * 3) * (1 - ex), 0.55 + flashE * 1.1 + 0.15 * Math.sin(T * 20) * (T < 61.6 ? 1 : 0));
    // signal waves pulse out on the 8th notes
    const wv = S2.waves; wv.g.visible = ip > 0.3; wv.g.position.set(-11.6, -0.3, 0.6 + ex * 34);
    for (const a of wv.arcs) {
      const ph = fract((T - tPod) / (BEAT / 2) * 0.5 - a.i / 3);
      const r = 2.6 + ph * 5.2;
      a.mesh.scale.setScalar(r * 1.55);
      a.m.opacity = Math.sin(ph * Math.PI) * 0.5 * sat(ip * 2) * (1 - ex) * (T > 61.62 ? 1 + flashE : 1);
    }
    // НА + BLUETOOTH
    if (T >= tNa - 0.02) { const q = ap(T, tNa - 0.02, 0.25); show(S2.na, { x: -6.6, y: -2.55, ...exO, s: oBack(q), op: sat(q * 3) * (1 - ex) }); }
    if (T >= tBt - 0.03) {
      const q = oExpo(ap(T, tBt - 0.03, 0.22));
      show(S2.bt, { x: lerp(34, 5.7, q), y: -2.55, ...exO, sx: 1 + (1 - q) * 0.6, ry: -0.12, op: 1 - ex, em: 1 + decay(T, tBt, 0.25) * 1.5 });
      S2.bt.L.forEach((l, i) => { l.p.position.y += Math.sin(T * 9 - i * 0.7) * 0.03 * sat((T - tBt) * 2); });
    }
    // HUD progress bar CONNECTING... → CONNECTED
    const hp = ap(T, tPod, 61.6 - tPod);
    if (T < 61.62) {
      show(S2.cg, { x: -1.0, y: -6.6, ...exO, op: 0.7 * sat(ip * 2) * (0.75 + 0.25 * Math.sin(T * 25)) });
    } else { const q = ap(T, 61.62, 0.25); show(S2.cd, { x: -0.6, y: -6.6, ...exO, s: oBack(q), op: 1 - ex, em: 1.4 }); }
    const bw = 13;
    S2.barBg.g.visible = true; S2.barBg.g.position.set(10.6, -6.6, ex * 34); S2.barBg.g.scale.set(bw, 0.3, 1); S2.barBg.g.material.opacity = sat(ip * 2) * (1 - ex);
    S2.bar.g.visible = hp > 0; S2.bar.g.scale.set(Math.max(hp * bw, 0.001), 0.3, 1); S2.bar.g.position.set(10.6 - bw / 2 + hp * bw / 2, -6.6, 0.12 + ex * 34);
    S2.bar.g.material.opacity = 1 - ex; S2.bar.g.material.color.setHex(T > 61.62 ? 0xffd0a0 : 0xff7a20);
    // CONNECT ghosts drifting in the far background
    S2.ghosts.forEach((g, i) => {
      const y = [-9, 8.5, -4, 10.5, 0][i] * 1.5, d = i % 2 ? 1 : -1;
      show(g, { x: d * (-20 + ((T - tPod) * (3 + i)) % 40), y: y * 1.3, z: -45 - i * 6 + ex * 34, op: 0.22 * sat(ip * 2) * (1 - ex) });
    });
    popE(S2.e2, T, tDai + 0.05, { x: 15.6, y: 7.6, s: 1, rz: -0.25 }, 62.1);
    cam.ry += Math.sin(T * 0.9) * 0.02;
  }
}

// ── Scene 3: «Я реальный белый — покажу, какой на вкус»
const S3 = { ya: W('Я', 'm9', 'white', 2.2), re: W('РЕАЛЬНЫЙ', 'ub', 'white', 32, 0.62), be: W('БЕЛЫЙ', 'ub', 'hot', 20, 0.5),
  po: W('ПОКАЖУ,', 'ub', 'orange', 21), ka: W('КАКОЙ', 'm9', 'white', 10.5), na: W('НА', 'm9', 'white', 3.6), vk: W('ВКУС', 'ub', 'red', 17.5, 0.55),
  lolly: makeLollipop(), e1: E('2728', 3.4), e2: E('2728', 2.4), e3: E('1f36c', 3.6), e4: E('1f60b', 3.4) };
{
  const [tYa, tRe, tBe, tPo, tKa, tNa, tVk] = WT[2];
  hit(tYa, { zoom: 0.8 }, 0.12);
  hit(tRe, { shake: 0.8, zoom: 1.6, rgb: 0.5 }, 0.2);
  hit(tBe, { flash: 1.0, bloom: 0.8 }, 0.18);
  burst(tBe, 0, -3.6, 1, { n: 300, speed: 30, life: 1.3, color: 0xffffff, size: 0.18 });
  ring(tBe, 0, -3.6, 0, { r: 32, life: 0.6, color: 0xffffff, op: 0.5 });
  hit(tPo - 0.12, { glitch: 0.25, rgb: 0.8 }, 0.12);
  hit(tVk, { zoom: 1.4, shake: 0.6 }, 0.2);
  burst(tVk, 0, -4.4, 1, { n: 140, speed: 18, life: 1.0, color: 0xff4a60 });
  hit(65.4, { glitch: 0.4, rgb: 0.8 }, 0.12);
}
function scene3(T) {
  if (!inW(T, 62.3, 65.65)) return;
  const [tYa, tRe, tBe, tPo, tKa, tNa, tVk] = WT[2];
  const sw = ioCubic(ap(T, tPo - 0.2, 0.42));         // cube-turn transition A → B
  const ex = ap(T, 65.36, 0.26);
  // phase A — group drifts and turns away
  if (T < tPo + 0.3) {
    const drift = (T - tRe) * 0.25;
    const A = { x: -sw * 26, z: -sw * 10, ry: -sw * 1.4 + drift * 0.18 };
    if (T >= tYa - 0.03) { const q = ap(T, tYa - 0.03, 0.25); show(S3.ya, { x: -13.6 + A.x, y: 6.1, z: A.z, s: oBack(q), op: sat(q * 3), ry: A.ry }); }
    if (T >= tRe - 0.04) {
      const q = ap(T, tRe - 0.04, 0.42);
      show(S3.re, { x: A.x, y: 1.5 + drift * 0.6, z: lerp(-34, 0, oExpo(q)) + A.z, rx: (1 - oBack(q, 1.4)) * -1.25, ry: A.ry, op: sat(q * 2.5) });
    }
    if (T >= tBe - 0.02) {
      const q = ap(T, tBe - 0.02, 0.18);
      show(S3.be, { x: A.x * 1.1, y: -4.4 - drift * 0.5, z: A.z + lerp(6, 0, oExpo(q)), ry: A.ry, s: lerp(1.25, 1, oExpo(q)), em: 1 + decay(T, tBe, 0.45) * 4, op: sat(q * 4) });
      popE(S3.e1, T, tBe + 0.04, { x: 12.6 + A.x, y: -1.0, z: 1, s: 1 }, tPo - 0.2);
      popE(S3.e2, T, tBe + 0.12, { x: -13.0 + A.x, y: -7.6, z: 1, s: 1 }, tPo - 0.2);
    }
  }
  // phase B — enters from the right like the next face of a cube
  if (T >= tPo - 0.22) {
    const B = { x: (1 - sw) * 26, z: -(1 - sw) * 10, ry: (1 - sw) * 1.4 };
    const fall = iCubic(ex);
    const q = ap(T, tPo - 0.22, 0.42);
    show(S3.po, { x: 0.8 + B.x, y: 5.4 - fall * 14, z: B.z, ry: B.ry + Math.sin(T * 1.6) * 0.05, rx: fall * 1.5, op: 1 - ex, sx: 1 + (1 - oExpo(q)) * 0.5 });
    if (T >= tKa - 0.03) { const k = ap(T, tKa - 0.03, 0.28); show(S3.ka, { x: -5.6, y: 0.2 - fall * 14, s: oBack(k), op: sat(k * 3) * (1 - ex), rx: fall * 1.5 }); }
    if (T >= tNa - 0.03) { const k = ap(T, tNa - 0.03, 0.25); show(S3.na, { x: 3.6, y: 0.2 - fall * 14, s: oBack(k), op: sat(k * 3) * (1 - ex), rx: fall * 1.5 }); }
    if (T >= tVk - 0.03) {
      const k = ap(T, tVk - 0.03, 0.7);
      show(S3.vk, { x: -0.6, y: -5.2 - fall * 14, s: oElastic(k), op: sat(k * 6) * (1 - ex), rx: fall * 1.5 });
      S3.vk.L.forEach((l, i) => {           // jelly wobble ("tasty")
        const j = Math.sin((T - tVk) * 14 - i * 0.9) * decay(T, tVk + 0.2, 0.6);
        l.p.scale.set(1 + j * 0.15, 1 - j * 0.15, 1); l.p.rotation.z = j * 0.12;
      });
    }
    // lollipop
    if (T >= tKa - 0.05) {
      const k = ap(T, tKa - 0.05, 0.55), lo = S3.lolly;
      lo.g.visible = true; lo.g.position.set(13.4, 0.2 + Math.sin(T * 2.5) * 0.4 - fall * 14, 1);
      lo.g.scale.setScalar(Math.max(0.001, 0.95 * oElastic(k) * (1 + 0.12 * decay(T, tVk, 0.3))));
      lo.g.rotation.set(0.1, Math.sin((T - tKa) * 3) * 0.6, -0.3 + Math.sin(T * 3) * 0.12);
      lo.set(sat(k * 4) * (1 - ex));
    }
    popE(S3.e3, T, tVk + 0.05, { x: -14.2, y: -5.4, z: 1, s: 1 }, 65.36);
    popE(S3.e4, T, tKa + 0.1, { x: 14.6, y: 7.2, z: 1, s: 1 }, 65.36);
  }
  cam.y += lerp(-1.2, 0.5, ap(T, 62.3, 3.3)); cam.ly = 0;
}

// ── Scene 4: «Каким бы я ни был, точно знаю, — не пи*жу»
const S4 = { ka: W('КАКИМ', 'ub', 'white', 13), by: W('БЫ', 'm9', 'orange', 3.6), ya: W('Я', 'm9', 'white', 1.7), nb: W('НИ БЫЛ,', 'ub', 'orange', 10.5),
  to: W('ТОЧНО', 'ub', 'orange', 27, 0.55), zn: W('ЗНАЮ,', 'm9', 'white', 10), ne: W('НЕ', 'm9', 'white', 3.6), pi: W('ПИ*ЖУ', 'ub', 'red', 15.5, 0.5),
  e1: E('1f4af', 3.6) };
{
  const [tKa, tBy, tYa, tNb, tTo, tZn, tNe, tPi] = WT[3];
  [tKa, tBy, tYa, tNb].forEach((t, i) => hit(t - 0.02, { glitch: 0.35 + i * 0.05, rgb: 0.7 }, 0.08));
  hit(tTo + 0.2, { shake: 1.0, zoom: 2, rgb: 1.0, bloom: 0.6 }, 0.25);
  hit(tZn, { zoom: 0.6 }, 0.12);
  hit(tPi, { glitch: 1.0, rgb: 2.2, shake: 1.8, blocks: 0.7, flash: 0.2 }, 0.32);
  burst(tPi, 8.2, -4.2, 1, { n: 260, speed: 30, life: 1.1, color: 0xff3a20 });
  ring(tPi, 8.2, -4.2, 0, { r: 26, life: 0.5, color: 0xff6a40 });
  hit(68.7, { glitch: 0.3, rgb: 0.6 }, 0.1);
}
function glitchIn(w, T, t0, seed) {   // fragmented reveal: letters jump in from random offsets with RGB flicker
  lettersIn(w, T, t0, 0, 0.16, (l, i, p) => {
    const f = frameOf(T);
    if (p < 1) { lOff(w, i, (hash(f + i * 7 + seed) - .5) * 2.5 * (1 - p), (hash(f * 3 + i + seed) - .5) * 1.2 * (1 - p), 0); l.op = hash(f + i + seed * 3) > 0.35 ? 1 : 0.15; }
  });
}
function scene4(T) {
  if (!inW(T, 65.55, 68.88)) return;
  const [tKa, tBy, tYa, tNb, tTo, tZn, tNe, tPi] = WT[3];
  const boom = ap(T, tPi, 0.2), back = oBack(ap(T, tPi + 0.24, 0.32), 1.3);
  const expl = boom * (1 - back);                       // letters explode then reassemble
  const ex = ap(T, 68.6, 0.26);
  const explode = (w, seed) => {
    if (expl <= 0) return;
    w.L.forEach((l, i) => {
      const a = hash(seed * 13 + i) * Math.PI * 2, r = 4 + hash(seed + i * 5) * 7;
      lOff(w, i, Math.cos(a) * r * oCubic(expl), Math.sin(a) * r * oCubic(expl), (hash(i + seed) - 0.3) * 8 * expl);
      l.p.rotation.x += (hash(seed + i * 3) - .5) * 6 * expl; l.p.rotation.z += (hash(seed + i * 9) - .5) * 6 * expl;
    });
  };
  const exit = (w, seed) => w.L.forEach((l, i) => {
    const q = iCubic(sat((ex - hash(seed + i) * 0.3) / 0.7)); lOff(w, i, 0, -q * 16, 0); l.p.rotation.x += q * 2; l.op *= 1 - q;
  });
  const row = [[S4.ka, tKa, -8.6, 1], [S4.by, tBy, 0.6, 2], [S4.ya, tYa, 4.2, 3], [S4.nb, tNb, 11.6, 4]];
  for (const [w, t, x, seed] of row) {
    if (T < t - 0.03) continue;
    show(w, { x, y: 6.6, z: 0, ry: 0.06 });
    glitchIn(w, T, t - 0.03, seed); explode(w, seed); exit(w, seed);
  }
  // ТОЧНО rushes at the camera, overshoots, then settles
  if (T >= tTo - 0.06) {
    const q = ap(T, tTo - 0.06, 0.3), s2 = ap(T, tTo + 0.24, 0.32);
    const z = q < 1 ? lerp(-80, 19, iExpo(q) * 0.6 + q * 0.4) : lerp(19, 0, oCubic(s2));
    show(S4.to, { x: 0, y: 0.9, z, em: 1 + (1 - s2) * 1.2, ry: Math.sin(T * 1.4) * 0.05 });
    explode(S4.to, 5); exit(S4.to, 5);
  }
  if (T >= tZn - 0.03) { const q = ap(T, tZn - 0.03, 0.3); show(S4.zn, { x: -10.3, y: -4.4, s: oBack(q), op: sat(q * 3) }); explode(S4.zn, 6); exit(S4.zn, 6); }
  if (T >= tNe - 0.03) { const q = ap(T, tNe - 0.03, 0.25); show(S4.ne, { x: -2.7, y: -4.4, s: oBack(q), op: sat(q * 3) }); explode(S4.ne, 7); exit(S4.ne, 7); }
  if (T >= tPi - 0.03) {
    const q = ap(T, tPi - 0.03, 0.18);
    show(S4.pi, { x: 8.0, y: -4.4, z: lerp(10, 0, oExpo(q)), em: 1 + decay(T, tPi, 0.3) * 2 });
    S4.pi.L.forEach((l, i) => { lOff(S4.pi, i, vnoise(T * 30 + i * 5) * 0.25 * decay(T, tPi, 0.5), 0, 0); });
    explode(S4.pi, 8); exit(S4.pi, 8);
  }
  popE(S4.e1, T, tPi + 0.5, { x: 14.6, y: -8.6, z: 1, s: 1, rz: -0.2 }, 68.6);
  // speed lines while ТОЧНО flies in
  const sl = ap(T, tTo - 0.06, 0.3);
  if (sl > 0 && sl < 1) showStreak(0, 0.9, -5, 60, 0.6 + sl * 2, Math.sin(sl * Math.PI) * 0.8);
}

// ── Scene 5: «И где бы я ни был, я всегда» — camera travels between words in space
const S5 = { words: [
    [W('И', 'm9', 'white', 1.8), -14, 6, -4, 0.2], [W('ГДЕ', 'ub', 'orange', 8.5), -3.5, 9.5, -10, 0.25], [W('БЫ', 'm9', 'white', 4.4), 6.5, 3.8, -5, -0.2],
    [W('Я', 'ub', 'white', 3.4), 14, 9, -12, -0.3], [W('НИ', 'm9', 'orange', 4.6), 19, -1.5, -7, -0.35], [W('БЫЛ,', 'ub', 'white', 8.5), 10, -7, -3, -0.2],
    [W('Я', 'm9', 'orange', 2.0), -1, -9.5, -6, 0.1]],
  vs: W('ВСЕГДА', 'ub', 'orange', 27, 0.55), e1: E('1f30d', 4.2), e2: E('1f4cd', 2.8), e3: E('2708-fe0f', 3.0) };
{
  const t = WT[4];
  t.slice(0, 7).forEach((x, i) => hit(x, { zoom: 0.5 + (i % 2) * 0.3 }, 0.12));
  hit(t[7], { zoom: 1.6, shake: 0.7, rgb: 0.6, bloom: 0.6 }, 0.25);
  burst(t[7], 0, 0, 2, { n: 220, speed: 26, life: 1.2, color: 0xffa040 });
  ring(t[7], 0, 0, 1, { r: 24, life: 0.7 });
  hit(71.1, { glitch: 0.5, rgb: 1.0 }, 0.12);
}
function scene5(T) {
  if (!inW(T, 68.8, 71.3)) return;
  const t = WT[4];
  const tVs = t[7];
  const back = ioCubic(ap(T, tVs - 0.25, 0.4));       // camera returns to the master shot
  const fade = ap(T, tVs - 0.15, 0.3);
  // camera target follows the word being sung
  let idx = 0; for (let i = 0; i < 7; i++) if (T >= t[i] - 0.12) idx = i;
  const cur = S5.words[idx], prev = S5.words[Math.max(0, idx - 1)];
  const mv = ioCubic(ap(T, t[idx] - 0.12, 0.2));
  const tx = lerp(prev[1], cur[1], mv), ty = lerp(prev[2], cur[2], mv), tz = lerp(prev[3], cur[3], mv);
  cam.x = lerp(tx * 0.85, 0, back); cam.y = lerp(ty * 0.85, 0, back); cam.z = lerp(tz + 21, 30, back);
  cam.lx = lerp(tx, 0, back); cam.ly = lerp(ty, 0, back); cam.lz = lerp(tz, 0, back);
  cam.roll += lerp(Math.sin(T * 2) * 0.05, 0, back);
  S5.words.forEach(([w, x, y, z, ry], i) => {
    if (T < t[i] - 0.03) return;
    const q = ap(T, t[i] - 0.03, 0.3);
    show(w, { x, y, z: z + (1 - oExpo(q)) * -8, ry: ry + (1 - oCubic(q)) * 1.5, op: sat(q * 3) * (1 - fade), s: oBack(q) });
  });
  popE(S5.e1, T, t[1] + 0.05, { x: -12, y: -3, z: -8, s: 1 }, tVs - 0.2);
  popE(S5.e2, T, t[1] + 0.08, { x: -3.5, y: 14.3, z: -10, s: 1 }, tVs - 0.2);
  if (T > t[2] && T < tVs) {
    const p = ap(T, t[2], tVs - t[2]);
    showE(S5.e3, { x: lerp(-24, 30, p), y: lerp(-4, 12, p) + Math.sin(p * 9) * 1.2, z: -14, s: 1.3, rz: -0.35, op: sat(p * 6) * (1 - fade) });
  }
  // ВСЕГДА — volumetric spin
  if (T >= tVs - 0.05) {
    const q = ap(T, tVs - 0.05, 0.7), out = iCubic(ap(T, 71.02, 0.26));
    show(S5.vs, { y: 0.3, z: 2, ry: (1 - oCubic(q)) * Math.PI * 2, s: lerp(0.4, 1, oCubic(q)) * (1 - out), rz: out * 1.5, em: 1 + decay(T, tVs, 0.4) });
    S5.vs.L.forEach((l, i) => {     // a second wave: each letter flips around X
      const r = ap(T, tVs + 0.35 + i * 0.05, 0.35);
      l.p.rotation.x = oCubic(r) * Math.PI * 2; l.p.position.y += Math.sin(r * Math.PI) * 0.25;
    });
  }
}

// ── Scene 6: «Ги-ги-ги-ги-гикаю, да» (the hook) + the repeat in the track
const GI_COL = ['white', 'orange', 'red', 'white', 'orange'];
const S6 = {
  gi: [0, 1, 2, 3].map(i => W('ГИ', 'ub', GI_COL[i], [9, 6.5, 11, 7.5][i], 0.55)),
  minis: Array.from({ length: 14 }, (_, i) => W('ГИ', i % 3 ? 'm9' : 'ub', ['orange', 'white', 'red'][i % 3], 2.2 + (i % 4) * 0.9, 0.3)),
  gk: W('ГИКАЮ,', 'ub', 'orange', 30.5, 0.62), da: W('ДА', 'ub', 'white', 9.5, 0.5),
  boom: [0, 1, 2, 3].map(() => E('1f4a5', 4)), nerd: E('1f913', 3.8), fire: E('1f525', 3.6),
  // part B
  ya: W('Я', 'ub', 'white', 5),
  tun: [0, 1, 2, 3, 4].map(i => W('ГИ', 'ub', GI_COL[(i + 1) % 5], 11, 0.5)),
  gk2: W('ГИКАЮ,', 'ub', 'white', 30, 0.62), da2: W('ДА', 'ub', 'orange', 11, 0.55),
  rows: [0, 1, 2, 3].map(i => W('ГИ ГИ ГИ ГИ ГИ ГИ ГИ ГИ ГИ ГИ', 'ub', 'ghost', 130, 0.2)),
  pe: ['1f913', '1f3ae', '1f47e', '26a1', '1f4bb', '1f525'].map(c => E(c, 3.4)),
  rings: Array.from({ length: 6 }, () => M(new THREE.Mesh(new THREE.TorusGeometry(9, 0.05, 6, 80), new THREE.MeshBasicMaterial({ color: 0xff7a30, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, toneMapped: false })))),
};
const GI_POS = [[-10.5, 4.2, 0.35], [10.2, 5.0, -0.4], [-6.0, -4.6, -0.2], [10.0, -4.4, 0.3]];
const GI_FROM = [[-30, 14], [30, 16], [-28, -16], [30, -14]];
{
  const h = WT[5];
  h.slice(0, 4).forEach((t, i) => {
    hit(t, { zoom: 1.6 + i * 0.4, shake: 0.6 + i * 0.25, rgb: 0.6 + i * 0.2, bloom: 0.4 }, 0.16);
    burst(t + 0.06, GI_POS[i][0], GI_POS[i][1], 1, { n: 110, speed: 20, life: 0.8, size: 0.15 });
    ring(t + 0.06, GI_POS[i][0], GI_POS[i][1], 0.5, { r: 14, life: 0.4 });
  });
  hit(h[4], { flash: 0.6, shake: 2.2, zoom: 3.5, rgb: 2.0, glitch: 0.6, bloom: 1.0 }, 0.3);
  burst(h[4], 0, 0.8, 2, { n: 420, speed: 40, life: 1.6, size: 0.22 });
  burst(h[4], 0, 0.8, 2, { n: 160, speed: 18, life: 1.0, size: 0.4, color: 0xffe0b0 });
  ring(h[4], 0, 0.8, 1, { r: 40, life: 0.7, color: 0xffd0a0 }); ring(h[4] + 0.1, 0, 0.8, 1, { r: 26, life: 0.6 });
  hit(h[4] + 0.19, { zoom: 1.2, shake: 0.6 }, 0.12); hit(h[4] + 0.41, { zoom: 1.2, shake: 0.6 }, 0.12);
  hit(h[5], { zoom: 2.0, shake: 1.2, rgb: 0.8, flash: 0.25 }, 0.22);
  burst(h[5], 0, -6.6, 1, { n: 160, speed: 22, life: 1.0, color: 0xffffff });
  hit(74.47, { glitch: 0.6, rgb: 1.2 }, 0.12);
  const b = WT[6];
  hit(b[0], { zoom: 0.8 }, 0.1);
  b.slice(1, 6).forEach((t, i) => { hit(t, { zoom: 1.4, rgb: 0.7, shake: 0.5 }, 0.14); });
  hit(b[6], { flash: 0.55, shake: 2.0, zoom: 3.2, rgb: 1.8, glitch: 0.5, bloom: 0.9 }, 0.3);
  burst(b[6], 0, 1, 2, { n: 400, speed: 40, life: 1.5, size: 0.22, color: 0xffffff });
  ring(b[6], 0, 1, 1, { r: 40, life: 0.7, color: 0xffffff });
  timing.lines[6].pulses.forEach((t, i) => {
    hit(t, { zoom: 1.6, shake: 0.7, rgb: 0.8, bloom: 0.5, flash: 0.1 }, 0.18);
    ring(t, 0, 1, 0.5, { r: 30, life: 0.5, color: i % 2 ? 0xffa060 : 0xffffff });
    burst(t, (i % 2 ? 1 : -1) * 13, i % 3 ? 7.4 : -7.6, 1, { n: 90, speed: 16, life: 0.8 });
  });
  hit(b[7], { flash: 0.5, shake: 1.8, zoom: 2.6, rgb: 1.2 }, 0.25);
  burst(b[7], 0, -4.6, 1, { n: 300, speed: 32, life: 1.2, color: 0xff8a30 });
  hit(80.74, { glitch: 1.0, rgb: 2.0, blocks: 0.5 }, 0.1);
}
function scene6(T) {
  if (inW(T, 71.2, 74.62)) scene6a(T);
  if (inW(T, 74.5, 80.82)) scene6b(T);
}
function scene6a(T) {
  const h = WT[5];
  const blast = ap(T, h[4], 0.32);
  const kk = kickEnv(T);
  S6.gi.forEach((w, i) => {
    if (T < h[i] - 0.06) return;
    const q = ap(T, h[i] - 0.06, 0.26);
    const [px, py, rz] = GI_POS[i], [fx0, fy0] = GI_FROM[i];
    let x = lerp(fx0, px, oBack(q, 1.3)), y = lerp(fy0, py, oBack(q, 1.3));
    // knocked by the next ГИ landing (collision), bouncing
    let jy = 0, jr = 0;
    for (let k = i + 1; k < 4; k++) { const d = decay(T, h[k], 0.22); jy += Math.sin((T - h[k]) * 26) * d * 1.3; jr += d * (k % 2 ? 0.35 : -0.35); x += (px - GI_POS[k][0]) * 0.08 * d; }
    const sq = decay(T, h[i] + 0.2, 0.12);           // squash on landing
    show(w, { x: x + Math.sin(T * 6 + i) * 0.2, y: y + jy + Math.sin(T * 5.3 + i * 2) * 0.25, z: 0, rz: rz * (1 - oCubic(q)) * 6 + rz * 0.3 + jr, sx: 1 + sq * 0.25, sy: 1 - sq * 0.2, s: 1 + kk * 0.05 });
    w.L.forEach((l, j) => { l.p.rotation.y = Math.sin(T * 7 + i + j) * 0.3; });
    if (blast > 0) scatter(w, blast, 10 + i, 30, 6);
  });
  // tiny ГИ copies tumbling in the background
  S6.minis.forEach((w, i) => {
    const t0 = h[i % 4] + 0.04;
    if (T < t0 || T > h[4] + 0.4) return;
    const dt = T - t0, a = hash(i * 7.7) * Math.PI * 2, v = 8 + hash(i) * 10;
    show(w, { x: GI_POS[i % 4][0] + Math.cos(a) * v * dt, y: GI_POS[i % 4][1] + Math.sin(a) * v * dt - 4 * dt * dt, z: -6 - hash(i * 3) * 14,
      rz: dt * (hash(i * 5) - .5) * 10, rx: dt * 3, op: sat(dt * 8) * (1 - ap(T, h[4], 0.3)) * 0.85 });
  });
  S6.boom.forEach((e, i) => { if (T >= h[i] + 0.05 && T < h[i] + 0.4) { const q = ap(T, h[i] + 0.05, 0.35); showE(e, { x: GI_POS[i][0] + (i % 2 ? -3 : 3), y: GI_POS[i][1] + 2.2, z: 1.5, s: oBack(sat(q * 2.5)) * (1 - q * 0.5), op: 1 - iCubic(q), rz: i }); } });
  // ГИКАЮ — giant
  if (T >= h[4] - 0.03) {
    const q = ap(T, h[4] - 0.03, 0.28), out = ap(T, 74.42, 0.2);
    show(S6.gk, { y: 1.3, z: lerp(22, 0, oExpo(q)), s: 1 + kk * 0.04, em: 1 + decay(T, h[4], 0.35) * 2, ry: Math.sin(T * 1.2) * 0.06 });
    const syl = [[0, 1, h[4]], [2, 3, h[4] + 0.19], [4, 5, h[4] + 0.41]];
    for (const [a, b, t] of syl) for (let j = a; j <= b && j < S6.gk.L.length; j++) {
      const d = decay(T, t, 0.13) * (T >= t ? 1 : 0);
      lOff(S6.gk, j, 0, d * 1.6, d * 2); S6.gk.L[j].em = 1 + d * 1.5;
    }
    S6.gk.L.forEach((l, j) => {
      const r = sat((out - j * 0.08) / 0.5); lOff(S6.gk, j, 0, 0, iExpo(r) * 40); l.op *= 1 - r;
      l.p.rotation.y += Math.sin(T * 4 + j) * 0.05;
    });
  }
  if (T >= h[5] - 0.03) {
    const q = ap(T, h[5] - 0.03, 0.2), out = ap(T, 74.42, 0.18);
    show(S6.da, { y: -6.7 + out * -8, s: lerp(2.4, 1, oExpo(q)), rz: -0.08, op: sat(q * 4) * (1 - out), em: 1 + decay(T, h[5], 0.3) * 2 });
  }
  popE(S6.nerd, T, h[4] + 0.1, { x: 14.3, y: -6.6, z: 1, s: 1.05, rz: 0.2 }, 74.42, 0.15);
  popE(S6.fire, T, h[5] + 0.03, { x: -14.3, y: -6.6, z: 1, s: 1 }, 74.42, 0.15);
}
function scene6b(T) {
  const b = WT[6];
  const kk = kickEnv(T);
  const tg = b[6];
  // tunnel flight: the group rushes toward the camera, each ГИ pops in ahead of us
  if (T < tg + 0.3) {
    const fly = T - 74.5, V = 62;
    const tunO = ap(T, tg - 0.05, 0.25);
    if (T >= b[0] - 0.03 && T < b[1] + 0.35) {
      const q = ap(T, b[0] - 0.03, 0.2);
      show(S6.ya, { y: 0.4, z: -14 + fly * V * 0.9, s: oBack(q), op: sat(q * 4) });
    }
    S6.tun.forEach((w, i) => {
      const t0 = b[i + 1];
      if (T < t0 - 0.04) return;
      const a = i * 2.35 + 0.6, r = 6.2;
      const zAppear = -26;
      const z = zAppear + (T - t0) * V;
      const q = ap(T, t0 - 0.04, 0.18);
      if (z > 27) return;
      show(w, { x: Math.cos(a) * r * (1 - tunO), y: Math.sin(a) * r * 0.75 * (1 - tunO), z, s: oBack(q) * (1 - tunO), rz: (1 - oCubic(q)) * (i % 2 ? 1 : -1) * 1.4 + Math.sin(T * 4 + i) * 0.1, op: sat(q * 4) * (1 - tunO) });
    });
    S6.rings.forEach((rg, i) => {
      const z = -60 + fract((T - 74.5) * 1.6 + i / 6) * 90;
      rg.g.visible = T < tg; rg.g.position.set(0, 0, z); rg.g.rotation.z = i;
      rg.g.material.opacity = sat((z + 60) / 30) * 0.5 * (1 - tunO);
    });
    if (T < tg) showStreak(0, 0, -20, 70, 3, 0.25 + 0.2 * Math.sin(T * 30));
    cam.roll += Math.sin((T - 74.5) * 3) * 0.08 * (1 - tunO);
  }
  // ГИКАЮ — giant, letters jumping in waves; background marquee rows
  if (T >= tg - 0.03) {
    const q = ap(T, tg - 0.03, 0.3), daU = oCubic(ap(T, b[7] - 0.05, 0.25)), out = ap(T, 80.72, 0.1);
    const PUL = timing.lines[6].pulses;
    show(S6.gk2, { y: lerp(0.9, 5.4, daU), z: lerp(-30, 0, oExpo(q)), s: lerp(1.5, 1, oExpo(q)) * lerp(1, 0.72, daU) * (1 + kk * 0.035), ry: Math.sin(T * 0.9) * 0.12, em: 1 + decay(T, tg, 0.3) * 1, op: 1 - out });
    S6.gk2.L.forEach((l, j) => {
      const wave = Math.sin((T - tg) * 2 * Math.PI * (timing.bpm / 60) / 2 - j * 0.8);
      lOff(S6.gk2, j, 0, Math.max(0, wave) * 1.1 * sat((T - tg - 0.3) * 3) * (1 - daU), 0);
      l.p.rotation.z = wave * 0.08 * sat((T - tg - 0.3) * 3);
      PUL.forEach((pt, k) => { if (k % 6 === j || (k + 3) % 6 === j) { const r = ap(T, pt, 0.36); if (r > 0 && r < 1) { l.p.rotation.x += oCubic(r) * Math.PI * 2; l.em = 1 + (1 - r) * 2; } } });
    });
    S6.rows.forEach((w, i) => {
      const dir = i % 2 ? 1 : -1;
      show(w, { x: dir * (((T - tg) * 7) % 26), y: [-9.5, -3.2, 3.2, 9.5][i] * 1.6, z: -34, op: 0.32 * sat((T - tg) * 3) * (1 - out) * (1 - 0.7 * ap(T, b[7] - 0.1, 0.2)) });
    });
    PUL.forEach((pt, k) => popE(S6.pe[k], T, pt, { x: [-14.5, 14.5, -14.8, 14.8, -14.5, 14.5][k], y: [-7.4, 7.6, 7.6, -7.4, -7.0, -7.0][k] * (k >= 4 ? 1 : 1), z: 1, s: 1 }, k < 4 ? PUL[k] + 1.2 : 80.6, 0.2));
    if (T >= b[7] - 0.04) {
      const d = ap(T, b[7] - 0.04, 0.2);
      show(S6.da2, { y: -4.9, s: lerp(2.6, 1, oExpo(d)), rz: 0.06, em: 1 + decay(T, b[7], 0.3) * 2, op: 1 - out });
    }
  }
}

// ── Scene 7: «Я гикаю, пока я вообще не отключусь» → digital breakdown → screen off
const S7 = { ya: W('Я', 'ub', 'white', 3.4), gk: W('ГИКАЮ,', 'ub', 'orange', 24.5, 0.55),
  po: W('ПОКА', 'm9', 'white', 8.4), ya2: W('Я', 'm9', 'orange', 1.8), vo: W('ВООБЩЕ', 'm9', 'white', 13.8),
  ne: W('НЕ', 'ub', 'orange', 4.6), ot: W('ОТКЛЮЧУСЬ', 'ub', 'red', 25, 0.5),
  echo: [0, 1, 2].map(() => W('ОТКЛЮЧУСЬ', 'ub', 'ghost', 25, 0.2)),
  sym: '#@%&*+?!$ГИ#@*+%&'.split('').map((c, i) => W(c, i % 2 ? 'm9' : 'ub', i % 3 ? 'orange' : 'white', 0.9, 0.25)),
  bolt: [0, 1, 2].map(() => E('26a1', 1.8)),
  nos: W('NO SIGNAL', 'm7', 'white', 13, 0.15), bat: E('1faab', 2.4), dead: E('1f635', 3.2),
  segs: Array.from({ length: 10 }, () => M(new THREE.Mesh(new THREE.BoxGeometry(1, 1, 0.2), new THREE.MeshBasicMaterial({ color: 0xff6a20, toneMapped: false, transparent: true })))),
  btSmall: makeBluetooth() };
{
  const t = WT[6 + 1 - 0];
  const L7 = timing.lines[7], w = L7.words.map(x => x[1]);
  hit(w[0], { zoom: 1.0, rgb: 0.6 }, 0.12);
  L7.giPulses.forEach((p, i) => { hit(p, { zoom: 1.3, shake: 0.4, rgb: 0.4 + i * 0.2 }, 0.13); });
  burst(w[1], 2.4, 2.6, 1, { n: 200, speed: 26, life: 1.1 });
  hit(w[2], { zoom: 0.6 }, 0.1); hit(w[3], { zoom: 0.5 }, 0.1); hit(w[5], { zoom: 0.8 }, 0.1);
  hit(w[6], { glitch: 1.0, rgb: 2.4, shake: 1.6, blocks: 0.8, flash: 0.25 }, 0.4);
  burst(w[6], 3.4, -5.8, 1, { n: 300, speed: 30, life: 1.2, color: 0xff3a20 });
  hit(L7.echo, { glitch: 0.7, rgb: 1.4 }, 0.3);
  L7.eighths.forEach((t, i) => hit(t, { glitch: 0.35 + i * 0.03, rgb: 0.6 + i * 0.06, jerk: 0.025 + i * 0.002, blocks: 0.15 + i * 0.03 }, 0.09));
  hit(L7.lastBeat, { flash: 1.0 }, 0.08);
}
function scene7(T) {
  if (!inW(T, 80.78, CLIP1 + 0.1)) return;
  const L7 = timing.lines[7], w = L7.words.map(x => x[1]);
  const [tYa, tGk, tPo, tYa2, tVo, tNe, tOt] = w;
  const kk = kickEnv(T);
  const B = ioCubic(ap(T, tPo - 0.2, 0.3));            // line 1 moves up for line 2
  const brk = ap(T, tOt, CLIP1 - 0.6 - tOt);           // digital breakdown progress
  const off = T >= L7.lastBeat;
  // falling-apart helper: letters drop out one by one as the signal dies
  const decayL = (word, seed, start) => word.L.forEach((l, i) => {
    const td = start + hash(seed * 17 + i) * (L7.lastBeat - 0.3 - start);
    if (T < td) { if (T > tOt && hash(frameOf(T) + i * 13 + seed) < brk * 0.35) l.op = 0.1; return; }
    const d = T - td; lOff(word, i, (hash(i + seed) - .5) * 3 * d, -9 * d * d - d, 0); l.p.rotation.z += (hash(i * 3 + seed) - .5) * 4 * d; l.op *= sat(1 - d * 1.6);
  });
  // line 1: Я ГИКАЮ with orbiting glowing symbols
  {
    const q = ap(T, tYa - 0.03, 0.25), g = ap(T, tGk - 0.03, 0.3);
    const L1 = { y: lerp(0.6, 6.4, B), s: lerp(1, 0.78, B) };
    show(S7.ya, { x: -13.6 * L1.s, y: L1.y, s: oBack(q) * L1.s, op: sat(q * 3) });
    if (T >= tGk - 0.03) {
      let gp = 0; L7.giPulses.forEach(p => gp = Math.max(gp, decay(T, p, 0.12)));
      show(S7.gk, { x: 2.6 * L1.s, y: L1.y, s: L1.s * lerp(1.6, 1, oExpo(g)) * (1 + gp * 0.08), em: 1 + gp * 1.5, op: sat(g * 4), ry: Math.sin(T * 1.1) * 0.06 });
      S7.gk.L.forEach((l, i) => { if ((i + Math.round(gp * 4)) % 2 && gp > 0.4) l.em = 2.5; });
      decayL(S7.gk, 3, 84.2);
    }
    decayL(S7.ya, 2, 84.0);
    // orbit: a tilted ring — in front it passes below the text, behind it passes above
    const R = lerp(19, 23, B), sp = ap(T, tGk, 0.6);
    S7.sym.forEach((sw, i) => {
      const th = (T - tGk) * 0.9 + i / S7.sym.length * Math.PI * 2;
      const fallT = 85 + hash(i * 4) * 4.5;
      const fall = T > fallT ? (T - fallT) : 0;
      if (T < tGk - 0.03 || fall > 1.2) return;
      show(sw, { x: Math.cos(th) * R * oCubic(sp), y: L1.y * 0.5 - Math.sin(th) * lerp(7.5, 9.5, B) - fall * fall * 12, z: Math.sin(th) * 9, rz: th * 2, ry: T * 2 + i, op: sat(sp * 2) * (0.6 + 0.4 * Math.sin(T * 6 + i)) * sat(1 - fall), em: 1.4 });
    });
    S7.bolt.forEach((e, i) => {
      const th = (T - tGk) * 0.9 + (i + 0.5) / 3 * Math.PI * 2;
      if (T < tGk || T > 86) return;
      showE(e, { x: Math.cos(th) * (R + 1), y: L1.y * 0.5 - Math.sin(th) * lerp(7.5, 9.5, B), z: Math.sin(th) * 9, op: sat(sp * 2) * (1 - ap(T, 85.6, 0.3)), s: 1 });
    });
  }
  // line 2
  const items = [[S7.po, tPo, -10.4, -0.6, 4], [S7.ya2, tYa2, -3.9, -0.6, 5], [S7.vo, tVo, 5.8, -0.6, 6], [S7.ne, tNe, -12.4, -6.0, 7]];
  for (const [wd, t, x, y, seed] of items) {
    if (T < t - 0.03) continue;
    const q = ap(T, t - 0.03, 0.25);
    show(wd, { x, y: y + (1 - oBack(q)) * -2, op: sat(q * 3) });
    decayL(wd, seed, 84.6);
  }
  if (T >= tOt - 0.03) {
    const q = ap(T, tOt - 0.03, 0.16);
    show(S7.ot, { x: 3.4, y: -6.0, z: lerp(8, 0, oExpo(q)), em: 1 + decay(T, tOt, 0.3) * 2 });
    S7.ot.L.forEach((l, i) => {        // slice jitter
      const f = frameOf(T);
      if (hash(f * 7 + i) < 0.25 + brk * 0.5) lOff(S7.ot, i, (hash(f + i * 3) - .5) * 1.6 * (0.3 + brk), (hash(f * 5 + i) - .5) * 0.5, 0);
    });
    decayL(S7.ot, 9, 86.6);
    // echoes
    S7.echo.forEach((e, k) => {
      const p = ap(T, L7.echo + k * 0.08, 1.6);
      if (p <= 0 || p >= 1) return;
      show(e, { x: 3.4 + (k - 1) * 1.2 * oCubic(p), y: -6.0 - (k + 1) * 0.5 * oCubic(p), z: -2 - (k + 1) * 3 * oCubic(p), op: (1 - p) * 0.8 });
    });
  }
  // HUD: battery draining on the 8ths, bluetooth disconnect, NO SIGNAL
  const E8 = L7.eighths;
  if (T >= 84.0 && !off) {
    let lost = 0; E8.forEach(t => { if (T >= t) lost++; });
    const left = Math.max(0, 10 - Math.ceil(lost * 10 / E8.length));
    const hp = ap(T, 84.0, 0.4);
    showE(S7.bat, { x: -16.6, y: -9.4, z: 0, s: oBack(hp), op: 1 });
    S7.segs.forEach((sg, i) => {
      sg.g.visible = i < left && hp > 0.5; sg.g.position.set(-14.6 + i * 0.75, -9.4, 0); sg.g.scale.set(0.55, 0.9, 1);
      sg.g.material.color.setHex(left <= 3 ? 0xff2a10 : 0xff7a20); sg.g.material.opacity = left <= 3 ? (Math.sin(T * 30) > 0 ? 1 : 0.3) : 1;
    });
    const bi = S7.btSmall; bi.g.visible = true; bi.g.position.set(16.6, -9.0, 0); bi.g.scale.setScalar(0.42 * oBack(hp)); bi.g.rotation.set(0, Math.sin(T * 2) * 0.3, 0);
    bi.set(T > 87.3 ? (hash(frameOf(T)) > 0.5 ? 0.2 : 0.9) : 1, T > 87.3 ? 0.3 : 1);
  }
  if (T >= 89.3 && !off) {
    const f = frameOf(T), q = ap(T, 89.3, 0.2);
    show(S7.nos, { y: 0.4, s: oBack(q), op: hash(f * 3) > 0.25 ? 1 : 0.2, em: 1.2 });
    S7.nos.L.forEach((l, i) => { if (hash(f + i * 11) < 0.2) lOff(S7.nos, i, (hash(f * 9 + i) - .5) * 1.5, 0, 0); });
    popE(S7.dead, T, 89.45, { x: 0, y: -4.4, z: 1, s: 1 });
  }
  // global breakdown FX
  fx.glitch += brk * 0.45; fx.rgb += brk * 1.2; fx.blocks += brk * 0.25; fx.sat *= lerp(1, 0.45, brk);
  fx.scan += brk * 0.25; fx.grain += brk * 0.1; fx.amb *= 1 - brk * 0.7; fx.smoke *= 1 - brk * 0.6;
  if (T > 86) fx.bright *= 0.85 + 0.15 * hash(frameOf(T) * 1.7);
  // last beat: CRT switch-off
  if (off) {
    fx.crt = ap(T, L7.lastBeat, 0.2);
    fx.dark = ap(T, L7.lastBeat + 0.2, 0.06);
  }
}

// ═════════════════════════ FRAME ═════════════════════════
function setState(T) {
  for (const o of ALL) o.reset();
  fx = { flash: 0, rgb: 0.12, glitch: 0, blocks: 0, shake: 0, zoom: 0, bloom: 0, jerk: 0, crt: 0, dark: 0, scan: 0.1, grain: 0.05, sat: 1, amb: 1, smoke: 1, bright: 1 };
  cam = { x: 0, y: 0, z: 30, lx: 0, ly: 0, lz: 0, roll: 0, ry: 0 };
  intro(T); scene1(T); scene2(T); scene3(T); scene4(T); scene5(T); scene6(T); scene7(T);
  // impulses
  for (const h of HITS) { const d = decay(T, h.t0, h.tau); if (d < 0.002) continue; for (const k in h.fx) fx[k] += h.fx[k] * d; }
  const kk = kickEnv(T);
  fx.zoom += kk * 0.9; fx.bloom += kk * 0.25; fx.rgb += kk * 0.25;
  finishWords();
  // bursts & rings
  for (const b of BURSTS) { const dt = T - b.t0; b.pts.visible = dt >= 0 && dt < b.life; b.mat.uniforms.uT.value = Math.max(0, dt); b.mat.uniforms.uAmp.value = fx.amb > 0.3 ? 1 : 0.6; }
  for (const r of RINGS) { const dt = T - r.t0, p = dt / r.life; r.mesh.visible = p >= 0 && p < 1; if (!r.mesh.visible) continue; r.mesh.scale.setScalar(Math.max(0.01, oCubic(p) * r.r)); r.m.opacity = (1 - p) * (1 - p) * r.op; r.mesh.quaternion.copy(camera.quaternion); }
  ambient.material.uniforms.uT.value = T; ambient.material.uniforms.uAmp.value = fx.amb * (0.9 + kk * 0.6);
  smokes.forEach(s => {
    const i = s.i; s.mesh.position.set(Math.sin(T * 0.07 + i * 2) * 14 + (i - 3) * 6, Math.cos(T * 0.05 + i) * 6 - 2, -48 - i * 5);
    s.mesh.rotation.z = T * 0.03 * (i % 2 ? 1 : -1) + i; s.m.opacity = 0.045 * fx.smoke * (1 + kk * 0.5);
  });
  // camera
  const sh = fx.shake * 0.45;
  camera.position.set(cam.x + vnoise(T * 22) * sh, cam.y + vnoise(T * 19 + 50) * sh, cam.z - fx.zoom * 0.9);
  camera.up.set(Math.sin(cam.roll + vnoise(T * 15 + 9) * sh * 0.03), Math.cos(cam.roll), 0);
  camera.lookAt(cam.lx + cam.ry * 30, cam.ly, cam.lz);
  // post
  bloom.strength = 0.5 + fx.bloom * 0.35;
  const u = VHS.uniforms;
  u.uFrame.value = frameOf(T); u.uRGB.value = fx.rgb; u.uGlitch.value = sat(fx.glitch); u.uBlocks.value = sat(fx.blocks); u.uFlash.value = sat(fx.flash * 0.5);
  u.uCRT.value = fx.crt; u.uScan.value = fx.scan; u.uGrain.value = fx.grain; u.uSat.value = fx.sat; u.uDark.value = sat(fx.dark + (1 - fx.bright));
  u.uJerk.value = fx.jerk * (hash(frameOf(T) * 1.3) - 0.5) * 2;
  renderer.toneMappingExposure = 1.0;
}

const halton = (i, b) => { let f = 1, r = 0; while (i > 0) { f /= b; r += f * (i % b); i = Math.floor(i / b); } return r; };
window.renderAt = (t) => {
  const T = CLIP0 + t;
  renderer.setRenderTarget(accRT); renderer.setClearColor(0x000000, 1); renderer.clear();
  for (let k = 0; k < SUB; k++) {
    const Tk = SUB > 1 ? T + (k / (SUB - 1) - 0.5) * SHUTTER : T;
    setState(Tk);
    if (SUB > 1) { const hx = halton(k + 1, 2) - 0.5, hy = halton(k + 1, 3) - 0.5; camera.setViewOffset(WIDTH, HEIGHT, hx, hy, WIDTH, HEIGHT); }
    composer.render();
    accQuad.material.uniforms.t.value = composer.readBuffer.texture;
    accQuad.material.uniforms.k.value = 1 / SUB;
    renderer.setRenderTarget(accRT); renderer.autoClear = false; accQuad.render(renderer); renderer.autoClear = true;
  }
  renderer.setRenderTarget(null); blitQuad.render(renderer);
  renderer.getContext().finish();
  return true;
};
window.readFrame = () => {          // raw RGBA of the canvas, bottom-up, base64
  const gl = renderer.getContext(); const a = new Uint8Array(WIDTH * HEIGHT * 4);
  gl.readPixels(0, 0, WIDTH, HEIGHT, gl.RGBA, gl.UNSIGNED_BYTE, a);
  let s = ''; const C = 0x8000; for (let i = 0; i < a.length; i += C) s += String.fromCharCode.apply(null, a.subarray(i, i + C));
  return btoa(s);
};
window.syncPixel = () => { const gl = renderer.getContext(); const a = new Uint8Array(4); gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, a); return a[0]; };
window.clipInfo = { duration: CLIP1 - CLIP0 };

// preview mode: open web/index.html?play to watch in real time with audio
if (Q.has('play')) {
  const audio = new Audio('../out/audio.m4a');
  document.body.addEventListener('click', () => audio.play(), { once: true });
  const loop = () => { window.renderAt(audio.currentTime); requestAnimationFrame(loop); };
  loop();
}
// warm up shaders / geometry uploads
window.renderAt(0);
window.clipReady = true;
