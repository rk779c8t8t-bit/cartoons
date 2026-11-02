import React from 'react';
import { AbsoluteFill, random, useCurrentFrame } from 'remotion';
import { C } from '../../theme';
import { starPath } from '../particles/Sparkles';

/** Three-layer parallax starfield. */
export const Starfield: React.FC<{ drift?: number; count?: number; seed?: string; warp?: number }> = ({
  drift = 1,
  count = 160,
  seed = 'sf',
  warp = 0,
}) => {
  const frame = useCurrentFrame();
  return (
    <svg width={1080} height={1920} style={{ position: 'absolute', inset: 0 }}>
      {Array.from({ length: count }, (_, i) => {
        const layer = i % 3;
        const sp = (layer + 1) * 0.35 * drift;
        let x = random(`${seed}x${i}`) * 1080;
        let y = (((random(`${seed}y${i}`) * 2000 + frame * sp) % 2000) + 2000) % 2000 - 40;
        const r = (layer + 1) * 1.1 * (0.6 + random(`${seed}r${i}`));
        const tw = 0.5 + 0.5 * Math.sin(frame * 0.15 + i);
        if (warp > 0) {
          // pull stars toward the centre (used to rush into the zodiac wheel)
          x = x + (540 - x) * warp;
          y = y + (900 - y) * warp;
        }
        return <circle key={i} cx={x} cy={y} r={r * (1 + warp * 2)} fill={i % 7 === 0 ? C.blush : i % 5 === 0 ? C.ice : '#fff'} opacity={0.4 + tw * 0.6} />;
      })}
      {Array.from({ length: 6 }, (_, i) => {
        const x = random(`${seed}bx${i}`) * 1080;
        const y = random(`${seed}by${i}`) * 1920;
        const k = Math.pow(Math.max(0, Math.sin(frame * 0.09 + i * 2)), 6);
        return (
          <g key={'b' + i} transform={`translate(${x} ${y}) scale(${0.4 + k})`} opacity={k}>
            <path d={starPath(40, 0.1)} fill="#fff" />
          </g>
        );
      })}
    </svg>
  );
};

/** Soft, layered clouds that drift down as the camera floats up. */
export const Clouds: React.FC<{ rise: number; opacity?: number }> = ({ rise, opacity = 1 }) => {
  const layers = [
    { y: 1450, speed: 0.6, scale: 1.0, color: '#ffd1ec', o: 0.55, blur: 18 },
    { y: 1650, speed: 1.0, scale: 1.3, color: '#e9c8ff', o: 0.7, blur: 14 },
    { y: 1820, speed: 1.6, scale: 1.7, color: '#fff0fa', o: 0.85, blur: 10 },
    { y: 300, speed: 0.4, scale: 0.9, color: '#c9a8ff', o: 0.3, blur: 22 },
  ];
  return (
    <AbsoluteFill style={{ opacity }}>
      {layers.map((l, li) => (
        <svg key={li} width={1080} height={1920} style={{ position: 'absolute', inset: 0, filter: `blur(${l.blur}px)`, transform: `translateY(${rise * l.speed}px)` }}>
          {Array.from({ length: 7 }, (_, i) => {
            const cx = (i / 6) * 1200 - 60 + random(`cl${li}${i}`) * 80;
            const r = (130 + random(`clr${li}${i}`) * 120) * l.scale;
            return <ellipse key={i} cx={cx} cy={l.y + random(`cly${li}${i}`) * 80} rx={r * 1.4} ry={r * 0.75} fill={l.color} opacity={l.o} />;
          })}
        </svg>
      ))}
    </AbsoluteFill>
  );
};
