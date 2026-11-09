// node render.js <outDir> [fps] [from] [to] [worker] [workers]  — пишет JPEG-кадры
// node render.js --preview <outDir> t1 t2 ...                     — отдельные кадры для проверки
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const WEB = path.join(__dirname, 'web');
async function open() {
  const browser = await chromium.launch({ args: ['--enable-unsafe-swiftshader', '--use-angle=swiftshader'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on('console', m => console.log('[page]', m.text()));
  page.on('pageerror', e => console.log('[pageerror]', e.message));
  await page.route('http://bees.local/**', r => {
    const p = new URL(r.request().url()).pathname;
    const f = p === '/three.module.js' ? path.join(__dirname, 'node_modules/three/build/three.module.js') : path.join(WEB, p);
    const type = { '.html': 'text/html', '.js': 'text/javascript', '.woff2': 'font/woff2' }[path.extname(f)] || 'application/octet-stream';
    r.fulfill({ status: 200, contentType: type, body: fs.readFileSync(f) });
  });
  await page.goto('http://bees.local/index.html');
  await page.waitForFunction(() => window.READY === true, null, { timeout: 60000 });
  return { browser, page };
}
const save = (file, url) => fs.writeFileSync(file, Buffer.from(url.split(',')[1], 'base64'));
(async () => {
  const a = process.argv.slice(2);
  if (a[0] === '--preview') {
    const { browser, page } = await open();
    fs.mkdirSync(a[1], { recursive: true });
    for (const t of a.slice(2).map(Number)) save(path.join(a[1], `t${t.toFixed(2)}.jpg`), await page.evaluate(t => window.renderFrame(t, 0.85), t));
    await browser.close(); return;
  }
  const [outDir, fps = 30, from = 0, to = 1e9, worker = 0, workers = 1] = [a[0], ...a.slice(1).map(Number)];
  fs.mkdirSync(outDir, { recursive: true });
  const { browser, page } = await open();
  const dur = await page.evaluate(() => window.DURATION);
  const total = Math.ceil(dur * fps);
  const t0 = Date.now();
  for (let f = Math.max(0, from); f < Math.min(total, to); f++) {
    if (f % workers !== worker) continue;
    save(path.join(outDir, `f${String(f).padStart(5, '0')}.jpg`), await page.evaluate(t => window.renderFrame(t, 0.93), f / fps));
    if (f % 60 === worker) console.log(`w${worker} frame ${f}/${total} ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  await browser.close();
})();
