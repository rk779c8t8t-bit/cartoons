import React from 'react';
import { AbsoluteFill, random, useCurrentFrame } from 'remotion';
import { Starfield } from '../components/bg/Cosmos';
import { ZODIAC, ZodiacWheel } from '../components/bg/ZodiacWheel';
import { Flash, Strobe } from '../components/fx/Flash';
import { Burst, starPath } from '../components/particles/Sparkles';
import { T } from '../components/text/Styles';
import { TextBlock, Word } from '../components/text/Word';
import { C, FONT } from '../theme';
import { BEATS, CUE, SCENES } from '../timing';
import { beatPulse, easeIn, easeOut, ramp } from '../util';

/** Signs + stars orbiting in a wide ring around the title. */
const Orbit: React.FC<{ speed: number; radius: number; frame: number }> = ({ speed, radius, frame }) => (
  <svg width={1080} height={1920} style={{ position: 'absolute', inset: 0 }}>
    {ZODIAC.map((g, i) => {
      const a = (i / 12) * Math.PI * 2 + frame * speed;
      const x = 540 + Math.cos(a) * radius;
      const y = 960 + Math.sin(a) * radius * 1.45;
      return (
        <g key={g}>
          <text x={x} y={y} textAnchor="middle" dominantBaseline="central" fontFamily={FONT.symbols} fontWeight={700} fontSize={64} fill={i % 2 ? C.pink : '#fff'} style={{ filter: `drop-shadow(0 0 10px ${C.pink})` }}>
            {g}
          </text>
          <g transform={`translate(${540 + Math.cos(a + 0.26) * radius * 0.9} ${960 + Math.sin(a + 0.26) * radius * 1.3}) rotate(${frame * 4})`}>
            <path d={starPath(14, 0.25)} fill={C.ice} />
          </g>
        </g>
      );
    })}
  </svg>
);

/** "ЗОДИА-ААК": letters stretch and tremble, then explode into glowing particles on the last syllable. */
const ZodiakTitle: React.FC = () => {
  const frame = useCurrentFrame();
  if (frame < CUE.zodia) return null;
  const boom = CUE.finalHit;
  const stretchK = ramp(frame, CUE.aak, boom, easeIn);
  const tremble = 3 + stretchK * 14;
  const line1 = Array.from('ЗОДИА-');
  const line2 = Array.from('ААК');
  const exploded = frame >= boom;
  const ek = ramp(frame, boom, boom + 14, easeOut);

  const letter = (ch: string, i: number, row: number, size: number) => {
    const idx = row * 10 + i;
    const appearAt = CUE.zodia + (row === 0 ? i * 2 : 8 + i * 3);
    if (frame < appearAt) return <span key={idx} style={{ display: 'inline-block', visibility: 'hidden', fontSize: size }}>{ch}</span>;
    const born = Math.min(1, (frame - appearAt) / 4);
    const jx = (random(`zx${idx}${frame}`) - 0.5) * tremble;
    const jy = (random(`zy${idx}${frame}`) - 0.5) * tremble;
    const isA = row === 1 && i < 2;
    const sy = isA ? 1 + stretchK * 0.75 : 1 + stretchK * 0.15;
    const sx = isA ? 1 + stretchK * 0.18 : 1;
    let t = `translate(${jx}px, ${jy}px) scale(${(2 - born) * sx}, ${(2 - born) * sy})`;
    let o = born;
    let blur = (1 - born) * 10;
    if (exploded) {
      const a = random('ze' + idx) * Math.PI * 2;
      const d = ek * (500 + random('zd' + idx) * 700);
      t = `translate(${Math.cos(a) * d}px, ${Math.sin(a) * d}px) rotate(${(random('zr' + idx) - 0.5) * 540 * ek}deg) scale(${1 + ek * 1.5})`;
      o = 1 - ek;
      blur = ek * 20;
    }
    return (
      <span
        key={idx}
        style={{
          display: 'inline-block',
          transform: t,
          transformOrigin: '50% 80%',
          opacity: o,
          filter: `blur(${blur}px)`,
          fontSize: size,
        }}
      >
        {ch}
      </span>
    );
  };

  const style: React.CSSProperties = {
    fontFamily: FONT.display,
    fontWeight: 900,
    color: '#fff',
    letterSpacing: '-0.02em',
    textShadow: `${'-5px 0 0 rgba(255,40,150,0.9), 5px 0 0 rgba(90,220,255,0.9)'}, 0 0 30px ${C.pink}, 0 0 80px ${C.violet}`,
    lineHeight: 1,
  };
  return (
    <div style={{ position: 'absolute', left: 40, right: 40, top: 700, textAlign: 'center', ...style }}>
      <div>{line1.map((c, i) => letter(c, i, 0, 150))}</div>
      <div style={{ marginTop: 40 }}>{line2.map((c, i) => letter(c, i, 1, 270))}</div>
    </div>
  );
};

export const S8Finale: React.FC = () => {
  const frame = useCurrentFrame();
  const { from } = SCENES.finale;
  const p = beatPulse(frame, 4);
  // wheel speeds up toward the end (speed ramp)
  const spin = ramp(frame, CUE.zodia, CUE.finalHit, easeIn);
  const rot = (frame - from) * 0.6 + spin * spin * 260;
  const showFirst = frame < CUE.zodia - 2;
  const punch = Math.exp(-Math.max(0, frame - CUE.finalHit) / 5) * (frame >= CUE.finalHit ? 0.18 : 0);
  const black = ramp(frame, CUE.finalHit + 6, CUE.finalHit + 13);
  return (
    <AbsoluteFill style={{ background: 'radial-gradient(ellipse at 50% 50%, #3a0f5e 0%, #12052a 55%, #05030a 100%)', overflow: 'hidden' }}>
      <AbsoluteFill style={{ transform: `scale(${1.02 + p * 0.03 + punch})` }}>
        <Starfield drift={1 + spin * 6} seed="z8" count={150} />
        <AbsoluteFill style={{ opacity: 0.55 + spin * 0.4 }}>
          <ZodiacWheel rotation={rot} cy={960} r={500} glow={1} highlight={spin} />
        </AbsoluteFill>
        {frame >= CUE.zodia && <Orbit speed={0.02 + spin * 0.08} radius={430 + spin * 40} frame={frame} />}
      </AbsoluteFill>

      {showFirst && (
        <>
          <TextBlock top={330}>
            <Word text="ТЫ МНОЙ" at={CUE.ty} enter="slam" enterDur={5} block style={T.extruded(112, '#fff', C.hot)} />
            <Word text="ОДЕРЖИМ" at={CUE.oderzhim} enter="glitch" enterDur={10} block style={{ ...T.extruded(116, '#fff', C.violet), color: C.blush }} />
          </TextBlock>
          <TextBlock top={720}>
            <Word text="УЖЕ ДАВНО," at={CUE.uzhe} enter="type" enterDur={14} block style={T.mono(70, '#fff')} />
          </TextBlock>
          <TextBlock top={1250}>
            <Word text="КАК" at={CUE.kak8} enter="rise" block style={T.lyric(80)} />
            <Word
              text="МАНЬЯК"
              at={CUE.manyak}
              enter="slam"
              enterDur={5}
              block
              style={{ ...T.chrome(190), filter: 'drop-shadow(0 0 16px rgba(255,45,149,0.9)) drop-shadow(0 8px 0 #2a0b30)' }}
              letterStyle={(i, _c, f) => ({ transform: `translate(${(random('mn' + i + f) - 0.5) * 8}px, ${(random('mny' + i + f) - 0.5) * 8}px)` })}
            />
          </TextBlock>
        </>
      )}
      <ZodiakTitle />

      {/* beat flashes on the last bars */}
      {BEATS.filter((b) => b >= CUE.zodia && b < CUE.finalHit).map((b) => (
        <Strobe key={b} at={b} duration={3} peak={0.35} color={C.pink} />
      ))}
      <Strobe at={CUE.ty} duration={4} peak={0.6} />
      <Burst at={CUE.finalHit} x={540} y={1000} count={140} shape="star" seed="fin" colors={['#fff', C.pink, C.ice, C.lilac]} speed={60} gravity={0.15} life={22} size={14} />
      <Burst at={CUE.finalHit} x={540} y={1000} count={90} shape="dot" seed="fin2" colors={['#fff', C.blush]} speed={80} gravity={0} life={18} />
      <Flash at={CUE.finalHit} duration={12} x={540} y={1000} peak={1} />
      <AbsoluteFill style={{ background: '#000', opacity: black }} />
    </AbsoluteFill>
  );
};
