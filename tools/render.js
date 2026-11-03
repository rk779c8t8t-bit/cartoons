#!/usr/bin/env node
// Рендер клипа: node tools/render.js [out/clip.mp4]
// Снимки отдельных кадров: node tools/render.js --stills 1.5,6,9 out/stills
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path'), fs = require('fs');
const ROOT = path.join(__dirname, '..');
(async () => {
  const args = process.argv.slice(2);
  const browser = await chromium.launch({ args: ['--allow-file-access-from-files'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  page.on('pageerror', e => { console.error('PAGE ERROR', e); process.exit(1); });
  await page.goto('file://' + path.join(ROOT, 'src', 'clip.html') + '?render=1');
  await page.evaluate(() => window.READY);
  const grab = async t => Buffer.from((await page.evaluate(t => { window.render(t); return document.getElementById('c').toDataURL('image/jpeg', .95); }, t)).split(',')[1], 'base64');
  if (args[0] === '--stills') {
    const dir = args[2] || path.join(ROOT, 'work', 'stills'); fs.mkdirSync(dir, { recursive: true });
    for (const t of args[1].split(',').map(Number)) fs.writeFileSync(path.join(dir, `t${t.toFixed(2)}.jpg`), await grab(t));
    await browser.close(); return;
  }
  const out = args[0] || path.join(ROOT, 'out', 'clip.mp4'); fs.mkdirSync(path.dirname(out), { recursive: true });
  const dur = await page.evaluate(() => window.DATA.duration), FPS = 30, N = Math.round(dur * FPS);
  const ff = spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-i', path.join(ROOT, 'src', 'audio', 'song.m4a'), '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'slow', '-crf', '21',
    '-pix_fmt', 'yuv420p', '-r', String(FPS), '-c:a', 'copy', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const t0 = Date.now();
  for (let i = 0; i < N; i++) {
    const buf = await grab(i / FPS);
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 60 === 0) console.log(`frame ${i}/${N}  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
  await browser.close(); console.log('done ->', out);
})();
