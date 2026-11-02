export const C = {
  black: '#05030a',
  ink: '#0d0718',
  plum: '#1c0b33',
  violet: '#8a4dff',
  lilac: '#c7a6ff',
  pink: '#ff4fb3',
  hot: '#ff2d95',
  blush: '#ffc2e5',
  silver: '#dfe3ee',
  chrome: '#a9b1c6',
  ice: '#7fe3ff',
  white: '#ffffff',
};

export const FONT = {
  display: "'Unbounded', sans-serif",
  metal: "'Russo One', sans-serif",
  script: "'Marck Script', cursive",
  mono: "'JetBrains Mono', monospace",
  pixel: "'Press Start 2P', monospace",
  symbols: "'Noto Sans Symbols', sans-serif",
};

export const W = 1080;
export const H = 1920;

// Glow + chromatic aberration shadow for text.
export const glow = (color: string, strength = 1) =>
  [
    `0 0 ${8 * strength}px ${color}`,
    `0 0 ${24 * strength}px ${color}`,
    `0 0 ${60 * strength}px ${color}`,
  ].join(', ');

export const chroma = (px = 4) => `${-px}px 0 0 rgba(255,40,150,0.75), ${px}px 0 0 rgba(90,220,255,0.75)`;

// Stacked shadows give fake 3D extrusion.
export const extrude = (color: string, depth = 10, dx = 1, dy = 1.4) =>
  Array.from({ length: depth }, (_, i) => `${(i + 1) * dx}px ${(i + 1) * dy}px 0 ${color}`).join(', ');
