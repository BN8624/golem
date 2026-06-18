// 정거장 산소 서브시스템 — 전력이 있으면 산소를 생산하고 정전이면 감소시키며 저산소 경보를 낸다
const D = require('./constants').constants;
const { clamp } = require('./util');

exports.step = (state, c) => {
  const O = (c && c.oxygen) || D.oxygen;
  const cap = ((c && c.caps) || D.caps).oxygen;
  const powered = state.power > 0;
  const delta = powered ? O.genIfPowered : -O.decayIfDark;
  state.oxygen = clamp(state.oxygen + delta - O.usePerPop * state.population, 0, cap);
  if (state.oxygen <= O.lowAlert) state.alerts.push('O2_LOW');
  return state;
};
