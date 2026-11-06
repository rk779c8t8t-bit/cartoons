// "ЭФИР" — cel-shaded music animation. Everything is a pure function of time t (seconds),
// so any frame can be rendered independently.
import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';

const Q = new URLSearchParams(location.search);
const W = +(Q.get('w') || 1920), H = +(Q.get('h') || 1080);
const ENV = await (await fetch('./env60.json')).json();

// ---------------------------------------------------------------- timing
const P = 0.525, B0 = 0.52;
const T = {
  IN: 1.25, LOOK: 2.1, DROP: 2.62, RISE: 3.15, BAR2: 4.72, BAR3: 6.82, LAND: 7.35,
  BAR4: 8.92, BRK: 9.44, RES: 9.97, H1: 10.5, H2: 10.82, OUT: 11.02, OFF: 11.32, END: 13.0,
};
const KICKS = [[2.62,1],[3.15,.6],[3.67,1],[4.2,1],[4.73,1],[5.25,1],[5.77,1],[6.29,1],[6.82,1],[7.35,1],[7.87,1],[8.39,1],[8.92,1],[9.97,1.3],[10.5,.8],[10.82,1],[11.32,1.2]];
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lerp = (a, b, t) => a + (b - a) * t;
const ss = (a, b, x) => { const t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t); };
const seg = (t, a, b) => clamp((t - a) / (b - a));
const eio = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
const eo = t => 1 - Math.pow(1 - t, 3);
const ei = t => t * t * t;
const eoBack = t => { const c = 1.9; return 1 + (c + 1) * Math.pow(t - 1, 3) + c * Math.pow(t - 1, 2); };
const fract = x => x - Math.floor(x);
const beatF = t => (t - B0) / P;
function kick(t, decay = 8) { let v = 0; for (const [k, w] of KICKS) if (t >= k) v = Math.max(v, w * Math.exp(-(t - k) * decay)); return v; }
function lastKick(t) { let l = -10; for (const [k] of KICKS) if (t >= k) l = k; return l; }
function env(name, t) { const a = ENV[name]; const f = t * 60; const i = Math.floor(f); if (i < 0) return a[0]; if (i >= a.length - 1) return 0; return lerp(a[i], a[i + 1], f - i); }
function envS(name, t) { return (env(name, t) + env(name, t - 1 / 60) + env(name, t - 2 / 60) + env(name, t + 1 / 60)) / 4; }
function rng(seed) { let s = seed >>> 0 || 1; return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; }
const noise1 = (x) => { const i = Math.floor(x), f = x - i; const h = n => fract(Math.sin(n * 127.1) * 43758.5453); const u = f * f * (3 - 2 * f); return lerp(h(i), h(i + 1), u) * 2 - 1; };
// animation time: nearly stops during the bullet-time break
const animT = t => (t >= T.BRK && t < T.RES) ? T.BRK + (t - T.BRK) * 0.035 : t;

// ---------------------------------------------------------------- renderer
const renderer = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(1); renderer.setSize(W, H);
renderer.outputColorSpace = THREE.LinearSRGBColorSpace; // final pass does the sRGB encode
document.body.appendChild(renderer.domElement);

function gradTex(steps) {
  const d = new Uint8Array(steps.length * 4);
  steps.forEach((v, i) => { d[i * 4] = d[i * 4 + 1] = d[i * 4 + 2] = v; d[i * 4 + 3] = 255; });
  const t = new THREE.DataTexture(d, steps.length, 1, THREE.RGBAFormat);
  t.minFilter = t.magFilter = THREE.NearestFilter; t.needsUpdate = true; return t;
}
const G3 = gradTex([80, 165, 255]);
const toon = (color, emissive = 0x000000, ei = 1) => new THREE.MeshToonMaterial({ color, gradientMap: G3, emissive, emissiveIntensity: ei });
const OUTLINE = new THREE.ShaderMaterial({
  uniforms: { th: { value: 0.0065 }, col: { value: new THREE.Color(0x0d0814) } },
  vertexShader: `uniform float th;
    #include <common>
    #include <morphtarget_pars_vertex>
    void main(){ vec3 n=normalize(normalMatrix*normal); vec4 mv=modelViewMatrix*vec4(position,1.0);
      float d=clamp(-mv.z,0.6,60.0); mv.xyz+=n*th*d; gl_Position=projectionMatrix*mv; }`,
  fragmentShader: `uniform vec3 col; void main(){ gl_FragColor=vec4(col,1.0); }`,
  side: THREE.BackSide,
});
const SPH = new THREE.SphereGeometry(1, 36, 24);
const capCache = {};
const cap = (r, l) => capCache[r + '_' + l] || (capCache[r + '_' + l] = new THREE.CapsuleGeometry(r, l, 8, 20));
function mk(geo, mat, parent, pos = [0, 0, 0], rot = [0, 0, 0], scl = 1, outline = true) {
  if (typeof mat === 'number') mat = toon(mat);
  const m = new THREE.Mesh(geo, mat);
  m.position.set(...pos); if (Array.isArray(rot)) m.rotation.set(...rot); else if (typeof rot === "number" && rot !== 0) { scl = rot; }
  if (typeof scl === 'number') m.scale.setScalar(scl); else m.scale.set(...scl);
  if (outline) { const o = new THREE.Mesh(geo, OUTLINE); o.raycast = () => {}; m.add(o); }
  parent.add(m); return m;
}
function grp(parent, pos = [0, 0, 0]) { const g = new THREE.Group(); g.position.set(...pos); parent.add(g); return g; }
function canvasTex(w, h, draw) { const c = document.createElement('canvas'); c.width = w; c.height = h; const x = c.getContext('2d'); draw(x, w, h); const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; t.userData.ctx = x; return t; }

// ---------------------------------------------------------------- characters
const DOWN = new THREE.Vector3(0, -1, 0);
function makeChar(cfg) {
  const root = new THREE.Group(); const J = {};
  J.hips = grp(root, [0, 0.99, 0]);
  mk(SPH, cfg.pants, J.hips, [0, 0, 0], 0, [0.35, 0.26, 0.28]);
  J.spine = grp(J.hips, [0, 0.08, 0]);
  mk(cap(0.34, 0.36), cfg.top, J.spine, [0, 0.3, 0], 0, [1.05, 1, 0.82]);
  if (cfg.tee) mk(cap(0.2, 0.34), cfg.tee, J.spine, [0, 0.31, 0.13], 0, [1, 1, 0.92]);
  if (cfg.collar) { mk(SPH, cfg.collar, J.spine, [0.1, 0.78, 0.12], [0.3, 0, 0.6], [0.14, 0.05, 0.1]); mk(SPH, cfg.collar, J.spine, [-0.1, 0.78, 0.12], [0.3, 0, -0.6], [0.14, 0.05, 0.1]); }
  if (cfg.chain) mk(new THREE.TorusGeometry(0.17, 0.018, 8, 32), toon(0xffc83a, 0x553300), J.spine, [0, 0.66, 0.2], [1.2, 0, 0], 1, false);
  J.chest = grp(J.spine, [0, 0.5, 0]);
  J.neck = grp(J.chest, [0, 0.12, 0]);
  mk(cap(0.1, 0.1), cfg.skin, J.neck, [0, 0.05, 0]);
  J.head = grp(J.neck, [0, 0.12, 0]);
  mk(SPH, cfg.skin, J.head, [0, 0.42, 0], 0, [0.5, 0.48, 0.47]);
  mk(SPH, cfg.skin, J.head, [0, 0.27, 0.07], 0, [0.4, 0.29, 0.37]);
  J.eyes = []; J.pupils = []; J.brows = [];
  for (const s of [1, -1]) {
    const eg = grp(J.head, [s * 0.17, 0.47, 0.39]);
    mk(SPH, 0xffffff, eg, [0, 0, 0], 0, [0.105, 0.135, 0.07]);
    const pu = grp(eg, [0, -0.01, 0.05]);
    mk(SPH, new THREE.MeshBasicMaterial({ color: cfg.iris || 0x2a6bd6 }), pu, [0, 0, 0], 0, [0.058, 0.07, 0.03], false);
    mk(SPH, new THREE.MeshBasicMaterial({ color: 0x050505 }), pu, [0, 0, 0.012], 0, [0.032, 0.04, 0.025], false);
    mk(SPH, new THREE.MeshBasicMaterial({ color: 0xffffff }), pu, [0.02, 0.028, 0.03], 0, 0.014, false);
    J.eyes.push(eg); J.pupils.push(pu);
    const bg = grp(J.head, [s * 0.17, 0.66, 0.405]);
    mk(cap(0.026, 0.13), cfg.brow, bg, [0, 0, 0], [0, 0, Math.PI / 2], 1, false);
    bg.userData.s = s; J.brows.push(bg);
    mk(SPH, cfg.skin, J.head, [s * 0.49, 0.42, -0.02], 0, [0.08, 0.12, 0.06]);
    if (cfg.blush) mk(SPH, new THREE.MeshBasicMaterial({ color: 0xff8a8a, transparent: true, opacity: .55 }), J.head, [s * 0.27, 0.3, 0.36], [0, s * 0.5, 0], [0.08, 0.04, 0.03], false);
  }
  mk(SPH, cfg.skin, J.head, [0, 0.37, 0.47], 0, [0.075, 0.065, 0.065]);
  J.mouth = grp(J.head, [0, 0.2, 0.4]);
  mk(SPH, 0x4a0c1a, J.mouth, [0, 0, 0], 0, [0.13, 0.08, 0.06]);
  mk(SPH, 0xffffff, J.mouth, [0, 0.05, 0.022], 0, [0.095, 0.022, 0.04], false);
  mk(SPH, 0xd0455a, J.mouth, [0, -0.04, 0.02], 0, [0.07, 0.03, 0.04], false);
  const capGeo = new THREE.SphereGeometry(1, 36, 18, 0, Math.PI * 2, 0, Math.PI * 0.47);
  if (cfg.hair === 'blond') {
    mk(capGeo, cfg.hairCol, J.head, [0, 0.44, -0.03], [-0.42, 0, 0], [0.53, 0.55, 0.52]);
    mk(SPH, cfg.hairCol, J.head, [0.1, 0.8, 0.26], [0.5, 0, -0.4], [0.24, 0.09, 0.17]);
    mk(SPH, cfg.hairCol, J.head, [-0.14, 0.78, 0.24], [0.5, 0, 0.5], [0.2, 0.08, 0.15]);
  } else {
    mk(capGeo, cfg.hairCol, J.head, [0, 0.47, -0.01], [-0.18, 0, 0], [0.545, 0.62, 0.535]);
    mk(new THREE.TorusGeometry(0.5, 0.085, 14, 48), cfg.hairCol, J.head, [0, 0.55, 0.0], [Math.PI / 2 - 0.18, 0, 0], [1.06, 1.03, 1]);
    mk(SPH, 0xffffff, J.head, [0, 0.62, 0.52], [-0.2, 0, 0], [0.09, 0.05, 0.02], false);
  }
  // arms
  for (const s of [1, -1]) {
    const k = s > 0 ? 'l' : 'r';
    const sh = J[k + 'Sh'] = grp(J.chest, [s * 0.42, 0.1, 0]);
    mk(SPH, cfg.top, sh, [0, 0, 0], 0, 0.17);
    mk(cap(0.13, 0.26), cfg.sleeve, sh, [0, -0.2, 0]);
    if (cfg.stripe) mk(cap(0.028, 0.34), cfg.stripe, sh, [s * 0.11, -0.21, 0.0], 0, 1, false);
    const el = J[k + 'El'] = grp(sh, [0, -0.42, 0]);
    mk(cap(0.115, 0.24), cfg.sleeve2 || cfg.sleeve, el, [0, -0.18, 0]);
    if (cfg.stripe) mk(cap(0.026, 0.3), cfg.stripe, el, [s * 0.1, -0.18, 0.0], 0, 1, false);
    if (cfg.cuff) mk(new THREE.TorusGeometry(0.105, 0.035, 8, 24), cfg.cuff, el, [0, -0.34, 0], [Math.PI / 2, 0, 0], 1, true);
    const hd = J[k + 'Hand'] = grp(el, [0, -0.4, 0]);
    mk(SPH, cfg.skin, hd, [0, 0, 0], 0, [0.13, 0.15, 0.115]);
    mk(SPH, cfg.skin, hd, [-s * 0.09, 0.03, 0.07], [0.4, 0, 0], [0.05, 0.08, 0.05]);
  }
  // legs
  for (const s of [1, -1]) {
    const k = s > 0 ? 'l' : 'r';
    const hp = J[k + 'Hip'] = grp(J.hips, [s * 0.17, -0.06, 0]);
    mk(cap(0.16, 0.24), cfg.pants, hp, [0, -0.2, 0]);
    const kn = J[k + 'Knee'] = grp(hp, [0, -0.42, 0]);
    mk(cap(0.145, 0.24), cfg.pants, kn, [0, -0.2, 0]);
    const ft = J[k + 'Foot'] = grp(kn, [0, -0.42, 0]);
    mk(SPH, cfg.shoe, ft, [0, -0.03, 0.08], 0, [0.16, 0.1, 0.25]);
    mk(SPH, cfg.sole || 0xffffff, ft, [0, -0.09, 0.08], 0, [0.165, 0.035, 0.255], false);
  }
  if (cfg.mic) {
    const mic = J.mic = grp(J.rHand, [0, 0, 0]);
    mk(new THREE.CylinderGeometry(0.035, 0.024, 0.34, 16), 0x1a1a22, mic, [0, 0.06, 0]);
    mk(SPH, toon(0xb8bcc8, 0x111111), mic, [0, 0.27, 0], 0, 0.08);
    mk(new THREE.TorusGeometry(0.06, 0.015, 8, 20), 0x303040, mic, [0, 0.21, 0], [Math.PI / 2, 0, 0], 1, false);
  }
  root.userData = { J, cfg };
  return root;
}

const _m = new THREE.Matrix4(), _q = new THREE.Quaternion(), _q2 = new THREE.Quaternion(), _q3 = new THREE.Quaternion();
const V = (a) => new THREE.Vector3(a[0], a[1], a[2]);
function ik(upper, lower, a, b, tWorld, pWorld) {
  const parent = upper.parent; parent.updateMatrixWorld(true);
  _m.copy(parent.matrixWorld).invert();
  const S = upper.position.clone();
  const Tt = tWorld.clone().applyMatrix4(_m);
  const Pp = pWorld.clone().applyMatrix4(_m);
  const d = Tt.clone().sub(S); let dist = d.length(); const dn = d.clone().normalize();
  dist = clamp(dist, 0.08, (a + b) * 0.998);
  const cosA = clamp((a * a + dist * dist - b * b) / (2 * a * dist), -1, 1), sinA = Math.sqrt(1 - cosA * cosA);
  const pv = Pp.clone().sub(S); pv.sub(dn.clone().multiplyScalar(pv.dot(dn)));
  if (pv.lengthSq() < 1e-8) pv.set(0, 0, 1); pv.normalize();
  const u = dn.clone().multiplyScalar(cosA).add(pv.multiplyScalar(sinA)).normalize();
  const E = S.clone().add(u.clone().multiplyScalar(a));
  const f = S.clone().add(dn.multiplyScalar(dist)).sub(E).normalize();
  upper.quaternion.setFromUnitVectors(DOWN, u);
  const fl = f.applyQuaternion(_q.copy(upper.quaternion).invert());
  lower.quaternion.setFromUnitVectors(DOWN, fl);
}
// orient `node` so that in character space it has rotation `eul`
function orientInChar(node, root, eul) {
  node.parent.updateMatrixWorld(true);
  node.parent.getWorldQuaternion(_q).invert();
  root.getWorldQuaternion(_q2);
  _q3.setFromEuler(new THREE.Euler(eul[0], eul[1], eul[2]));
  node.quaternion.copy(_q).multiply(_q2).multiply(_q3);
}
const DEF = {
  hx: 0, hy: 0, hz: 0, hips: [0, 0, 0], spine: [0, 0, 0], chest: [0, 0, 0], neck: [0, 0, 0], head: [0, 0, 0],
  lH: [0.5, 0.85, 0.05], rH: [-0.5, 0.85, 0.05], lHp: [1, -0.4, -1], rHp: [-1, -0.4, -1],
  lF: [0.2, 0.12, 0.02], rF: [-0.2, 0.12, 0.02], lFp: [0.3, 0, 1], rFp: [-0.3, 0, 1], lFr: [0, 0.15, 0], rFr: [0, -0.15, 0],
  mouth: 0, blink: 0, brow: 0, browT: 0, look: [0, 0], smile: 0, mic: [0.25, 0, 0], lHr: [0, 0, 0], rHr: [0, 0, 0],
};
function blend(a, b, w) {
  const o = {};
  for (const k in DEF) {
    const x = a[k] ?? DEF[k], y = b[k] ?? DEF[k];
    o[k] = Array.isArray(x) ? x.map((v, i) => lerp(v, y[i], w)) : lerp(x, y, w);
  }
  return o;
}
function applyPose(ch, p) {
  p = blend(p, p, 0);
  const J = ch.userData.J;
  J.hips.position.set(p.hx, 0.99 + p.hy, p.hz); J.hips.rotation.set(...p.hips);
  J.spine.rotation.set(...p.spine); J.chest.rotation.set(...p.chest); J.neck.rotation.set(...p.neck); J.head.rotation.set(...p.head);
  ch.updateMatrixWorld(true);
  const W = (a) => ch.localToWorld(V(a));
  const sL = [0.42 + p.hx, 1.67 + p.hy, p.hz], sR = [-0.42 + p.hx, 1.67 + p.hy, p.hz];
  const mid = (s, t, d) => [(s[0] + t[0]) / 2 + d[0] * .6, (s[1] + t[1]) / 2 + d[1] * .6, (s[2] + t[2]) / 2 + d[2] * .6];
  ik(J.lSh, J.lEl, 0.42, 0.4, W(p.lH), W(mid(sL, p.lH, p.lHp)));
  ik(J.rSh, J.rEl, 0.42, 0.4, W(p.rH), W(mid(sR, p.rH, p.rHp)));
  const hL = [0.17 + p.hx, 0.93 + p.hy, p.hz], hR = [-0.17 + p.hx, 0.93 + p.hy, p.hz];
  ik(J.lHip, J.lKnee, 0.42, 0.42, W(p.lF), W(mid(hL, p.lF, p.lFp)));
  ik(J.rHip, J.rKnee, 0.42, 0.42, W(p.rF), W(mid(hR, p.rF, p.rFp)));
  orientInChar(J.lFoot, ch, p.lFr); orientInChar(J.rFoot, ch, p.rFr);
  orientInChar(J.lHand, ch, p.lHr); orientInChar(J.rHand, ch, p.rHr);
  if (J.mic) orientInChar(J.mic, ch, p.mic);
  // face
  J.mouth.scale.set(1 + 0.3 * p.smile - 0.2 * p.mouth, lerp(0.14, 1.35, clamp(p.mouth, 0, 1.2)), 1);
  J.mouth.position.y = 0.2 - 0.02 * p.mouth;
  for (const e of J.eyes) e.scale.y = Math.max(0.06, 1 - p.blink);
  for (const pu of J.pupils) pu.position.set(p.look[0] * 0.035, -0.01 + p.look[1] * 0.04, 0.05);
  for (const b of J.brows) { b.position.y = 0.66 + p.brow * 0.07; b.rotation.z = b.userData.s * p.browT; }
}

// ---------------------------------------------------------------- MAIN WORLD
const main = new THREE.Scene();
main.fog = new THREE.FogExp2(0x1a0830, 0.0045);
const mainCam = new THREE.PerspectiveCamera(40, W / H, 0.1, 900);

const sky = new THREE.Mesh(new THREE.SphereGeometry(800, 32, 16), new THREE.ShaderMaterial({
  side: THREE.BackSide, depthWrite: false, fog: false,
  uniforms: { top: { value: new THREE.Color(0x05021a) }, bot: { value: new THREE.Color(0x5b1660) }, glow: { value: 0 } },
  vertexShader: `varying vec3 vp; void main(){ vp=normalize(position); gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0); }`,
  fragmentShader: `uniform vec3 top,bot; uniform float glow; varying vec3 vp; void main(){ float h=clamp(vp.y*1.6+0.15,0.0,1.0); vec3 c=mix(bot,top,pow(h,0.7)); c+=bot*glow*exp(-abs(vp.y)*8.0); gl_FragColor=vec4(c,1.0); }`,
}));
main.add(sky);
// stars
{
  const r = rng(7), n = 1400, pos = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) { const th = r() * Math.PI * 2, ph = Math.acos(r() * 0.95); pos.set([Math.sin(ph) * Math.cos(th) * 700, Math.cos(ph) * 700 - 40, Math.sin(ph) * Math.sin(th) * 700], i * 3); }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  main.add(new THREE.Points(g, new THREE.PointsMaterial({ color: 0xfff4e0, size: 2.2, sizeAttenuation: false, fog: false })));
}
const amb = new THREE.HemisphereLight(0x8a7bd0, 0x2a1030, 0.9); main.add(amb);
const key = new THREE.DirectionalLight(0xfff1e0, 1.6); key.position.set(4, 9, 8); main.add(key);
const rimA = new THREE.PointLight(0xff2bd6, 30, 0, 0); rimA.position.set(-6, 6, -5); main.add(rimA);
const rimB = new THREE.PointLight(0x2bd9ff, 30, 0, 0); rimB.position.set(6, 6, -5); main.add(rimB);
const front = new THREE.PointLight(0xffffff, 0, 0, 0); front.position.set(0, 4, 6); main.add(front);
for (const l of [rimA, rimB, front]) { l.intensity = 1; }

// world = everything that flies away during the flight
const world = grp(main);
const STAGE_TOP = 0.4;
// rooftop / studio floor
mk(new THREE.BoxGeometry(26, 1, 22), 0x2a1f3d, world, [0, -0.5, 1]);
mk(new THREE.BoxGeometry(26.4, 0.25, 0.4), 0x8a8fa8, world, [0, 0.12, 12]); // front ledge
for (let i = -12; i <= 12; i += 2) mk(new THREE.CylinderGeometry(0.06, 0.06, 1.1, 8), 0x8a8fa8, world, [i, 0.55, 11.9]);
mk(new THREE.BoxGeometry(26, 0.1, 0.1), 0x8a8fa8, world, [0, 1.1, 11.9]);
// building body under the roof
mk(new THREE.BoxGeometry(25.6, 80, 21.6), toon(0x231a36), world, [0, -41, 1], 0, 1, false);
const stage = grp(world);
mk(new THREE.CylinderGeometry(4.2, 4.4, STAGE_TOP, 64), 0x1c1430, stage, [0, STAGE_TOP / 2, 0]);
mk(new THREE.TorusGeometry(4.25, 0.06, 8, 96), toon(0xffffff, 0xffd6ff, 1), stage, [0, STAGE_TOP, 0], [Math.PI / 2, 0, 0], 1, false);
// disco tiles
const tileGeo = new THREE.BoxGeometry(0.5, 0.06, 0.5);
const tileMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
const tilePos = [];
for (let x = -4; x <= 4; x += 0.55) for (let z = -4; z <= 4; z += 0.55) if (x * x + z * z < 3.85 * 3.85) tilePos.push([x, z]);
const tiles = new THREE.InstancedMesh(tileGeo, tileMat, tilePos.length);
tiles.instanceColor = new THREE.InstancedBufferAttribute(new Float32Array(tilePos.length * 3), 3);
stage.add(tiles);
// shockwave ring
const shock = new THREE.Mesh(new THREE.RingGeometry(0.85, 1, 96), new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide }));
shock.rotation.x = -Math.PI / 2; shock.position.y = STAGE_TOP + 0.08; world.add(shock);
// speakers
const speakers = [];
for (const s of [-1, 1]) {
  const sp = grp(world, [s * 6.2, 0, -1.5]);
  mk(new RoundedBoxGeometry(1.8, 3.2, 1.4, 3, 0.12), 0x15121c, sp, [0, 1.6, 0]);
  const cones = [];
  for (const [y, r] of [[2.45, 0.42], [1.2, 0.62]]) {
    mk(new THREE.CylinderGeometry(r + 0.08, r + 0.08, 0.06, 32), 0x2c2838, sp, [0, y, 0.7], [Math.PI / 2, 0, 0]);
    const c = mk(new THREE.ConeGeometry(r, 0.25, 32, 1, true), toon(0x3a3550), sp, [0, y, 0.72], [-Math.PI / 2, 0, 0], 1, false);
    mk(SPH, 0x9a96b0, c, [0, -0.1, 0], 0, 0.12 / r * 0.9);
    cones.push(c);
  }
  sp.userData.cones = cones; speakers.push(sp);
}
// LED wall texture
const led = canvasTex(1024, 384, () => {});
function drawLED(t) {
  const x = led.userData.ctx, w = 1024, h = 384; const k = kick(t, 6); const post = t >= T.DROP;
  const g = x.createLinearGradient(0, 0, w, h);
  g.addColorStop(0, post ? '#3a0008' : '#1a0640'); g.addColorStop(1, post ? '#120010' : '#06123a'); x.fillStyle = g; x.fillRect(0, 0, w, h);
  // equalizer
  for (let i = 0; i < 48; i++) {
    const v = clamp(0.15 + env('rms', t - i * 0.004) * (0.5 + 0.5 * Math.abs(Math.sin(i * 1.7 + t * 6))) * (0.6 + 0.6 * k));
    x.fillStyle = post ? `hsl(${350 + i},90%,${45 + v * 20}%)` : `hsl(${260 + i * 2},90%,${50 + v * 20}%)`;
    const bh = v * h * 0.85; x.fillRect(i * (w / 48) + 3, h - bh, w / 48 - 6, bh);
  }
  x.save(); x.textAlign = 'center'; x.textBaseline = 'middle';
  x.font = `bold ${160 + k * 18}px DejaVu Sans`; x.shadowColor = post ? '#ff2040' : '#ff40ff'; x.shadowBlur = 40;
  x.fillStyle = '#fff'; x.fillText(post ? 'МЭШАП' : 'ЭФИР', w / 2 + (post ? noise1(t * 30) * 8 * k : 0), h / 2);
  x.restore();
  // scanlines
  x.fillStyle = 'rgba(0,0,0,0.25)'; for (let y = 0; y < h; y += 4) x.fillRect(0, y, w, 1.5);
  led.needsUpdate = true;
}
// walls (hinged at the floor)
const walls = {};
{
  const wallMat = toon(0x3b2758);
  const back = walls.back = grp(world, [0, 0, -8.5]);
  mk(new THREE.BoxGeometry(26, 11, 0.5), wallMat, back, [0, 5.5, 0]);
  mk(new THREE.PlaneGeometry(14, 5.25), new THREE.MeshBasicMaterial({ map: led, toneMapped: false }), back, [0, 5.4, 0.27], 0, 1, false);
  mk(new THREE.BoxGeometry(14.6, 5.8, 0.3), 0x15121c, back, [0, 5.4, 0.16]);
  for (const s of [-1, 1]) for (let i = 0; i < 3; i++) mk(new THREE.BoxGeometry(0.25, 9, 0.2), new THREE.MeshBasicMaterial({ color: 0xff40d0 }), back, [s * (8.5 + i * 1.3), 5, 0.3], 0, 1, false);
  for (const s of [-1, 1]) {
    const side = walls[s < 0 ? 'left' : 'right'] = grp(world, [s * 12.8, 0, 1]);
    mk(new THREE.BoxGeometry(0.5, 11, 22), wallMat, side, [0, 5.5, 0]);
    for (let i = 0; i < 6; i++) mk(new THREE.BoxGeometry(0.2, 0.25, 18), new THREE.MeshBasicMaterial({ color: i % 2 ? 0x40e0ff : 0xff40d0 }), side, [-s * 0.3, 1.5 + i * 1.6, 0], 0, 1, false);
  }
}
// truss + spot beams
const truss = grp(world, [0, 9.2, -1]);
const beams = [];
{
  for (const z of [-2, 2]) mk(new THREE.BoxGeometry(22, 0.35, 0.35), 0x8a8fa8, truss, [0, 0, z]);
  for (let x = -10; x <= 10; x += 2.5) mk(new THREE.BoxGeometry(0.2, 0.2, 4), 0x8a8fa8, truss, [x, 0, 0]);
  const beamGeo = new THREE.ConeGeometry(1.6, 10, 32, 1, true); beamGeo.translate(0, -5, 0);
  for (let i = 0; i < 8; i++) {
    const x = -8.75 + i * 2.5; const holder = grp(truss, [x, -0.3, i % 2 ? 2 : -2]);
    mk(new THREE.CylinderGeometry(0.25, 0.35, 0.6, 16), 0x111118, holder, [0, 0, 0]);
    const b = new THREE.Mesh(beamGeo, new THREE.MeshBasicMaterial({ color: 0xff40ff, transparent: true, opacity: 0.12, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide, fog: false }));
    holder.add(b); beams.push(holder);
  }
}
// crowd (silhouettes)
const crowd = [];
{
  const r = rng(11);
  const body = new THREE.InstancedMesh(cap(0.32, 0.6), new THREE.MeshToonMaterial({ color: 0x1d0f2e, gradientMap: G3 }), 140);
  const head = new THREE.InstancedMesh(SPH, new THREE.MeshToonMaterial({ color: 0x24133a, gradientMap: G3 }), 140);
  const arm = new THREE.InstancedMesh(cap(0.09, 0.7), new THREE.MeshToonMaterial({ color: 0x1d0f2e, gradientMap: G3 }), 280);
  let n = 0;
  while (n < 140) {
    const x = (r() * 2 - 1) * 11.5, z = -6 + r() * 17.2;
    if (Math.hypot(x, z) < 5.2) continue;
    if (x > -4.8 && x < 7.5 && z > 3.5) continue;
    if (z < -1.5 && Math.abs(x) < 7.5) continue;
    crowd.push({ x, z, ph: r(), s: 0.85 + r() * 0.3, up: r() < 0.45, d: Math.hypot(x, z) }); n++;
  }
  world.add(body, head, arm);
  crowd.meshes = { body, head, arm };
}
// confetti
const CONF_N = 420;
const confetti = new THREE.InstancedMesh(new THREE.PlaneGeometry(0.12, 0.2), new THREE.MeshBasicMaterial({ side: THREE.DoubleSide, fog: false }), CONF_N);
confetti.instanceColor = new THREE.InstancedBufferAttribute(new Float32Array(CONF_N * 3), 3);
{ const r = rng(5), pal = [0xff2a55, 0xffffff, 0xffd23a, 0x3ad7ff, 0xff4fd8]; for (let i = 0; i < CONF_N; i++) confetti.setColorAt(i, new THREE.Color(pal[Math.floor(r() * pal.length)])); }
main.add(confetti);

// city
const city = grp(main);
{
  const winTex = canvasTex(64, 128, (x, w, h) => {
    x.fillStyle = '#000'; x.fillRect(0, 0, w, h); const r = rng(3);
    for (let yy = 4; yy < h; yy += 12) for (let xx = 4; xx < w; xx += 12) { const v = r(); x.fillStyle = v < 0.35 ? '#ffd27a' : v < 0.45 ? '#7ad7ff' : v < 0.5 ? '#ff7ad7' : '#120c20'; x.fillRect(xx, yy, 7, 8); }
  });
  winTex.wrapS = winTex.wrapT = THREE.RepeatWrapping; winTex.magFilter = THREE.NearestFilter;
  const r = rng(21); const bGeo = new THREE.BoxGeometry(1, 1, 1);
  const cols = [0x1a1430, 0x221a3e, 0x161028, 0x2a1d44];
  for (let i = 0; i < 170; i++) {
    const a = r() * Math.PI * 2, d = 30 + Math.pow(r(), 0.8) * 190;
    const x = Math.cos(a) * d, z = Math.sin(a) * d - 20;
    if (z > 20 && Math.abs(x) < 40) continue; // keep the camera side open
    const w = 6 + r() * 12, dd = 6 + r() * 12; const top = -6 + r() * (d > 70 ? 45 : 14) + (d > 120 ? 20 : 0);
    const h = top + 120; const tex = winTex.clone(); tex.repeat.set(Math.max(1, Math.round(w / 12)), Math.max(1, Math.round(h / 26))); tex.needsUpdate = true;
    const m = new THREE.Mesh(bGeo, new THREE.MeshToonMaterial({ color: cols[i % 4], gradientMap: G3, emissiveMap: tex, emissive: 0xffffff, emissiveIntensity: 0.65 }));
    m.scale.set(w, h, dd); m.position.set(x, top - h / 2, z); city.add(m);
    if (r() < 0.25) { const ant = new THREE.Mesh(new THREE.CylinderGeometry(0.15, 0.15, 6, 6), new THREE.MeshBasicMaterial({ color: 0x302848 })); ant.position.set(x, top + 3, z); city.add(ant);
      const bl = new THREE.Mesh(SPH, new THREE.MeshBasicMaterial({ color: 0xff2030 })); bl.scale.setScalar(0.35); bl.position.set(x, top + 6, z); bl.userData.blink = r(); city.add(bl); }
  }
  // moon
  const moon = new THREE.Mesh(new THREE.CircleGeometry(16, 64), new THREE.MeshBasicMaterial({ color: 0xfff0d0, fog: false }));
  moon.position.set(-90, 75, -300); moon.lookAt(0, 0, 0); city.add(moon);
  const halo = new THREE.Mesh(new THREE.CircleGeometry(34, 64), new THREE.MeshBasicMaterial({ color: 0xff9ad0, transparent: true, opacity: 0.18, fog: false, depthWrite: false }));
  halo.position.set(-90, 75, -301); halo.lookAt(0, 0, 0); city.add(halo);
  // billboard
  const bb = canvasTex(1024, 512, (x, w, h) => {
    const g = x.createLinearGradient(0, 0, 0, h); g.addColorStop(0, '#ff2a55'); g.addColorStop(1, '#6a0a8a'); x.fillStyle = g; x.fillRect(0, 0, w, h);
    x.fillStyle = '#fff'; x.textAlign = 'center'; x.font = 'bold 190px DejaVu Sans'; x.shadowColor = '#000'; x.shadowBlur = 20; x.fillText('ЭФИР', w / 2, 250);
    x.font = 'bold 70px DejaVu Sans'; x.fillStyle = '#ffe14a'; x.fillText('★ МЭШАП 2002 ★', w / 2, 400);
  });
  const board = grp(city, [-34, 4, -48]); board.rotation.y = 0.55;
  mk(new THREE.BoxGeometry(26, 13, 0.6), 0x111018, board, [0, 0, 0]);
  mk(new THREE.PlaneGeometry(25, 12), new THREE.MeshBasicMaterial({ map: bb, fog: false }), board, [0, 0, 0.32], 0, 1, false);
  for (const s of [-1, 1]) mk(new THREE.BoxGeometry(0.6, 30, 0.6), 0x2a2438, board, [s * 9, -21, -0.5]);
}
city.visible = true;

// characters
const crooner = makeChar({ skin: 0xffcfae, top: 0xf4f4fa, tee: 0xbcd4ff, collar: 0xffffff, sleeve: 0xf4f4fa, pants: 0x6a8fd8, shoe: 0x222230, sole: 0xeeeeee, hair: 'blond', hairCol: 0xffe08a, brow: 0xc8a050, iris: 0x2a7be0, blush: true, mic: true, chain: true });
const mc = makeChar({ skin: 0xffd9bf, top: 0xd81e30, tee: 0xffffff, sleeve: 0xd81e30, stripe: 0xffffff, cuff: 0xffffff, pants: 0x50566e, shoe: 0xffffff, sole: 0xd81e30, hair: 'beanie', hairCol: 0xd81e30, brow: 0xd8b070, iris: 0x2a9ad6 });
main.add(crooner, mc);

// boombox
const boom = grp(main);
const boomCones = [];
{
  mk(new RoundedBoxGeometry(4.6, 1.7, 1.3, 4, 0.22), 0xc9ccd8, boom, [0, 0, 0]);
  mk(new RoundedBoxGeometry(4.3, 0.5, 1.32, 3, 0.1), 0x23202c, boom, [0, 0.45, 0.01]);
  mk(new THREE.BoxGeometry(1.2, 0.36, 0.1), new THREE.MeshBasicMaterial({ color: 0x40ffd0 }), boom, [0, 0.45, 0.66], 0, 1, false);
  for (const s of [-1, 1]) {
    mk(new THREE.CylinderGeometry(0.62, 0.62, 0.1, 40), 0x23202c, boom, [s * 1.45, -0.18, 0.62], [Math.PI / 2, 0, 0]);
    const c = mk(new THREE.ConeGeometry(0.55, 0.3, 40, 1, true), toon(0x3a3550), boom, [s * 1.45, -0.18, 0.7], [-Math.PI / 2, 0, 0], 1, false);
    mk(SPH, 0xd81e30, c, [0, -0.1, 0], 0.13);
    boomCones.push(c);
  }
  mk(new THREE.BoxGeometry(1.1, 0.5, 0.08), 0x1a1a24, boom, [0, -0.2, 0.66]);
  for (let i = 0; i < 4; i++) mk(new THREE.BoxGeometry(0.16, 0.12, 0.12), 0xffffff, boom, [-0.42 + i * 0.28, 0.0, 0.66]);
  mk(new THREE.TorusGeometry(1.4, 0.09, 10, 40, Math.PI), 0x8a8fa8, boom, [0, 0.85, -0.3], [0, 0, 0]);
  // jet flames
  for (const s of [-1, 1]) {
    const fl = new THREE.Mesh(new THREE.ConeGeometry(0.35, 2.2, 20, 1, true), new THREE.MeshBasicMaterial({ color: 0x40e0ff, transparent: true, opacity: 0.8, blending: THREE.AdditiveBlending, depthWrite: false, fog: false }));
    fl.position.set(s * 1.5, -0.4, -1.4); fl.rotation.x = -Math.PI / 2; fl.userData.flame = true; boom.add(fl);
  }
}

// TV tunnel
const tvGroup = grp(main);
const tvs = [];
const SCREEN_VS = `varying vec2 vUv; void main(){ vUv=uv; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0); }`;
const SCREEN_FS = `uniform float uTime,uSeed,uKick,uRed,uMode; varying vec2 vUv;
  float h(vec2 p){return fract(sin(dot(p,vec2(12.9898,78.233)))*43758.5453);}
  void main(){ vec2 uv=vUv; vec3 c;
    float m=uMode;
    if(m<1.0){ float i=floor(uv.x*7.0); c=vec3(step(1.0,mod(i,2.0)+0.5*step(3.0,i)),step(2.0,mod(i+1.0,4.0)),step(1.0,mod(i,2.0)+step(4.0,i)))*0.9+0.1; }
    else if(m<2.0){ c=vec3(h(floor(uv*vec2(160.,120.))+floor(uTime*24.0)+uSeed)); }
    else if(m<3.0){ vec2 p=uv-0.5; float r=length(p*vec2(1.3,1.0)); c=mix(vec3(1.0,0.85,0.1),vec3(0.05),smoothstep(0.32,0.3,r)*0.0);
      c=vec3(1.0,0.85,0.15)*smoothstep(0.36,0.35,r); vec2 e=vec2(abs(p.x)-0.11,p.y-0.08); c*=1.0-smoothstep(0.045,0.04,length(e*vec2(1.0,0.7)));
      float sm=abs(length(p-vec2(0.0,0.05))-0.2); c*=1.0-step(sm,0.025)*step(p.y,-0.02); c+=vec3(0.25,0.0,0.4)*(1.0-smoothstep(0.35,0.36,r)); }
    else { float bars=floor(uv.x*10.0); float v=0.3+0.6*abs(sin(bars*1.7+uTime*7.0+uSeed)); c=mix(vec3(0.1,0.0,0.2),vec3(0.2,1.0,0.8),step(uv.y,v)*step(0.1,fract(uv.x*10.0))); }
    c=mix(c,vec3(1.0,0.08,0.15)*(0.6+0.4*h(floor(uv*40.0)+floor(uTime*12.0))),uRed);
    c*=0.85+0.15*sin(uv.y*240.0); c*=1.0+uKick*1.3; vec2 q=uv-0.5; c*=1.0-dot(q,q)*1.4;
    gl_FragColor=vec4(c,1.0); }`;
{
  const r = rng(31);
  const bodyGeo = new RoundedBoxGeometry(1.7, 1.3, 1.25, 3, 0.18);
  const bodyCols = [0x7a5038, 0xd8d0c0, 0x2a2a34, 0xc23040, 0x3a6ad0];
  for (let i = 0; i < 64; i++) {
    const g = grp(tvGroup);
    mk(bodyGeo, bodyCols[i % 5], g, [0, 0, 0]);
    const mat = new THREE.ShaderMaterial({ vertexShader: SCREEN_VS, fragmentShader: SCREEN_FS, uniforms: { uTime: { value: 0 }, uSeed: { value: r() * 10 }, uKick: { value: 0 }, uRed: { value: 0 }, uMode: { value: Math.floor(r() * 4) } } });
    mk(new THREE.PlaneGeometry(1.28, 0.96), mat, g, [-0.08, 0.02, 0.63], 0, 1, false);
    mk(new THREE.CylinderGeometry(0.02, 0.02, 0.9, 6), 0x222222, g, [0.25, 0.95, 0], [0, 0, -0.45], 1, false);
    mk(new THREE.CylinderGeometry(0.02, 0.02, 0.9, 6), 0x222222, g, [-0.25, 0.95, 0], [0, 0, 0.45], 1, false);
    const ang = i * 2.39996 + r() * 0.3, rad = 6 + r() * 5;
    tvs.push({ g, mat, ang, rad, z0: -(i / 64) * 96, spin: (r() - .5) * 1.5, tumble: r() * 6.28, seed: r() });
  }
}
// speed lines
const lines = [];
{
  const r = rng(41); const geo = new THREE.BoxGeometry(0.04, 0.04, 6);
  for (let i = 0; i < 90; i++) {
    const m = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ color: i % 3 ? 0xffffff : 0xff4fd8, transparent: true, opacity: 0.0, blending: THREE.AdditiveBlending, depthWrite: false, fog: false }));
    lines.push({ m, ang: r() * 6.283, rad: 2.5 + r() * 12, z0: r() * 100, sp: 1.6 + r() }); main.add(m);
  }
}

// ---------------------------------------------------------------- ROOM (the TV in a dark bedroom)
const room = new THREE.Scene();
room.background = new THREE.Color(0x05040a);
const roomCam = new THREE.PerspectiveCamera(40, W / H, 0.05, 100);
const rt = new THREE.WebGLRenderTarget(1024, 768, { samples: 4, type: THREE.HalfFloatType });
const crtMat = new THREE.ShaderMaterial({
  uniforms: { tex: { value: rt.texture }, uTime: { value: 0 }, uOff: { value: 0 }, uStatic: { value: 0 }, uDot: { value: 0 }, uBright: { value: 1.25 } },
  vertexShader: SCREEN_VS,
  fragmentShader: `uniform sampler2D tex; uniform float uTime,uOff,uStatic,uDot,uBright; varying vec2 vUv;
    float h(vec2 p){return fract(sin(dot(p,vec2(12.9898,78.233)))*43758.5453);}
    void main(){ vec2 c=vUv-0.5; c*=1.0+dot(c,c)*0.18;
      float sy=mix(1.0,0.006,smoothstep(0.0,0.55,uOff)); float sx=mix(1.0,0.006,smoothstep(0.55,1.0,uOff));
      vec2 cc=c/vec2(sx,sy); vec3 col=vec3(0.0);
      if(abs(cc.x)<0.5&&abs(cc.y)<0.5){ col=texture2D(tex,cc+0.5).rgb*uBright;
        col=mix(col,vec3(h(floor((cc+0.5)*vec2(200.,150.))+floor(uTime*30.0))),uStatic);
        col*=0.82+0.18*sin((cc.y+0.5)*480.0); col+=vec3(uOff*2.5); float e=max(abs(cc.x),abs(cc.y)); col*=smoothstep(0.5,0.42,e)*0.6+0.4; }
      col+=vec3(0.8,0.9,1.0)*uDot*exp(-length(c*vec2(1.0,1.3))*40.0)*3.0;
      gl_FragColor=vec4(col,1.0); }`,
});
const tvRoom = grp(room, [0, 0, 0]);
const roomLights = {};
{
  const wall = canvasTex(512, 512, (x, w, h) => { x.fillStyle = '#2c3a2a'; x.fillRect(0, 0, w, h); for (let i = 0; i < 16; i++) { x.fillStyle = i % 2 ? '#344632' : '#263224'; x.fillRect(i * 32, 0, 16, h); } x.fillStyle = '#4a5a30'; for (let y = 0; y < h; y += 64) for (let xx = 0; xx < w; xx += 64) { x.beginPath(); x.arc(xx + 32 + (y / 64 % 2) * 16, y + 32, 7, 0, 7); x.fill(); } });
  wall.wrapS = wall.wrapT = THREE.RepeatWrapping; wall.repeat.set(4, 2);
  mk(new THREE.PlaneGeometry(16, 8), new THREE.MeshToonMaterial({ map: wall, gradientMap: G3 }), room, [0, 4, -1.6], 0, 1, false);
  const floorT = canvasTex(256, 256, (x, w, h) => { for (let i = 0; i < 8; i++) { x.fillStyle = i % 2 ? '#5a3a24' : '#4e321e'; x.fillRect(0, i * 32, w, 32); x.fillStyle = '#2a1a10'; x.fillRect(0, i * 32, w, 2); } });
  floorT.wrapS = floorT.wrapT = THREE.RepeatWrapping; floorT.repeat.set(4, 4);
  mk(new THREE.PlaneGeometry(16, 16), new THREE.MeshToonMaterial({ map: floorT, gradientMap: G3 }), room, [0, 0, 4], [-Math.PI / 2, 0, 0], 1, false);
  // rug
  mk(new THREE.CircleGeometry(2.2, 48), toon(0x7a1e2c), room, [0, 0.01, 2], [-Math.PI / 2, 0, 0], 1, false);
  // dresser
  mk(new RoundedBoxGeometry(3.4, 0.62, 1.6, 2, 0.05), 0x6a4028, room, [0, 0.31, -0.4]);
  for (const s of [-1, 1]) { mk(new THREE.BoxGeometry(1.5, 0.4, 0.05), 0x7a4a30, room, [s * 0.8, 0.31, 0.42]); mk(SPH, 0xd0b060, room, [s * 0.8, 0.31, 0.46], 0, 0.05); }
  // lace doily
  mk(new THREE.CircleGeometry(0.9, 24), toon(0xeee8d8), room, [-0.1, 0.625, -0.3], [-Math.PI / 2, 0, 0], [1.4, 1, 1], false);
  // TV
  const tv = grp(room, [0, 0.62, -0.35]);
  mk(new RoundedBoxGeometry(2.4, 1.75, 1.5, 4, 0.16), 0x5a3a26, tv, [0, 0.875, 0]);
  mk(new RoundedBoxGeometry(1.72, 1.32, 0.2, 3, 0.1), 0x1a1820, tv, [-0.25, 0.9, 0.68]);
  mk(new THREE.PlaneGeometry(1.52, 1.14), crtMat, tv, [-0.25, 0.9, 0.79], 0, 1, false);
  mk(new THREE.BoxGeometry(0.42, 1.3, 0.05), 0x2a2228, tv, [0.89, 0.9, 0.76], 0, 1, false);
  for (let i = 0; i < 3; i++) mk(new THREE.CylinderGeometry(0.09, 0.09, 0.08, 20), 0xc8c0b0, tv, [0.89, 1.3 - i * 0.32, 0.8], [Math.PI / 2, 0, 0]);
  mk(SPH, new THREE.MeshBasicMaterial({ color: 0xff3020 }), tv, [0.89, 0.38, 0.79], 0, 0.035, false);
  for (const s of [-1, 1]) mk(new THREE.CylinderGeometry(0.018, 0.018, 1.5, 8), 0x9a9aa8, tv, [s * 0.35, 2.3, -0.1], [0, 0, -s * 0.5], 1, false);
  mk(SPH, 0x2a2a30, tv, [0, 1.78, -0.1], 0, [0.22, 0.12, 0.18]);
  roomLights.tvPos = new THREE.Vector3(-0.25, 1.52, 0.44);
  // small boombox on the dresser (foreshadow)
  const bb = grp(room, [1.35, 0.62, -0.2]); bb.rotation.y = -0.4;
  mk(new RoundedBoxGeometry(0.7, 0.36, 0.22, 2, 0.05), 0xc9ccd8, bb, [0, 0.18, 0]);
  for (const s of [-1, 1]) mk(new THREE.CylinderGeometry(0.11, 0.11, 0.04, 20), 0x23202c, bb, [s * 0.2, 0.17, 0.11], [Math.PI / 2, 0, 0]);
  // poster
  const post = canvasTex(256, 384, (x, w, h) => { x.fillStyle = '#d81e30'; x.fillRect(0, 0, w, h); x.fillStyle = '#fff'; x.beginPath(); x.arc(128, 150, 70, 0, 7); x.fill(); x.fillStyle = '#d81e30'; x.fillRect(58, 70, 140, 60); x.fillStyle = '#111'; x.font = 'bold 54px DejaVu Sans'; x.textAlign = 'center'; x.fillText('MC', 128, 300); x.font = 'bold 26px DejaVu Sans'; x.fillText('ТУР 2002', 128, 345); });
  mk(new THREE.PlaneGeometry(0.9, 1.35), new THREE.MeshToonMaterial({ map: post, gradientMap: G3 }), room, [2.6, 2.4, -1.58], [0, 0, 0.04], 1, false);
  // window with moonlight
  mk(new THREE.PlaneGeometry(1.6, 2), new THREE.MeshBasicMaterial({ color: 0x24305a }), room, [-3.2, 2.6, -1.58], 0, 1, false);
  mk(new THREE.CircleGeometry(0.22, 32), new THREE.MeshBasicMaterial({ color: 0xfff0d0 }), room, [-3.5, 3.1, -1.57], 0, 1, false);
  mk(new THREE.BoxGeometry(1.7, 0.08, 0.06), 0xd8d0c0, room, [-3.2, 2.6, -1.55], 0, 1, false);
  mk(new THREE.BoxGeometry(0.08, 2.1, 0.06), 0xd8d0c0, room, [-3.2, 2.6, -1.55], 0, 1, false);
  for (const s of [-1, 1]) mk(new THREE.BoxGeometry(0.5, 2.6, 0.08), 0x7a2a3a, room, [-3.2 + s * 1.0, 2.55, -1.5], 0, 1, false);
  roomLights.amb = new THREE.HemisphereLight(0x5a6aa0, 0x100808, 0.5); room.add(roomLights.amb);
  roomLights.moon = new THREE.DirectionalLight(0x8090ff, 0.6); roomLights.moon.position.set(-4, 4, 3); room.add(roomLights.moon);
  roomLights.glow = new THREE.PointLight(0xb070ff, 4, 9, 1.2); roomLights.glow.position.set(-0.25, 1.6, 1.4); room.add(roomLights.glow);
}
// end title (camera-attached)
const titleTex = canvasTex(1600, 400, () => {});
const titleMat = new THREE.MeshBasicMaterial({ map: titleTex, transparent: true, opacity: 0, depthTest: false, depthWrite: false, toneMapped: false });
const title = new THREE.Mesh(new THREE.PlaneGeometry(1.6, 0.4), titleMat); title.renderOrder = 999; title.position.set(0, -0.05, -2); roomCam.add(title); room.add(roomCam);
function drawTitle(t) {
  const x = titleTex.userData.ctx; x.clearRect(0, 0, 1600, 400); x.textAlign = 'center'; x.textBaseline = 'middle';
  const fl = (noise1(t * 25) > -0.7) ? 1 : 0.3;
  x.font = 'bold 150px DejaVu Sans'; x.shadowColor = '#ff2a6a'; x.shadowBlur = 50; x.fillStyle = `rgba(255,${200 + 55 * fl},${230},${fl})`; x.fillText('ЭФИР ОКОНЧЕН', 800, 170);
  x.shadowBlur = 20; x.shadowColor = '#40e0ff'; x.font = '60px DejaVu Sans'; x.fillStyle = '#bff6ff'; x.fillText('★ спасибо за просмотр ★', 800, 310);
  titleTex.needsUpdate = true;
}

// ---------------------------------------------------------------- post
const composer = new EffectComposer(renderer, new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, samples: 4 }));
const rpass = new RenderPass(main, mainCam); composer.addPass(rpass);
const bloom = new UnrealBloomPass(new THREE.Vector2(W, H), 0.55, 0.5, 0.8); composer.addPass(bloom);
const fin = new ShaderPass({
  uniforms: { tDiffuse: { value: null }, uTime: { value: 0 }, uCA: { value: 0 }, uGrain: { value: 0.035 }, uVig: { value: 0.55 }, uFlash: { value: 0 }, uGlitch: { value: 0 }, uDesat: { value: 0 }, uFade: { value: 0 }, uTint: { value: new THREE.Color(1, 1, 1) }, uLines: { value: 0 } },
  vertexShader: SCREEN_VS,
  fragmentShader: `uniform sampler2D tDiffuse; uniform float uTime,uCA,uGrain,uVig,uFlash,uGlitch,uDesat,uFade,uLines; uniform vec3 uTint; varying vec2 vUv;
    float h(vec2 p){return fract(sin(dot(p,vec2(12.9898,78.233)))*43758.5453);}
    void main(){ vec2 uv=vUv;
      if(uGlitch>0.0){ float row=floor(uv.y*28.0); float r=h(vec2(row,floor(uTime*30.0))); if(r<uGlitch*0.55) uv.x+=(h(vec2(row,uTime*3.1))-0.5)*0.14*uGlitch; }
      vec2 d=uv-0.5; float ca=uCA*0.01*(0.25+length(d)*1.6);
      vec3 c=vec3(texture2D(tDiffuse,uv+d*ca).r,texture2D(tDiffuse,uv).g,texture2D(tDiffuse,uv-d*ca).b);
      // speed lines (radial streaks)
      if(uLines>0.0){ float a=atan(d.y,d.x); float s=h(vec2(floor(a*90.0),0.0)); float m=step(0.82,s)*smoothstep(0.18,0.55,length(d)); c+=vec3(m*uLines*0.35); }
      float l=dot(c,vec3(0.299,0.587,0.114)); c=mix(c,vec3(l)*uTint,uDesat);
      c=c/(1.0+c*0.12);
      c*=1.0-uVig*dot(d,d)*1.7;
      c+=(h(uv*vec2(1931.0,1093.0)+fract(uTime*7.13))-0.5)*uGrain;
      c=mix(c,vec3(1.6),clamp(uFlash,0.0,1.0)); c*=1.0-uFade;
      c=pow(max(c,0.0),vec3(1.0/2.2));
      gl_FragColor=vec4(c,1.0); }`,
});
composer.addPass(fin);

// ---------------------------------------------------------------- CHOREOGRAPHY
// returns pose + root transform for each character
function stand(t, ph = 0) { const br = Math.sin(t * 2.2 + ph); return { hy: -0.03 + br * 0.01, spine: [0.02 * br, 0, 0], lH: [0.48, 0.92, 0.05], rH: [-0.48, 0.92, 0.05] }; }
function singPose(t) {
  const sw = Math.sin((t - B0) * Math.PI / P * 0.5), sw2 = Math.sin((t - B0) * Math.PI / P);
  const v = envS('voc', t);
  return {
    hx: sw * 0.06, hy: -0.06 + 0.02 * sw2, hips: [0, sw * 0.12, sw * 0.05], spine: [-0.06, -sw * 0.05, -sw * 0.04], chest: [-0.04, 0, 0],
    head: [-0.22 + 0.05 * Math.sin(t * 3.1), sw * 0.1, sw * 0.14],
    rH: [-0.05, 1.86, 0.42], rHp: [-1, -0.6, 0], mic: [0.35, 0, 0], rHr: [-0.3, 0, 0],
    lH: [0.92 + 0.12 * sw, 1.55 + 0.25 * Math.sin(t * 2.4), 0.45], lHp: [1, -0.6, -0.4], lHr: [0, 0, 0.6],
    lF: [0.24, 0.12, 0.08], rF: [-0.2, 0.12, -0.05],
    mouth: clamp(v * 1.25 - 0.08), blink: 0.45 + 0.1 * Math.sin(t * 2), brow: 0.5, browT: -0.22, smile: 0.4,
  };
}
function rapPose(t, alt = 0) {
  const b = beatF(t), ph = fract(b), k = Math.exp(-ph * P * 9), i = Math.floor(b) + alt, side = i % 2 ? 1 : -1;
  const v = envS('voc', t);
  const nod = Math.exp(-ph * P * 7);
  const pointBeat = (i % 4) === 3;
  return {
    hy: -0.1 - 0.14 * k, hips: [0.05, side * 0.12, 0], spine: [0.18 + 0.1 * k, side * 0.1, 0], chest: [0.05, side * 0.08, 0],
    head: [-0.05 + 0.28 * nod - 0.14, -side * 0.12, side * 0.05],
    lH: side > 0 ? [0.28, 1.25 - 0.3 * k, 0.7] : [0.55, 1.15, 0.35],
    rH: side < 0 ? (pointBeat ? [-0.25, 1.85, 0.95] : [-0.28, 1.25 - 0.3 * k, 0.7]) : [-0.55, 1.15, 0.35],
    lHp: [1, -0.8, -0.2], rHp: [-1, -0.8, -0.2], lHr: [-0.4 + 0.5 * k, 0, 0], rHr: [-0.4 + 0.5 * k, 0, 0],
    lF: [0.34, 0.12, 0.06], rF: [-0.34, 0.12, -0.02], lFr: [0, 0.35, 0], rFr: [0, -0.35, 0],
    mouth: clamp(v * 1.35 - 0.1 + 0.15 * k), brow: -0.25, browT: 0.32, blink: 0, smile: -0.2,
  };
}
function dancePose(t, mirror = 1) {
  const b = beatF(t), ph = fract(b), k = Math.exp(-ph * P * 8), st = Math.sin(b * Math.PI);
  const bar = Math.floor(b / 2) % 2; const v = envS('voc', t);
  const raise = bar === 0;
  const up = 2.35 + 0.25 * k;
  return {
    hx: 0.22 * st * mirror, hy: -0.12 - 0.12 * k, hips: [0, 0.18 * st * mirror, -0.08 * st * mirror], spine: [0.08, -0.1 * st * mirror, 0.1 * st * mirror],
    head: [0.18 * k - 0.05, 0.15 * st * mirror, -0.1 * st * mirror],
    lH: raise ? [0.42, up, 0.2] : [0.95 + 0.1 * st, 1.6 + 0.4 * st, 0.3], rH: raise ? [-0.42, up, 0.2] : [-0.95 + 0.1 * st, 1.6 - 0.4 * st, 0.3],
    lHp: [1, -0.5, -0.3], rHp: [-1, -0.5, -0.3], lHr: raise ? [Math.PI, 0, 0] : [0, 0, 1.4], rHr: raise ? [Math.PI, 0, 0] : [0, 0, -1.4],
    lF: [0.3 + 0.15 * Math.max(0, st), 0.12 + 0.12 * Math.max(0, -st * mirror) * 0, 0.05], rF: [-0.3 + 0.15 * Math.min(0, st), 0.12, 0.0],
    lFr: [0, 0.3, 0], rFr: [0, -0.3, 0],
    mouth: clamp(v * 1.2 - 0.1), smile: 0.6, brow: 0.2,
  };
}
function crouchPose(d = 0.35) { return { hy: -d, spine: [0.45, 0, 0], head: [-0.3, 0, 0], lH: [0.55, 0.6, 0.0], rH: [-0.55, 0.6, 0.0], lF: [0.3, 0.12, 0.1], rF: [-0.3, 0.12, 0.1], lHp: [1, 0, -1], rHp: [-1, 0, -1], brow: -0.2, mouth: 0.1 }; }
function airPose(t, a = 0) { return { hy: 0.05, spine: [-0.2, 0, 0], head: [-0.25, 0, 0], lH: [0.6, 2.75, 0.2], rH: [-0.6, 2.75, 0.2], lF: [0.3, 0.35, -0.2], rF: [-0.25, 0.55, 0.25], lFp: [0, 0, 1], rFp: [0, 0, 1], mouth: 0.9, brow: 0.6, smile: 0.5, lHr: [Math.PI, 0, 0], rHr: [Math.PI, 0, 0] }; }
function tuckPose() { return { hy: 0.15, spine: [0.6, 0, 0], head: [0.35, 0, 0], lH: [0.25, 0.9, 0.6], rH: [-0.25, 0.9, 0.6], lF: [0.2, 0.75, 0.45], rF: [-0.2, 0.75, 0.45], lFp: [0, 1, 1], rFp: [0, 1, 1], brow: -0.4, browT: 0.4, mouth: 0.3 }; }
function heroLand() { return { hy: -0.48, hips: [0.1, 0.2, 0], spine: [0.55, 0.15, 0], head: [-0.45, -0.1, 0], rH: [-0.25, 0.14, 0.62], rHp: [-1, 0.2, -0.4], lH: [1.1, 1.2, -0.6], lHp: [1, -0.4, -0.5], lF: [0.35, 0.12, 0.45], rF: [-0.3, 0.1, -0.55], rFr: [-0.9, 0, 0], brow: -0.5, browT: 0.45, mouth: 0.05, smile: -0.3 }; }
function surfPose(t, who) {
  const b = beatF(t), ph = fract(b), k = Math.exp(-ph * P * 8), sw = Math.sin(t * 2.6);
  const v = envS('voc', t);
  if (who === 'mc') return {
    hy: -0.25 - 0.12 * k, hips: [0, 0.5, 0], spine: [0.2, -0.3, 0.05 * sw], head: [0.1 * k - 0.05, -0.35, 0],
    lH: [0.9, 1.5, 0.6], rH: [-0.15 + 0.1 * k, 1.75, 1.05], rHp: [-1, -1, 0], lHp: [1, -0.6, -0.4], rHr: [-1.4, 0, 0],
    lF: [0.42, 0.12, 0.25], rF: [-0.42, 0.12, -0.25], lFr: [0, 0.7, 0], rFr: [0, 0.4, 0],
    mouth: clamp(v * 1.35 - 0.1 + 0.1 * k), brow: -0.2, browT: 0.3, smile: 0.2,
  };
  return {
    hy: -0.28 - 0.1 * k, hips: [0, -0.4, 0], spine: [0.1, 0.25, -0.05 * sw], head: [-0.25, 0.3, 0.1 * sw],
    rH: [-0.1, 1.72, 0.45], rHp: [-1, -0.6, 0], mic: [0.35, 0, 0], lH: [1.15, 1.9 + 0.2 * sw, 0.2], lHp: [1, -0.5, -0.4], lHr: [0, 0, 1.2],
    lF: [0.42, 0.12, -0.25], rF: [-0.42, 0.12, 0.25], lFr: [0, -0.4, 0], rFr: [0, -0.7, 0],
    mouth: clamp(v * 1.2), blink: 0.3, brow: 0.5, smile: 0.5,
  };
}
function blinkAt(t, seed) { let b = 0; for (let i = 0; i < 12; i++) { const bt = 0.6 + i * 1.07 + seed * 0.37 + Math.sin(i * 3.1 + seed) * 0.3; b = Math.max(b, 1 - clamp(Math.abs(t - bt) / 0.07)); } return b; }

// boombox position
function boomState(t) {
  const u = seg(t, 6.95, 7.33); const e = eo(u);
  const p = new THREE.Vector3(lerp(0, 0, e), lerp(-9, 4.2, e), lerp(14, 0, e));
  const k = kick(t, 10);
  const land = Math.exp(-Math.max(0, t - T.LAND) * 6) * (t >= T.LAND ? 1 : 0);
  const ft = animT(t);
  p.y += Math.sin(ft * 3) * 0.12 - land * 0.35 - k * 0.04;
  const rot = new THREE.Euler(0.06 * Math.sin(ft * 2.2) - (1 - e) * 0.5 + 0.08 * land, 0.0, 0.07 * Math.sin(ft * 1.7));
  return { p, rot, sq: 1 - 0.12 * land - 0.05 * k, vis: t > 6.9 && t < T.OUT + 0.01 };
}
const BOOM_TOP = 0.85;

function charState(who, t) {
  const ta = animT(t);
  let pose, x = 0, y = STAGE_TOP, z = 0, ry = 0, rx = 0, rz = 0, sc = [1, 1, 1], vis = true, onBoom = false;
  const isMC = who === 'mc';
  if (ta < T.BAR3 - 0.25) {
    if (!isMC) {
      if (ta < T.LOOK) { pose = singPose(ta); }
      else if (ta < T.DROP) {
        const u = seg(ta, T.LOOK, T.DROP);
        const look = { ...stand(ta), hy: -0.08, head: [-0.75, 0, 0.1], spine: [-0.15, 0, 0], rH: [-0.4, 1.45, 0.45], lH: [0.55, 1.5, 0.45], mic: [0.6, 0, 0], mouth: 0.75, brow: 0.9, browT: -0.1, look: [0, 1] };
        pose = blend(singPose(ta), look, eo(seg(ta, T.LOOK, T.LOOK + 0.18)));
        z = -0.4 * eio(u); x = -0.3 * eio(u);
      } else if (ta < 3.5) {
        const u = seg(ta, T.DROP, 3.25), e = eo(u);
        x = lerp(-0.3, -2.6, e); z = lerp(-0.4, 0.2, e);
        const fl = Math.sin(ta * 30);
        pose = { hy: -0.15, spine: [-0.5 * (1 - u) - 0.1, 0, 0.1], head: [-0.4 * (1 - u), 0.3, 0], lH: [1.0, 2.0 + 0.3 * fl, -0.1], rH: [-1.0, 2.0 - 0.3 * fl, -0.1], mic: [1.2, 0, 0], lF: [0.3, 0.12 + 0.3 * Math.max(0, fl) * (1 - u), 0.2], rF: [-0.3, 0.12, -0.1], mouth: 1.0, brow: 1, browT: -0.3, look: [0.5, 0] };
        rz = 0.35 * Math.sin(u * Math.PI) ; ry = 0.5 * e;
        pose = blend(pose, { ...stand(ta), ry: 0, mouth: 0.6, brow: 1, browT: -0.2, rH: [-0.45, 1.2, 0.35], mic: [0.6, 0, 0], head: [0, 0.4, 0] }, ss(3.1, 3.5, ta));
      } else if (ta < T.BAR2) {
        x = -2.6; z = 0.2; ry = 0.5;
        const nodOn = ss(4.42, 4.6, ta), b = beatF(ta), nod = Math.exp(-fract(b) * P * 7);
        const shrug = Math.sin(Math.PI * seg(ta, 4.2, 4.5));
        pose = { ...stand(ta), hy: -0.04 + 0.12 * shrug - 0.06 * nod * nodOn, head: [0.25 * nod * nodOn - 0.05, 0.45 - 0.2 * nodOn, 0.1 * shrug], spine: [0.1 * nodOn, 0, 0],
          rH: [-0.6 - 0.3 * shrug, 1.2 + 0.3 * shrug, 0.4], lH: [0.6 + 0.3 * shrug, 1.0 + 0.4 * shrug, 0.3], lHr: [0, 0, 1.2 * shrug], mic: [0.6, 0, 0],
          mouth: lerp(0.5, 0.15, nodOn), smile: lerp(-0.2, 0.8, nodOn), brow: lerp(0.9, 0.3, nodOn), blink: blinkAt(ta, 1) + (ta > 3.85 && ta < 3.95 ? 1 : 0) + (ta > 4.02 && ta < 4.1 ? 1 : 0), look: [lerp(0.8, 0, nodOn), 0] };
      } else {
        const u = eio(seg(ta, T.BAR2, T.BAR2 + 0.4));
        x = lerp(-2.6, -1.25, u); z = lerp(0.2, 0.3, u); ry = lerp(0.5, 0.15, u);
        pose = blend({ ...stand(ta) }, dancePose(ta, -1), u);
        pose.mic = [0.6, 0, 0];
      }
    } else {
      if (ta < 2.12) { vis = false; pose = tuckPose(); }
      else if (ta < T.DROP) {
        const u = seg(ta, 2.12, T.DROP);
        y = STAGE_TOP + 15 * (1 - u * u); rx = -u * Math.PI * 4; pose = blend(tuckPose(), heroLand(), ss(0.8, 1, u));
        if (u > 0.85) rx = lerp(-Math.PI * 4 * 0.85, -Math.PI * 4, (u - 0.85) / 0.15);
        sc = [1 - 0.15 * u, 1 + 0.25 * u, 1 - 0.15 * u];
      } else if (ta < T.RISE + 0.15) {
        const imp = Math.exp(-(ta - T.DROP) * 14);
        pose = heroLand(); pose.hy -= 0.1 * imp; sc = [1 + 0.18 * imp, 1 - 0.22 * imp, 1 + 0.18 * imp];
        pose.head = [lerp(-0.45, 0.1, ss(2.8, 3.2, ta)), -0.1, 0];
        pose = blend(pose, rapPose(ta), eio(seg(ta, 3.05, T.RISE + 0.15)));
      } else if (ta < T.BAR2) { pose = rapPose(ta); }
      else {
        const u = eio(seg(ta, T.BAR2, T.BAR2 + 0.4));
        x = lerp(0, 1.25, u); z = lerp(0, 0.3, u); ry = lerp(0, -0.15, u);
        pose = blend(rapPose(ta), dancePose(ta, 1), u);
      }
    }
  } else {
    // jump -> boombox -> flight
    const bx = isMC ? 1.15 : -1.15;
    const startX = isMC ? 1.25 : -1.25;
    const bs = boomState(t);
    if (ta < T.BAR3) {
      const u = seg(ta, T.BAR3 - 0.25, T.BAR3);
      x = startX; z = 0.3; ry = isMC ? -0.15 : 0.15;
      pose = blend(dancePose(ta, isMC ? 1 : -1), crouchPose(0.38), eo(u));
      if (!isMC) pose.mic = [0.6, 0, 0];
    } else if (ta < T.LAND) {
      const u = seg(ta, T.BAR3, T.LAND);
      const topY = bs.p.y + BOOM_TOP;
      x = lerp(startX, bx, u); z = lerp(0.3, 0, u);
      y = lerp(STAGE_TOP, topY, u) + 4.2 * 4 * u * (1 - u) * 0.9;
      ry = lerp(isMC ? -0.15 : 0.15, 0, u);
      rx = isMC ? -u * Math.PI * 2 * ss(0.1, 0.9, u) : 0;
      pose = blend(airPose(ta), crouchPose(0.3), ss(0.75, 1, u));
      if (!isMC) pose.mic = [0.6, 0, 0];
      sc = [1 - 0.1 * Math.sin(u * Math.PI), 1 + 0.15 * Math.sin(u * Math.PI), 1 - 0.1 * Math.sin(u * Math.PI)];
    } else {
      onBoom = true; x = bx; y = 0; z = 0;
      const land = Math.exp(-(ta - T.LAND) * 7);
      if (ta < T.BAR4) {
        pose = blend(surfPose(ta, who), crouchPose(0.35), land);
        if (!isMC) pose.mic = [0.35, 0, 0];
      } else if (ta < T.RES) {
        // spin jump into the frozen pose
        const u = seg(ta, T.BAR4, T.BRK + 0.03);
        const hj = Math.sin(Math.PI * Math.min(1, u * 0.95)) * (isMC ? 2.2 : 1.6);
        y = hj; ry = (isMC ? 1 : -1) * eo(u) * Math.PI * 2;
        if (isMC) { rx = 0; }
        const fz = isMC
          ? { hy: 0.1, spine: [-0.15, 0, -0.2], head: [-0.1, 0, -0.1], rH: [-0.45, 2.0, 1.1], rHr: [-1.5, 0, 0], lH: [1.2, 1.7, -0.3], lF: [0.5, 0.5, 0.3], rF: [-0.35, 0.05, -0.4], lFp: [1, 0, 1], mouth: 1.0, brow: -0.4, browT: 0.4, smile: 0.4 }
          : { hy: 0.05, spine: [-0.3, 0, 0.15], head: [-0.4, 0, 0.15], rH: [-0.5, 2.65, 0.3], mic: [-0.3, 0, 0], lH: [1.25, 1.75, 0.2], lHr: [0, 0, 1.4], lF: [0.4, 0.55, -0.3], rF: [-0.3, 0.2, 0.1], mouth: 1.1, brow: 0.9, smile: 0.6, blink: 0.6 };
        pose = blend(surfPose(ta, who), fz, ss(0, 0.35, u));
      } else {
        // big pose after the break, nods on the last hits
        const k = kick(t, 9);
        const fin = isMC
          ? { hy: -0.22 - 0.1 * k, spine: [0.1, 0.2, 0], head: [0.25 * k - 0.1, 0.2, 0.05], lH: [-0.1, 1.55, 0.45], rH: [0.15, 1.45, 0.4], lHp: [1, -1, 0], rHp: [-1, -1, 0], lF: [0.4, 0.12, 0.05], rF: [-0.4, 0.12, -0.05], lFr: [0, 0.4, 0], rFr: [0, -0.4, 0], mouth: clamp(envS('voc', t) * 1.3), brow: -0.3, browT: 0.35, smile: 0.3 }
          : { hy: -0.15 - 0.08 * k, spine: [-0.2, -0.2, 0], head: [-0.3 + 0.2 * k, -0.2, 0], rH: [-0.35, 2.7, 0.35], mic: [-0.4, 0, 0], lH: [1.2, 1.4, 0.3], lHr: [0, 0, 1.2], lF: [0.35, 0.12, 0.05], rF: [-0.35, 0.12, 0], mouth: clamp(envS('voc', t) * 1.3), blink: 0.5, brow: 0.8, smile: 0.7 };
        const land2 = Math.exp(-(t - T.RES) * 9);
        pose = blend(fin, crouchPose(0.3), land2 * 0.6);
      }
    }
    if (onBoom) {
      // character space attached to boombox top
      const m = new THREE.Matrix4().compose(bs.p, new THREE.Quaternion().setFromEuler(bs.rot), new THREE.Vector3(1, 1, 1));
      const lp = new THREE.Vector3(x, BOOM_TOP * bs.sq + y, z).applyMatrix4(m);
      x = lp.x; y = lp.y; z = lp.z; rx += bs.rot.x; rz += bs.rot.z;
    }
  }
  pose.blink = Math.max(pose.blink || 0, blinkAt(ta, isMC ? 2 : 0));
  return { pose, x, y, z, rx, ry, rz, sc, vis };
}
function placeChar(ch, s) {
  ch.visible = s.vis;
  ch.position.set(s.x, s.y, s.z);
  ch.rotation.set(s.rx, s.ry, s.rz, 'YXZ');
  ch.scale.set(...s.sc);
  ch.updateMatrixWorld(true);
  applyPose(ch, s.pose);
}

// flight distance (integral of speed)
function speed(t) {
  if (t < 7.2) return 0;
  let v = 32 * ss(7.2, 7.8, t);
  if (t >= T.BRK - 0.05 && t < T.RES) v *= 0.02;
  v *= 1 + 0.35 * kick(t, 5);
  if (t > T.H1) v *= lerp(1, 0.2, ss(T.H1, T.OUT, t));
  return v;
}
function dist(t) { let s = 0; const n = 400; const a = 7.2; if (t <= a) return 0; const dt = (t - a) / n; for (let i = 0; i < n; i++) s += speed(a + (i + 0.5) * dt) * dt; return s; }

// ---------------------------------------------------------------- CAMERA
const tmpA = new THREE.Vector3(), tmpB = new THREE.Vector3();
function headPos(ch) { return ch.userData.J.head.getWorldPosition(new THREE.Vector3()).add(new THREE.Vector3(0, 0.35, 0)); }
function camMain(t, cs) {
  let p, l, fov = 40, roll = 0;
  const crP = new THREE.Vector3(cs.cr.x, cs.cr.y, cs.cr.z), mcP = new THREE.Vector3(cs.mc.x, cs.mc.y, cs.mc.z);
  if (t < T.LOOK) {
    const u = eio(seg(t, 0, T.LOOK));
    const a = lerp(0.55, -0.25, u);
    p = new THREE.Vector3(Math.sin(a) * lerp(7.5, 4.6, u), lerp(2.9, 2.0, u), Math.cos(a) * lerp(7.5, 4.6, u));
    l = new THREE.Vector3(0, lerp(1.9, 2.05, u), 0); fov = lerp(42, 34, u);
  } else if (t < T.DROP) {
    const u = seg(t, T.LOOK, T.DROP);
    p = new THREE.Vector3(lerp(-1.4, -0.6, u), lerp(1.6, 1.3, eo(u)), lerp(4.8, 7.5, eo(u)));
    const my = STAGE_TOP + 15 * (1 - Math.pow(seg(t, 2.12, T.DROP), 2));
    l = new THREE.Vector3(0, lerp(2.5, Math.min(my, 9), ss(0.15, 0.6, u)) * (1 - ss(0.82, 1, u)) + 1.6 * ss(0.82, 1, u), 0);
    fov = lerp(36, 52, eo(u));
  } else if (t < 3.67) {
    const u = seg(t, T.DROP, 3.67);
    p = new THREE.Vector3(lerp(-0.6, 0.8, u), lerp(1.2, 1.5, u), lerp(7.5, 6.4, eo(u)));
    l = new THREE.Vector3(lerp(-0.4, 0, u), 1.5, 0); fov = lerp(52, 44, eo(u));
  } else if (t < 4.2) {
    const u = seg(t, 3.67, 4.2), hp = headPos(mc);
    const a = lerp(-0.5, -0.15, eio(u));
    p = hp.clone().add(new THREE.Vector3(Math.sin(a) * 2.3, -0.75, Math.cos(a) * 2.3)); l = hp.clone().add(new THREE.Vector3(0, -0.05, 0)); fov = 38; roll = -0.06;
  } else if (t < T.BAR2) {
    const u = seg(t, 4.2, T.BAR2), hp = headPos(crooner);
    p = hp.clone().add(new THREE.Vector3(lerp(1.6, 1.3, u), -0.15, lerp(2.0, 1.7, u))); l = hp.clone().add(new THREE.Vector3(0.2, -0.15, 0)); fov = 36; roll = 0.04;
  } else if (t < T.BAR3 - 0.25) {
    const u = eio(seg(t, T.BAR2, T.BAR3 - 0.25));
    const a = lerp(-0.25, 0.32, u);
    const r = lerp(6.0, 17.5, u);
    p = new THREE.Vector3(Math.sin(a) * r, lerp(1.9, 9.5, u), Math.cos(a) * r);
    l = new THREE.Vector3(0, lerp(1.6, 2.6, u), lerp(0, -2, u)); fov = lerp(44, 50, u);
  } else if (t < T.LAND + 0.15) {
    const u = seg(t, T.BAR3 - 0.25, T.LAND + 0.15);
    const cy = (cs.cr.y + cs.mc.y) / 2;
    p = new THREE.Vector3(lerp(5.5, 3.6, eio(u)), lerp(9.5, 5.4, eio(u)), lerp(16.6, 9.6, eio(u)));
    l = new THREE.Vector3(0, lerp(2.6, cy + 1.3, ss(0, 0.4, u)), lerp(-2, 0, u)); fov = lerp(46, 52, u); roll = -0.08 * Math.sin(u * Math.PI);
  } else if (t < 8.39) {
    const u = seg(t, T.LAND + 0.15, 8.39);
    const a = lerp(0.65, -0.55, eio(u));
    p = new THREE.Vector3(Math.sin(a) * 7.8, 5.2 + 0.8 * Math.sin(u * Math.PI), Math.cos(a) * 7.8);
    l = new THREE.Vector3(0, 5.6, 0); fov = 50; roll = 0.12 * Math.sin(a * 1.4);
  } else if (t < T.BAR4) {
    const u = seg(t, 8.39, T.BAR4);
    p = new THREE.Vector3(lerp(2.8, 1.6, u), lerp(3.0, 3.4, u), lerp(5.2, 4.4, u));
    l = new THREE.Vector3(0, 6.3, 0); fov = 58; roll = -0.12;
  } else if (t < T.BRK) {
    const u = seg(t, T.BAR4, T.BRK);
    p = new THREE.Vector3(lerp(7.4, 6.2, u), lerp(5.0, 6.6, u), lerp(5.6, 5.4, u));
    l = new THREE.Vector3(0, lerp(6.4, 7.6, u), 0); fov = 48;
  } else if (t < T.RES) {
    const u = seg(t, T.BRK, T.RES);
    const a = lerp(0.85, 0.85 - Math.PI * 0.95, eio(u));
    p = new THREE.Vector3(Math.sin(a) * 5.2, 6.9 + 0.6 * Math.sin(u * Math.PI), Math.cos(a) * 5.2);
    l = new THREE.Vector3(0, 7.0, 0); fov = 44;
  } else if (t < T.H1) {
    const u = seg(t, T.RES, T.H1);
    p = new THREE.Vector3(lerp(0.4, 0.2, u), lerp(5.6, 5.8, u), lerp(4.3, 5.0, eo(u)));
    l = new THREE.Vector3(0, 6.0, 0); fov = lerp(40, 44, u);
  } else {
    const u = seg(t, T.H1, T.OUT + 0.4);
    p = new THREE.Vector3(lerp(0.2, 0, u), lerp(5.8, 5.9, u), lerp(5.0, 13.5, eio(u)));
    l = new THREE.Vector3(0, 5.6, 0); fov = lerp(44, 48, u);
  }
  // camera shake on hits
  const sh = kick(t, 10) * (t > T.DROP ? 1 : 0) + (t >= T.DROP && t < T.DROP + 0.4 ? 1.8 * Math.exp(-(t - T.DROP) * 9) : 0);
  const n = (o) => noise1(t * 32 + o) * sh * 0.06;
  p.add(new THREE.Vector3(n(0), n(13), n(29)));
  roll += noise1(t * 20 + 91) * sh * 0.015;
  // handheld drift
  p.add(new THREE.Vector3(noise1(t * 0.7 + 3) * 0.06, noise1(t * 0.6 + 8) * 0.05, 0));
  return { p, l, fov, roll };
}
function setCam(cam, c) { cam.position.copy(c.p); cam.up.set(0, 1, 0); cam.lookAt(c.l); cam.rotateZ(c.roll); cam.fov = c.fov; cam.updateProjectionMatrix(); }

// ---------------------------------------------------------------- UPDATE WORLD
const _mat = new THREE.Matrix4(), _pos = new THREE.Vector3(), _quat = new THREE.Quaternion(), _scl = new THREE.Vector3(), _col = new THREE.Color();
function updateMain(t) {
  const ta = animT(t);
  const post = t >= T.DROP; const k = kick(ta, 7);
  // palette
  const a = post ? 0xff1a3a : 0xff2bd6, b = post ? 0xffffff : 0x2bd9ff;
  rimA.color.set(a); rimB.color.set(b);
  rimA.intensity = (post ? 1.6 : 1.1) + 1.4 * k; rimB.intensity = (post ? 0.8 : 1.1) + 0.9 * k;
  const flick = t > 2.3 && t < T.DROP ? (noise1(t * 40) > 0 ? 1 : 0.15) : 1;
  key.intensity = 1.5 * flick * (t > T.BAR3 ? 0.85 : 1); amb.intensity = 0.8 * flick;
  front.intensity = 0.6 * k;
  // tiles
  const sr = (ta - T.DROP) * 14;
  for (let i = 0; i < tilePos.length; i++) {
    const [x, z] = tilePos[i]; const r = Math.hypot(x, z);
    const wave = post && ta < 3.5 ? Math.exp(-Math.pow(r - sr, 2) * 2) : 0;
    _pos.set(x, STAGE_TOP + 0.03 + wave * 0.45, z); _quat.setFromEuler(new THREE.Euler(wave * 0.6 * Math.sin(i), 0, wave * 0.6 * Math.cos(i)));
    _mat.compose(_pos, _quat, _scl.set(1, 1, 1)); tiles.setMatrixAt(i, _mat);
    let h, l;
    if (!post) { h = 0.75 + 0.12 * Math.sin(r * 0.9 - ta * 4); l = 0.35 + 0.25 * Math.max(0, Math.sin(r * 2 - ta * 6)); }
    else { const bi = Math.floor(beatF(ta)); const ch = ((Math.floor(x * 2) + Math.floor(z * 2) + bi) & 1); h = ch ? 0.98 : 0.0; l = ch ? 0.45 + 0.3 * k : 0.85 * (0.4 + 0.6 * k); }
    _col.setHSL(h, ch_s(post), clamp(l + 0.3 * wave)); tiles.setColorAt(i, _col);
  }
  tiles.instanceMatrix.needsUpdate = true; tiles.instanceColor.needsUpdate = true;
  // shockwave
  shock.visible = ta > T.DROP && ta < T.DROP + 0.9; const su = seg(ta, T.DROP, T.DROP + 0.9);
  shock.scale.setScalar(0.3 + eo(su) * 16); shock.material.opacity = (1 - su) * 0.9;
  // speakers
  for (const s of speakers) for (const c of s.userData.cones) c.scale.set(1 + 0.12 * k, 1 + 0.6 * k, 1 + 0.12 * k);
  // LED
  if (t < T.BAR3 + 0.5) drawLED(ta);
  // walls fall
  const fall = (t0, dur = 0.9) => { const u = seg(ta, t0, t0 + dur); return { r: ei(u) * Math.PI / 2 * 1.05, d: Math.max(0, ta - t0 - dur * 0.75) }; };
  { const f = fall(T.BAR2); walls.back.rotation.x = -f.r; walls.back.position.y = -12 * f.d * f.d; walls.back.position.z = -8.5 - 3 * f.d; }
  { const f = fall(5.25); walls.left.rotation.z = f.r; walls.left.position.y = -12 * f.d * f.d; walls.left.position.x = -12.8 - 3 * f.d; }
  { const f = fall(5.77); walls.right.rotation.z = -f.r; walls.right.position.y = -12 * f.d * f.d; walls.right.position.x = 12.8 + 3 * f.d; }
  { const u = seg(ta, 6.29, 7.2); truss.position.y = 9.2 + 30 * ei(u); truss.rotation.z = 0.4 * ei(u); truss.rotation.x = -0.3 * ei(u); }
  for (const w of Object.values(walls)) w.visible = ta < 6.8;
  // beams
  beams.forEach((bm, i) => {
    const sw = post ? Math.sin(ta * 2.8 + i * 1.3) * 0.5 : Math.sin(ta * 1.2 + i) * 0.35;
    bm.rotation.set(0.25 * Math.cos(ta * 1.7 + i) + (i % 2 ? -0.2 : 0.2), 0, sw);
    const m = bm.children[1].material; m.color.set(post ? (i % 2 ? 0xff2040 : 0xffffff) : (i % 2 ? 0xff40ff : 0x40d0ff)); m.opacity = (0.05 + 0.06 * k) * flick;
  });
  // crowd
  {
    const { body, head, arm } = crowd.meshes; const e = new THREE.Euler();
    crowd.forEach((c, i) => {
      const hitT = T.DROP + c.d / 14; const knock = ta > hitT ? Math.exp(-(ta - hitT) * 5) * (1 - c.d / 20) : 0;
      const bb = post ? Math.max(0, Math.sin((beatF(ta) + c.ph * 0.3) * Math.PI * 2)) * 0.25 : Math.max(0, Math.sin(ta * 2.4 + c.ph * 6)) * 0.06;
      const y = bb + knock * 0.8; const lean = -knock * 0.9 + Math.sin(ta * 2 + c.ph * 5) * 0.06;
      e.set(lean, 0, Math.sin(ta * 2.4 + c.ph * 9) * 0.1);
      _quat.setFromEuler(e);
      _mat.compose(_pos.set(c.x, 0.95 * c.s + y, c.z), _quat, _scl.set(c.s, c.s, c.s)); body.setMatrixAt(i, _mat);
      const hp = new THREE.Vector3(0, 0.95 * c.s, 0).applyQuaternion(_quat).add(new THREE.Vector3(c.x, 0.95 * c.s + y + 0.05, c.z));
      _mat.compose(hp, _quat, _scl.set(0.3 * c.s, 0.32 * c.s, 0.3 * c.s)); head.setMatrixAt(i, _mat);
      for (const s of [-1, 1]) {
        const up = (c.up || post) ? 1 : 0; const wave = Math.sin(ta * (post ? 6 : 3) + c.ph * 7 + s) * 0.35;
        e.set(lean, 0, s * (up ? 2.7 + wave : 0.25));
        const q = new THREE.Quaternion().setFromEuler(e);
        const sp = new THREE.Vector3(s * 0.33 * c.s, 0.55 * c.s, 0).applyQuaternion(_quat).add(new THREE.Vector3(c.x, 0.95 * c.s + y, c.z));
        const off = new THREE.Vector3(0, -0.45 * c.s, 0).applyQuaternion(q);
        _mat.compose(sp.add(off), q, _scl.set(c.s, c.s, c.s)); arm.setMatrixAt(i * 2 + (s > 0 ? 1 : 0), _mat);
      }
    });
    body.instanceMatrix.needsUpdate = head.instanceMatrix.needsUpdate = arm.instanceMatrix.needsUpdate = true;
  }
  // world flight
  const d = dist(t);
  world.position.set(0, -0.25 * d - 0, -d * 0.9);
  city.position.set(0, -0.12 * d - 6 * ss(7.0, 9.0, t), -d * 0.35);
  world.visible = d < 120; city.visible = t < 10.6;
  // sky colors
  const skyM = sky.material.uniforms;
  skyM.bot.value.set(t < T.DROP ? 0x5b1660 : t < T.BAR3 ? 0x7a1030 : 0x4a1a8a);
  if (t > T.RES) skyM.bot.value.lerp(new THREE.Color(0xa00a20), 0.5);
  skyM.glow.value = 0.4 + k * 0.6;
  main.fog.color.copy(skyM.bot.value).multiplyScalar(0.4);
  // boombox
  const bs = boomState(t); boom.visible = bs.vis; boom.position.copy(bs.p); boom.rotation.copy(bs.rot); boom.scale.set(1 + (1 - bs.sq) * 0.5, bs.sq, 1);
  for (const c of boomCones) c.scale.set(1 + 0.15 * k, 1 + 0.8 * k, 1 + 0.15 * k);
  boom.children.forEach(c => { if (c.userData.flame) { const f = 0.8 + 0.4 * noise1(t * 40 + c.position.x) + 0.5 * k; c.scale.set(1, f * (0.3 + 0.7 * ss(7.0, 7.6, t)), 1); } });
  // TVs
  const tunnelOn = t > 7.0;
  tvGroup.visible = tunnelOn;
  const red = ss(T.RES - 0.02, T.RES + 0.05, t);
  const conv = ss(T.H1, T.OUT, t);
  tvs.forEach((tv, i) => {
    let z = tv.z0 + d * 1.0; z = ((z + 80) % 100 + 100) % 100 - 80; // range [-80,20]
    const appear = ss(7.0, 7.6, t);
    const ang = tv.ang + ta * 0.25; const rad = tv.rad * lerp(2.5, 1, appear);
    let p = new THREE.Vector3(Math.cos(ang) * rad, 5 + Math.sin(ang) * rad, z);
    // converge into a ring around the heroes at the end
    const ra = i / tvs.length * Math.PI * 2; const ring = new THREE.Vector3(Math.cos(ra) * 7.5, 5.8 + Math.sin(ra) * 4.6, -3 - (i % 3) * 1.4);
    p.lerp(ring, eio(conv));
    tv.g.position.copy(p);
    tv.g.rotation.set(Math.sin(ta * tv.spin + tv.tumble) * 0.6 * (1 - conv), ta * tv.spin + tv.tumble + Math.PI * (1 - conv) * 0, Math.cos(ta * tv.spin) * 0.4 * (1 - conv));
    if (conv > 0) { tv.g.lookAt(0, 5.8, 8); }
    else tv.g.lookAt(0, 5, p.z + 6), tv.g.rotateZ(ta * tv.spin);
    const u = tv.mat.uniforms; u.uTime.value = ta; u.uKick.value = k * (0.5 + 0.5 * ((i + Math.floor(beatF(ta))) % 3 === 0)); u.uRed.value = red;
  });
  // speed lines
  lines.forEach((ln) => {
    const on = speed(t) / 32;
    let z = ((ln.z0 - d * ln.sp) % 100 + 100) % 100 - 80; z = -z - 60;
    z = ((ln.z0 + d * ln.sp) % 100) - 80;
    ln.m.position.set(Math.cos(ln.ang) * ln.rad, 5 + Math.sin(ln.ang) * ln.rad, z);
    ln.m.scale.z = 1 + on * 2; ln.m.material.opacity = on * 0.55; ln.m.visible = on > 0.02;
  });
  // confetti
  {
    const r = rng(99);
    for (let i = 0; i < CONF_N; i++) {
      const burst = i < CONF_N / 2 ? 0 : 1; const t0 = burst ? T.RES : T.DROP;
      const dt = ta - t0; const cr = r(), c2 = r(), c3 = r(), c4 = r(), c5 = r();
      if (dt < 0 || dt > 4) { _mat.makeScale(0, 0, 0); confetti.setMatrixAt(i, _mat); continue; }
      let p;
      if (!burst) { // rain from the truss
        const x0 = (cr * 2 - 1) * 8, z0 = (c2 * 2 - 1) * 5, y0 = 9 + c3 * 2;
        p = new THREE.Vector3(x0 + Math.sin(dt * 3 + c4 * 6) * 0.4, y0 - dt * (1.6 + c5) + 3.5 * Math.exp(-dt * 3) * c3, z0);
      } else { // explosion around the heroes, they move with the boombox
        const th = cr * Math.PI * 2, ph = Math.acos(c2 * 2 - 1), v = 6 + c3 * 8;
        const dir = new THREE.Vector3(Math.sin(ph) * Math.cos(th), Math.cos(ph), Math.sin(ph) * Math.sin(th));
        const dd = (1 - Math.exp(-dt * 3)) / 3 * v;
        p = new THREE.Vector3(0, 6.2, 0).addScaledVector(dir, dd); p.y -= dt * dt * 0.8; p.z += (t >= T.RES ? -0 : 0);
      }
      _quat.setFromEuler(new THREE.Euler(dt * 7 * c4 + i, dt * 5 * c5, dt * 3));
      _mat.compose(p, _quat, _scl.setScalar(1.2)); confetti.setMatrixAt(i, _mat);
    }
    confetti.instanceMatrix.needsUpdate = true;
  }
  // characters
  const cs = { cr: charState('cr', t), mc: charState('mc', t) };
  placeChar(crooner, cs.cr); placeChar(mc, cs.mc);
  return cs;
}
function ch_s(post) { return post ? 0.9 : 0.85; }

// ---------------------------------------------------------------- FRAME
function roomCamAt(t) {
  if (t < T.IN) {
    const u = seg(t, 0, T.IN); const e = ei(u) * 0.75 + u * 0.25;
    const target = new THREE.Vector3(-0.25, 1.52, 0.44);
    const p = new THREE.Vector3(lerp(1.6, -0.25, eio(u)), lerp(2.3, 1.52, eio(u)), lerp(7.5, 1.05, e));
    return { p, l: target.clone().add(new THREE.Vector3(0, 0, -1)), fov: 40, roll: lerp(0.05, 0, u) };
  }
  const u = seg(t, T.OUT, T.OFF + 0.1); const e = eo(u);
  const p = new THREE.Vector3(lerp(-0.25, 0.9, e), lerp(1.52, 1.95, e), lerp(1.0, 6.2, e));
  p.x += Math.sin((t - T.OFF) * 0.4) * 0.1 * ss(T.OFF, 13, t); p.z += 0.4 * ss(T.OFF, 13, t);
  return { p, l: new THREE.Vector3(lerp(-0.25, 0, e), lerp(1.52, 1.25, e), -0.5), fov: lerp(40, 38, e), roll: 0 };
}
window.renderFrame = function (t) {
  const inRoom = t < T.IN || t >= T.OUT;
  const cs = updateMain(t);
  const cm = camMain(t, cs);
  fin.uniforms.uTime.value = t;
  const k = kick(animT(t), 8);
  if (inRoom) {
    // main world rendered into the TV
    mainCam.aspect = 4 / 3; setCam(mainCam, cm);
    renderer.setRenderTarget(rt); renderer.render(main, mainCam); renderer.setRenderTarget(null);
    mainCam.aspect = W / H;
    setCam(roomCam, roomCamAt(t));
    const cu = crtMat.uniforms; cu.uTime.value = t;
    cu.uStatic.value = t < 0.35 ? 1 - ss(0.12, 0.35, t) : 0;
    cu.uOff.value = seg(t, T.OFF + 0.05, T.OFF + 0.25);
    cu.uDot.value = t > T.OFF + 0.25 ? Math.exp(-(t - T.OFF - 0.25) * 2.5) : 0;
    cu.uBright.value = 1.3 * (t > T.OFF + 0.25 ? 0 : 1);
    const tvOn = t < T.OFF + 0.25 ? 1 : cu.uDot.value * 0.3;
    roomLights.glow.intensity = (3 + 3 * k) * tvOn; roomLights.glow.color.set(t < T.IN ? (t < 0.35 ? 0xd0d8ff : 0xb070ff) : 0xff3050);
    roomLights.amb.intensity = 0.35 + 0.2 * tvOn;
    titleMat.opacity = ss(11.9, 12.3, t) * (1 - ss(12.65, 12.95, t));
    if (titleMat.opacity > 0) drawTitle(t);
    rpass.scene = room; rpass.camera = roomCam;
    bloom.strength = 0.4; bloom.threshold = 0.85;
  } else {
    mainCam.aspect = W / H; setCam(mainCam, cm);
    rpass.scene = main; rpass.camera = mainCam;
    bloom.strength = 0.42 + 0.25 * k; bloom.threshold = 0.82;
  }
  // grading
  const F = fin.uniforms;
  const frozen = t >= T.BRK && t < T.RES ? ss(T.BRK, T.BRK + 0.08, t) : 0;
  F.uDesat.value = frozen * 0.75; F.uTint.value.setRGB(0.75, 0.9, 1.25);
  F.uCA.value = 0.25 + 1.6 * k + (t >= T.DROP && t < 3.0 ? 2.5 * Math.exp(-(t - T.DROP) * 6) : 0) + frozen * 1.2;
  F.uFlash.value = Math.max(
    t >= T.IN && t < T.IN + 0.25 ? 0.6 * Math.exp(-(t - T.IN) * 20) : 0,
    t >= T.DROP ? 0.7 * Math.exp(-(t - T.DROP) * 16) : 0,
    t >= T.RES ? 0.6 * Math.exp(-(t - T.RES) * 16) : 0,
    t >= T.OUT ? 0.3 * Math.exp(-(t - T.OUT) * 25) : 0,
    t >= T.BRK && t < T.BRK + 0.2 ? 0.25 * Math.exp(-(t - T.BRK) * 18) : 0);
  F.uGlitch.value = Math.max(ss(1.05, 1.25, t) * (t < T.IN + 0.12 ? 1 : 0), t > 2.3 && t < T.DROP + 0.1 ? 0.5 * ss(2.3, 2.6, t) : 0, t > T.OUT - 0.12 && t < T.OUT + 0.06 ? 0.9 : 0, t > T.OFF && t < T.OFF + 0.1 ? 0.4 : 0);
  F.uLines.value = inRoom ? 0 : clamp(speed(t) / 32) * (0.6 + 0.6 * k);
  F.uFade.value = ss(12.7, 13.0, t);
  F.uVig.value = inRoom ? 0.9 : 0.55;
  composer.render();
};
window.T = T;
window.ready = true;
