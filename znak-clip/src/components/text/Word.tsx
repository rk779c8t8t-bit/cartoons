import React from 'react';
import { random, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { clamp, easeIn, easeOut, ramp } from '../../util';

export type EnterMode = 'pop' | 'slam' | 'type' | 'spin' | 'rise' | 'flicker' | 'drop' | 'glitch' | 'zoom' | 'cut';
export type ExitMode = 'fade' | 'blur' | 'up' | 'shatter' | 'zoom' | 'cut';

export type WordProps = {
  text: string;
  at: number; // frame the word appears (relative to the parent Sequence)
  enter?: EnterMode;
  exitAt?: number;
  exit?: ExitMode;
  enterDur?: number;
  style?: React.CSSProperties;
  /** Per-letter style hook, e.g. stretching one letter. */
  letterStyle?: (i: number, ch: string, frame: number) => React.CSSProperties | undefined;
  seed?: string;
  block?: boolean;
};

/**
 * One animated word/phrase. Letters are rendered as spans so letter-level effects
 * (typewriter, shatter, stretch) can share one component.
 */
export const Word: React.FC<WordProps> = ({
  text,
  at,
  enter = 'pop',
  exitAt,
  exit = 'fade',
  enterDur,
  style,
  letterStyle,
  seed = text,
  block = false,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame - at;
  if (t < 0) return null;
  if (exitAt !== undefined && exit === 'cut' && frame >= exitAt) return null;

  const letters = Array.from(text);
  let transform = '';
  let opacity = 1;
  let filter = '';
  let visibleLetters = letters.length;

  const sp = spring({ frame: t, fps, config: { damping: 11, stiffness: 170, mass: 0.7 } });
  switch (enter) {
    case 'pop':
      transform = `scale(${0.2 + sp * 0.8})`;
      opacity = clamp(t / 3);
      break;
    case 'slam': {
      const d = enterDur ?? 6;
      const k = ramp(frame, at, at + d, easeIn);
      transform = `scale(${2.8 - 1.8 * k}) rotate(${(1 - k) * -6}deg)`;
      filter = `blur(${(1 - k) * 14}px)`;
      opacity = clamp(t / 2);
      if (t >= d && t < d + 5) transform += ` translate(${(random(seed + t) - 0.5) * 18}px, ${(random(seed + 'y' + t) - 0.5) * 18}px)`;
      break;
    }
    case 'type': {
      const d = enterDur ?? Math.max(4, letters.length * 1.6);
      visibleLetters = Math.ceil(ramp(frame, at, at + d) * letters.length);
      break;
    }
    case 'spin': {
      const s = spring({ frame: t, fps, config: { damping: 14, stiffness: 120 } });
      transform = `perspective(900px) rotateY(${(1 - s) * 100}deg) rotateZ(${(1 - s) * -10}deg)`;
      opacity = clamp(t / 4);
      break;
    }
    case 'rise': {
      const k = ramp(frame, at, at + (enterDur ?? 10), easeOut);
      transform = `translateY(${(1 - k) * 80}px)`;
      filter = `blur(${(1 - k) * 12}px)`;
      opacity = k;
      break;
    }
    case 'flicker': {
      const on = t > 9 || [0, 2, 3, 6, 8].includes(t);
      opacity = on ? 1 : 0.12;
      break;
    }
    case 'drop': {
      const s = spring({ frame: t, fps, config: { damping: 8, stiffness: 200 } });
      transform = `translateY(${(1 - s) * -260}px)`;
      opacity = clamp(t / 2);
      break;
    }
    case 'glitch': {
      const d = enterDur ?? 8;
      if (t < d) {
        const j = (1 - t / d) * 40;
        transform = `translate(${(random(seed + 'gx' + t) - 0.5) * j}px, ${(random(seed + 'gy' + t) - 0.5) * j * 0.3}px) skewX(${(random(seed + 'gs' + t) - 0.5) * j * 0.6}deg)`;
        opacity = random(seed + 'go' + t) > 0.25 ? 1 : 0.3;
      }
      break;
    }
    case 'zoom': {
      const k = ramp(frame, at, at + (enterDur ?? 14), easeOut);
      transform = `scale(${0.05 + 0.95 * k})`;
      filter = `blur(${(1 - k) * 10}px)`;
      opacity = clamp(k * 2);
      break;
    }
    case 'cut':
      break;
  }

  let letterOut: ((i: number) => React.CSSProperties) | null = null;
  if (exitAt !== undefined && frame >= exitAt) {
    const e = frame - exitAt;
    const k = clamp(e / 10);
    switch (exit) {
      case 'fade':
        opacity *= 1 - k;
        break;
      case 'blur':
        opacity *= 1 - k;
        filter += ` blur(${k * 24}px)`;
        transform += ` scale(${1 + k * 0.25})`;
        break;
      case 'up':
        opacity *= 1 - k;
        transform += ` translateY(${-k * 120}px)`;
        break;
      case 'zoom':
        opacity *= 1 - easeIn(k);
        transform += ` scale(${1 + easeIn(k) * 3})`;
        break;
      case 'shatter':
        letterOut = (i: number) => {
          const kk = clamp(e / 18);
          const a = random(seed + 'sa' + i) * Math.PI * 2;
          const v = 200 + random(seed + 'sv' + i) * 500;
          return {
            transform: `translate(${Math.cos(a) * v * kk}px, ${Math.sin(a) * v * kk + kk * kk * 300}px) rotate(${(random(seed + 'sr' + i) - 0.5) * 720 * kk}deg) scale(${1 - kk * 0.7})`,
            opacity: 1 - kk,
            filter: `blur(${kk * 6}px)`,
          };
        };
        break;
    }
  }

  // Gradient-clipped text must be painted on each letter when letters get their own
  // transforms/filters, otherwise the clip breaks (solid block or invisible text).
  const { filter: styleFilter, ...restStyle } = style ?? {};
  const clipped = restStyle.WebkitBackgroundClip === 'text' || restStyle.backgroundClip === 'text';
  const perLetter = clipped && (!!letterStyle || !!letterOut);
  const paint: React.CSSProperties = {};
  if (perLetter) {
    for (const k of ['backgroundImage', 'WebkitBackgroundClip', 'backgroundClip', 'color'] as const) {
      if (restStyle[k] !== undefined) {
        (paint as Record<string, unknown>)[k] = restStyle[k];
        delete (restStyle as Record<string, unknown>)[k];
      }
    }
  }
  const outerFilter = [filter.trim(), perLetter ? '' : styleFilter ?? ''].filter(Boolean).join(' ');

  return (
    <span
      style={{
        display: block ? 'block' : 'inline-block',
        whiteSpace: 'nowrap',
        transform,
        opacity,
        ...restStyle,
        filter: outerFilter || undefined,
      }}
    >
      {letters.map((ch, i) => {
        if (ch === ' ') return <span key={i} style={{ display: 'inline-block', width: '0.34em' }} />;
        const own = { ...(letterOut ? letterOut(i) : {}), ...(letterStyle ? letterStyle(i, ch, frame) : {}) };
        const f = [perLetter ? styleFilter ?? '' : '', own.filter ?? ''].filter(Boolean).join(' ');
        return (
          <span
            key={i}
            style={{
              display: 'inline-block',
              visibility: i < visibleLetters ? 'visible' : 'hidden',
              ...paint,
              ...own,
              filter: f || undefined,
            }}
          >
            {ch}
          </span>
        );
      })}
      {enter === 'type' && visibleLetters < letters.length && (
        <span style={{ display: 'inline-block', width: '0.08em', height: '0.9em', background: 'currentColor', marginLeft: 4, verticalAlign: '-0.1em' }} />
      )}
    </span>
  );
};

/** Centered block for laying out lines of words. */
export const TextBlock: React.FC<{
  top?: number;
  children: React.ReactNode;
  style?: React.CSSProperties;
  align?: 'center' | 'left' | 'right';
}> = ({ top = 760, children, style, align = 'center' }) => (
  <div
    style={{
      position: 'absolute',
      left: 70,
      right: 70,
      top,
      textAlign: align,
      lineHeight: 1.05,
      ...style,
    }}
  >
    {children}
  </div>
);
