// 정거장 경제 서브시스템 — 매 턴 인구에 비례해 크레딧을 벌어들인다(BUILD 비용의 재원)
const D = require('./constants').constants;
const { clamp } = require('./util');

exports.step = (state, c) => {
  const E = (c && c.economy) || D.economy;
  const cap = ((c && c.caps) || D.caps).credits;
  state.credits = clamp(state.credits + E.incomePerPop * state.population, 0, cap);
  return state;
};
