// [Card1 REF] 서사 비트(A겹) 누적본 — base RESONANCE에 더해 첫 조각 각성 비트 AWAKENING(F1 보유)을 ADD한 정답 참조
const { ALL_FRAGMENTS } = require('./constants');

exports.fireBeats = (fragments, firedBeats) => {
  const out = [];
  const has = (f) => fragments.includes(f);
  // AWAKENING: 첫 조각을 얻는 순간 방계 혈통의 각성이 일어난다(THIS CARD)
  if (has('F1') && !firedBeats.includes('AWAKENING')) {
    out.push('AWAKENING');
  }
  // RESONANCE: 다섯 조각이 모두 모이면 진정한 왕권이 공명한다(코어 비트 보존)
  if (ALL_FRAGMENTS.every(has) && !firedBeats.includes('RESONANCE')) {
    out.push('RESONANCE');
  }
  return out;
};
