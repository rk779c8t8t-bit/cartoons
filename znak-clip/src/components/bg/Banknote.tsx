import React from 'react';
import { useCurrentFrame } from 'remotion';
import { C } from '../../theme';
import { heartPath, starPath } from '../particles/Sparkles';

/** Guilloche rosette: overlapping sinusoidal rings, the classic security-print pattern. */
const Rosette: React.FC<{ cx: number; cy: number; r: number; color: string; petals?: number; rings?: number }> = ({
  cx,
  cy,
  r,
  color,
  petals = 18,
  rings = 7,
}) => (
  <g fill="none" stroke={color} strokeWidth={1.2} opacity={0.75}>
    {Array.from({ length: rings }, (_, k) => {
      const pts: string[] = [];
      const rr = r * (0.45 + k * 0.08);
      for (let i = 0; i <= 360; i += 2) {
        const a = (i * Math.PI) / 180;
        const m = rr + Math.sin(a * petals + k) * r * 0.12;
        pts.push(`${cx + Math.cos(a) * m},${cy + Math.sin(a) * m}`);
      }
      return <polyline key={k} points={pts.join(' ')} />;
    })}
  </g>
);

/** Fine wave lines across the note. */
const Waves: React.FC<{ w: number; h: number; color: string }> = ({ w, h, color }) => (
  <g fill="none" stroke={color} strokeWidth={1} opacity={0.4}>
    {Array.from({ length: 26 }, (_, k) => {
      const pts: string[] = [];
      for (let x = 0; x <= w; x += 8) pts.push(`${x},${(k / 26) * h + Math.sin(x * 0.03 + k * 0.6) * 9}`);
      return <polyline key={k} points={pts.join(' ')} />;
    })}
  </g>
);

/**
 * Original fantasy banknote ("ЗНАК" bank, 100 ★ ). Not a replica of any real currency.
 * `watermark` 0..1 reveals the hidden heart-star watermark with a holographic sheen.
 */
export const Banknote: React.FC<{ watermark?: number; wet?: number }> = ({ watermark = 0, wet = 0 }) => {
  const frame = useCurrentFrame();
  const W = 960;
  const H = 440;
  const holo = (frame * 4) % 360;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width={W} height={H} style={{ overflow: 'visible' }}>
      <defs>
        <linearGradient id="bn-paper" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#dfe6ef" />
          <stop offset="50%" stopColor="#c3cddc" />
          <stop offset="100%" stopColor="#e8d9ea" />
        </linearGradient>
        <linearGradient id="bn-holo" x1="0" y1="0" x2="1" y2="0" gradientTransform={`rotate(${holo / 6})`}>
          <stop offset="0%" stopColor={`hsl(${holo},90%,70%)`} />
          <stop offset="33%" stopColor={`hsl(${(holo + 120) % 360},90%,75%)`} />
          <stop offset="66%" stopColor={`hsl(${(holo + 240) % 360},90%,72%)`} />
          <stop offset="100%" stopColor={`hsl(${holo},90%,70%)`} />
        </linearGradient>
        <radialGradient id="bn-wm">
          <stop offset="0%" stopColor="#fff" stopOpacity={0.95} />
          <stop offset="100%" stopColor="#fff" stopOpacity={0} />
        </radialGradient>
        <clipPath id="bn-clip">
          <rect width={W} height={H} rx={18} />
        </clipPath>
      </defs>
      <g clipPath="url(#bn-clip)">
        <rect width={W} height={H} fill="url(#bn-paper)" />
        <Waves w={W} h={H} color="#5a4a8a" />
        <rect x={18} y={18} width={W - 36} height={H - 36} rx={12} fill="none" stroke="#3b2f66" strokeWidth={3} />
        <rect x={30} y={30} width={W - 60} height={H - 60} rx={8} fill="none" stroke="#3b2f66" strokeWidth={1} strokeDasharray="4 3" />
        <Rosette cx={150} cy={220} r={120} color="#4b3a85" petals={16} />
        <Rosette cx={810} cy={220} r={120} color="#7a2f6b" petals={22} />
        {/* centre oval: watermark window */}
        <ellipse cx={480} cy={215} rx={130} ry={160} fill="#f2f0f7" stroke="#3b2f66" strokeWidth={2} />
        <ellipse cx={480} cy={215} rx={115} ry={145} fill="none" stroke="#3b2f66" strokeWidth={1} strokeDasharray="2 4" />
        <g opacity={0.12 + watermark * 0.88}>
          <ellipse cx={480} cy={215} rx={120} ry={150} fill="url(#bn-wm)" opacity={watermark} />
          <g transform="translate(480 215)">
            <path d={heartPath(230)} fill="url(#bn-holo)" opacity={0.85} />
            <path d={starPath(70, 0.4)} fill="#fff" opacity={0.9} />
          </g>
        </g>
        {/* denominations */}
        <text x={150} y={238} textAnchor="middle" fontFamily="Unbounded" fontWeight={900} fontSize={84} fill="#2a1f55">
          100
        </text>
        <text x={810} y={240} textAnchor="middle" fontFamily="Unbounded" fontWeight={900} fontSize={90} fill="#5a1f4f">
          $
        </text>
        <text x={480} y={62} textAnchor="middle" fontFamily="Unbounded" fontWeight={800} fontSize={26} fill="#2a1f55" letterSpacing="6">
          БАНК ЗНАК · ЗВЁЗДНЫЙ ВЫПУСК
        </text>
        <text x={480} y={410} textAnchor="middle" fontFamily="JetBrains Mono" fontWeight={800} fontSize={22} fill="#2a1f55" letterSpacing="4">
          ЛЮБОВЬ НЕ ПРОДАЁТСЯ
        </text>
        <text x={70} y={410} fontFamily="JetBrains Mono" fontWeight={800} fontSize={24} fill="#7a2f6b">
          ZN 030326
        </text>
        <text x={890} y={64} textAnchor="end" fontFamily="JetBrains Mono" fontWeight={800} fontSize={24} fill="#7a2f6b">
          ZN 030326
        </text>
        {/* holographic security strip */}
        <rect x={640} y={0} width={26} height={H} fill="url(#bn-holo)" opacity={0.7} />
        {/* wet spot after the tear lands */}
        {wet > 0 && <ellipse cx={600} cy={180} rx={60 * wet} ry={40 * wet} fill="#9fb6ff" opacity={0.25} />}
      </g>
    </svg>
  );
};

/** Falling teardrop with refraction highlight. */
export const Tear: React.FC<{ x: number; y: number; scale?: number }> = ({ x, y, scale = 1 }) => (
  <svg width={120} height={170} style={{ position: 'absolute', left: x - 60 * scale, top: y - 140 * scale, transform: `scale(${scale})`, transformOrigin: '50% 82%', overflow: 'visible' }}>
    <defs>
      <radialGradient id="tear" cx="40%" cy="60%" r="60%">
        <stop offset="0%" stopColor="#ffffff" />
        <stop offset="40%" stopColor="#bfefff" stopOpacity={0.85} />
        <stop offset="100%" stopColor={C.ice} stopOpacity={0.5} />
      </radialGradient>
    </defs>
    <path d="M60,5 C60,5 15,80 15,110 C15,140 36,160 60,160 C84,160 105,140 105,110 C105,80 60,5 60,5 Z" fill="url(#tear)" stroke="#fff" strokeWidth={2} />
    <ellipse cx={45} cy={110} rx={10} ry={20} fill="#fff" opacity={0.85} />
  </svg>
);
