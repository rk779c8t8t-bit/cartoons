import React from 'react';
import { random } from 'remotion';
import { C, FONT } from '../../theme';

// The twelve signs in their standard order (Aries → Pisces).
export const ZODIAC = ['♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓'];

/** Astrological wheel: rings, ticks, all 12 signs, constellation lines. */
export const ZodiacWheel: React.FC<{
  cx?: number;
  cy?: number;
  r?: number;
  rotation: number;
  glow?: number;
  highlight?: number; // 0..1 brightens glyphs
}> = ({ cx = 540, cy = 900, r = 430, rotation, glow = 1, highlight = 0 }) => (
  <svg width={1080} height={1920} style={{ position: 'absolute', inset: 0, overflow: 'visible' }}>
    <defs>
      <filter id="zw-glow" x="-30%" y="-30%" width="160%" height="160%">
        <feGaussianBlur stdDeviation="6" result="b" />
        <feMerge>
          <feMergeNode in="b" />
          <feMergeNode in="SourceGraphic" />
        </feMerge>
      </filter>
      <radialGradient id="zw-core">
        <stop offset="0%" stopColor={C.violet} stopOpacity={0.5} />
        <stop offset="100%" stopColor={C.violet} stopOpacity={0} />
      </radialGradient>
    </defs>
    <circle cx={cx} cy={cy} r={r * 1.1} fill="url(#zw-core)" />
    <g filter="url(#zw-glow)" opacity={glow} transform={`rotate(${rotation} ${cx} ${cy})`}>
      {[1, 0.86, 0.62, 0.3].map((k, i) => (
        <circle key={i} cx={cx} cy={cy} r={r * k} fill="none" stroke={i % 2 ? C.pink : C.silver} strokeWidth={i === 0 ? 4 : 2} opacity={0.85} />
      ))}
      {/* 72 ticks */}
      {Array.from({ length: 72 }, (_, i) => {
        const a = (i / 72) * Math.PI * 2;
        const r1 = r * 0.86;
        const r2 = r * (i % 6 === 0 ? 0.79 : 0.83);
        return <line key={i} x1={cx + Math.cos(a) * r1} y1={cy + Math.sin(a) * r1} x2={cx + Math.cos(a) * r2} y2={cy + Math.sin(a) * r2} stroke={C.silver} strokeWidth={i % 6 === 0 ? 3 : 1.5} />;
      })}
      {/* 12 dividers */}
      {Array.from({ length: 12 }, (_, i) => {
        const a = (i / 12) * Math.PI * 2;
        return <line key={i} x1={cx + Math.cos(a) * r * 0.62} y1={cy + Math.sin(a) * r * 0.62} x2={cx + Math.cos(a) * r} y2={cy + Math.sin(a) * r} stroke={C.lilac} strokeWidth={2} opacity={0.7} />;
      })}
      {/* glyphs, kept upright */}
      {ZODIAC.map((g, i) => {
        const a = ((i + 0.5) / 12) * Math.PI * 2;
        const x = cx + Math.cos(a) * r * 0.74;
        const y = cy + Math.sin(a) * r * 0.74;
        return (
          <text
            key={g}
            x={x}
            y={y}
            textAnchor="middle"
            dominantBaseline="central"
            fontFamily={FONT.symbols}
            fontWeight={700}
            fontSize={r * 0.15}
            fill={i % 2 ? C.blush : '#fff'}
            opacity={0.75 + highlight * 0.25}
            transform={`rotate(${-rotation} ${x} ${y})`}
          >
            {g}
          </text>
        );
      })}
      {/* constellation web in the middle ring */}
      {Array.from({ length: 10 }, (_, i) => {
        const a1 = random('c1' + i) * Math.PI * 2;
        const a2 = a1 + 0.6 + random('c2' + i);
        const r1 = r * (0.32 + random('c3' + i) * 0.26);
        const r2 = r * (0.32 + random('c4' + i) * 0.26);
        const p1 = [cx + Math.cos(a1) * r1, cy + Math.sin(a1) * r1];
        const p2 = [cx + Math.cos(a2) * r2, cy + Math.sin(a2) * r2];
        return (
          <g key={i}>
            <line x1={p1[0]} y1={p1[1]} x2={p2[0]} y2={p2[1]} stroke={C.ice} strokeWidth={1.5} opacity={0.6} />
            <circle cx={p1[0]} cy={p1[1]} r={4} fill="#fff" />
            <circle cx={p2[0]} cy={p2[1]} r={3} fill={C.ice} />
          </g>
        );
      })}
    </g>
  </svg>
);

/**
 * A sign "orb". We do not know which signs are meant in the lyric, so the orb spins
 * through all twelve and settles on a mystery glyph instead of inventing one.
 */
export const SignOrb: React.FC<{ x: number; y: number; frame: number; appear: number; settle: number; label: string; color: string; size?: number }> = ({
  x,
  y,
  frame,
  appear,
  settle,
  label,
  color,
  size = 220,
}) => {
  if (frame < appear) return null;
  const t = frame - appear;
  const s = Math.min(1, t / 6);
  const spinning = frame < settle;
  const glyph = spinning ? ZODIAC[Math.floor(t / 2) % 12] : '?';
  return (
    <div style={{ position: 'absolute', left: x - size / 2, top: y - size / 2, width: size, height: size, transform: `scale(${s * (spinning ? 1 : 1 + Math.exp(-(frame - settle) / 4) * 0.25)})` }}>
      <div
        style={{
          position: 'absolute',
          inset: 0,
          borderRadius: '50%',
          background: `radial-gradient(circle at 35% 30%, #fff 0%, ${color} 35%, #2a0b4d 100%)`,
          boxShadow: `0 0 60px 10px ${color}, inset 0 0 30px rgba(255,255,255,0.6)`,
        }}
      />
      <div
        style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontFamily: spinning ? FONT.symbols : FONT.display,
          fontWeight: spinning ? 700 : 900,
          fontSize: size * 0.5,
          color: '#fff',
          textShadow: `0 0 20px #fff`,
          filter: spinning ? 'blur(1.5px)' : undefined,
        }}
      >
        {glyph}
      </div>
      <div style={{ position: 'absolute', top: size + 16, left: -60, right: -60, textAlign: 'center', fontFamily: FONT.mono, fontWeight: 800, fontSize: 34, color: '#fff', letterSpacing: '0.2em', textShadow: `0 0 16px ${color}` }}>
        {label}
      </div>
    </div>
  );
};
