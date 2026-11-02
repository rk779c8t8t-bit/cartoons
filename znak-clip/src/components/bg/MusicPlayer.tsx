import React from 'react';
import { useAudioData, visualizeAudio } from '@remotion/media-utils';
import { staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import { C, FONT } from '../../theme';
import { CLIP_START } from '../../timing';
import { starPath } from '../particles/Sparkles';

/** Real spectrum of the track at the current frame (32 bands). */
export const useSpectrum = (bands = 32) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const audioData = useAudioData(staticFile('verse.wav'));
  if (!audioData) return new Array(bands).fill(0) as number[];
  return visualizeAudio({ fps, frame, audioData, numberOfSamples: 64, smoothing: true }).slice(0, bands);
};

/** Glassy music player card; waveform bars driven by the real audio. */
export const MusicPlayer: React.FC<{ appear: number; stretch?: number }> = ({ appear, stretch = 0 }) => {
  const frame = useCurrentFrame();
  const spec = useSpectrum(28);
  const elapsed = 2 * 60 + 19 + frame / 30; // show song position (≈ 2:19 + clip time)
  const mm = Math.floor(elapsed / 60);
  const ss = Math.floor(elapsed % 60).toString().padStart(2, '0');
  const progress = (CLIP_START + frame / 30) / 216;
  return (
    <div
      style={{
        position: 'absolute',
        left: 110,
        width: 860,
        top: 1100,
        height: 560,
        borderRadius: 48,
        background: 'linear-gradient(160deg, rgba(255,255,255,0.22), rgba(255,255,255,0.04))',
        border: '2px solid rgba(255,255,255,0.35)',
        boxShadow: '0 30px 80px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.5)',
        backdropFilter: 'blur(18px)',
        opacity: Math.min(1, Math.max(0, (frame - appear) / 6)) * (1 - stretch),
        transform: `translateY(${Math.max(0, 1 - (frame - appear) / 8) * 200}px)`,
        overflow: 'hidden',
      }}
    >
      <div style={{ position: 'absolute', left: 40, top: 40, width: 150, height: 150, borderRadius: 24, background: `linear-gradient(135deg, ${C.hot}, ${C.violet})` }}>
        <svg width={150} height={150}>
          <g transform={`translate(75 75) rotate(${frame * 2})`}>
            <path d={starPath(52, 0.4)} fill="#fff" />
          </g>
        </svg>
      </div>
      <div style={{ position: 'absolute', left: 220, top: 52, fontFamily: FONT.display, fontWeight: 900, fontSize: 64, color: '#fff' }}>ЗНАК</div>
      <div style={{ position: 'absolute', left: 222, top: 140, fontFamily: FONT.mono, fontWeight: 800, fontSize: 30, color: C.blush }}>Toxi$, Дора</div>
      {/* waveform */}
      <div style={{ position: 'absolute', left: 40, right: 40, top: 230, height: 170, display: 'flex', alignItems: 'center', gap: 8 }}>
        {spec.map((v, i) => {
          const h = 12 + Math.min(1, Math.sqrt(v) * 2.4) * 160;
          return <div key={i} style={{ flex: 1, height: h, borderRadius: 8, background: `linear-gradient(180deg, ${C.ice}, ${C.pink})`, boxShadow: `0 0 14px ${C.pink}` }} />;
        })}
      </div>
      {/* progress */}
      <div style={{ position: 'absolute', left: 40, right: 40, top: 430, height: 8, borderRadius: 4, background: 'rgba(255,255,255,0.25)' }}>
        <div style={{ width: `${progress * 100}%`, height: '100%', borderRadius: 4, background: '#fff' }} />
      </div>
      <div style={{ position: 'absolute', left: 40, top: 452, fontFamily: FONT.mono, fontSize: 26, color: '#fff' }}>
        {mm}:{ss}
      </div>
      <div style={{ position: 'absolute', right: 40, top: 452, fontFamily: FONT.mono, fontSize: 26, color: '#fff' }}>3:36</div>
      {/* controls */}
      <svg width={300} height={70} style={{ position: 'absolute', left: 280, top: 470 }}>
        <path d="M40,15 L40,55 L10,35 Z M70,15 L70,55 L40,35 Z" fill="#fff" />
        <rect x={130} y={14} width={12} height={42} rx={3} fill="#fff" />
        <rect x={156} y={14} width={12} height={42} rx={3} fill="#fff" />
        <path d="M230,15 L230,55 L260,35 Z M260,15 L260,55 L290,35 Z" fill="#fff" />
      </svg>
    </div>
  );
};
