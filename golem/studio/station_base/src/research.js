// 정거장 연구 서브시스템 — 전력이 있을 때 인구에 비례해 연구점수를 누적한다(승리 판정의 입력)
const D = require('./constants').constants;
const { clamp } = require('./util');

exports.step = (state, c) => {
  const R = (c && c.research) || D.research;
  const cap = ((c && c.caps) || D.caps).research;
  if (state.power > 0) {
    state.research = clamp(state.research + R.perPopIfPowered * state.population, 0, cap);
  }
  return state;
};
