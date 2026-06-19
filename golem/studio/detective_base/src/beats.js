// 서사 비트 발동 로직(A겹) — 단서 집합이 조건을 만족할 때 결정적으로 발동할 비트를 반환한다
const { ALL_CLUES } = require('./constants');

// 이미 발동한 비트를 제외하고, 현재 단서로 새로 발동하는 비트 목록을 반환한다
exports.fireBeats = (clues, firedBeats) => {
  const out = [];
  const has = (c) => clues.includes(c);
  // DEDUCTION: 세 단서(상처·편지·발자국)가 모두 모이면 진실의 윤곽이 드러난다
  if (ALL_CLUES.every(has) && !firedBeats.includes('DEDUCTION')) {
    out.push('DEDUCTION');
  }
  return out;
};
