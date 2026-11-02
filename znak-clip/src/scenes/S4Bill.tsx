import React from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame } from 'remotion';
import { Banknote, Tear } from '../components/bg/Banknote';
import { Flash } from '../components/fx/Flash';
import { Bokeh, Burst, Glitter } from '../components/particles/Sparkles';
import { T } from '../components/text/Styles';
import { TextBlock, Word } from '../components/text/Word';
import { C, FONT } from '../theme';
import { CUE, SCENES } from '../timing';
import { easeIn, easeInOut, ramp } from '../util';

export const S4Bill: React.FC = () => {
  const frame = useCurrentFrame();
  const { from, to } = SCENES.bill;
  const hitF = CUE.slyozy + 1; // tear lands on "слёзы"

  // camera: macro pan across the guilloche → pull back for the tear → push into the watermark
  const scale = interpolate(
    frame,
    [from, CUE.kupyuroy, hitF - 6, hitF, CUE.vodyanoy, to],
    [3.0, 2.4, 1.05, 1.0, 1.05, 1.55],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: easeInOut }
  );
  const panX = interpolate(frame, [from, CUE.kupyuroy, hitF - 6, CUE.vodyanoy, to], [300, -260, 0, 0, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: easeInOut,
  });
  const panY = interpolate(frame, [from, hitF - 6, CUE.vodyanoy, to], [40, 0, -60, -180], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: easeInOut });
  const tilt = Math.sin(frame * 0.05) * 6;
  const wm = ramp(frame, CUE.vodyanoy - 2, CUE.znak4 + 4);
  const tearY = interpolate(frame, [hitF - 16, hitF], [-120, 860], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: easeIn });
  const sweep = ramp(frame, CUE.vodyanoy - 4, CUE.vodyanoy + 22);
  const toHeart = ramp(frame, to - 8, to, easeIn);

  return (
    <AbsoluteFill style={{ background: 'radial-gradient(ellipse at 50% 48%, #2a1450 0%, #0d0718 55%, #05030a 100%)', overflow: 'hidden' }}>
      <Bokeh seed="bill" count={14} speed={0.6} opacity={0.35} colors={[C.violet, C.pink, C.ice]} />
      <AbsoluteFill
        style={{
          justifyContent: 'center',
          alignItems: 'center',
          transform: `perspective(1600px) translate(${panX}px, ${panY}px) scale(${scale}) rotateX(${tilt}deg) rotateZ(-4deg)`,
        }}
      >
        <div style={{ filter: `drop-shadow(0 40px 60px rgba(0,0,0,0.7)) drop-shadow(0 0 ${30 * wm}px rgba(255,255,255,${0.6 * wm}))` }}>
          <Banknote watermark={wm} wet={ramp(frame, hitF, hitF + 10)} />
        </div>
        {/* back-light sweep across the note */}
        <div
          style={{
            position: 'absolute',
            width: 240,
            height: 700,
            left: -300 + sweep * 1700,
            background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.65), transparent)',
            transform: 'rotate(20deg)',
            mixBlendMode: 'overlay',
            opacity: sweep > 0 && sweep < 1 ? 1 : 0,
          }}
        />
      </AbsoluteFill>

      {frame < hitF && frame >= hitF - 16 && <Tear x={600} y={tearY} scale={1.1} />}
      <Burst at={hitF} x={600} y={880} count={70} shape="star" colors={[C.ice, '#fff', C.lilac, C.pink]} seed="tear" speed={30} gravity={0.25} life={34} />
      <Flash at={hitF} duration={6} x={600} y={880} peak={0.5} star={true} color={C.ice} />
      {wm > 0 && <Glitter count={30} seed="wm" area={{ x: 280, y: 600, w: 520, h: 640 }} size={[8, 26]} opacity={wm} />}

      <TextBlock top={220}>
        <Word text="Я ВЫТРУ" at={CUE.ya4} enter="type" enterDur={12} block style={T.mono(66, '#fff')} exitAt={CUE.vidish - 2} exit="up" />
        <Word text="КУПЮРОЙ" at={CUE.kupyuroy} enter="spin" block style={T.chrome(140)} exitAt={CUE.vidish - 2} exit="up" />
      </TextBlock>
      <TextBlock top={1380}>
        <Word text="слёзы" at={CUE.slyozy} enter="drop" block style={{ ...T.script(170, '#e6f8ff'), textShadow: `0 0 30px ${C.ice}, 0 0 60px ${C.ice}` }} exitAt={CUE.vidish - 2} exit="blur" />
      </TextBlock>
      <TextBlock top={250}>
        <Word text="ВИДИШЬ" at={CUE.vidish} enter="rise" block style={T.lyric(72)} />
      </TextBlock>
      <TextBlock top={1400}>
        <Word
          text="ВОДЯНОЙ"
          at={CUE.vodyanoy}
          enter="zoom"
          enterDur={12}
          block
          style={{
            fontFamily: FONT.display,
            fontWeight: 900,
            fontSize: 132,
            backgroundImage: `linear-gradient(${frame * 6}deg, #fff, ${C.ice}, ${C.pink}, ${C.lilac}, #fff)`,
            WebkitBackgroundClip: 'text',
            color: 'transparent',
            filter: 'drop-shadow(0 6px 0 #1a0b2e) drop-shadow(0 0 24px rgba(5,3,10,0.9)) drop-shadow(0 0 16px rgba(255,255,255,0.6))',
          }}
        />
        <Word
          text="ЗНАК?"
          at={CUE.znak4}
          enter="zoom"
          enterDur={8}
          block
          style={{
            fontFamily: FONT.display,
            fontWeight: 900,
            fontSize: 190,
            backgroundImage: `linear-gradient(${-frame * 6}deg, #fff, ${C.pink}, ${C.ice}, #fff)`,
            WebkitBackgroundClip: 'text',
            color: 'transparent',
            filter: 'drop-shadow(0 8px 0 #1a0b2e) drop-shadow(0 0 24px rgba(5,3,10,0.9)) drop-shadow(0 0 30px rgba(255,79,179,0.9))',
          }}
        />
      </TextBlock>
      {/* match cut: watermark heart floods to pink as the heart scene begins */}
      <AbsoluteFill style={{ background: `radial-gradient(circle at 50% 50%, ${C.pink} 0%, ${C.hot} ${toHeart * 60}%, transparent ${toHeart * 90}%)`, opacity: toHeart }} />
    </AbsoluteFill>
  );
};
