import React from 'react';
import { AbsoluteFill, random, useCurrentFrame } from 'remotion';
import { Club } from '../components/bg/Club';
import { useSpectrum } from '../components/bg/MusicPlayer';
import { Strobe } from '../components/fx/Flash';
import { heartPath, starPath } from '../components/particles/Sparkles';
import { T } from '../components/text/Styles';
import { TextBlock, Word } from '../components/text/Word';
import { C, FONT } from '../theme';
import { CUE, SCENES } from '../timing';
import { beatPulse, easeOut, ramp } from '../util';

/** Vibrates its children with the bass. */
const Vibrate: React.FC<{ amount: number; children: React.ReactNode; seed: string }> = ({ amount, children, seed }) => {
  const frame = useCurrentFrame();
  const x = (random(seed + 'x' + frame) - 0.5) * amount;
  const y = (random(seed + 'y' + frame) - 0.5) * amount;
  return <div style={{ transform: `translate(${x}px, ${y}px) scale(${1 + amount * 0.002})` }}>{children}</div>;
};

/** "БИТКОМ": the frame fills up with hearts, stars, $, tickets and words. */
const PackedFill: React.FC<{ from: number; full: number }> = ({ from, full }) => {
  const frame = useCurrentFrame();
  if (frame < from) return null;
  const N = 150;
  const k = ramp(frame, from, full, easeOut);
  const shown = Math.floor(k * N);
  const items = ['heart', 'star', '$', 'word', 'ticket'];
  return (
    <svg width={1080} height={1920} style={{ position: 'absolute', inset: 0 }}>
      {Array.from({ length: shown }, (_, i) => {
        const kind = items[i % items.length];
        const x = random('pf' + i) * 1080;
        const y = random('pfy' + i) * 1920;
        const born = from + (i / N) * (full - from);
        const s = Math.min(1, (frame - born) / 4);
        const sz = 60 + random('pfs' + i) * 140;
        const rot = (random('pfr' + i) - 0.5) * 60;
        const col = [C.pink, C.ice, C.silver, C.violet, C.hot][i % 5];
        return (
          <g key={i} transform={`translate(${x} ${y}) rotate(${rot}) scale(${s})`}>
            {kind === 'heart' && <path d={heartPath(sz * 1.4)} fill={col} />}
            {kind === 'star' && <path d={starPath(sz * 0.7, 0.35)} fill={col} />}
            {kind === '$' && (
              <text fontFamily="Unbounded" fontWeight={900} fontSize={sz} fill={col} textAnchor="middle" dy={sz * 0.35}>
                $
              </text>
            )}
            {kind === 'word' && (
              <text fontFamily="Unbounded" fontWeight={900} fontSize={sz * 0.45} fill="#fff" stroke={col} strokeWidth={3} textAnchor="middle">
                БИТКОМ
              </text>
            )}
            {kind === 'ticket' && (
              <g>
                <rect x={-sz * 0.6} y={-sz * 0.3} width={sz * 1.2} height={sz * 0.6} rx={10} fill={col} />
                <text fontFamily="JetBrains Mono" fontWeight={800} fontSize={sz * 0.2} fill="#120725" textAnchor="middle" dy={sz * 0.07}>
                  SOLD OUT
                </text>
              </g>
            )}
          </g>
        );
      })}
    </svg>
  );
};

export const S3Club: React.FC = () => {
  const frame = useCurrentFrame();
  const { from, to } = SCENES.club;
  const spec = useSpectrum(8);
  const bass = Math.min(1, (spec[0] + spec[1]) * 3);
  const vib = 6 + bass * 18 + beatPulse(frame, 3) * 12;
  const zoomIn = 1.25 - 0.25 * ramp(frame, from, from + 10, easeOut);
  const fill = ramp(frame, CUE.bitkom, CUE.club - 2);
  const clearText = frame >= CUE.mesta - 2;
  return (
    <AbsoluteFill style={{ background: C.black }}>
      <AbsoluteFill style={{ transform: `scale(${zoomIn + beatPulse(frame, 4) * 0.02})` }}>
        <Club energy={1 + fill} />
      </AbsoluteFill>

      {!clearText && (
        <Vibrate amount={vib} seed="l3a">
          <TextBlock top={560}>
            <Word text="ЭЙ," at={CUE.ey} enter="slam" block style={T.extruded(230, '#fff', C.hot)} />
            <Word text="бэйби," at={CUE.baby} enter="spin" block style={{ ...T.script(170), marginTop: 10 }} />
          </TextBlock>
          <TextBlock top={1010}>
            <Word text="DON'T " at={CUE.dont2} enter="glitch" style={T.neon(C.ice, 104)} />
            <Word text="STOP" at={CUE.stop2} enter="glitch" style={T.neon(C.pink, 104)} />
          </TextBlock>
        </Vibrate>
      )}
      {clearText && (
        <>
          <Vibrate amount={vib} seed="l3b">
            <TextBlock top={520}>
              <Word text="МЕСТА НЕТ —" at={CUE.mesta} enter="type" enterDur={10} block style={T.mono(70, '#fff')} />
            </TextBlock>
          </Vibrate>
          <PackedFill from={CUE.bitkom} full={CUE.club + 4} />
          <Vibrate amount={vib * 1.4} seed="l3c">
            <TextBlock top={760}>
              <Word
                text="БИТКОМ"
                at={CUE.bitkom}
                enter="slam"
                block
                style={{ ...T.extruded(150, '#fff', C.violet), WebkitTextStroke: `3px ${C.hot}` }}
              />
            </TextBlock>
            <TextBlock top={1010}>
              <Word text="КЛАБ" at={CUE.club} enter="slam" enterDur={4} block style={{ ...T.chrome(220), fontFamily: FONT.display, fontWeight: 900 }} />
            </TextBlock>
          </Vibrate>
        </>
      )}
      <Strobe at={CUE.ey} duration={5} peak={0.7} color={C.pink} />
      <Strobe at={CUE.bitkom} duration={4} peak={0.8} />
      <Strobe at={CUE.club} duration={4} peak={0.9} color={C.ice} />
      {/* hard cut: 2 frames of white then black */}
      {frame >= to - 3 && <AbsoluteFill style={{ background: frame >= to - 1 ? C.black : '#fff' }} />}
    </AbsoluteFill>
  );
};
