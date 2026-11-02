import React from 'react';
import { AbsoluteFill, random, useCurrentFrame } from 'remotion';
import { C, FONT } from '../../theme';
import { BEATS } from '../../timing';
import { Glitter } from '../particles/Sparkles';
import { GirlSilhouette } from './GirlSilhouette';

/** Spotlight cone from above. */
const Spot: React.FC<{ x: number; angle: number; color: string; opacity?: number }> = ({ x, angle, color, opacity = 0.5 }) => (
  <div
    style={{
      position: 'absolute',
      left: x - 260,
      top: -200,
      width: 520,
      height: 2300,
      transformOrigin: '50% 0%',
      transform: `rotate(${angle}deg)`,
      background: `linear-gradient(180deg, ${color} 0%, transparent 85%)`,
      clipPath: 'polygon(46% 0, 54% 0, 100% 100%, 0 100%)',
      opacity,
      mixBlendMode: 'screen',
    }}
  />
);

/** Glossy magazine cover: masthead, cover lines, barcode, silhouette, paparazzi flashes. */
export const MagazineCover: React.FC<{ mood: number }> = ({ mood }) => {
  // mood 0 = pop (pink gloss), 1 = rock (cold chrome)
  const frame = useCurrentFrame();
  const zoom = 1.18 - 0.16 * Math.min(1, frame / 140);
  const bgPop = `radial-gradient(ellipse at 50% 35%, #ff8bd0 0%, #e0338f 35%, #5a0f4a 75%, #12041c 100%)`;
  const bgRock = `radial-gradient(ellipse at 50% 35%, #a9c4ff 0%, #4a4f8c 35%, #1a1238 75%, #05030a 100%)`;
  return (
    <AbsoluteFill style={{ overflow: 'hidden', background: C.black }}>
      <AbsoluteFill style={{ background: bgPop }} />
      <AbsoluteFill style={{ background: bgRock, opacity: mood }} />
      {/* layer 1: spotlights, slow parallax */}
      <AbsoluteFill style={{ transform: `scale(${zoom * 1.05})` }}>
        <Spot x={260} angle={-14 + Math.sin(frame * 0.04) * 6} color={mood > 0.5 ? C.ice : '#ffd1ee'} opacity={0.35} />
        <Spot x={820} angle={14 + Math.cos(frame * 0.05) * 6} color={mood > 0.5 ? C.violet : C.pink} opacity={0.35} />
        <Glitter count={46} seed="mag" size={[5, 18]} drift={0.6} />
      </AbsoluteFill>
      {/* layer 2: masthead */}
      <div style={{ position: 'absolute', left: 0, right: 0, top: 110, textAlign: 'center', transform: `scale(${zoom})` }}>
        <div
          style={{
            fontFamily: FONT.display,
            fontWeight: 900,
            fontSize: 210,
            letterSpacing: '0.02em',
            lineHeight: 1,
            color: 'transparent',
            WebkitTextStroke: `4px ${C.white}`,
            textShadow: `0 0 30px rgba(255,255,255,0.4)`,
            opacity: 0.92,
          }}
        >
          ЗНАК
        </div>
        <div style={{ fontFamily: FONT.mono, fontWeight: 800, fontSize: 30, color: C.white, letterSpacing: '0.5em', marginTop: 8 }}>
          №03 · НОЧНОЙ ВЫПУСК
        </div>
      </div>
      {/* layer 3: silhouette */}
      <div style={{ position: 'absolute', left: 180, top: 470, transform: `scale(${zoom * 1.02})`, transformOrigin: '50% 30%' }}>
        <GirlSilhouette width={720} tint={mood > 0.5 ? C.ice : C.pink} glint={mood} />
      </div>
      {/* layer 4: cover lines */}
      <div style={{ position: 'absolute', left: 50, top: 470, transform: `scale(${zoom})`, transformOrigin: '0 0' }}>
        <div style={{ background: C.hot, color: C.white, fontFamily: FONT.display, fontWeight: 800, fontSize: 30, padding: '8px 18px', display: 'inline-block', transform: 'rotate(-4deg)' }}>
          ЭКСКЛЮЗИВ
        </div>
        <div style={{ fontFamily: FONT.display, fontWeight: 800, fontSize: 34, color: C.white, marginTop: 22, lineHeight: 1.15 }}>
          ВСЯ НОЧЬ
          <br />
          БЕЗ СТОП-КРАНА
        </div>
      </div>
      <div style={{ position: 'absolute', right: 50, top: 560, textAlign: 'right', transform: `scale(${zoom})`, transformOrigin: '100% 0' }}>
        <div style={{ fontFamily: FONT.script, fontSize: 64, color: C.white, textShadow: `0 0 20px ${C.pink}` }}>Дора</div>
        <div style={{ fontFamily: FONT.mono, fontWeight: 800, fontSize: 24, color: C.blush, letterSpacing: '0.2em' }}>НА ОБЛОЖКЕ</div>
      </div>
      {/* barcode */}
      <svg width={180} height={110} style={{ position: 'absolute', right: 60, bottom: 80, background: '#fff', padding: 10 }}>
        {Array.from({ length: 34 }, (_, i) => (
          <rect key={i} x={i * 4.6} y={0} width={1 + Math.floor(random('bc' + i) * 3)} height={80} fill="#000" />
        ))}
        <text x={80} y={100} fontFamily="JetBrains Mono" fontSize={14} textAnchor="middle">
          0 3 0 3 2 6
        </text>
      </svg>
      {/* paparazzi flashes on beats */}
      {BEATS.filter((b) => b > 14 && b < 142).map((b, i) => {
        const t = frame - b;
        if (t < 0 || t > 5) return null;
        const x = 80 + random('pz' + i) * 920;
        const y = 400 + random('py' + i) * 1300;
        return (
          <div
            key={b}
            style={{
              position: 'absolute',
              left: x - 160,
              top: y - 160,
              width: 320,
              height: 320,
              borderRadius: '50%',
              background: 'radial-gradient(circle, #fff 0%, rgba(255,255,255,0.6) 20%, transparent 70%)',
              opacity: 1 - t / 5,
              mixBlendMode: 'screen',
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};
