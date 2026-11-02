// Usage: node scripts/stills.mjs 45 120 300 ...   → out/stills/fNNN.png + out/stills/sheet.jpg
import { bundle } from '@remotion/bundler';
import { renderStill, selectComposition } from '@remotion/renderer';
import { execSync } from 'node:child_process';
import path from 'node:path';

const frames = process.argv.slice(2).map(Number);
const browserExecutable = '/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell';
const serveUrl = await bundle({ entryPoint: path.resolve('src/index.ts') });
const composition = await selectComposition({ serveUrl, id: 'ZnakDora', browserExecutable });
const outs = [];
for (const f of frames) {
  const output = `out/stills/f${String(f).padStart(4, '0')}.png`;
  await renderStill({ composition, serveUrl, output, frame: f, browserExecutable, chromiumOptions: { gl: 'angle' } });
  outs.push(output);
}
const n = outs.length;
execSync(`ffmpeg -v error -y ${outs.map((o) => `-i ${o}`).join(' ')} -filter_complex "${outs.map((_, i) => `[${i}]scale=270:480,drawtext=text='${frames[i]}':x=8:y=8:fontsize=28:fontcolor=yellow:box=1:boxcolor=black[v${i}]`).join(';')};${outs.map((_, i) => `[v${i}]`).join('')}xstack=inputs=${n}:layout=${outs.map((_, i) => `${(i % 6) * 270}_${Math.floor(i / 6) * 480}`).join('|')}:fill=black" out/stills/sheet.jpg`);
console.log('done', n);
