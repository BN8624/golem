// 정거장 물 서브시스템 — 전력이 있으면 재활용기 레벨만큼 정수하고 인구 소비를 빼며 부족 경보를 낸다
const D = require('./constants').constants;
const { clamp } = require('./util');

exports.step = (state, c) => {
  const W = (c && c.water) || D.water;
  const cap = ((c && c.caps) || D.caps).water;
  const powered = state.power > 0;
  const prod = powered ? W.recycleIfPowered * state.recycler : 0;
  state.water = clamp(state.water + prod - W.usePerPop * state.population, 0, cap);
  if (state.water <= W.lowAlert) state.alerts.push('WATER_LOW');
  return state;
};
