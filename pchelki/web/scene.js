// «Пчёлки» — намеренно убогий 3D-клип. Всё — чистая функция от времени t,
// поэтому кадры можно рендерить в любом порядке и параллельно.
import * as THREE from 'three';

const W = 1080, H = 1920;          // итоговый кадр
const W3 = 540, H3 = 960;          // 3D рендерим в половинном разрешении без сглаживания (лесенки = стиль 2005)
const BPM = 135.5, BEAT = 60 / BPM, BEAT0 = 0.17;
const DURATION = 38.34;

// ---------- утилиты ----------
function rng(seed) {
  return function () {
    seed |= 0; seed = seed + 0x6D2B79F5 | 0;
    let t = Math.imul(seed ^ seed >>> 15, 1 | seed);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
}
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lerp = (a, b, k) => a + (b - a) * k;
const smooth = k => { k = clamp(k); return k * k * (3 - 2 * k); };
const easeOutBack = k => { const c = 2.2; k = clamp(k) - 1; return 1 + (c + 1) * k * k * k + c * k * k; };
const beatPos = t => (t - BEAT0) / BEAT;
const beatPhase = t => { const b = beatPos(t); return b - Math.floor(b); };
const beatIdx = t => Math.floor(beatPos(t));
const bounce = t => Math.exp(-beatPhase(t) * 7);    // 1 в момент удара, затухает
const hash = n => { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };

// ---------- рендерер ----------
const glc = document.createElement('canvas');
glc.width = W3; glc.height = H3;
const renderer = new THREE.WebGLRenderer({ canvas: glc, antialias: false, preserveDrawingBuffer: true });
renderer.setPixelRatio(1);
renderer.setSize(W3, H3, false);
const out = document.getElementById('out');
const ctx = out.getContext('2d');

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(50, W3 / H3, 0.1, 300);
camera.setViewOffset(W3, H3, 0, Math.round(H3 * 0.09), W3, H3); // действие чуть выше — низ под текст
scene.add(new THREE.HemisphereLight(0xffffff, 0x775533, 1.6));
const sun = new THREE.DirectionalLight(0xffffff, 2.6); sun.position.set(4, 7, 9); scene.add(sun);
const rim = new THREE.DirectionalLight(0xff99ff, 1.0); rim.position.set(-6, -3, 3); scene.add(rim);

// ---------- текстуры ----------
function canvasTex(w, h, draw, repeat = 1) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  draw(c.getContext('2d'));
  const t = new THREE.CanvasTexture(c);
  t.magFilter = THREE.NearestFilter; t.minFilter = THREE.NearestFilter;
  t.colorSpace = THREE.SRGBColorSpace;
  if (repeat !== 1) { t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(repeat, repeat); }
  return t;
}
const stripeTex = (c1, c2, n) => canvasTex(16, 64, g => {
  for (let i = 0; i < n; i++) { g.fillStyle = i % 2 ? c2 : c1; g.fillRect(0, Math.floor(i * 64 / n), 16, Math.ceil(64 / n) + 1); }
});
const boxStripeTex = (c1, c2) => canvasTex(64, 16, g => {
  for (let i = 0; i < 5; i++) { g.fillStyle = i % 2 ? c2 : c1; g.fillRect(Math.floor(i * 64 / 5), 0, 14, 16); }
});

// ---------- ПЧЁЛЫ ----------
const YELLOWS = ['#ffd400', '#ffbf00', '#fff200', '#ff9f00', '#e8ff00', '#ffe14d'];
const BASE = { normal: 0.85, giant: 2.1, tiny: 0.42, fat: 0.95, long: 0.78, cube: 0.9 };

const blackMat = new THREE.MeshPhongMaterial({ color: 0x111111, shininess: 200, specular: 0xffffff, flatShading: true });
const whiteMat = new THREE.MeshPhongMaterial({ color: 0xffffff, shininess: 220, specular: 0xffffff, flatShading: true });
const mouthMat = new THREE.MeshPhongMaterial({ color: 0xe0102a, shininess: 90, specular: 0xffffff });
const tongueMat = new THREE.MeshPhongMaterial({ color: 0xff6fa8, shininess: 90 });
const wingMat = new THREE.MeshPhongMaterial({ color: 0x9fe8ff, transparent: true, opacity: 0.6, shininess: 255, specular: 0xffffff, side: THREE.DoubleSide });
const legMat = new THREE.MeshPhongMaterial({ color: 0x222222, shininess: 160, specular: 0xaaaaaa, flatShading: true });

function makeBee(type, seed) {
  const R = rng(seed * 7919 + 17);
  const root = new THREE.Group(), flip = new THREE.Group(), tilt = new THREE.Group();
  root.add(flip); flip.add(tilt);
  const yc = YELLOWS[Math.floor(R() * YELLOWS.length)];

  // тело
  let bodyLen, bodyR, hx, hy, hz, headR;
  if (type === 'cube') {
    const m = new THREE.MeshPhongMaterial({ map: boxStripeTex(yc, '#151515'), shininess: 140, specular: 0xffffff, flatShading: true });
    tilt.add(new THREE.Mesh(new THREE.BoxGeometry(2.2, 1.7, 1.7), m));
    bodyLen = 1.1; bodyR = 0.85; headR = 0.85;
    hx = 0.45; hy = 0.15; hz = 0.86;   // лицо прямо на боковой грани куба
  } else {
    const n = type === 'long' ? 11 : 7;
    const m = new THREE.MeshPhongMaterial({ map: stripeTex(yc, '#151515', n), shininess: 140, specular: 0xffffff, flatShading: true });
    const g = new THREE.SphereGeometry(1, 8, 6); g.rotateZ(Math.PI / 2);
    const body = new THREE.Mesh(g, m);
    const s = { normal: [1.25, 1, 1], giant: [1.3, 1.05, 1.0], tiny: [1.15, 1, 1], fat: [1.2, 1.45, 1.4], long: [2.7, 0.72, 0.72] }[type];
    body.scale.set(s[0], s[1], s[2]);
    body.rotation.z = (R() - 0.5) * 0.25;   // слегка криво
    tilt.add(body);
    bodyLen = s[0]; bodyR = s[1];
    headR = { normal: 0.78, giant: 0.85, tiny: 0.9, fat: 0.5, long: 0.72 }[type];
    const head = new THREE.Mesh(new THREE.SphereGeometry(headR, 7, 5),
      new THREE.MeshPhongMaterial({ color: yc, shininess: 160, specular: 0xffffff, flatShading: true }));
    hx = bodyLen * 0.82 + headR * 0.5; hy = 0.2 + (type === 'fat' ? 0.5 : 0);
    head.position.set(hx, hy, 0);
    head.scale.set(1, 1 + (R() - 0.5) * 0.4, 1);
    tilt.add(head);
    hz = headR * 0.78;
  }

  // огромные выпученные глаза разного размера
  const pupils = [];
  const eyeBase = Math.max(0.42, headR * 0.55) * (type === 'tiny' ? 1.35 : 1);
  for (const side of [-1, 1]) {
    const er = eyeBase * (0.75 + R() * 0.6);
    const eye = new THREE.Mesh(new THREE.SphereGeometry(er, 8, 6), whiteMat);
    eye.position.set(hx + side * er * 0.95, hy + headR * 0.35 + (R() - 0.5) * 0.15, hz + er * 0.2);
    eye.scale.z = 0.8 + R() * 0.5;
    tilt.add(eye);
    const pr = er * (0.32 + R() * 0.2);
    const pupil = new THREE.Mesh(new THREE.SphereGeometry(pr, 6, 4), blackMat);
    pupil.userData.base = new THREE.Vector3(eye.position.x, eye.position.y, eye.position.z + er * eye.scale.z * 0.85);
    pupil.userData.r = er * 0.35;
    tilt.add(pupil); pupils.push(pupil);
  }

  // нелепая улыбка
  const mw = headR * (0.5 + R() * 0.25);
  const smile = new THREE.Mesh(new THREE.TorusGeometry(mw, mw * 0.22, 4, 9, Math.PI), mouthMat);
  smile.rotation.z = Math.PI;
  smile.position.set(hx + (R() - 0.5) * 0.2, hy - headR * 0.25, hz + 0.12);
  smile.scale.set(1, 0.6 + R() * 0.6, 1);
  tilt.add(smile);
  if (R() < 0.55) { // язык или зуб
    if (R() < 0.5) {
      const tooth = new THREE.Mesh(new THREE.BoxGeometry(mw * 0.45, mw * 0.5, 0.08), whiteMat);
      tooth.position.set(smile.position.x + 0.05, smile.position.y - mw * 0.55, hz + 0.2);
      tilt.add(tooth);
    } else {
      const tongue = new THREE.Mesh(new THREE.SphereGeometry(mw * 0.35, 6, 4), tongueMat);
      tongue.scale.set(1, 1.5, 0.4);
      tongue.position.set(smile.position.x, smile.position.y - mw * 0.75, hz + 0.18);
      tilt.add(tongue);
    }
  }

  // усики
  const antennae = [];
  for (const side of [-1, 1]) {
    const piv = new THREE.Group();
    piv.position.set(hx + side * headR * 0.35, hy + headR * 0.8, 0.1);
    const len = 0.5 + R() * 0.6;
    const stick = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, len, 4), legMat);
    stick.position.y = len / 2; piv.add(stick);
    const ball = new THREE.Mesh(new THREE.SphereGeometry(0.12 + R() * 0.08, 5, 4), blackMat);
    ball.position.y = len; piv.add(ball);
    piv.rotation.z = -side * 0.35;
    tilt.add(piv); antennae.push(piv);
  }

  // маленькие крылья-пропеллер
  const wing = new THREE.Group();
  wing.position.set(-bodyLen * 0.1, bodyR * (type === 'cube' ? 1 : 0.95) + 0.08, 0);
  const hub = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 0.25, 5), legMat); hub.position.y = -0.05; wing.add(hub);
  const wl = (type === 'long' ? 0.75 : 0.6) * (0.85 + R() * 0.3);
  for (let i = 0; i < 2; i++) {
    const blade = new THREE.Mesh(new THREE.BoxGeometry(wl * 2, 0.03, 0.32), wingMat);
    blade.rotation.y = i * Math.PI / 2; blade.position.y = 0.08; wing.add(blade);
  }
  tilt.add(wing);

  // короткие лапки
  const legs = [];
  const nl = type === 'long' ? 6 : 4;
  for (let i = 0; i < nl; i++) {
    const piv = new THREE.Group();
    const lx = lerp(-bodyLen * 0.5, bodyLen * 0.45, nl === 1 ? 0.5 : i / (nl - 1));
    piv.position.set(lx, -bodyR * 0.85, (i % 2 ? 1 : -1) * 0.25 + 0.2);
    const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.05, 0.38, 4), legMat);
    leg.position.y = -0.17; piv.add(leg);
    const foot = new THREE.Mesh(new THREE.SphereGeometry(0.1, 4, 3), legMat);
    foot.position.set(0.05, -0.36, 0); piv.add(foot);
    tilt.add(piv); legs.push(piv);
  }

  // жало
  const sting = new THREE.Mesh(new THREE.ConeGeometry(0.17, 0.55, 5), blackMat);
  sting.rotation.z = Math.PI / 2;
  sting.position.set(-bodyLen - 0.2, -0.05, 0);
  tilt.add(sting);

  root.visible = false;
  scene.add(root);
  return { root, flip, tilt, wing, pupils, antennae, legs, sting, type, base: BASE[type], seed: R() * 100, wingDir: R() < 0.5 ? 1 : -1 };
}

// пул пчёл
const ORDER = ['normal', 'fat', 'tiny', 'long', 'cube', 'normal', 'tiny', 'fat', 'long', 'normal'];
const bees = [];
for (let i = 0; i < 64; i++) bees.push(makeBee(ORDER[i % ORDER.length], i + 1));
const GIANT = makeBee('giant', 901);
const GIANT2 = makeBee('giant', 777);
const BIGCUBE = makeBee('cube', 555); BIGCUBE.base = 1.7;
const ALL = [...bees, GIANT, GIANT2, BIGCUBE];

// поставить пчелу в кадр
function pose(b, t, pos, o = {}) {
  b.root.visible = true;
  const vel = o.vel || [1, 0, 0];
  const bob = o.noBob ? 0 : 0.16 * Math.sin(t * 8 + b.seed);
  b.root.position.set(pos[0], pos[1] + bob, pos[2]);
  let face = o.face != null ? o.face : (vel[0] >= 0 ? 1 : -1);
  if (o.back) face = -face;
  b.flip.scale.x = face;
  b.flip.rotation.y = o.yaw || 0;
  const sp = Math.hypot(vel[0], vel[1]) + 0.01;
  const bank = o.noBank ? 0 : Math.atan2(vel[1], Math.abs(vel[0]) + 1.5) * 0.7;
  b.tilt.rotation.set(o.roll || 0, 0, bank + (o.pitch || 0) + 0.12 * Math.sin(t * 5.3 + b.seed * 2));
  const s = b.base * (o.scale || 1), q = o.squash || 0;
  b.root.scale.set(s * (1 + q * 0.6), s * (1 - q), s * (1 + q * 0.6));
  // пропеллер, глаза, усики, лапки
  b.wing.rotation.y = (t * (o.wing || 38) + b.seed) * b.wingDir;
  b.pupils.forEach((p, i) => {
    const bs = p.userData.base, r = p.userData.r;
    const a = t * (o.crazyEyes ? 25 : 7) + b.seed * 3 + i * 2.1;
    p.position.set(bs.x + r * Math.sin(a), bs.y + r * Math.cos(a * 1.3), bs.z);
  });
  b.antennae.forEach((a, i) => { a.rotation.x = 0.35 * Math.sin(t * 11 + i + b.seed); });
  b.legs.forEach((l, i) => { l.rotation.z = 0.6 * Math.sin(t * 16 + i * 1.7 + b.seed); });
  b.sting.scale.setScalar(o.sting || 1);
}
// поза по траектории (скорость — численная производная)
function fly(b, t, path, o = {}) {
  const p = path(t), p1 = path(t + 0.03);
  pose(b, t, p, Object.assign({ vel: [(p1[0] - p[0]) / 0.03, (p1[1] - p[1]) / 0.03, 0] }, o));
}

// ---------- БАХ-звёздочки ----------
function starShape(n, r1, r2) {
  const s = new THREE.Shape();
  for (let i = 0; i <= n * 2; i++) {
    const a = i / (n * 2) * Math.PI * 2 + Math.PI / 2, r = i % 2 ? r2 : r1;
    i ? s.lineTo(Math.cos(a) * r, Math.sin(a) * r) : s.moveTo(Math.cos(a) * r, Math.sin(a) * r);
  }
  return s;
}
const starGeo = new THREE.ExtrudeGeometry(starShape(6, 1, 0.45), { depth: 0.25, bevelEnabled: false });
const stars = [];
for (let i = 0; i < 8; i++) {
  const m = new THREE.Mesh(starGeo, new THREE.MeshPhongMaterial({ color: i % 2 ? 0xfff200 : 0xffffff, emissive: i % 2 ? 0x775500 : 0x444444, shininess: 200, flatShading: true }));
  m.visible = false; scene.add(m); stars.push(m);
}
let starUsed = 0;
function bonk(t, tc, pos, size = 1) {
  const age = t - tc;
  if (age < 0 || age > 0.45 || starUsed >= stars.length) return;
  const m = stars[starUsed++];
  m.visible = true;
  m.position.set(pos[0], pos[1], pos[2] + 0.5);
  m.scale.setScalar(size * easeOutBack(age / 0.15) * (1 - smooth((age - 0.3) / 0.15)));
  m.rotation.set(0, 0, age * 6);
  shakeAmt = Math.max(shakeAmt, 0.35 * (1 - age / 0.45));
}

// ---------- ФОНЫ ----------
const floorTexCache = {};
const floorTex = (a, b) => floorTexCache[a + b] || (floorTexCache[a + b] = canvasTex(2, 2, g => {
  g.fillStyle = a; g.fillRect(0, 0, 2, 2); g.fillStyle = b; g.fillRect(0, 0, 1, 1); g.fillRect(1, 1, 1, 1);
}, 40));
const floor = new THREE.Mesh(new THREE.PlaneGeometry(240, 240), new THREE.MeshPhongMaterial({ shininess: 60 }));
floor.rotation.x = -Math.PI / 2; floor.position.set(0, -7, -60); scene.add(floor);

const BURST_N = 18;
function burstGeo(odd) {
  const pos = [];
  for (let i = odd; i < BURST_N; i += 2) {
    const a0 = i / BURST_N * Math.PI * 2, a1 = (i + 1) / BURST_N * Math.PI * 2;
    pos.push(0, 0, 0, Math.cos(a0) * 150, Math.sin(a0) * 150, 0, Math.cos(a1) * 150, Math.sin(a1) * 150, 0);
  }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); return g;
}
const burst = new THREE.Group();
const burstA = new THREE.Mesh(burstGeo(0), new THREE.MeshBasicMaterial({ side: THREE.DoubleSide }));
const burstB = new THREE.Mesh(burstGeo(1), new THREE.MeshBasicMaterial({ side: THREE.DoubleSide }));
burst.add(burstA, burstB); burst.position.set(0, 2, -70); scene.add(burst);

const hexGeo = new THREE.CylinderGeometry(1, 1, 0.6, 6); hexGeo.rotateX(Math.PI / 2);
const HEX_COLS = 13, HEX_ROWS = 21;
const hexes = new THREE.InstancedMesh(hexGeo, new THREE.MeshPhongMaterial({ shininess: 120, specular: 0xffffff, flatShading: true }), HEX_COLS * HEX_ROWS);
{
  const c = new THREE.Color();
  for (let i = 0; i < HEX_COLS * HEX_ROWS; i++) {
    c.set(['#ffb300', '#ff8f00', '#ffd54f', '#ffa000'][Math.floor(hash(i) * 4)]);
    hexes.setColorAt(i, c);
  }
}
scene.add(hexes);
const dummy = new THREE.Object3D();
function updateHexes(t) {
  let k = 0;
  for (let r = 0; r < HEX_ROWS; r++) for (let q = 0; q < HEX_COLS; q++) {
    const x = (q - HEX_COLS / 2) * 1.85 + (r % 2) * 0.92, y = (r - HEX_ROWS / 2) * 1.6 + 2;
    const d = Math.hypot(x, y - 2);
    dummy.position.set(x, y, -18 + 0.9 * Math.sin(t * 4 - d * 0.6) + 0.8 * bounce(t) * Math.exp(-d * 0.15));
    dummy.rotation.set(0, 0, 0); dummy.scale.setScalar(0.92);
    dummy.updateMatrix(); hexes.setMatrixAt(k++, dummy.matrix);
  }
  hexes.instanceMatrix.needsUpdate = true;
}

const ico = new THREE.Mesh(new THREE.IcosahedronGeometry(45, 1), new THREE.MeshBasicMaterial({ wireframe: true }));
scene.add(ico);

// «облака» из кривых шаров (только геометрия, ничего лишнего)
const blobs = new THREE.Group();
for (let i = 0; i < 9; i++) {
  const m = new THREE.Mesh(new THREE.SphereGeometry(1, 6, 4), new THREE.MeshPhongMaterial({ color: 0xffffff, flatShading: true, shininess: 30 }));
  m.scale.set(3 + hash(i) * 3, 1.5 + hash(i + 9) * 1.5, 1.5);
  m.position.set((hash(i + 3) - 0.5) * 40, (hash(i + 5) - 0.2) * 30, -35 - hash(i + 7) * 15);
  blobs.add(m);
}
scene.add(blobs);

const BG = {
  green: { sky: '#39ff14', floor: ['#ff00ff', '#39ff14'] },
  yellow: { sky: '#ffee00', hex: true },
  blue: { sky: '#33c4ff', burst: ['#33c4ff', '#8fe3ff'], blobs: true },
  pink: { sky: '#ff4fc8', floor: ['#ffffff', '#ff1aa8'], ico: '#fff200' },
  green2: { sky: '#39ff14', burst: ['#39ff14', '#c8ff00'] },
  yellow2: { sky: '#ffee00', floor: ['#ff6a00', '#ffee00'], blobs: true },
  blue2: { sky: '#33c4ff', ico: '#ff00ff', floor: ['#0044ff', '#33c4ff'] },
  pink2: { sky: '#ff4fc8', burst: ['#ff4fc8', '#ffb3ec'] },
};
function setBG(name, t) {
  const b = BG[name];
  scene.background = new THREE.Color(b.sky);
  floor.visible = !!b.floor;
  if (b.floor) { floor.material.map = floorTex(b.floor[0], b.floor[1]); floor.material.map.offset.set(0, t * 0.9); floor.material.needsUpdate = true; }
  burst.visible = !!b.burst;
  if (b.burst) { burstA.material.color.set(b.burst[0]); burstB.material.color.set(b.burst[1]); burst.rotation.z = t * 0.4; }
  hexes.visible = !!b.hex; if (b.hex) updateHexes(t);
  ico.visible = !!b.ico; if (b.ico) { ico.material.color.set(b.ico); ico.rotation.set(t * 0.2, t * 0.31, 0); }
  blobs.visible = !!b.blobs; if (b.blobs) blobs.position.x = Math.sin(t * 0.3) * 4;
}

// ---------- КАМЕРА ----------
let shakeAmt = 0;
const PUNCH = [0.0, 3.5, 7.2, 10.72, 11.89, 18.4, 22.05, 26.35, 28.7, 31.73, 32.74];
function setCam(t, pos, look, fov = 50, dutch = 0) {
  let f = fov;
  for (const p of PUNCH) { const a = t - p; if (a >= 0 && a < 0.6) f *= 1 - 0.13 * Math.exp(-a * 9); }
  camera.fov = f;
  camera.position.set(pos[0], pos[1], pos[2]);
  camera.up.set(Math.sin(dutch), Math.cos(dutch), 0);
  camera.lookAt(look[0], look[1], look[2]);
  if (shakeAmt > 0) {
    const s = shakeAmt;
    camera.position.x += (hash(t * 97) - 0.5) * s; camera.position.y += (hash(t * 53 + 1) - 0.5) * s;
  }
  camera.updateProjectionMatrix();
}

// ---------- ХОРЕОГРАФИЯ ----------
// экран при z=0 и камере на z=14: x ≈ ±3.7, y ≈ ±6.5; низ (y<-3.6) оставляем тексту
const EDGE = [[-6.5, 0], [6.5, 0], [0, 9], [0, -9]];

function sceneA(t) { // 0 — 3.45: прилетают из-за краёв
  setBG('green', t);
  const lt = t;
  for (let i = 0; i < 9; i++) {
    const b = bees[i];
    const t0 = i * 0.28 - 0.3, e = EDGE[i % 4], e2 = EDGE[(i + 1 + (i % 2)) % 4];
    const tgt = [Math.sin(i * 2.3) * 2.4, 1.5 + Math.cos(i * 1.7) * 2.6, -i * 0.4];
    const path = tt => {
      const k = tt - t0;
      if (k < 1.0) { const s = easeOutBack(k / 1.0); return [lerp(e[0], tgt[0], s), lerp(e[1], tgt[1], s), tgt[2]]; }
      const w = k - 1.0;
      return [tgt[0] + Math.sin(w * (2 + i % 3)) * 1.2, tgt[1] + Math.sin(w * 3.1 + i) * 0.8, tgt[2] + Math.sin(w * 2) * 1.5];
    };
    if (lt < t0) continue;
    fly(b, t, path, { back: i === 3 || i === 7, roll: i === 5 ? t * 9 : 0, squash: 0.15 * bounce(t) });
  }
  // гигант выглядывает снизу из-за края
  const k = smooth((t - 1.2) / 1.2);
  pose(GIANT, t, [2.6, lerp(-14, -6.2, k), -3], { face: -1, pitch: 0.5, noBank: true, crazyEyes: t > 2.4 });
  // одна пчела врезается в другую
  bonk(t, 2.55, [0.3, 2.2, 0], 1.2);
  setCam(t, [0, 1.3, lerp(16, 13, smooth(t / 3.4))], [0, 1.3, 0]);
}

function sceneB(t) { // 3.45 — 7.15: карусель над сотами
  setBG('yellow', t);
  const lt = t - 3.45;
  for (let i = 0; i < 10; i++) {
    const b = bees[10 + i];
    const ang = lt * (1.3 + (i % 3) * 0.25) * (i % 2 ? 1 : -1) + i * Math.PI * 2 / 10;
    const path = tt => { const a = ang + (tt - t) * (1.3 + (i % 3) * 0.25) * (i % 2 ? 1 : -1); return [Math.cos(a) * 3.1, 1.6 + Math.sin(a * 2) * 1.2 + (i % 3 - 1) * 1.6, Math.sin(a) * 3]; };
    fly(b, t, path, { roll: i % 4 === 0 ? t * 10 : 0, back: i % 5 === 2, squash: 0.2 * bounce(t) });
  }
  // толстяк летит задом наперёд через экран
  const k = (lt - 0.3) / 2.2;
  if (k > 0 && k < 1) pose(bees[1], t, [lerp(-7, 7, k), 3.5 + Math.sin(k * 12) * 0.6, 2], { face: -1, roll: Math.sin(t * 8) * 0.6 });
  // резко влетает в камеру (на «пристаёт»)
  const r = (t - 4.6) / 1.1;
  if (r > 0 && r < 1) pose(BIGCUBE, t, [lerp(1.5, -0.3, r), lerp(2, 1.4, r), lerp(-30, 12.2, r * r * r)], { face: -1, roll: r * 6, crazyEyes: true, wing: 80 });
  setCam(t, [Math.sin(lt * 0.6) * 1.5, 1.4, 14], [0, 1.4, 0], 50, Math.sin(lt * 0.9) * 0.08);
}

function sceneC(t) { // 7.15 — 10.65: столкновения и «жалят»
  setBG('blue', t);
  const pairs = [[7.45, 4.3, 0], [7.95, 1.5, -1], [8.3, -0.6, 1]];
  pairs.forEach(([tc, y, z], k) => {
    for (const side of [-1, 1]) {
      const b = bees[20 + k * 2 + (side > 0 ? 1 : 0)];
      const d = t - tc;
      let x, roll = 0;
      if (d < 0) x = side * (0.65 - d * 6.5);
      else { x = side * (0.65 + d * 4); roll = d * 25 * side; }
      if (Math.abs(x) > 9) continue;
      const big = k === 1 && side > 0;
      pose(b, t, [big ? x * 1.4 : x, y + (d > 0 ? d * d * 3 : 0), z], { face: d < 0 ? -side : side, back: d > 0, roll, crazyEyes: d > 0, scale: big ? 1.4 : 1 });
    }
    bonk(t, tc, [0, y, z], 1.3);
  });
  // «жалят»: ряд пчёл падает сверху и поворачивается жалом к камере
  for (let i = 0; i < 6; i++) {
    const b = bees[26 + i];
    const t0 = 8.43 + i * 0.07;
    if (t < t0 - 0.4) continue;
    const drop = smooth((t - (t0 - 0.4)) / 0.4);
    const x = (i - 2.5) * 1.25, y = lerp(9, 1.6 + (i % 2) * 1.6, drop);
    const turn = smooth((t - t0) / 0.3) * (1 - smooth((t - 9.95) / 0.3));
    const wig = Math.sin(t * 18 + i) * 0.35 * turn;
    pose(b, t, [x, y, 0.5], { face: 1, yaw: turn * Math.PI * 0.62, roll: wig, sting: 1 + turn * 1.6 * (0.6 + 0.4 * bounce(t)), noBank: true, squash: 0.2 * bounce(t) });
  }
  setCam(t, [0, 2, 14], [0, 2, 0]);
}

function sceneD(t) { // 10.65 — 16.45: «Тому приносят мёд» — огромный рой
  setBG('pink', t);
  const N = 44;
  for (let j = 0; j < N; j++) {
    const b = bees[j % 64 === j ? j : 0];
    const ph = hash(j) * Math.PI * 2, lat = (hash(j + 50) - 0.5) * 2.4;
    const rad = 2.2 + hash(j + 99) * 2.0;
    const t0 = 10.65 + hash(j + 7) * 1.1;
    const e = EDGE[j % 4];
    const swirl = tt => {
      const w = tt * (1.4 + hash(j + 3) * 0.8);
      const pulse = 1 + 0.18 * bounce(tt);
      const tw = smooth((tt - 14.2) / 0.8) * (1 - smooth((tt - 15.9) / 0.4));   // вытягивается в торнадо
      const r = rad * pulse * lerp(1, 0.45, tw);
      return [Math.cos(ph + w) * r * Math.cos(lat), 2.2 + Math.sin(lat) * r * lerp(1, 3.2, tw), Math.sin(ph + w) * r * Math.cos(lat)];
    };
    const path = tt => {
      const k = smooth((tt - t0) / 0.9);
      const s = swirl(tt);
      return [lerp(e[0] * 1.3, s[0], k), lerp(e[1] * 1.1, s[1], k), s[2]];
    };
    if (t < t0 - 0.2) continue;
    fly(b, t, path, { roll: j % 5 === 0 ? t * 8 : 0, back: j % 7 === 3, squash: 0.25 * bounce(t) });
  }
  // гигантская пчела в центре роя улыбается на «мёд»
  const g = smooth((t - 11.6) / 0.5);
  if (g > 0) pose(GIANT2, t, [0, 2.2, 0], { face: 1, scale: g * (1 + 0.1 * bounce(t)), yaw: -0.5 + Math.sin(t * 2) * 0.3, crazyEyes: true, noBank: true, roll: Math.sin(t * 3) * 0.3 });
  bonk(t, 12.6, [-1.8, 3.2, 3], 1); bonk(t, 13.9, [1.6, 0.8, 3], 1);
  const zoom = 11.89 < t ? lerp(14, 11, smooth((t - 11.89) / 3)) : 15;
  setCam(t, [Math.sin(t * 0.7) * 2, 2.6, zoom], [0, 2.2, 0], 52, Math.sin(t * 0.8) * 0.12);
}

function sceneE(t) { // 16.45 — 18.4: проигрыш — синхронный танец сеткой
  setBG('green2', t);
  const bi = beatIdx(t), bp = beatPhase(t), move = bi % 4;
  let k = 0;
  for (let r = 0; r < 4; r++) for (let c = 0; c < 3; c++) {
    const b = bees[[0, 3, 4, 1, 9, 5, 7, 8, 2, 6, 10, 13][k++]];
    let x = (c - 1) * 2.4, y = 5.2 - r * 3.0, roll = 0, sq = 0, face = 1, hop = 0;
    if (move === 0) { x -= 0.7 * Math.sin(bp * Math.PI); face = -1; }
    if (move === 1) { x += 0.7 * Math.sin(bp * Math.PI); }
    if (move === 2) roll = smooth(bp / 0.8) * Math.PI * 2;
    if (move === 3) { hop = Math.sin(bp * Math.PI) * 0.9; sq = 0.35 * Math.exp(-bp * 6); }
    pose(b, t, [x, y + hop, 0], { face, roll, squash: sq, noBank: true, noBob: true });
  }
  setCam(t, [0, 0.8, 14.5], [0, 0.8, 0]);
}

function sceneF(t) { // 18.4 — 25.75: «Им каждая ромашка нальёт нектара в чашку» — паровозик
  setBG('yellow2', t);
  const lead = tt => [Math.sin(tt * 1.15) * 2.9, 1.8 + Math.sin(tt * 2.3) * 3.3, Math.cos(tt * 1.15) * 2.5];
  for (let i = 0; i < 11; i++) {
    const b = i === 0 ? BIGCUBE : bees[30 + i];
    const flipT = 24.32 + i * 0.05, fl = smooth((t - flipT) / 0.45) * Math.PI * 2;
    const path = tt => lead(tt - i * 0.33);
    const enter = smooth((t - 18.4 - i * 0.12) / 0.6);
    const p = path(t), p1 = path(t + 0.03);
    pose(b, t, [p[0], lerp(-10, p[1], enter), p[2]], { vel: [(p1[0] - p[0]), (p1[1] - p[1]), 0], roll: fl, squash: 0.2 * bounce(t), back: i === 6 });
  }
  // двое летят навстречу паровозику и врезаются
  for (const [i, tc, side] of [[50, 20.9, 1], [51, 23.0, -1]]) {
    const d = t - tc, hit = lead(tc - 4 * 0.33);
    if (d < -1.4 || d > 1.2) continue;
    const x = d < 0 ? hit[0] + side * (-d) * 5.5 : hit[0] + side * d * 5, y = hit[1] + (d > 0 ? d * 4 : 0);
    pose(bees[i], t, [x, y, hit[2] + 0.5], { face: d < 0 ? -side : side, back: d > 0, roll: d > 0 ? d * 30 : 0, crazyEyes: d > 0 });
    bonk(t, tc, hit, 1.1);
  }
  // на «нальёт» — резкий наезд камеры на куб-пчелу
  const zk = smooth((t - 22.05) / 0.25) * (1 - smooth((t - 22.9) / 0.4));
  const cp = lead(t);
  const camPos = [lerp(0, cp[0] * 0.7, zk), lerp(1.6, cp[1], zk), lerp(14.5, cp[2] + 6.5, zk)];
  const look = [lerp(0, cp[0], zk), lerp(1.6, cp[1], zk), lerp(0, cp[2], zk)];
  setCam(t, camPos, look, 50, Math.sin(t * 1.1) * 0.1);
}

function sceneG(t) { // 25.75 — 31.73: хоровод-пропеллеры, дождь из мелких пчёл, «нальют» с вращением
  setBG('blue2', t);
  const lt = t - 25.75;
  const wave = t > 28.7 ? 1 : 0;
  for (let i = 0; i < 8; i++) {
    const b = bees[[0, 1, 3, 4, 5, 8, 9, 13][i]];
    const a = lt * 0.8 + i * Math.PI / 4;
    const bi = beatIdx(t), bp = beatPhase(t);
    const spinY = (bi % 2 === i % 2) ? smooth(bp / 0.7) * Math.PI * 2 : 0;
    const roll = wave * Math.sin(t * 4 - i * 0.8) * 1.3 + wave * ((t - 28.7) * 3);
    pose(b, t, [Math.cos(a) * 2.7, 1.8 + Math.sin(a) * 2.7, Math.sin(a * 2) * 0.8], { face: Math.cos(a) < 0 ? 1 : -1, yaw: spinY, roll, noBank: true, squash: 0.25 * bounce(t) });
  }
  // «одуванчики»: сверху сыплются мелкие пчёлы
  for (let j = 0; j < 14; j++) {
    const b = bees[[2, 6, 12, 16, 22, 26, 32, 36, 42, 46, 52, 56, 62, 39][j]];
    const t0 = 27.32 + j * 0.12;
    const d = t - t0;
    if (d < 0) continue;
    const y = 8.5 - d * (4 + hash(j) * 3) + Math.sin(d * 6 + j) * 0.3;
    if (y < -9) continue;
    pose(b, t, [(hash(j + 20) - 0.5) * 7, y, 2 + hash(j + 40) * 2], { face: hash(j) > 0.5 ? 1 : -1, roll: d * (8 + j), noBank: true, crazyEyes: true });
  }
  // великан поднимается снизу в центре
  const g = smooth((t - 29.6) / 1.2);
  if (g > 0) pose(GIANT, t, [0, lerp(-12, 1.9, g), -1.5], { face: 1, yaw: Math.sin(t * 2) * 0.4, crazyEyes: true, noBank: true, squash: 0.15 * bounce(t) });
  const dutch = wave ? (t - 28.7) * 0.5 : 0;
  setCam(t, [0, 1.8, lerp(14, 16.5, wave * smooth((t - 28.7) / 3))], [0, 1.8, 0], 50, dutch);
}

function sceneH(t) { // 31.73 — 34.1: «нектар в стаканчики» — взрыв роя и обратное схлопывание
  setBG('pink2', t);
  for (let j = 0; j < 30; j++) {
    const b = bees[(j * 3 + 1) % 64];
    const dir = [Math.cos(j * 2.4) * (0.6 + hash(j)), Math.sin(j * 2.4) * (0.6 + hash(j + 1)), 0.4 + hash(j + 2) * 1.2];
    const path = tt => {
      const out = smooth((tt - 31.73) / 0.9) * 4.5;
      const back = smooth((tt - 32.74) / 0.85);
      const r = out * (1 - back) + back * 0.25;
      return [dir[0] * r, 2 + dir[1] * r, dir[2] * r * 1.6 - back * 0.5];
    };
    fly(b, t, path, { roll: (t - 31.73) * (j % 2 ? 6 : -6), crazyEyes: true, back: j % 4 === 1, squash: 0.25 * bounce(t) });
  }
  bonk(t, 33.6, [0, 2, 2], 3.2);
  bonk(t, 33.65, [-1, 3, 3], 1.4);
  bonk(t, 33.7, [1.2, 1.2, 3], 1.4);
  setCam(t, [0, 2, 14.5], [0, 2, 0], 50, Math.sin(t * 2) * 0.08);
}

function sceneI(t) { // 34.1 — конец: все танцуют, великан наезжает на камеру
  setBG('green', t);
  const bp = beatPhase(t), bi = beatIdx(t);
  for (let i = 0; i < 18; i++) {
    const b = bees[(i * 5 + 2) % 64];
    const e = EDGE[i % 4];
    const home = [((i % 3) - 1) * 2.4, 5.6 - Math.floor(i / 3) * 1.9, -2 - (i % 2)];
    const k = easeOutBack((t - 34.1 - i * 0.05) / 0.7);
    const side = bi % 2 ? 1 : -1;
    const p = [lerp(e[0], home[0], k) + side * 0.5 * Math.sin(bp * Math.PI), lerp(e[1], home[1], k) + Math.abs(Math.sin(bp * Math.PI)) * 0.5, home[2]];
    pose(b, t, p, { face: side, roll: bi % 4 === 3 ? smooth(bp / 0.8) * Math.PI * 2 : 0, squash: 0.3 * bounce(t), noBank: true, noBob: true });
  }
  const g = smooth((t - 35.6) / 2.0);
  pose(GIANT, t, [Math.sin(t * 3) * 0.3 * (1 - g), lerp(-11, 1.3, smooth((t - 34.6) / 1.0)), lerp(-2, 7.6, g)], { face: 1, yaw: -0.75 * g, crazyEyes: true, noBank: true, roll: Math.sin(t * 6) * 0.15, squash: 0.2 * bounce(t) });
  if (t > 37.6) shakeAmt = Math.max(shakeAmt, 0.25);
  setCam(t, [0, 1.6, 14], [0, 1.6, 0]);
}

const SCENES = [
  [0, sceneA], [3.45, sceneB], [7.15, sceneC], [10.65, sceneD], [16.45, sceneE],
  [18.4, sceneF], [25.75, sceneG], [31.73, sceneH], [34.1, sceneI],
];
const CUTS = SCENES.slice(1).map(s => s[0]);

// ---------- ТЕКСТ ----------
const LYRICS = [
  [['Кто', 0.00], ['пчёлок', 0.18], ['уважает,', 0.90]],
  [['Кто', 3.50], ['к', 3.84], ['ним', 4.00], ['не', 4.18], ['пристаёт,', 4.38]],
  [['Того', 7.20], ['они', 7.66], ['не', 8.14], ['жалят,', 8.43]],
  [['Тому', 10.72], ['приносят', 11.10], ['мёд.', 11.89]],
  [['Им', 18.40], ['каждая', 19.82], ['ромашка', 20.49]],
  [['Нальёт', 22.05], ['нектара', 23.56], ['в', 24.13], ['чашку,', 24.32]],
  [['И', 26.35], ['даже', 26.92], ['одуванчики', 27.32]],
  [['Нальют', 28.70], ['нектар', 31.73], ['в', 32.55], ['стаканчики.', 32.74]],
];
const LINE_HIDE = [3.42, 7.1, 10.6, 16.9, 21.98, 26.3, 28.66, 35.4];
const WORD_END = [2.0, 5.7, 10.0, 16.4, 21.95, 25.6, 28.7, 34.0];
const FONT_SIZE = 142;
const HILITE = ['#ff2bd6', '#00e5ff', '#ff6a00', '#7cff00'];

function layoutLine(li) {
  ctx.font = `${FONT_SIZE}px Pangolin`;
  const words = LYRICS[li].map(([w]) => ({ w, width: ctx.measureText(w).width }));
  const space = FONT_SIZE * 0.3, maxW = 1010;
  const rows = [[]]; let cur = 0;
  for (const wd of words) {
    if (cur > 0 && cur + space + wd.width > maxW) { rows.push([]); cur = 0; }
    rows[rows.length - 1].push(wd); cur += (cur ? space : 0) + wd.width;
  }
  return { rows, space };
}
let LAYOUT = null;

function drawWord(text, x, y, scale, rot, fill, t, seed, active) {
  ctx.save();
  ctx.translate(x, y); ctx.rotate(rot); ctx.scale(scale, scale);
  ctx.font = `${FONT_SIZE}px Pangolin`;
  ctx.textBaseline = 'middle'; ctx.textAlign = 'left';
  const w = ctx.measureText(text).width;
  let cx = -w / 2;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i], cw = ctx.measureText(ch).width;
    const r = (hash(seed * 13 + i) - 0.5) * 0.22 + (active ? Math.sin(t * 12 + i) * 0.06 : 0);
    const dy = (hash(seed * 7 + i * 3) - 0.5) * 14 + (active ? Math.sin(t * 10 + i * 0.9) * 6 : 0);
    ctx.save();
    ctx.translate(cx + cw / 2, dy); ctx.rotate(r);
    // дешёвый «3D»-WordArt: выдавленная тень
    ctx.lineJoin = 'round';
    for (let k = 9; k >= 1; k--) { ctx.fillStyle = k > 7 ? '#000' : '#5a1a00'; ctx.fillText(ch, -cw / 2 + k * 1.2, k * 1.6); }
    ctx.lineWidth = 14; ctx.strokeStyle = '#000'; ctx.strokeText(ch, -cw / 2, 0);
    ctx.fillStyle = fill; ctx.fillText(ch, -cw / 2, 0);
    // пластиковый блик
    ctx.globalAlpha = 0.45; ctx.fillStyle = '#fff';
    ctx.save(); ctx.beginPath(); ctx.rect(-cw / 2, -FONT_SIZE * 0.5, cw, FONT_SIZE * 0.32); ctx.clip(); ctx.fillText(ch, -cw / 2, 0); ctx.restore();
    ctx.restore();
    cx += cw;
  }
  ctx.restore();
}

function drawLyrics(t) {
  let li = -1;
  for (let i = 0; i < LYRICS.length; i++) if (t >= LYRICS[i][0][1] - 0.08 && t < LINE_HIDE[i]) li = i;
  if (li < 0) return;
  if (!LAYOUT) LAYOUT = LYRICS.map((_, i) => layoutLine(i));
  const words = LYRICS[li], { rows, space } = LAYOUT[li];
  const lineH = FONT_SIZE * 1.15;
  const baseY = rows.length > 1 ? 1600 : 1700;
  const fadeOut = clamp((LINE_HIDE[li] - t) / 0.12);
  let wi = 0;
  rows.forEach((row, r) => {
    const total = row.reduce((s, w) => s + w.width, 0) + space * (row.length - 1);
    let x = W / 2 - total / 2;
    const y = baseY + r * lineH;
    for (const wd of row) {
      const idx = wi++;
      const start = words[idx][1];
      const next = idx + 1 < words.length ? words[idx + 1][1] : WORD_END[li];
      const age = t - start;
      const cx = x + wd.width / 2; x += wd.width + space;
      if (age < -0.04) continue;                       // ещё не спето — не показываем
      const a = Math.max(0, age + 0.04);
      const active = t < next;
      const kind = idx % 3;                            // разные анимации появления
      let sc = easeOutBack(a / 0.22) * (kind === 2 ? lerp(2.2, 1, smooth(a / 0.18)) : 1);
      let rot = kind === 1 ? lerp(-1.2, 0, smooth(a / 0.22)) : 0;
      let dy = kind === 0 ? -Math.abs(Math.sin(a * 14)) * 60 * Math.exp(-a * 5) : 0;
      rot += (hash(li * 10 + idx) - 0.5) * 0.12;
      if (active) { sc *= 1.12 + 0.06 * bounce(t) + Math.min(0.25, Math.max(0, age - 0.5) * 0.08); }
      sc *= fadeOut;
      if (sc <= 0.01) continue;
      const fill = active ? HILITE[(li + idx) % HILITE.length] : '#fff8b0';
      drawWord(wd.w, cx, y + dy, sc, rot + (active ? Math.sin(t * 6) * 0.04 : 0), fill, t, li * 10 + idx, active);
    }
  });
}

// ---------- переход: крутящаяся звезда ----------
function drawStarWipe(t) {
  for (const c of CUTS) {
    const d = t - c;
    if (d < -0.2 || d > 0.2) continue;
    const k = 1 - Math.abs(d) / 0.2;
    const R = smooth(k) * 1700;
    ctx.save(); ctx.translate(W / 2, H * 0.42); ctx.rotate(t * 5);
    ctx.beginPath();
    for (let i = 0; i <= 10; i++) { const a = i / 10 * Math.PI * 2, r = i % 2 ? R * 0.5 : R; i ? ctx.lineTo(Math.cos(a) * r, Math.sin(a) * r) : ctx.moveTo(Math.cos(a) * r, Math.sin(a) * r); }
    ctx.closePath();
    ctx.fillStyle = ['#fff200', '#ff2bd6', '#00e5ff', '#7cff00'][CUTS.indexOf(c) % 4];
    ctx.fill(); ctx.lineWidth = 16; ctx.strokeStyle = '#000'; ctx.stroke();
    ctx.restore();
  }
}

// ---------- кадр ----------
function renderAt(t) {
  ALL.forEach(b => { b.root.visible = false; });
  stars.forEach(s => { s.visible = false; });
  starUsed = 0; shakeAmt = 0;
  let fn = SCENES[0][1];
  for (const [s, f] of SCENES) if (t >= s) fn = f;
  fn(t);
  renderer.render(scene, camera);
  ctx.imageSmoothingEnabled = false;          // пиксельный апскейл ×2 — фирменная «дешёвость»
  ctx.drawImage(glc, 0, 0, W, H);
  // дешёвая виньетка
  const g = ctx.createRadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, H * 0.75);
  g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, 'rgba(0,0,0,0.35)');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  drawStarWipe(t);
  drawLyrics(t);
}

window.DURATION = DURATION;
window.renderFrame = (t, q = 0.93) => { renderAt(t); return out.toDataURL('image/jpeg', q); };
window.renderAt = renderAt;
Promise.all([document.fonts.load(`${FONT_SIZE}px Pangolin`, 'Кто пчёлок')]).then(() => { window.READY = true; });
