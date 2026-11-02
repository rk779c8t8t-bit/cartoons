import React from 'react';
import { Composition } from 'remotion';
import './fonts';
import { ZnakVideo } from './Video';
import { DURATION, FPS } from './timing';

export const Root: React.FC = () => (
  <Composition id="ZnakDora" component={ZnakVideo} durationInFrames={DURATION} fps={FPS} width={1080} height={1920} />
);
