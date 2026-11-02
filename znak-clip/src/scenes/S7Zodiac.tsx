import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { Starfield } from '../components/bg/Cosmos';
import { SignOrb, ZodiacWheel } from '../components/bg/ZodiacWheel';
import { Flash } from '../components/fx/Flash';
import { Burst, Glitter } from '../components/particles/Sparkles';
import { T } from '../components/text/Styles';
import { TextBlock, Word } from '../components/text/Word';
import { C } from '../theme';
import { CUE, SCENES } from '../timing';
import { backOut, easeIn, easeInOut, ramp } from '../util';

export const S7Zodiac: React.FC = () => {
  const frame = useCurrentFrame();
  const { from, to } = SCENES.zodiac;
  const enter = ramp(frame, from, from + 16, backOut);
  const rot = (frame - from) * 0.45;
  // orbs: start apart, fuse in the centre in the last frames
  const fuse = ramp(frame, to - 12, to, easeIn);
  const ax = 280 + fuse * 260;
  const bx = 800 - fuse * 260;
  const oy = 1440 - fuse * 540;
  const beam = ramp(frame, CUE.plus, CUE.plus + 6);
  const pushIn = ramp(frame, from, to, easeInOut);
  return (
    <AbsoluteFill style={{ background: 'radial-gradient(ellipse at 50% 47%, #2a0f52 0%, #0d0620 55%, #05030a 100%)', overflow: 'hidden' }}>
      <Starfield drift={0.3} seed="z7" count={120} />
      <AbsoluteFill style={{ transform: `scale(${(0.3 + 0.7 * enter) * (1 + pushIn * 0.06)})`, transformOrigin: '540px 900px' }}>
        <ZodiacWheel rotation={rot} cy={900} r={420} glow={0.9} highlight={beam} />
      </AbsoluteFill>
      <Glitter count={26} seed="zg" colors={['#fff', C.ice, C.lilac]} />

      <TextBlock top={150}>
        <Word text="ЗНАЮ, " at={CUE.znayu} enter="type" enterDur={6} style={T.mono(60, '#fff')} exitAt={CUE.no7 - 3} exit="up" />
        <Word text="ТЫ НЕ ВЕРИШЬ" at={CUE.neverish} enter="type" enterDur={18} style={T.mono(60, '#fff')} exitAt={CUE.no7 - 3} exit="up" />
        <Word text="В ГОРОСКОП," at={CUE.goroskop} enter="spin" block style={{ ...T.extruded(104, '#fff', C.violet), marginTop: 18 }} exitAt={CUE.no7 - 3} exit="up" />
      </TextBlock>

      {/* the two signs */}
      <SignOrb x={ax} y={oy} frame={frame} appear={CUE.tvoy} settle={CUE.znakA + 4} label={fuse > 0.2 ? '' : 'ТВОЙ'} color={C.pink} />
      <SignOrb x={bx} y={oy} frame={frame} appear={CUE.moy - 2} settle={CUE.znakB + 4} label={fuse > 0.2 ? '' : 'МОЙ'} color={C.ice} />
      {/* glowing link between them on "плюс" */}
      {beam > 0 && (
        <div
          style={{
            position: 'absolute',
            left: ax,
            width: Math.max(0, bx - ax) * beam,
            top: oy - 5,
            height: 10,
            borderRadius: 6,
            background: `linear-gradient(90deg, ${C.pink}, #fff, ${C.ice})`,
            boxShadow: `0 0 30px 10px rgba(255,255,255,0.6)`,
          }}
        />
      )}
      {frame >= CUE.plus && frame < to - 12 && (
        <div style={{ position: 'absolute', left: 0, right: 0, top: oy - 110, textAlign: 'center', ...T.neon('#fff', 150), transform: `scale(${1 + Math.exp(-(frame - CUE.plus) / 4) * 0.6})` }}>
          +
        </div>
      )}

      <TextBlock top={330}>
        <Word text="НО " at={CUE.no7} enter="rise" style={T.lyric(80)} exitAt={to - 6} exit="blur" />
        <Word text="ТВОЙ ЗНАК" at={CUE.tvoy} enter="pop" style={{ ...T.lyric(80), color: C.pink }} exitAt={to - 6} exit="blur" />
      </TextBlock>
      <TextBlock top={1700}>
        <Word text="ПЛЮС " at={CUE.plus} enter="slam" enterDur={4} style={T.neon(C.lilac, 84)} exitAt={to - 6} exit="blur" />
        <Word text="МОЙ ЗНАК" at={CUE.moy} enter="pop" style={{ ...T.lyric(84), color: C.ice }} exitAt={to - 6} exit="blur" />
      </TextBlock>

      <Flash at={CUE.plus} duration={10} x={540} y={1440} peak={1} />
      <Burst at={CUE.plus} x={540} y={1440} count={50} shape="star" seed="plus" colors={['#fff', C.pink, C.ice]} speed={36} gravity={0.1} />
      <Flash at={to - 2} duration={10} x={540} y={900} peak={1} />
    </AbsoluteFill>
  );
};
