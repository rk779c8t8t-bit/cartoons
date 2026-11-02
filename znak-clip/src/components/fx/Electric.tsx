import React from 'react';
import { random, useCurrentFrame } from 'remotion';
import { C } from '../../theme';

/** Jagged electric arcs crawling around a rectangle (e.g. behind "РОКСТАР"). */
export const ElectricArcs: React.FC<{
  x: number;
  y: number;
  w: number;
  h: number;
  from: number;
  arcs?: number;
  color?: string;
  intensity?: number;
}> = ({ x, y, w, h, from, arcs = 6, color = C.ice, intensity = 1 }) => {
  const frame = useCurrentFrame();
  if (frame < from) return null;
  const seedF = Math.floor(frame / 2);
  const paths = Array.from({ length: arcs }, (_, a) => {
    // random endpoints on the rect perimeter
    const pt = (k: string) => {
      const s = random(`${k}${a}${seedF}`) * 2 * (w + h);
      if (s < w) return [x + s, y];
      if (s < w + h) return [x + w, y + s - w];
      if (s < 2 * w + h) return [x + w - (s - w - h), y + h];
      return [x, y + h - (s - 2 * w - h)];
    };
    const [x1, y1] = pt('p');
    const [x2, y2] = pt('q');
    const n = 9;
    let d = `M${x1},${y1}`;
    for (let i = 1; i <= n; i++) {
      const t = i / n;
      const jx = (random(`jx${a}${i}${seedF}`) - 0.5) * 70;
      const jy = (random(`jy${a}${i}${seedF}`) - 0.5) * 70;
      d += ` L${x1 + (x2 - x1) * t + (i < n ? jx : 0)},${y1 + (y2 - y1) * t + (i < n ? jy : 0)}`;
    }
    return d;
  });
  const flick = random('fl' + frame) > 0.2 ? 1 : 0.35;
  return (
    <svg width={1080} height={1920} style={{ position: 'absolute', inset: 0, pointerEvents: 'none', opacity: flick * intensity }}>
      <defs>
        <filter id="arc-glow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="7" result="b" />
          <feMerge>
            <feMergeNode in="b" />
            <feMergeNode in="b" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      <g filter="url(#arc-glow)" fill="none" strokeLinejoin="bevel">
        {paths.map((d, i) => (
          <g key={i}>
            <path d={d} stroke={color} strokeWidth={6} opacity={0.8} />
            <path d={d} stroke="#fff" strokeWidth={2} />
          </g>
        ))}
      </g>
    </svg>
  );
};
