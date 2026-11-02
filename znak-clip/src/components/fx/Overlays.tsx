import React from 'react';
import { AbsoluteFill, Img, random, staticFile, useCurrentFrame } from 'remotion';

/** Film grain from pre-generated noise tiles, jittered each frame. */
export const FilmGrain: React.FC<{ opacity?: number }> = ({ opacity = 0.13 }) => {
  const frame = useCurrentFrame();
  const i = frame % 8;
  const dx = Math.floor(random('gx' + frame) * 40);
  const dy = Math.floor(random('gy' + frame) * 40);
  return (
    <AbsoluteFill style={{ mixBlendMode: 'overlay', opacity, pointerEvents: 'none', overflow: 'hidden' }}>
      <Img
        src={staticFile(`grain/g${i}.png`)}
        style={{
          position: 'absolute',
          left: -dx,
          top: -dy,
          width: 1160,
          height: 2000,
          imageRendering: 'pixelated',
        }}
      />
    </AbsoluteFill>
  );
};

/** VHS layer: scanlines, a rolling tracking band and soft colour fringing at the edges. */
export const VHS: React.FC<{ intensity?: number }> = ({ intensity = 1 }) => {
  const frame = useCurrentFrame();
  const bandY = ((frame * 23) % 2400) - 240;
  const jitter = random('vj' + Math.floor(frame / 2)) < 0.08 ? 1 : 0;
  return (
    <AbsoluteFill style={{ pointerEvents: 'none' }}>
      <AbsoluteFill
        style={{
          opacity: 0.22 * intensity,
          background: 'repeating-linear-gradient(0deg, rgba(0,0,0,0.55) 0px, rgba(0,0,0,0.55) 1px, transparent 2px, transparent 4px)',
        }}
      />
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          top: bandY,
          height: 140 + jitter * 60,
          opacity: (0.09 + jitter * 0.12) * intensity,
          background: 'linear-gradient(180deg, transparent, rgba(255,255,255,0.7) 45%, rgba(140,200,255,0.6) 55%, transparent)',
          mixBlendMode: 'overlay',
        }}
      />
      <AbsoluteFill
        style={{
          opacity: 0.35 * intensity,
          mixBlendMode: 'screen',
          background:
            'linear-gradient(90deg, rgba(255,40,160,0.18) 0%, transparent 8%, transparent 92%, rgba(80,220,255,0.18) 100%)',
        }}
      />
    </AbsoluteFill>
  );
};

export const Vignette: React.FC<{ strength?: number }> = ({ strength = 0.75 }) => (
  <AbsoluteFill
    style={{
      pointerEvents: 'none',
      background: `radial-gradient(ellipse 75% 60% at 50% 48%, transparent 55%, rgba(4,0,10,${strength}) 100%)`,
    }}
  />
);

/** Slow drifting light leaks in the palette colours. */
export const LightLeak: React.FC<{ opacity?: number; seed?: number }> = ({ opacity = 0.35, seed = 0 }) => {
  const frame = useCurrentFrame();
  const a = frame * 0.012 + seed;
  const x1 = 540 + Math.sin(a) * 520;
  const y1 = 400 + Math.cos(a * 0.7) * 300;
  const x2 = 540 + Math.cos(a * 0.8) * 560;
  const y2 = 1500 + Math.sin(a * 1.1) * 300;
  return (
    <AbsoluteFill
      style={{
        pointerEvents: 'none',
        mixBlendMode: 'screen',
        opacity,
        background: `radial-gradient(circle 520px at ${x1}px ${y1}px, rgba(255,60,170,0.55), transparent 70%), radial-gradient(circle 600px at ${x2}px ${y2}px, rgba(120,80,255,0.5), transparent 70%)`,
      }}
    />
  );
};
