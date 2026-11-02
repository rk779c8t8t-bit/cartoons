import React from 'react';
import { AbsoluteFill, random, useCurrentFrame } from 'remotion';
import { MagazineCover } from '../components/bg/MagazineCover';
import { ElectricArcs } from '../components/fx/Electric';
import { Flash, Strobe } from '../components/fx/Flash';
import { Burst } from '../components/particles/Sparkles';
import { T } from '../components/text/Styles';
import { TextBlock, Word } from '../components/text/Word';
import { C } from '../theme';
import { CUE, SCENES } from '../timing';
import { ramp, easeOut, hit } from '../util';

export const S1Popstar: React.FC = () => {
  const frame = useCurrentFrame();
  const mood = ramp(frame, CUE.rockstar - 2, CUE.rockstar + 4);
  const shake = hit(frame, CUE.rockstar, 6) * 22;
  const sx = (random('s1x' + frame) - 0.5) * shake;
  const sy = (random('s1y' + frame) - 0.5) * shake;
  const popOut = ramp(frame, CUE.rockstar - 6, CUE.rockstar, easeOut);
  return (
    <AbsoluteFill style={{ transform: `translate(${sx}px, ${sy}px)` }}>
      <MagazineCover mood={mood} />
      {/* black before the first flash, so the clip opens on the camera flash */}
      <AbsoluteFill style={{ background: C.black, opacity: frame < CUE.flash + 1 ? 0.96 : 0 }} />

      <TextBlock top={1250}>
        <Word text="ВЫГЛЯЖУ КАК" at={CUE.vyglyazhu} enter="type" enterDur={14} exitAt={CUE.no1 - 4} exit="up" block style={T.mono(58, C.white)} />
      </TextBlock>
      <TextBlock top={1335}>
        <div style={{ opacity: 1 - popOut, transform: `translateY(${-popOut * 40}px) scale(${1 - popOut * 0.3})` }}>
          <Word text="ПОПСТАР" at={CUE.popstar} enter="slam" block style={T.glossyPink(132)} />
        </div>
      </TextBlock>
      <TextBlock top={1255}>
        <Word text="НО В ДУШЕ НАВЕКИ" at={CUE.no1} enter="type" enterDur={26} block style={T.mono(54, C.ice)} />
      </TextBlock>
      <TextBlock top={1340}>
        <Word text="РОКСТАР" at={CUE.rockstar} enter="glitch" block style={T.chrome(156)} />
      </TextBlock>
      <ElectricArcs x={150} y={1330} w={780} h={190} from={CUE.rockstar} />

      <Burst at={CUE.popstar + 3} x={540} y={1420} count={70} shape="star" colors={[C.pink, C.blush, C.white]} seed="pop" speed={34} />
      <Burst at={CUE.rockstar} x={540} y={1420} count={60} shape="dot" colors={[C.ice, C.white, C.chrome]} seed="rock" speed={40} gravity={0.2} />

      <Flash at={CUE.flash} duration={16} x={540} y={700} />
      <Flash at={CUE.popstar} duration={7} x={540} y={1420} peak={0.55} star={false} color={C.blush} />
      <Strobe at={CUE.rockstar} color={C.ice} duration={5} peak={0.6} />
      {/* exit: second flash bloom that becomes the headlights of scene 2 */}
      <Flash at={SCENES.popstar.to - 6} duration={10} x={540} y={1380} peak={0.9} />
    </AbsoluteFill>
  );
};
