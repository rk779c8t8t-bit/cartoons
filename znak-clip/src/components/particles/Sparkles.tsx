import React from 'react';
import { random, useCurrentFrame } from 'remotion';
import { C } from '../../theme';

export const starPath = (r: number, inner = 0.18) => {
  const i = r * inner;
  return `M0,${-r} L${i},${-i} L${r},0 L${i},${i} L0,${r} L${-i},${i} L${-r},0 L${-i},${-i} Z`;
};

export const heartPath = (s: number) =>
  `M0,${0.3 * s} C${-0.05 * s},${0.25 * s} ${-0.5 * s},${-0.05 * s} ${-0.5 * s},${-0.3 * s} C${-0.5 * s},${-0.55 * s} ${-0.2 * s},${-0.62 * s} 0,${-0.38 * s} C${0.2 * s},${-0.62 * s} ${0.5 * s},${-0.55 * s} ${0.5 * s},${-0.3 * s} C${0.5 * s},${-0.05 * s} ${0.05 * s},${0.25 * s} 0,${0.3 * s} Z`;

/** Twinkling 4-point glitter scattered over the frame. */
export const Glitter: React.FC<{
  count?: number;
  seed?: string;
  colors?: string[];
  area?: { x: number; y: number; w: number; h: number };
  size?: [number, number];
  opacity?: number;
  drift?: number;
}> = ({
  count = 40,
  seed = 'g',
  colors = [C.silver, C.pink, C.white, C.lilac],
  area = { x: 0, y: 0, w: 1080, h: 1920 },
  size = [6, 22],
  opacity = 1,
  drift = 0,
}) => {
  const frame = useCurrentFrame();
  return (
    <svg width={1080} height={1920} style={{ position: 'absolute', inset: 0, opacity, pointerEvents: 'none' }}>
      {Array.from({ length: count }, (_, i) => {
        const x = area.x + random(`${seed}x${i}`) * area.w;
        const y = area.y + ((random(`${seed}y${i}`) * area.h + frame * drift * (0.5 + random(`${seed}d${i}`))) % area.h);
        const ph = random(`${seed}p${i}`) * Math.PI * 2;
        const sp = 0.12 + random(`${seed}s${i}`) * 0.2;
        const tw = Math.pow(Math.max(0, Math.sin(frame * sp + ph)), 3);
        const r = size[0] + random(`${seed}r${i}`) * (size[1] - size[0]);
        const col = colors[i % colors.length];
        return (
          <g key={i} transform={`translate(${x} ${y}) rotate(${frame * 2 + i * 17}) scale(${0.3 + tw})`} opacity={0.2 + tw * 0.8}>
            <path d={starPath(r)} fill={col} />
            <circle r={r * 0.25} fill="#fff" />
          </g>
        );
      })}
    </svg>
  );
};

/** Deterministic burst of particles from a point. */
export const Burst: React.FC<{
  at: number;
  x: number;
  y: number;
  count?: number;
  speed?: number;
  life?: number;
  gravity?: number;
  colors?: string[];
  shape?: 'dot' | 'star' | 'heart' | 'dollar';
  size?: number;
  seed?: string;
  spread?: number;
  direction?: number;
}> = ({
  at,
  x,
  y,
  count = 60,
  speed = 28,
  life = 30,
  gravity = 0.5,
  colors = [C.pink, C.silver, C.white, C.ice],
  shape = 'dot',
  size = 10,
  seed = 'b',
  spread = Math.PI * 2,
  direction = -Math.PI / 2,
}) => {
  const frame = useCurrentFrame();
  const t = frame - at;
  if (t < 0 || t > life) return null;
  return (
    <svg width={1080} height={1920} style={{ position: 'absolute', inset: 0, pointerEvents: 'none', overflow: 'visible' }}>
      {Array.from({ length: count }, (_, i) => {
        const a = direction + (random(`${seed}a${i}`) - 0.5) * spread;
        const v = speed * (0.3 + random(`${seed}v${i}`) * 0.9);
        const drag = Math.pow(0.93, t);
        const dist = (v * (1 - drag)) / 0.07;
        const px = x + Math.cos(a) * dist;
        const py = y + Math.sin(a) * dist + 0.5 * gravity * t * t;
        const lifeK = 1 - t / life;
        const s = size * (0.4 + random(`${seed}s${i}`)) * (0.3 + lifeK * 0.7);
        const col = colors[i % colors.length];
        const rot = t * (random(`${seed}r${i}`) - 0.5) * 30;
        return (
          <g key={i} transform={`translate(${px} ${py}) rotate(${rot})`} opacity={Math.min(1, lifeK * 1.5)}>
            {shape === 'dot' && <circle r={s * 0.5} fill={col} />}
            {shape === 'star' && <path d={starPath(s * 1.2)} fill={col} />}
            {shape === 'heart' && <path d={heartPath(s * 2.2)} fill={col} />}
            {shape === 'dollar' && (
              <text fontFamily="Unbounded" fontWeight={900} fontSize={s * 3} fill={col} textAnchor="middle" dy={s}>
                $
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
};

/** Slowly floating bokeh dots for depth. */
export const Bokeh: React.FC<{ count?: number; seed?: string; colors?: string[]; speed?: number; opacity?: number }> = ({
  count = 18,
  seed = 'bk',
  colors = [C.pink, C.violet, C.ice],
  speed = 1,
  opacity = 0.5,
}) => {
  const frame = useCurrentFrame();
  return (
    <svg width={1080} height={1920} style={{ position: 'absolute', inset: 0, opacity, pointerEvents: 'none' }}>
      <defs>
        {colors.map((c, i) => (
          <radialGradient id={`${seed}rg${i}`} key={i}>
            <stop offset="0%" stopColor={c} stopOpacity={0.9} />
            <stop offset="70%" stopColor={c} stopOpacity={0.25} />
            <stop offset="100%" stopColor={c} stopOpacity={0} />
          </radialGradient>
        ))}
      </defs>
      {Array.from({ length: count }, (_, i) => {
        const r = 30 + random(`${seed}r${i}`) * 110;
        const x = random(`${seed}x${i}`) * 1080 + Math.sin(frame * 0.02 + i) * 30;
        const y = (((random(`${seed}y${i}`) * 2200 - frame * speed * (0.5 + random(`${seed}v${i}`))) % 2200) + 2200) % 2200 - 140;
        return <circle key={i} cx={x} cy={y} r={r} fill={`url(#${seed}rg${i % colors.length})`} />;
      })}
    </svg>
  );
};
