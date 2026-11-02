import React from 'react';
import { C, FONT, chroma, extrude, glow } from '../../theme';

/** Shared text looks so every scene stays inside one visual language. */
export const T = {
  lyric: (size = 78): React.CSSProperties => ({
    fontFamily: FONT.display,
    fontWeight: 800,
    fontSize: size,
    color: C.silver,
    letterSpacing: '-0.01em',
    textShadow: `${chroma(3)}, 0 6px 30px rgba(0,0,0,0.85)`,
  }),
  glossyPink: (size = 160): React.CSSProperties => ({
    fontFamily: FONT.display,
    fontWeight: 900,
    fontSize: size,
    letterSpacing: '-0.03em',
    backgroundImage: 'linear-gradient(180deg, #fff 0%, #ffd6ef 22%, #ff7cc8 48%, #ff2d95 52%, #ff86cf 80%, #ffe3f4 100%)',
    WebkitBackgroundClip: 'text',
    backgroundClip: 'text',
    color: 'transparent',
    filter: `drop-shadow(0 0 18px rgba(255,79,179,0.9)) drop-shadow(0 10px 0 #7a1050)`,
  }),
  chrome: (size = 170): React.CSSProperties => ({
    fontFamily: FONT.metal,
    fontSize: size,
    letterSpacing: '0.02em',
    backgroundImage:
      'linear-gradient(180deg, #ffffff 0%, #c9d1e6 30%, #59627a 49%, #f2f5ff 52%, #8d97b3 75%, #e8ecf8 100%)',
    WebkitBackgroundClip: 'text',
    backgroundClip: 'text',
    color: 'transparent',
    filter: 'drop-shadow(0 0 10px rgba(127,227,255,0.9)) drop-shadow(0 8px 0 #1a2235)',
  }),
  neon: (color = C.pink, size = 120): React.CSSProperties => ({
    fontFamily: FONT.display,
    fontWeight: 800,
    fontSize: size,
    color: '#fff',
    textShadow: glow(color, 1.1),
  }),
  extruded: (size = 140, face = C.silver, side = C.violet): React.CSSProperties => ({
    fontFamily: FONT.display,
    fontWeight: 900,
    fontSize: size,
    color: face,
    textShadow: `${extrude(side, 12)}, 0 0 50px rgba(255,79,179,0.7)`,
  }),
  script: (size = 110, color = C.blush): React.CSSProperties => ({
    fontFamily: FONT.script,
    fontSize: size,
    color,
    textShadow: glow(C.pink, 0.8),
  }),
  mono: (size = 56, color = C.silver): React.CSSProperties => ({
    fontFamily: FONT.mono,
    fontWeight: 800,
    fontSize: size,
    color,
    textShadow: `${chroma(2)}, 0 0 20px rgba(127,227,255,0.6)`,
  }),
};
