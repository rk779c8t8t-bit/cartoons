import React from 'react';
import { useCurrentFrame } from 'remotion';
import { C } from '../../theme';
import { starPath } from '../particles/Sparkles';

/**
 * Original stylised pop-star silhouette: voluminous hair, cat-eye sunglasses,
 * hoop earrings and a star choker. Rim-lit in pink/ice.
 */
export const GirlSilhouette: React.FC<{ width?: number; glint?: number; tint?: string }> = ({
  width = 900,
  glint = 0,
  tint = C.pink,
}) => {
  const frame = useCurrentFrame();
  const sway = Math.sin(frame * 0.05) * 1.5;
  const sweep = ((frame * 9) % 700) - 150;
  return (
    <svg viewBox="0 0 600 900" width={width} height={(width * 900) / 600} style={{ overflow: 'visible' }}>
      <defs>
        <linearGradient id="gs-body" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#1a0d2b" />
          <stop offset="100%" stopColor="#050208" />
        </linearGradient>
        <linearGradient id="gs-skin" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#4a2a66" />
          <stop offset="100%" stopColor="#24103a" />
        </linearGradient>
        <linearGradient id="gs-lens" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#ffe0f3" />
          <stop offset="35%" stopColor={tint} />
          <stop offset="70%" stopColor="#3b1066" />
          <stop offset="100%" stopColor="#7fe3ff" />
        </linearGradient>
        <linearGradient id="gs-sweep" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#fff" stopOpacity={0} />
          <stop offset="50%" stopColor="#fff" stopOpacity={0.9} />
          <stop offset="100%" stopColor="#fff" stopOpacity={0} />
        </linearGradient>
        <clipPath id="gs-lens-clip">
          <path d="M205,318 C210,296 262,290 292,300 C296,322 288,352 258,356 C228,360 205,345 205,318 Z" />
          <path d="M395,318 C390,296 338,290 308,300 C304,322 312,352 342,356 C372,360 395,345 395,318 Z" />
        </clipPath>
        <filter id="gs-rim" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="6" />
        </filter>
      </defs>
      <g transform={`rotate(${sway} 300 600)`}>
        {/* rim light halo */}
        <g filter="url(#gs-rim)" opacity={0.9}>
          <path
            d="M300,110 C170,110 118,215 128,330 C136,430 96,500 72,590 C52,665 70,720 46,790 C34,830 40,870 30,900 L570,900 C560,870 566,830 554,790 C530,720 548,665 528,590 C504,500 464,430 472,330 C482,215 430,110 300,110 Z"
            fill="none"
            stroke={tint}
            strokeWidth={10}
          />
        </g>
        {/* hair back volume */}
        <path
          d="M300,110 C170,110 118,215 128,330 C136,430 96,500 72,590 C52,665 70,720 46,790 C34,830 40,870 30,900 L570,900 C560,870 566,830 554,790 C530,720 548,665 528,590 C504,500 464,430 472,330 C482,215 430,110 300,110 Z"
          fill="url(#gs-body)"
        />
        {/* shoulders */}
        <path d="M120,900 C130,760 200,700 255,680 L345,680 C400,700 470,760 480,900 Z" fill="#0b0512" />
        {/* neck */}
        <path d="M262,560 L262,690 C280,705 320,705 338,690 L338,560 Z" fill="#2a1540" />
        {/* face */}
        <path d="M300,190 C236,190 205,250 205,320 C205,420 250,520 300,540 C350,520 395,420 395,320 C395,250 364,190 300,190 Z" fill="url(#gs-skin)" />
        {/* cheek rim light */}
        <path d="M395,320 C395,420 350,520 300,540" stroke={tint} strokeWidth={5} fill="none" opacity={0.8} />
        <path d="M205,320 C205,420 250,520 300,540" stroke="#9fe8ff" strokeWidth={3} fill="none" opacity={0.5} />
        {/* fringe */}
        <path d="M300,175 C250,172 205,215 200,300 C220,250 262,222 298,214 Z" fill="#0a0412" />
        <path d="M300,175 C350,172 395,215 400,300 C380,250 338,222 302,214 Z" fill="#0a0412" />
        {/* hair strands highlights */}
        <g fill="none" stroke={tint} strokeWidth={3} opacity={0.55}>
          <path d="M160,330 C150,450 120,560 90,700" />
          <path d="M440,330 C450,450 480,560 510,700" />
          <path d="M180,250 C160,330 168,420 150,520" opacity={0.6} />
          <path d="M420,250 C440,330 432,420 450,520" opacity={0.6} />
        </g>
        {/* lips */}
        <path d="M272,452 C288,444 312,444 328,452 C316,466 284,466 272,452 Z" fill={tint} opacity={0.85} />
        {/* sunglasses */}
        <g>
          <path d="M205,318 C210,296 262,290 292,300 C296,322 288,352 258,356 C228,360 205,345 205,318 Z" fill="url(#gs-lens)" />
          <path d="M395,318 C390,296 338,290 308,300 C304,322 312,352 342,356 C372,360 395,345 395,318 Z" fill="url(#gs-lens)" />
          <path d="M292,306 Q300,298 308,306" stroke={C.silver} strokeWidth={5} fill="none" />
          <path d="M205,312 L176,296 M395,312 L424,296" stroke={C.silver} strokeWidth={6} />
          <g clipPath="url(#gs-lens-clip)">
            <rect x={sweep} y={280} width={70} height={100} fill="url(#gs-sweep)" transform={`skewX(-25)`} />
          </g>
        </g>
        {/* hoop earrings */}
        <circle cx={196} cy={420} r={26} fill="none" stroke={C.silver} strokeWidth={5} />
        <circle cx={404} cy={420} r={26} fill="none" stroke={C.silver} strokeWidth={5} />
        {/* choker + star pendant */}
        <path d="M262,630 Q300,648 338,630" stroke={C.silver} strokeWidth={6} fill="none" />
        <g transform="translate(300 662)">
          <path d={starPath(22, 0.38)} fill={C.silver} />
        </g>
        {/* glints */}
        {[
          [250, 310],
          [345, 314],
          [404, 446],
          [300, 662],
        ].map(([x, y], i) => {
          const k = Math.max(0, Math.sin(frame * 0.18 + i * 1.7)) * (0.5 + glint);
          return (
            <g key={i} transform={`translate(${x} ${y}) scale(${0.3 + k}) rotate(${frame * 3})`} opacity={k}>
              <path d={starPath(30, 0.12)} fill="#fff" />
            </g>
          );
        })}
      </g>
    </svg>
  );
};
