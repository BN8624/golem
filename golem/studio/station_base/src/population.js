// 정거장 인구 서브시스템 — 생존 자원이 모두 양수면 주기마다 늘고, 하나라도 고갈이면 사상자가 난다
const D = require('./constants').constants;
const { clamp } = require('./util');

exports.step = (state, c) => {
  const PP = (c && c.population) || D.population;
  const cap = ((c && c.caps) || D.caps).population;
  const alive = state.oxygen > 0 && state.water > 0 && state.food > 0;
  if (!alive) {
    state.population = clamp(state.population - 1, 0, cap);
    state.alerts.push('CASUALTY');
  } else if (state.turn % PP.growEvery === 0 && state.population < cap) {
    state.population = clamp(state.population + 1, 0, cap);
    state.alerts.push('BIRTH');
  }
  if (state.population <= PP.lowAlert) state.alerts.push('POP_LOW');
  return state;
};
