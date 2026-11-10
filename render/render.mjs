// Frame-accurate renderer: drives web/index.html in headless Chromium,
// captures every frame and pipes it into ffmpeg.
//   node render/render.mjs [--fps 30] [--from 0] [--to 36] [--workers 3] [--out out/clip.mp4] [--scale 1]
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { createRequire } from 'node:module';
const { chromium } = createRequire(import.meta.url)('playwright');

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const args = Object.fromEntries(process.argv.slice(2).reduce((a, v, i, arr) =>
  v.startsWith('--') ? [...a, [v.slice(2), arr[i + 1]]] : a, []));
const FPS = +(args.fps ?? 30);
const W = Math.round(1920 * +(args.scale ?? 1)), H = Math.round(1080 * +(args.scale ?? 1));
const timing = JSON.parse(fs.readFileSync(path.join(ROOT, 'web/timing.json'), 'utf8'));
const DUR = timing.clip.end - timing.clip.start;
const from = +(args.from ?? 0), to = Math.min(+(args.to ?? DUR), DUR);
const WORKERS = +(args.workers ?? 3);
const OUT = path.resolve(args.out ?? path.join(ROOT, 'out/video_noaudio.mp4'));
const SUB = +(args.sub ?? 1);           // motion-blur subframes
const STILLS = args.stills;             // comma list of times -> png stills instead of video
fs.mkdirSync(path.dirname(OUT), { recursive: true });

const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json', '.webp': 'image/webp', '.png': 'image/png' };
const server = http.createServer((req, res) => {
  const p = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
  if (!p.startsWith(ROOT) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': MIME[path.extname(p)] ?? 'application/octet-stream' });
  fs.createReadStream(p).pipe(res);
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const URL_ = `http://127.0.0.1:${server.address().port}/web/index.html?w=${W}&h=${H}&sub=${SUB}&fps=${FPS}`;

const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
async function openPage() {
  const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
  page.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') console.log('[page]', m.text()); });
  page.on('pageerror', e => console.log('[pageerror]', e.message));
  await page.goto(URL_);
  await page.waitForFunction(() => window.clipReady === true, null, { timeout: 120000 });
  return page;
}
async function grab(page, t) {
  await page.evaluate(t => window.renderAt(t), t);
  return page.screenshot({ type: 'png', clip: { x: 0, y: 0, width: W, height: H } });
}

if (STILLS) {
  const page = await openPage();
  const dir = args.dir ?? path.join(ROOT, 'out/stills'); fs.mkdirSync(dir, { recursive: true });
  for (const s of STILLS.split(',')) {
    const t = +s; const buf = await grab(page, t);
    fs.writeFileSync(path.join(dir, `t${t.toFixed(2).padStart(6, '0')}.png`), buf);
  }
  await browser.close(); server.close(); process.exit(0);
}

const f0 = Math.round(from * FPS), f1 = Math.round(to * FPS);
const total = f1 - f0, per = Math.ceil(total / WORKERS);
const tmp = path.join(path.dirname(OUT), 'parts'); fs.mkdirSync(tmp, { recursive: true });
const t0 = Date.now(); let done = 0;
const parts = await Promise.all(Array.from({ length: WORKERS }, async (_, w) => {
  const a = f0 + w * per, b = Math.min(f1, a + per);
  const file = path.join(tmp, `part${w}.mkv`);
  if (a >= b) return null;
  const page = await openPage();
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', `${W}x${H}`, '-framerate', String(FPS), '-i', '-', '-vf', 'vflip',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '8', '-pix_fmt', 'yuv444p', file], { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let f = a; f < b; f++) {
    const buf = Buffer.from(await page.evaluate(t => { window.renderAt(t); return window.readFrame(); }, f / FPS), 'base64');
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    done++;
    if (done % 30 === 0) {
      const el = (Date.now() - t0) / 1000;
      console.log(`${done}/${total} frames, ${(el / done).toFixed(2)} s/frame, eta ${((total - done) * el / done / 60).toFixed(1)} min`);
    }
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
  return file;
}));
const list = path.join(tmp, 'list.txt');
fs.writeFileSync(list, parts.filter(Boolean).map(p => `file '${p}'`).join('\n'));
await new Promise(r => spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', list, '-c', 'copy', OUT], { stdio: 'inherit' }).on('close', r));
console.log('done', OUT, ((Date.now() - t0) / 1000).toFixed(0), 's');
await browser.close(); server.close();
