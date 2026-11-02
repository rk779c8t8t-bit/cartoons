import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';

/** Camera-flash: white burst with a cool tint and a four-point star at the hotspot. */
export const Flash: React.FC<{
  at: number;
  duration?: number;
  x?: number;
  y?: number;
  color?: string;
  star?: boolean;
  peak?: number;
}> = ({ at, duration = 10, x = 540, y = 760, color = '#ffffff', star = true, peak = 1 }) => {
  const frame = useCurrentFrame();
  const t = frame - at;
  if (t < 0 || t > duration) return null;
  const p = t / duration;
  const o = peak * (t < 1 ? 1 : Math.pow(1 - p, 2.2));
  const s = 0.6 + p * 1.6;
  return (
    <AbsoluteFill style={{ pointerEvents: 'none', mixBlendMode: 'screen' }}>
      <AbsoluteFill
        style={{
          opacity: o,
          background: `radial-gradient(circle at ${x}px ${y}px, ${color} 0%, ${color} 18%, rgba(190,220,255,0.85) 40%, rgba(255,120,200,0.25) 75%, rgba(0,0,0,0) 100%)`,
        }}
      />
      {star && (
        <svg width={1080} height={1920} style={{ position: 'absolute', opacity: o }}>
          <g transform={`translate(${x} ${y}) scale(${s}) rotate(${p * 25})`}>
            <path d="M0,-520 L18,-18 L520,0 L18,18 L0,520 L-18,18 L-520,0 L-18,-18 Z" fill="#fff" />
            <path
              d="M0,-260 L10,-10 L260,0 L10,10 L0,260 L-10,10 L-260,0 L-10,-10 Z"
              fill="#fff"
              transform="rotate(45)"
              opacity={0.7}
            />
          </g>
        </svg>
      )}
    </AbsoluteFill>
  );
};

/** Short full-frame strobe of a colour, for beat hits. */
export const Strobe: React.FC<{ at: number; color?: string; duration?: number; peak?: number }> = ({
  at,
  color = '#fff',
  duration = 4,
  peak = 0.8,
}) => {
  const frame = useCurrentFrame();
  const t = frame - at;
  if (t < 0 || t > duration) return null;
  return <AbsoluteFill style={{ background: color, opacity: peak * (1 - t / duration), mixBlendMode: 'screen' }} />;
};
