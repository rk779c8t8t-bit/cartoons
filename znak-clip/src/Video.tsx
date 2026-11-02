import React from 'react';
import { AbsoluteFill, Audio, staticFile, useCurrentFrame } from 'remotion';
import { FilmGrain, LightLeak, VHS, Vignette } from './components/fx/Overlays';
import { S1Popstar } from './scenes/S1Popstar';
import { S2Night } from './scenes/S2Night';
import { S3Club } from './scenes/S3Club';
import { S4Bill } from './scenes/S4Bill';
import { S5Heart } from './scenes/S5Heart';
import { S6Cosmos } from './scenes/S6Cosmos';
import { S7Zodiac } from './scenes/S7Zodiac';
import { S8Finale } from './scenes/S8Finale';
import { C } from './theme';
import { SCENES } from './timing';
import { beatPulse } from './util';

const ORDER: Array<[keyof typeof SCENES, React.FC]> = [
  ['popstar', S1Popstar],
  ['night', S2Night],
  ['club', S3Club],
  ['bill', S4Bill],
  ['heart', S5Heart],
  ['cosmos', S6Cosmos],
  ['zodiac', S7Zodiac],
  ['finale', S8Finale],
];

/**
 * Scenes use absolute clip frames (so every cue in timing.ts is shared),
 * therefore they are mounted by range instead of offset Sequences.
 */
export const ZnakVideo: React.FC = () => {
  const frame = useCurrentFrame();
  const punch = 1 + beatPulse(frame, 4) * 0.008;
  return (
    <AbsoluteFill style={{ background: C.black, overflow: 'hidden' }}>
      <Audio src={staticFile('verse.wav')} />
      <AbsoluteFill style={{ transform: `scale(${punch})` }}>
        {ORDER.map(([id, Scene]) => {
          const { from, to } = SCENES[id];
          return frame >= from && frame < to ? <Scene key={id} /> : null;
        })}
      </AbsoluteFill>
      <LightLeak opacity={0.18} />
      <Vignette strength={0.7} />
      <VHS intensity={0.8} />
      <FilmGrain opacity={0.12} />
    </AbsoluteFill>
  );
};
