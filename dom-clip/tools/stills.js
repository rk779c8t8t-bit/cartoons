// Render still frames for review: node stills.js out_dir t1 t2 ...
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const START_OFF = 11.82; // stills take song time
(async () => {
  const [out, ...ts] = process.argv.slice(2);
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch({ args: ['--allow-file-access-from-files'] });
  const page = await browser.newPage({ viewport: { width: 600, height: 1000 } });
  const errs = []; page.on('pageerror', e => errs.push(String(e))); page.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') errs.push(m.text()); });
  await page.goto('file://' + path.resolve(__dirname, '../src/index.html'));
  await page.waitForFunction(() => window.READY || window.INIT_ERR, null, { timeout: 120000 });
  const ie = await page.evaluate(() => window.INIT_ERR); if (ie) { console.error(ie); process.exit(1); }
  for (const t of ts) {
    const t0 = Date.now();
    const url = await page.evaluate(tt => window.grab(+tt - START, .9), t);
    fs.writeFileSync(path.join(out, `t${(+t).toFixed(2).padStart(7, '0')}.jpg`), Buffer.from(url.split(',')[1], 'base64'));
    console.log(t, Date.now() - t0, 'ms');
  }
  if (errs.length) console.log('ERRORS:\n' + errs.slice(0, 20).join('\n'));
  await browser.close();
})();
