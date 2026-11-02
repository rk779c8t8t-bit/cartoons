import React from 'react';
import { AbsoluteFill, random, useCurrentFrame } from 'remotion';
import { Clouds, Starfield } from '../components/bg/Cosmos';
import { LightLeak } from '../components/fx/Overlays';
import { Bokeh, Glitter } from '../components/particles/Sparkles';
import { T } from '../components/text/Styles';
import { TextBlock, Word } from '../components/text/Word';
import { C, FONT } from '../theme';
import { CUE, SCENES } from '../timing';
import { easeInOut, easeOut, ramp } from '../util';

/** Gentle zero-gravity bob. */
const Float: React.FC<{ seed: number; children: React.ReactNode; amp?: number }> = ({ seed, children, amp = 14 }) => {
  const frame = useCurrentFrame();
  return (
    <div style={{ transform: `translate(${Math.sin(frame * 0.05 + seed) * amp * 0.6}px, ${Math.sin(frame * 0.07 + seed * 2) * amp}px) rotate(${Math.sin(frame * 0.04 + seed) * 2}deg)` }}>
      {children}
    </div>
  );
};

/** "FALLING IN LOVE": letters drift up, blur and fade into the clouds as light motes. */
const Dissolving: React.FC<{ text: string; at: number; dissolveAt: number; style: React.CSSProperties; seed: string }> = ({
  text,
  at,
  dissolveAt,
  style,
  seed,
}) => {
  const frame = useCurrentFrame();
  return (
    <Word
      text={text}
      at={at}
      enter="zoom"
      enterDur={16}
      block
      seed={seed}
      style={style}
      letterStyle={(i) => {
        const d = Math.max(0, frame - dissolveAt - i * 1.2);
        const k = Math.min(1, d / 22);
        return {
          transform: `translate(${(random(seed + 'dx' + i) - 0.5) * 160 * k}px, ${-k * (120 + random(seed + 'dy' + i) * 160)}px) rotate(${(random(seed + 'dr' + i) - 0.5) * 50 * k}deg)`,
          opacity: 1 - k,
          filter: `blur(${k * 18}px)`,
        };
      }}
    />
  );
};

const Motes: React.FC<{ from: number }> = ({ from }) => {
  const frame = useCurrentFrame();
  if (frame < from) return null;
  const t = frame - from;
  return (
    <svg width={1080} height={1920} style={{ position: 'absolute', inset: 0, mixBlendMode: 'screen' }}>
      {Array.from({ length: 80 }, (_, i) => {
        const x0 = 130 + random('mo' + i) * 820;
        const y0 = 700 + random('moy' + i) * 380;
        const k = Math.min(1, t / 30);
        const x = x0 + Math.sin(t * 0.08 + i) * 30;
        const y = y0 - t * (2 + random('mov' + i) * 5);
        return <circle key={i} cx={x} cy={y} r={2 + random('mor' + i) * 5} fill={i % 2 ? '#fff' : C.blush} opacity={k * (1 - Math.min(1, t / 40))} />;
      })}
    </svg>
  );
};

export const S6Cosmos: React.FC = () => {
  const frame = useCurrentFrame();
  const { from, to } = SCENES.cosmos;
  const p = ramp(frame, from, to, easeInOut);
  const rise = p * 520;
  const enter = 1 - ramp(frame, from, from + 14, easeOut);
  const dissolveAt = CUE.inlove + 12;
  const warp = ramp(frame, to - 10, to);
  return (
    <AbsoluteFill style={{ background: 'linear-gradient(180deg, #05030a 0%, #1c0b33 35%, #4b1670 65%, #c25aa8 88%, #ffc2e5 100%)', overflow: 'hidden' }}>
      <AbsoluteFill style={{ transform: `translateY(${p * 160}px) rotate(${p * 4}deg) scale(1.1)` }}>
        <Starfield drift={0.6} warp={warp} />
      </AbsoluteFill>
      <AbsoluteFill
        style={{
          background: 'radial-gradient(circle 420px at 30% 30%, rgba(138,77,255,0.45), transparent), radial-gradient(circle 380px at 75% 55%, rgba(255,79,179,0.35), transparent)',
          mixBlendMode: 'screen',
        }}
      />
      <Clouds rise={rise} />
      <Bokeh seed="cos" count={12} speed={-1.5} opacity={0.45} colors={['#fff', C.blush, C.lilac]} />
      <Glitter count={30} seed="cg" drift={-1.4} colors={['#fff', C.blush, C.ice]} />

      <TextBlock top={380} style={{ lineHeight: 1.1 }}>
        <Float seed={1}>
          <Word text="Я ХОЧУ" at={CUE.yahochu} enter="rise" block style={T.lyric(86)} exitAt={CUE.falling - 4} exit="up" />
          <Word text="забыться" at={CUE.zabytsya} enter="rise" enterDur={14} block style={T.script(180)} exitAt={CUE.falling - 4} exit="up" />
        </Float>
      </TextBlock>
      <TextBlock top={800} style={{ lineHeight: 1.15 }}>
        <Float seed={2.4}>
          <Word text="СРЕДИ " at={CUE.sredi} enter="rise" style={T.lyric(80)} exitAt={CUE.falling - 4} exit="up" />
          <Word text="ЗВЁЗД" at={CUE.zvyozd} enter="pop" style={{ ...T.neon('#fff', 104), color: '#fff' }} exitAt={CUE.falling - 4} exit="up" />
          <br />
          <Word text="И ОБЛАКОВ," at={CUE.oblakov} enter="rise" enterDur={14} style={{ ...T.lyric(86), color: C.blush }} exitAt={CUE.falling - 4} exit="up" />
        </Float>
      </TextBlock>

      <TextBlock top={700} style={{ lineHeight: 1.0 }}>
        <Float seed={4} amp={10}>
          <Dissolving text="FALLING" at={CUE.falling} dissolveAt={dissolveAt} seed="fa" style={{ ...T.glossyPink(150), fontWeight: 900 }} />
          <Dissolving text="in love" at={CUE.inlove} dissolveAt={dissolveAt + 6} seed="il" style={{ ...T.script(180, '#fff'), fontFamily: FONT.script }} />
        </Float>
      </TextBlock>
      <Motes from={dissolveAt} />
      <LightLeak opacity={0.25} seed={3} />
      {/* entry from blurred pink */}
      <AbsoluteFill style={{ background: 'linear-gradient(180deg, #ffc2e5, #c7a6ff)', opacity: enter * 0.9 }} />
    </AbsoluteFill>
  );
};
