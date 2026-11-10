// Converts Fontsource WOFF subsets (latin + cyrillic) into three.js typeface JSON.
import opentype from 'opentype.js';
import fs from 'node:fs';

const FS = 'node_modules/@fontsource';
const fonts = [
  ['unbounded-900', 'unbounded', 'unbounded', 900],
  ['montserrat-900', 'montserrat', 'montserrat', 900],
  ['montserrat-700', 'montserrat', 'montserrat', 700],
];
const toAB = b => b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength);

for (const [out, pkg, name, w] of fonts) {
  const subsets = ['latin', 'cyrillic'].map(s =>
    opentype.parse(toAB(fs.readFileSync(`${FS}/${pkg}/files/${name}-${s}-${w}-normal.woff`))));
  const base = subsets[0];
  const scale = 1000 / base.unitsPerEm;
  const glyphs = {};
  for (const f of subsets) {
    for (let i = 0; i < f.glyphs.length; i++) {
      const g = f.glyphs.get(i);
      const codes = g.unicodes?.length ? g.unicodes : (g.unicode !== undefined ? [g.unicode] : []);
      for (const code of codes) {
        const ch = String.fromCodePoint(code);
        if (glyphs[ch]) continue;
        let o = '';
        for (const c of g.path.commands) {
          const r = v => Math.round(v * scale);
          if (c.type === 'M') o += `m ${r(c.x)} ${r(c.y)} `;
          else if (c.type === 'L') o += `l ${r(c.x)} ${r(c.y)} `;
          else if (c.type === 'Q') o += `q ${r(c.x)} ${r(c.y)} ${r(c.x1)} ${r(c.y1)} `;
          else if (c.type === 'C') o += `b ${r(c.x)} ${r(c.y)} ${r(c.x1)} ${r(c.y1)} ${r(c.x2)} ${r(c.y2)} `;
        }
        glyphs[ch] = { ha: Math.round(g.advanceWidth * scale), x_min: 0, x_max: 0, o };
      }
    }
  }
  const json = {
    glyphs, familyName: out, ascender: Math.round(base.ascender * scale),
    descender: Math.round(base.descender * scale), underlinePosition: 0, underlineThickness: 0,
    boundingBox: { yMin: Math.round(base.descender * scale), xMin: 0, yMax: Math.round(base.ascender * scale), xMax: 1000 },
    resolution: 1000, original_font_information: { format: 0, fontFamily: out },
  };
  fs.writeFileSync(`web/assets/${out}.json`, JSON.stringify(json));
  console.log(out, Object.keys(glyphs).length, 'glyphs');
}
