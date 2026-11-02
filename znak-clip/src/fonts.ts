import { continueRender, delayRender, staticFile } from 'remotion';

const faces: Array<[string, string, string]> = [
  ['Unbounded', 'unbounded-cyrillic-400-normal.woff2', '400'],
  ['Unbounded', 'unbounded-cyrillic-800-normal.woff2', '800'],
  ['Unbounded', 'unbounded-cyrillic-900-normal.woff2', '900'],
  ['Unbounded', 'unbounded-latin-400-normal.woff2', '400'],
  ['Unbounded', 'unbounded-latin-800-normal.woff2', '800'],
  ['Unbounded', 'unbounded-latin-900-normal.woff2', '900'],
  ['Russo One', 'russo-one-cyrillic-400-normal.woff2', '400'],
  ['Russo One', 'russo-one-latin-400-normal.woff2', '400'],
  ['Marck Script', 'marck-script-cyrillic-400-normal.woff2', '400'],
  ['Marck Script', 'marck-script-latin-400-normal.woff2', '400'],
  ['JetBrains Mono', 'jetbrains-mono-cyrillic-400-normal.woff2', '400'],
  ['JetBrains Mono', 'jetbrains-mono-cyrillic-800-normal.woff2', '800'],
  ['JetBrains Mono', 'jetbrains-mono-latin-400-normal.woff2', '400'],
  ['JetBrains Mono', 'jetbrains-mono-latin-800-normal.woff2', '800'],
  ['Press Start 2P', 'press-start-2p-cyrillic-400-normal.woff2', '400'],
  ['Press Start 2P', 'press-start-2p-latin-400-normal.woff2', '400'],
  ['Noto Sans Symbols', 'noto-sans-symbols-symbols-700-normal.woff2', '700'],
];

const handle = delayRender('fonts');
Promise.all(
  faces.map(([family, file, weight]) => {
    const f = new FontFace(family, `url(${staticFile('fonts/' + file)}) format('woff2')`, { weight });
    (document.fonts as unknown as { add: (f: FontFace) => void }).add(f);
    return f.load();
  })
)
  .then(() => continueRender(handle))
  .catch((e) => {
    console.error(e);
    continueRender(handle);
  });
