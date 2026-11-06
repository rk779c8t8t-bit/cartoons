// usage: node render.js <outdir> <fps> <startFrame> <endFrame> [w h] [times...]
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const root = __dirname;
const [out, fps, f0, f1, w = '1920', h = '1080', ...extra] = process.argv.slice(2);
const types = { '.js': 'text/javascript', '.html': 'text/html', '.json': 'application/json' };
const srv = http.createServer((q, r) => { const p = path.join(root, decodeURIComponent(q.url.split('?')[0])); fs.readFile(p, (e, d) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream' }); r.end(d); }); });
srv.listen(0, async () => {
  const port = srv.address().port;
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const pg = await b.newPage({ viewport: { width: +w, height: +h } });
  pg.on('console', m => console.log('[page]', m.text())); pg.on('pageerror', e => console.log('[err]', e.message));
  await pg.goto(`http://localhost:${port}/index.html?w=${w}&h=${h}`);
  await pg.waitForFunction(() => window.ready === true, null, { timeout: 60000 });
  fs.mkdirSync(out, { recursive: true });
  const times = extra.length ? extra.map(Number) : null;
  const list = times || Array.from({ length: +f1 - +f0 }, (_, i) => (+f0 + i) / +fps);
  let i = 0; const st = Date.now();
  for (const t of list) {
    await pg.evaluate(t => window.renderFrame(t), t);
    const name = times ? `t_${t.toFixed(2)}.jpg` : `f_${String(+f0 + i).padStart(5, '0')}.jpg`;
    const buf = await pg.screenshot({ type: 'jpeg', quality: 96 });
    fs.writeFileSync(path.join(out, name), buf); i++;
    if (i % 20 === 0) console.log(`${out} ${i}/${list.length} ${((Date.now() - st) / i).toFixed(0)}ms/f`);
  }
  await b.close(); srv.close();
});
