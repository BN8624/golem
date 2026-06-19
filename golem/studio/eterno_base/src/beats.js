// 서사 비트 발동 로직(A겹) — 조각 집합이 조건을 만족할 때 결정적으로 발동할 비트를 반환한다. 카드는 비트를 추가한다
const { ALL_FRAGMENTS } = require('./constants');

// 이미 발동한 비트를 제외하고, 현재 조각으로 새로 발동하는 비트 목록을 반환한다
exports.fireBeats = (fragments, firedBeats) => {
  const out = [];
  const has = (f) => fragments.includes(f);
  // RESONANCE: 다섯 조각이 모두 모이면 진정한 왕권이 공명한다(코어 비트)
  if (ALL_FRAGMENTS.every(has) && !firedBeats.includes('RESONANCE')) {
    out.push('RESONANCE');
  }
  return out;
};
