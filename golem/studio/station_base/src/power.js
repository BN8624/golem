// 정거장 전력 서브시스템 — 태양광 발전에서 인구 소비를 빼 전력을 갱신하고 정전 경보를 올린다
const D = require('./constants').constants;
const { clamp } = require('./util');

exports.step = (state, c) => {
  const P = (c && c.power) || D.power;
  const cap = ((c && c.caps) || D.caps).power;
  const gen = P.genPerSolar * state.solar;
  const use = P.usePerPop * state.population;
  state.power = clamp(state.power + gen - use, 0, cap);
  if (state.power === 0) state.alerts.push('POWER_OUT');
  return state;
};
