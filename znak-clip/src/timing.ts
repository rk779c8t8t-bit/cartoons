// All timing is derived from analysis of the original track (see analysis/README.md).
// Absolute times are seconds in the full song; the clip starts one beat before Dora's first word.

export const FPS = 30;
export const CLIP_START = 139.16; // s, on a beat
export const CLIP_END = 177.89; // s, on a strong beat; leaves ~2.5 s for a soft outro
export const DURATION = Math.round((CLIP_END - CLIP_START) * FPS); // 1162 frames

// Text appears a hair before the vocal so it reads as "on" the word.
const LEAD = 2;

export const at = (absSeconds: number) => Math.round((absSeconds - CLIP_START) * FPS);
export const w = (absSeconds: number) => at(absSeconds) - LEAD;

// Beat grid (librosa beat tracker, ~110 BPM).
const BEATS_ABS = [
  139.16, 139.71, 140.25, 140.81, 141.34, 141.87, 142.43, 142.99, 143.52, 144.06, 144.61, 145.15,
  145.71, 146.24, 146.8, 147.33, 147.89, 148.42, 148.96, 149.51, 150.07, 150.6, 151.16, 151.7,
  152.25, 152.79, 153.3, 153.86, 154.44, 154.97, 155.53, 156.08, 156.62, 157.15, 157.71, 158.24,
  158.8, 159.34, 159.87, 160.43, 160.96, 161.49, 162.05, 162.59, 163.17, 163.7, 164.23, 164.77,
  165.33, 165.88, 166.44, 166.97, 167.53, 168.07, 168.62, 169.16, 169.71, 170.25, 170.81, 171.34,
  171.9, 172.43, 172.97, 173.52, 174.08, 174.61, 175.17, 175.71,
];
export const BEATS = BEATS_ABS.map(at);

// Scene boundaries (frames). Each scene starts exactly where its line starts in the vocal.
export const SCENES = {
  popstar: { from: 0, to: at(143.9) }, // 0 – 142
  night: { from: at(143.9), to: at(148.06) }, // 142 – 267
  club: { from: at(148.06), to: at(152.46) }, // 267 – 399
  bill: { from: at(152.46), to: at(156.62) }, // 399 – 524
  heart: { from: at(156.62), to: at(161.76) }, // 524 – 678
  cosmos: { from: at(161.76), to: at(166.26) }, // 678 – 813
  zodiac: { from: at(166.26), to: at(170.48) }, // 813 – 940
  finale: { from: at(170.48), to: DURATION }, // 940 – 1113
} as const;

// Word cues (frames, absolute in the clip). Values come from word-level ASR timestamps.
export const CUE = {
  // Line 1
  flash: at(139.71) - 3,
  vyglyazhu: w(139.76),
  kak1: w(140.42),
  popstar: w(140.6),
  no1: w(141.22),
  vdushe: w(141.46),
  naveki: w(142.24),
  rockstar: w(142.86),
  // Line 2
  edu: w(143.9),
  delat: w(144.42),
  show: w(144.88),
  aznachit: w(145.56),
  vsyu: w(146.04),
  noch: w(146.36),
  music: w(146.8),
  dont1: w(147.2),
  stop1: w(147.58),
  // Line 3
  ey: w(148.06),
  baby: w(148.96),
  dont2: w(149.28),
  stop2: w(149.92),
  mesta: w(150.42),
  net: w(150.8),
  bitkom: w(151.16),
  club: w(152.0),
  cut3: at(152.46),
  // Line 4
  ya4: w(152.46),
  vytru: w(152.88),
  kupyuroy: w(153.62),
  slyozy: w(154.18),
  vidish: w(154.8),
  vodyanoy: w(155.4),
  znak4: w(156.22),
  // Line 5
  okey: w(156.62),
  yamogu: w(157.5),
  vlyubit: w(157.9),
  vsebya: w(158.34),
  legko: w(158.76),
  no5: w(159.36),
  netogo: w(159.92),
  kak5: w(160.8),
  zhe: w(161.08),
  tak: w(161.48),
  // Line 6
  yahochu: w(161.76),
  zabytsya: w(162.26),
  sredi: w(162.84),
  zvyozd: w(163.5),
  oblakov: w(164.0),
  falling: w(164.94),
  inlove: w(165.4),
  // Line 7
  znayu: w(166.26),
  neverish: w(166.52),
  goroskop: w(167.38),
  no7: w(168.2),
  tvoy: w(168.68),
  znakA: w(168.96),
  plus: w(169.64),
  moy: w(169.78),
  znakB: w(170.08),
  // Line 8
  ty: w(170.48),
  mnoy: w(170.84),
  oderzhim: w(171.0),
  uzhe: w(171.44),
  davno: w(171.78),
  kak8: w(172.8),
  manyak: w(173.08),
  zodia: w(173.86),
  aak: w(174.5),
  finalHit: at(175.17),
  blackout: at(175.46),
};
