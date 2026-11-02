import React from 'react';
import { AbsoluteFill, random, useCurrentFrame } from 'remotion';
import { C } from '../../theme';
import { BEATS } from '../../timing';
import { beatPulse } from '../../util';

/** Mirror ball with rotating tile highlights. */
const MirrorBall: React.FC<{ x: number; y: number; r: number }> = ({ x, y, r }) => {
  const frame = useCurrentFrame();
  const tiles = [];
  for (let la = -80; la <= 80; la += 14) {
    const ringR = Math.cos((la * Math.PI) / 180) * r;
    const cy = y + Math.sin((la * Math.PI) / 180) * r;
    const n = Math.max(4, Math.round(ringR / 9));
    for (let k = 0; k < n; k++) {
      const a = (k / n) * Math.PI * 2 + frame * 0.04;
      const z = Math.cos(a);
      if (z < 0) continue;
      const cx = x + Math.sin(a) * ringR;
      const lit = random(`mb${la}${k}`) > 0.82 || Math.sin(a * 3 + frame * 0.3) > 0.97;
      tiles.push(<rect key={`${la}-${k}`} x={cx - 6 * z} y={cy - 6} width={12 * z} height={12} fill={lit ? '#fff' : `rgba(200,210,235,${0.25 + z * 0.5})`} />);
    }
  }
  return (
    <svg width={1080} height={1920} style={{ position: 'absolute', inset: 0 }}>
      <line x1={x} y1={0} x2={x} y2={y - r} stroke="#555" strokeWidth={3} />
      <circle cx={x} cy={y} r={r} fill="#2a2440" />
      {tiles}
      <circle cx={x - r * 0.35} cy={y - r * 0.4} r={r * 0.3} fill="#fff" opacity={0.25} />
    </svg>
  );
};

/** Crowd of original silhouettes with hands up, bouncing on the beat. */
export const Crowd: React.FC<{ y?: number; count?: number; seed?: string; color?: string; scale?: number }> = ({
  y = 1500,
  count = 14,
  seed = 'cr',
  color = '#05020a',
  scale = 1,
}) => {
  const frame = useCurrentFrame();
  const p = beatPulse(frame, 5);
  return (
    <svg width={1080} height={1920} style={{ position: 'absolute', inset: 0 }}>
      {Array.from({ length: count }, (_, i) => {
        const x = (i / (count - 1)) * 1160 - 40 + (random(seed + 'x' + i) - 0.5) * 40;
        const s = (0.8 + random(seed + 's' + i) * 0.5) * scale;
        const jump = -p * (20 + random(seed + 'j' + i) * 30) * s;
        const armUp = random(seed + 'a' + i) > 0.4;
        const wave = Math.sin(frame * 0.3 + i) * 10;
        return (
          <g key={i} transform={`translate(${x} ${y + jump}) scale(${s})`} fill={color}>
            <circle cx={0} cy={-210} r={42} />
            <path d="M-70,-150 C-60,-170 60,-170 70,-150 L95,400 L-95,400 Z" />
            {armUp ? (
              <>
                <path d={`M-55,-140 L${-110 + wave},-330 L${-90 + wave},-340 L-30,-150 Z`} />
                <path d={`M55,-140 L${110 - wave},-330 L${90 - wave},-340 L30,-150 Z`} />
              </>
            ) : (
              <path d={`M55,-140 L${120 - wave},-300 L${102 - wave},-312 L30,-150 Z`} />
            )}
          </g>
        );
      })}
    </svg>
  );
};

/** Packed club: haze, rotating lasers, spotlights, strobes, mirror ball, crowd. */
export const Club: React.FC<{ energy?: number }> = ({ energy = 1 }) => {
  const frame = useCurrentFrame();
  const p = beatPulse(frame, 4);
  const lasers = 14;
  return (
    <AbsoluteFill style={{ overflow: 'hidden', background: 'radial-gradient(ellipse at 50% 30%, #2b0b4d 0%, #12052a 50%, #05030a 100%)' }}>
      {/* lasers from two emitters */}
      <svg width={1080} height={1920} style={{ position: 'absolute', inset: 0, mixBlendMode: 'screen' }}>
        <defs>
          <filter id="lz" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="5" result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        <g filter="url(#lz)">
          {[200, 880].map((ex, e) =>
            Array.from({ length: lasers }, (_, i) => {
              const base = (i / (lasers - 1) - 0.5) * 110;
              const swing = Math.sin(frame * 0.07 + e * 2) * 28;
              const a = ((base + swing + 90) * Math.PI) / 180;
              const L = 2600;
              const col = (i + e) % 3 === 0 ? C.ice : (i + e) % 3 === 1 ? C.pink : C.violet;
              return (
                <line
                  key={`${e}-${i}`}
                  x1={ex}
                  y1={180}
                  x2={ex + Math.cos(a) * L}
                  y2={180 + Math.sin(a) * L}
                  stroke={col}
                  strokeWidth={3 + p * 3}
                  opacity={(0.45 + p * 0.5) * energy}
                />
              );
            })
          )}
        </g>
      </svg>
      {/* haze */}
      <AbsoluteFill style={{ background: 'radial-gradient(ellipse at 50% 70%, rgba(138,77,255,0.35), transparent 60%)', opacity: 0.7 + p * 0.3 }} />
      <MirrorBall x={540} y={330} r={110} />
      {/* spot cones */}
      {[0, 1, 2].map((i) => {
        const ang = Math.sin(frame * 0.05 + i * 2.1) * 30;
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: 180 + i * 360 - 300,
              top: 0,
              width: 600,
              height: 2000,
              transformOrigin: '50% 0',
              transform: `rotate(${ang}deg)`,
              background: `linear-gradient(180deg, ${i === 1 ? 'rgba(255,79,179,0.5)' : 'rgba(127,227,255,0.4)'}, transparent 80%)`,
              clipPath: 'polygon(47% 0, 53% 0, 100% 100%, 0 100%)',
              mixBlendMode: 'screen',
            }}
          />
        );
      })}
      <Crowd y={1560} count={12} seed="far" color="#120725" scale={0.75} />
      <Crowd y={1720} count={9} seed="near" />
      {/* beat strobes */}
      {BEATS.map((b, i) => {
        const t = frame - b;
        if (t < 0 || t > 3 || i % 2) return null;
        return <AbsoluteFill key={b} style={{ background: '#fff', opacity: 0.18 * (1 - t / 3) * energy, mixBlendMode: 'screen' }} />;
      })}
    </AbsoluteFill>
  );
};
