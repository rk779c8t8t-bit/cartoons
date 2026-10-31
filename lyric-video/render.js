// Рендер кадров engine.html через headless Chromium -> ffmpeg.
// node render.js <out.mp4> <startFrame> <endFrame>     — один фрагмент
// node render.js --still <frame> <out.jpg>             — один кадр (превью)
const { chromium } = require("playwright");
const { spawn } = require("child_process");
const path = require("path");

async function open() {
  const browser = await chromium.launch({ args: ["--allow-file-access-from-files", "--disable-gpu"] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  page.on("pageerror", e => { console.error("PAGE ERROR", e); process.exit(1); });
  await page.goto("file://" + path.resolve(__dirname, "engine.html"));
  await page.waitForFunction(() => window.READY === true, null, { timeout: 60000 });
  return { browser, page };
}

(async () => {
  const a = process.argv.slice(2);
  const { browser, page } = await open();
  if (a[0] === "--still") {
    await page.evaluate(f => window.renderFrame(f), +a[1]);
    await page.screenshot({ path: a[2], type: "jpeg", quality: 92 });
    await browser.close(); return;
  }
  const [out, s, e] = [a[0], +a[1], +a[2]];
  const ff = spawn("ffmpeg", ["-v", "error", "-y", "-f", "image2pipe", "-c:v", "mjpeg", "-framerate", "30", "-i", "-",
    "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-r", "30", out], { stdio: ["pipe", "inherit", "inherit"] });
  const t0 = Date.now();
  for (let f = s; f < e; f++) {
    await page.evaluate(f => window.renderFrame(f), f);
    const buf = await page.screenshot({ type: "jpeg", quality: 96 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once("drain", r));
    if ((f - s) % 150 === 0) console.log(`[${s}-${e}] frame ${f} ${((Date.now() - t0) / (f - s + 1)).toFixed(0)}ms/f`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on("close", r));
  await browser.close();
})();
