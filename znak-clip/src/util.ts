import { Easing, interpolate, random } from 'remotion';
import { BEATS } from './timing';

export const clamp = (v: number, a = 0, b = 1) => Math.min(b, Math.max(a, v));

/** 0→1 ramp between frames a and b, clamped, with optional easing. */
export const ramp = (frame: number, a: number, b: number, ease: (t: number) => number = (t) => t) =>
  ease(clamp((frame - a) / Math.max(1, b - a)));

export const easeOut = Easing.out(Easing.cubic);
export const easeIn = Easing.in(Easing.cubic);
export const easeInOut = Easing.inOut(Easing.cubic);
export const backOut = Easing.out(Easing.back(2.2));
export const expoOut = Easing.out(Easing.exp);

export const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

/** Exponential decay pulse since the last beat (1 on the beat, →0). */
export const beatPulse = (frame: number, decay = 4) => {
  let last = -999;
  for (const b of BEATS) {
    if (b <= frame) last = b;
    else break;
  }
  return Math.exp(-(frame - last) / decay);
};

export const beatIndex = (frame: number) => {
  let i = -1;
  for (let k = 0; k < BEATS.length; k++) if (BEATS[k] <= frame) i = k;
  return i;
};

/** Pulse after a specific cue frame. */
export const hit = (frame: number, cue: number, decay = 5) => (frame < cue ? 0 : Math.exp(-(frame - cue) / decay));

export const rnd = (seed: string | number) => random(seed);
export const rr = (seed: string | number, a: number, b: number) => a + random(seed) * (b - a);

/** Speed ramp: maps linear progress to fast-slow-fast motion. */
export const speedRamp = (t: number) => {
  const x = clamp(t);
  return x < 0.5 ? 0.5 * Math.pow(x * 2, 0.45) : 1 - 0.5 * Math.pow((1 - x) * 2, 0.45);
};

export { interpolate };
