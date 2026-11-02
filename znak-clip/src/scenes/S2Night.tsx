import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { Car, NightCity } from '../components/bg/NightCity';
import { MusicPlayer, useSpectrum } from '../components/bg/MusicPlayer';
import { Flash } from '../components/fx/Flash';
import { T } from '../components/text/Styles';
import { TextBlock, Word } from '../components/text/Word';
import { C } from '../theme';
import { CUE, SCENES } from '../timing';
import { easeIn, ramp, speedRamp } from '../util';

export const S2Night: React.FC = () => {
  const frame = useCurrentFrame();
  const { from, to } = SCENES.night;
  // speed ramp: rush in, cruise, then accelerate into the club
  const k = speedRamp(ramp(frame, from, to));
  const speed = 0.7 + k * 1.6;
  // last 10 frames: waveform bars stretch into laser beams (match cut into scene 3)
  const stretch = ramp(frame, to - 10, to, easeIn);
  const spec = useSpectrum(16);
  const camScale = 1 + ramp(frame, from, from + 12) * 0 + (1 - ramp(frame, from, from + 14)) * 0.25;
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ transform: `scale(${camScale})` }}>
        <NightCity start={from} speed={speed} />
        <Car y={1400} scale={1.15} glow={0.8 + spec[1] * 2} />
      </AbsoluteFill>
      {/* soft scrim so lyrics stay readable over the city */}
      <AbsoluteFill style={{ background: 'linear-gradient(180deg, rgba(5,3,10,0.55) 0%, rgba(5,3,10,0.25) 45%, transparent 60%)' }} />

      <TextBlock top={250}>
        <Word text="ЕДУ " at={CUE.edu} enter="flicker" style={T.neon(C.ice, 96)} exitAt={CUE.music - 4} exit="blur" />
        <Word text="ДЕЛАТЬ" at={CUE.delat} enter="flicker" style={T.neon(C.ice, 96)} exitAt={CUE.music - 4} exit="blur" />
      </TextBlock>
      <TextBlock top={380}>
        <Word text="ШОУ" at={CUE.show} enter="zoom" enterDur={8} block style={{ ...T.extruded(250, '#fff', C.hot), letterSpacing: '0.06em' }} exitAt={CUE.music - 4} exit="zoom" />
      </TextBlock>
      <TextBlock top={720}>
        <Word text="А ЗНАЧИТ," at={CUE.aznachit} enter="rise" style={T.lyric(64)} exitAt={CUE.music - 2} exit="up" />
        <br />
        <Word text="ВСЮ " at={CUE.vsyu} enter="rise" style={T.lyric(64)} exitAt={CUE.music - 2} exit="up" />
        <Word text="НОЧЬ" at={CUE.noch} enter="pop" style={{ ...T.lyric(64), color: C.pink }} exitAt={CUE.music - 2} exit="up" />
      </TextBlock>

      {/* "music don't stop" — the player */}
      <MusicPlayer appear={CUE.music - 3} stretch={stretch} />
      <TextBlock top={330} style={{ lineHeight: 1.1, opacity: 1 - stretch }}>
        <Word text="MUSIC" at={CUE.music} enter="slam" block style={T.glossyPink(150)} />
        <Word text="DON'T" at={CUE.dont1} enter="pop" block style={T.extruded(130, C.silver, C.violet)} />
        <Word text="STOP" at={CUE.stop1} enter="slam" block style={{ ...T.chrome(170), fontFamily: "'Unbounded', sans-serif", fontWeight: 900 }} />
      </TextBlock>

      {/* bars → lasers */}
      {stretch > 0 && (
        <AbsoluteFill style={{ mixBlendMode: 'screen' }}>
          {Array.from({ length: 16 }, (_, i) => {
            const x = 150 + i * 52;
            const h = 160 + stretch * 1900;
            return (
              <div
                key={i}
                style={{
                  position: 'absolute',
                  left: x,
                  top: 1330 - h / 2,
                  width: 12 * (1 - stretch * 0.6),
                  height: h,
                  borderRadius: 8,
                  background: i % 2 ? C.pink : C.ice,
                  boxShadow: `0 0 30px 8px ${i % 2 ? C.pink : C.ice}`,
                  opacity: 0.6 + spec[i] * 2,
                  transform: `rotate(${(i - 7.5) * stretch * 4}deg)`,
                }}
              />
            );
          })}
        </AbsoluteFill>
      )}
      {/* entry: flash bloom carried from scene 1 */}
      <Flash at={from - 1} duration={8} x={540} y={1380} star={false} peak={0.8} />
    </AbsoluteFill>
  );
};
