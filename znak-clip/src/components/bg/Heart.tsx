import React from 'react';
import { random } from 'remotion';
import { C } from '../../theme';

const HEART = 'M300,520 C280,500 60,360 60,200 C60,110 130,50 210,50 C255,50 285,75 300,105 C315,75 345,50 390,50 C470,50 540,110 540,200 C540,360 320,500 300,520 Z';
// zigzag crack from top notch to bottom tip
const CRACK = 'M300,105 L280,170 L322,230 L270,300 L330,365 L285,430 L300,520';
const LEFT = `M300,105 C285,75 255,50 210,50 C130,50 60,110 60,200 C60,360 280,500 300,520 L285,430 L330,365 L270,300 L322,230 L280,170 Z`;
const RIGHT = `M300,105 C315,75 345,50 390,50 C470,50 540,110 540,200 C540,360 320,500 300,520 L285,430 L330,365 L270,300 L322,230 L280,170 Z`;

/** Big glossy heart. split 0..1 cracks it then pulls the halves apart. */
export const GlossyHeart: React.FC<{ beat: number; crack: number; split: number; size?: number }> = ({
  beat,
  crack,
  split,
  size = 900,
}) => {
  const s = 1 + beat * 0.06;
  const gap = split * 170;
  const rot = split * 16;
  return (
    <svg viewBox="0 0 600 580" width={size} height={(size * 580) / 600} style={{ overflow: 'visible', transform: `scale(${s})` }}>
      <defs>
        <radialGradient id="hg" cx="38%" cy="30%" r="80%">
          <stop offset="0%" stopColor="#ffe3f4" />
          <stop offset="25%" stopColor="#ff86cf" />
          <stop offset="60%" stopColor={C.hot} />
          <stop offset="100%" stopColor="#6a0a45" />
        </radialGradient>
        <linearGradient id="hshine" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#fff" stopOpacity={0.85} />
          <stop offset="100%" stopColor="#fff" stopOpacity={0} />
        </linearGradient>
        <filter id="hglow" x="-30%" y="-30%" width="160%" height="160%">
          <feGaussianBlur stdDeviation="22" />
        </filter>
      </defs>
      <path d={HEART} fill={C.pink} filter="url(#hglow)" opacity={0.8 * (1 - split * 0.7)} />
      {split <= 0 ? (
        <g>
          <path d={HEART} fill="url(#hg)" />
          <path d="M150,110 C110,120 95,170 105,210 C140,160 180,130 230,118 C205,100 175,102 150,110 Z" fill="url(#hshine)" />
          {crack > 0 && (
            <path d={CRACK} fill="none" stroke="#fff" strokeWidth={6} strokeDasharray={600} strokeDashoffset={600 * (1 - crack)} strokeLinejoin="miter" />
          )}
        </g>
      ) : (
        <>
          <g transform={`translate(${-gap} ${split * 30}) rotate(${-rot} 300 520)`}>
            <path d={LEFT} fill="url(#hg)" />
            <path d="M150,110 C110,120 95,170 105,210 C140,160 180,130 230,118 C205,100 175,102 150,110 Z" fill="url(#hshine)" />
          </g>
          <g transform={`translate(${gap} ${split * 30}) rotate(${rot} 300 520)`}>
            <path d={RIGHT} fill="url(#hg)" />
          </g>
          {/* shards */}
          {Array.from({ length: 16 }, (_, i) => {
            const a = random('sh' + i) * Math.PI * 2;
            const d = split * (120 + random('shd' + i) * 260);
            const y0 = 140 + random('shy' + i) * 360;
            return (
              <polygon
                key={i}
                points="0,-14 10,8 -9,10"
                transform={`translate(${300 + Math.cos(a) * d} ${y0 + Math.sin(a) * d}) rotate(${split * 400 * (random('shr' + i) - 0.5)}) scale(${1 + random('shs' + i) * 1.5})`}
                fill={i % 2 ? C.blush : C.hot}
                opacity={1 - split * 0.5}
              />
            );
          })}
        </>
      )}
    </svg>
  );
};
