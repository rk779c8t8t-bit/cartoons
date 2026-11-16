// Render frames [from,to) of the clip and pipe them to ffmpeg: node render.js from to out.mp4
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');
(async () => {
  const [from, to, out] = [+process.argv[2], +process.argv[3], process.argv[4]];
  const FPS = 30;
  const browser = await chromium.launch({ args: ['--allow-file-access-from-files'] });
  const page = await browser.newPage({ viewport: { width: 600, height: 1000 } });
  page.on('pageerror', e => console.error('PAGEERR', String(e)));
  await page.goto('file://' + path.resolve(__dirname, '../src/index.html'));
  await page.waitForFunction(() => window.READY || window.INIT_ERR, null, { timeout: 180000 });
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p', '-r', String(FPS), out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const t0 = Date.now();
  for (let f = from; f < to; f++) {
    const url = await page.evaluate(tt => window.grab(tt, .95), f / FPS);
    const buf = Buffer.from(url.slice(url.indexOf(',') + 1), 'base64');
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if ((f - from) % 300 === 0) console.log(`[${from}-${to}] frame ${f} ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
  await browser.close();
})();
