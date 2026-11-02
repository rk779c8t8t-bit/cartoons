import React from 'react';
import { AbsoluteFill, Freeze, useCurrentFrame } from 'remotion';
import { GlossyHeart } from '../components/bg/Heart';
import { Flash, Strobe } from '../components/fx/Flash';
import { Bokeh, Glitter } from '../components/particles/Sparkles';
import { T } from '../components/text/Styles';
import { TextBlock, Word } from '../components/text/Word';
import { C, FONT } from '../theme';
import { CUE, SCENES } from '../timing';
import { backOut, beatPulse, easeOut, ramp } from '../util';

const HeartLayer: React.FC = () => {
  const frame = useCurrentFrame();
  const { from } = SCENES.heart;
  const enter = ramp(frame, from - 2, from + 12, backOut);
  const crack = ramp(frame, CUE.netogo - 3, CUE.netogo + 2);
  const split = ramp(frame, CUE.netogo + 2, CUE.netogo + 20, easeOut);
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ background: 'radial-gradient(ellipse at 50% 45%, #5b0f4a 0%, #26093f 45%, #07030f 100%)' }} />
      <Bokeh seed="hb" count={16} speed={1.2} opacity={0.5} colors={[C.pink, C.violet, C.blush]} />
      <Glitter count={34} seed="hg" colors={[C.blush, '#fff', C.pink]} drift={-0.8} />
      <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center', transform: `translateY(-60px) scale(${0.2 + 0.8 * enter})` }}>
        <GlossyHeart beat={beatPulse(frame, 5)} crack={crack} split={split} size={860} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export const S5Heart: React.FC = () => {
  const frame = useCurrentFrame();
  const freezing = frame >= CUE.kak5;
  const blur = ramp(frame, CUE.kak5, CUE.tak + 6) * 16;
  const desat = ramp(frame, CUE.kak5, CUE.kak5 + 6) * 0.7;
  const toClouds = ramp(frame, SCENES.heart.to - 8, SCENES.heart.to);
  return (
    <AbsoluteFill style={{ background: C.black }}>
      {/* "Как же так?" — the picture stops dead and goes soft */}
      <AbsoluteFill style={{ filter: `blur(${blur + toClouds * 20}px) saturate(${1 - desat})` }}>
        <Freeze frame={CUE.kak5} active={freezing}>
          <HeartLayer />
        </Freeze>
      </AbsoluteFill>

      <TextBlock top={200}>
        <Word text="ОКЕЙ," at={CUE.okey} enter="pop" block style={T.extruded(150, '#fff', C.hot)} exitAt={CUE.no5 - 3} exit="up" />
        <Word text="Я МОГУ " at={CUE.yamogu} enter="type" enterDur={6} style={T.mono(58, '#fff')} exitAt={CUE.no5 - 3} exit="up" />
      </TextBlock>
      <TextBlock top={1370}>
        <Word text="влюбить в себя" at={CUE.vlyubit} enter="rise" block style={T.script(120)} exitAt={CUE.no5 - 3} exit="blur" />
        <Word text="ЛЕГКО," at={CUE.legko} enter="slam" block style={T.glossyPink(150)} exitAt={CUE.no5 - 3} exit="blur" />
      </TextBlock>

      <TextBlock top={250}>
        <Word text="НО" at={CUE.no5} enter="cut" block style={{ ...T.lyric(110), color: '#fff' }} exitAt={CUE.kak5 - 1} exit="cut" />
      </TextBlock>
      {/* "НЕ ТОГО" — hard, high-contrast: black type on a white slab */}
      {frame >= CUE.netogo && frame < CUE.kak5 && (
        <div
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            top: 1380,
            height: 230,
            background: '#fff',
            transform: `skewY(-4deg) scaleX(${ramp(frame, CUE.netogo, CUE.netogo + 3)})`,
            boxShadow: `0 0 80px ${C.hot}`,
          }}
        />
      )}
      <TextBlock top={1395}>
        <Word
          text="НЕ ТОГО."
          at={CUE.netogo}
          enter="slam"
          enterDur={4}
          block
          style={{ fontFamily: FONT.display, fontWeight: 900, fontSize: 150, color: C.black, transform: 'skewY(-4deg)', letterSpacing: '-0.03em' }}
          exitAt={CUE.kak5 - 1}
          exit="cut"
        />
      </TextBlock>

      <TextBlock top={820} style={{ lineHeight: 1.15 }}>
        <Word text="КАК " at={CUE.kak5} enter="cut" style={{ ...T.lyric(120), color: '#fff' }} exitAt={SCENES.heart.to - 6} exit="blur" />
        <Word text="ЖЕ " at={CUE.zhe} enter="cut" style={{ ...T.lyric(120), color: '#fff' }} exitAt={SCENES.heart.to - 6} exit="blur" />
        <br />
        <Word text="ТАК?" at={CUE.tak} enter="zoom" enterDur={6} style={{ ...T.lyric(200), color: C.blush }} exitAt={SCENES.heart.to - 6} exit="blur" />
      </TextBlock>

      <Strobe at={CUE.netogo} duration={4} peak={0.9} />
      <Flash at={CUE.okey - 1} duration={8} x={540} y={900} peak={0.6} star={false} color={C.pink} />
      {/* soft pink haze leading into the clouds */}
      <AbsoluteFill style={{ background: 'linear-gradient(180deg, #ffc2e5, #c7a6ff)', opacity: toClouds * 0.9 }} />
    </AbsoluteFill>
  );
};
