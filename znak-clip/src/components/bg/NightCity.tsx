import React from 'react';
import { AbsoluteFill, random, useCurrentFrame } from 'remotion';
import { C, FONT, glow } from '../../theme';

const VPX = 540;
const VPY = 900;
const CAM_H = 1060; // camera height above the road (world units)
const WALL = 820; // lateral distance of the building walls
const SIGNS = ['ШОУ', 'OPEN', '24/7', 'LOVE', 'БАР', '★', 'CLUB', '♥', 'НОЧЬ', 'XXL', 'STAR', 'ZNAK'];
const SIGN_COLORS = [C.pink, C.ice, C.violet, C.hot, C.lilac];

/** World (lateral, height(+down), depth) → screen. */
const P = (L: number, h: number, z: number) => [VPX + L / z, VPY + h / z] as const;
const quad = (pts: ReadonlyArray<readonly [number, number]>) => pts.map((p) => p.join(',')).join(' ');

/** Driving forward down a neon street corridor: building walls with windows, blade signs, wet road. */
export const NightCity: React.FC<{ speed?: number; start: number }> = ({ speed = 1, start }) => {
  const frame = useCurrentFrame();
  // integrate a variable speed approximately: position grows with t*speed
  const t = (frame - start) * speed;
  const travel = t * 0.06;
  const ZN = 0.35;
  const ZF = 14;
  const seg = 1.0;
  const nSeg = Math.ceil((ZF - ZN) / seg);
  const zs = Array.from({ length: nSeg }, (_, i) => {
    const z = ((((i * seg - travel) % (nSeg * seg)) + nSeg * seg) % (nSeg * seg)) + ZN;
    return { i: i + Math.floor((travel + (nSeg * seg - i * seg)) / (nSeg * seg)) * nSeg, z };
  }).sort((a, b) => b.z - a.z);

  return (
    <AbsoluteFill style={{ overflow: 'hidden', background: 'linear-gradient(180deg, #07021a 0%, #1d0640 40%, #5a1270 47%, #120418 50%, #05030a 100%)' }}>
      {/* far skyline at the end of the street */}
      <svg width={1080} height={1920} style={{ position: 'absolute' }}>
        {Array.from({ length: 9 }, (_, i) => {
          const bw = 18 + random('fb' + i) * 20;
          const bh = 40 + random('fbh' + i) * 120;
          const x = VPX - 90 + i * 20;
          return <rect key={i} x={x} y={VPY + 70 - bh} width={bw} height={bh} fill="#14062a" />;
        })}
      </svg>
      <div style={{ position: 'absolute', left: 240, width: 600, top: VPY - 220, height: 360, background: 'radial-gradient(ellipse at 50% 70%, rgba(255,79,179,0.7), transparent 65%)' }} />

      <svg width={1080} height={1920} style={{ position: 'absolute' }}>
        <defs>
          <linearGradient id="road" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#2a0f3a" />
            <stop offset="100%" stopColor="#030106" />
          </linearGradient>
          <linearGradient id="wallL" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#0a0414" />
            <stop offset="100%" stopColor="#1c0a33" />
          </linearGradient>
          <linearGradient id="wallR" x1="1" y1="0" x2="0" y2="0">
            <stop offset="0%" stopColor="#0a0414" />
            <stop offset="100%" stopColor="#1c0a33" />
          </linearGradient>
        </defs>
        {/* road */}
        <polygon points={quad([P(-WALL, CAM_H, ZF), P(WALL, CAM_H, ZF), P(WALL, CAM_H, ZN), P(-WALL, CAM_H, ZN)])} fill="url(#road)" />
        {/* walls */}
        {([-1, 1] as const).map((side) => (
          <polygon
            key={side}
            points={quad([P(side * WALL, -4200, ZN), P(side * WALL, -4200, ZF), P(side * WALL, CAM_H, ZF), P(side * WALL, CAM_H, ZN)])}
            fill={side < 0 ? 'url(#wallL)' : 'url(#wallR)'}
          />
        ))}
        {/* windows + lane dashes, per depth slice */}
        {zs.map(({ i, z }) => {
          const fade = Math.min(1, (ZF - z) / 3);
          const items: React.ReactNode[] = [];
          ([-1, 1] as const).forEach((side) => {
            for (let row = 0; row < 7; row++) {
              const h0 = -3600 + row * 560;
              const lit = random(`w${side}${i}${row}`) > 0.45;
              if (!lit) continue;
              const z0 = z + 0.15;
              const z1 = z + 0.6;
              const col = random(`wc${side}${i}${row}`) > 0.5 ? '#ffb6e6' : '#9fe8ff';
              items.push(
                <polygon
                  key={`w${side}${row}`}
                  points={quad([P(side * WALL, h0, z0), P(side * WALL, h0, z1), P(side * WALL, h0 + 300, z1), P(side * WALL, h0 + 300, z0)])}
                  fill={col}
                  opacity={(0.25 + 0.35 * random(`wo${side}${i}${row}`)) * fade}
                />
              );
            }
          });
          // lane dash
          items.push(
            <polygon key="lane" points={quad([P(-14, CAM_H, z), P(14, CAM_H, z), P(14, CAM_H, z + 0.4), P(-14, CAM_H, z + 0.4)])} fill="#ffe2f4" opacity={0.8 * fade} />
          );
          return <g key={i}>{items}</g>;
        })}
      </svg>

      {/* blade neon signs on the walls + reflections on the wet road */}
      {zs.map(({ i, z }) => {
        if (i % 2 === 1 && i % 3 !== 0) return null;
        const side = (i % 2 === 0 ? -1 : 1) as -1 | 1;
        const [x, y] = P(side * (WALL - 120), 380, z);
        const s = 1 / z;
        const label = SIGNS[((i % SIGNS.length) + SIGNS.length) % SIGNS.length];
        const col = SIGN_COLORS[((i % SIGN_COLORS.length) + SIGN_COLORS.length) % SIGN_COLORS.length];
        const size = 150 * s;
        if (size > 420 || z > ZF - 0.5) return null;
        const flick = random(`nf${i}${Math.floor(frame / 3)}`) > 0.06 ? 1 : 0.3;
        const fade = Math.min(1, (ZF - z) / 3);
        const [, gy] = P(0, CAM_H, z);
        return (
          <React.Fragment key={'s' + i}>
            <div
              style={{
                position: 'absolute',
                left: x - size * 1.6,
                width: size * 3.2,
                top: y - size * 0.6,
                textAlign: 'center',
                fontFamily: FONT.display,
                fontWeight: 800,
                fontSize: size,
                color: '#fff',
                textShadow: glow(col, Math.max(0.5, s * 0.7)),
                opacity: flick * fade,
                whiteSpace: 'nowrap',
              }}
            >
              {label}
            </div>
            <div
              style={{
                position: 'absolute',
                left: x - size * 0.6,
                width: size * 1.2,
                top: gy,
                height: size * 2.5,
                background: `linear-gradient(180deg, ${col}, transparent)`,
                opacity: 0.3 * fade * flick,
                filter: `blur(${10 * s + 4}px)`,
                mixBlendMode: 'screen',
              }}
            />
          </React.Fragment>
        );
      })}

      {/* oncoming headlights in the left lane */}
      {Array.from({ length: 4 }, (_, i) => {
        const k = (((t * 0.02 + i / 4) % 1) + 1) % 1;
        const z = 12 - k * 11.5;
        const [x, y] = P(-380, CAM_H - 120, z);
        const s = 1 / z;
        return (
          <React.Fragment key={'h' + i}>
            <div style={{ position: 'absolute', left: x - 70 * s, top: y - 12 * s, width: 40 * s, height: 24 * s, borderRadius: 99, background: '#fff', boxShadow: `0 0 ${60 * s}px ${24 * s}px rgba(200,230,255,0.6)` }} />
            <div style={{ position: 'absolute', left: x + 30 * s, top: y - 12 * s, width: 40 * s, height: 24 * s, borderRadius: 99, background: '#fff', boxShadow: `0 0 ${60 * s}px ${24 * s}px rgba(200,230,255,0.6)` }} />
          </React.Fragment>
        );
      })}

      {/* rain */}
      <svg width={1080} height={1920} style={{ position: 'absolute', opacity: 0.35 }}>
        {Array.from({ length: 70 }, (_, i) => {
          const x = random('rx' + i) * 1080;
          const y = ((random('ry' + i) * 1920 + frame * 60) % 2100) - 100;
          return <line key={i} x1={x} y1={y} x2={x - 10} y2={y + 50} stroke="#cfe9ff" strokeWidth={2} />;
        })}
      </svg>
    </AbsoluteFill>
  );
};

/** Rear view of an original sleek coupe with a full-width pink light bar. */
export const Car: React.FC<{ y?: number; scale?: number; glow?: number }> = ({ y = 1440, scale = 1, glow: g = 1 }) => {
  const frame = useCurrentFrame();
  const bob = Math.sin(frame * 0.35) * 3;
  return (
    <div style={{ position: 'absolute', left: 540 - 380 * scale, top: y + bob, width: 760 * scale, height: 380 * scale }}>
      <div style={{ position: 'absolute', left: '-20%', right: '-20%', top: '78%', height: '70%', background: 'radial-gradient(ellipse at 50% 20%, rgba(255,45,149,0.7), transparent 70%)', filter: 'blur(20px)', opacity: g }} />
      <svg viewBox="0 0 760 380" width="100%" height="100%">
        <defs>
          <linearGradient id="carbody" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#2a1840" />
            <stop offset="60%" stopColor="#0d0716" />
            <stop offset="100%" stopColor="#050208" />
          </linearGradient>
          <linearGradient id="glass" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#45307a" />
            <stop offset="100%" stopColor="#0b0618" />
          </linearGradient>
        </defs>
        <path d="M120,150 C170,70 270,40 380,40 C490,40 590,70 640,150 L700,190 C730,205 740,240 735,290 L720,330 L40,330 L25,290 C20,240 30,205 60,190 Z" fill="url(#carbody)" />
        <path d="M175,145 C215,90 290,70 380,70 C470,70 545,90 585,145 Z" fill="url(#glass)" />
        <path d="M180,140 C230,95 300,80 380,80" stroke="#c9b6ff" strokeWidth={3} fill="none" opacity={0.5} />
        <rect x={60} y={200} width={640} height={22} rx={11} fill={C.hot} />
        <rect x={60} y={200} width={640} height={22} rx={11} fill="#fff" opacity={0.35 * g} />
        <rect x={300} y={248} width={160} height={44} rx={6} fill="#dfe3ee" />
        <text x={380} y={280} textAnchor="middle" fontFamily="JetBrains Mono" fontWeight={800} fontSize={26} fill="#1a1030">
          ЗН 030
        </text>
        <rect x={60} y={318} width={110} height={40} rx={10} fill="#050208" />
        <rect x={590} y={318} width={110} height={40} rx={10} fill="#050208" />
      </svg>
      <div style={{ position: 'absolute', left: '6%', right: '6%', top: '50%', height: 30, borderRadius: 20, boxShadow: `0 0 60px 20px rgba(255,45,149,${0.6 * g})` }} />
    </div>
  );
};
