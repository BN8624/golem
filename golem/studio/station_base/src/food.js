// 정거장 식량 서브시스템 — 농장 생산에서 인구 소비를 빼되 배급제면 소비를 절반(바닥)으로 줄이고 부족 경보를 낸다
const D = require('./constants').constants;
const { clamp, floorDiv } = require('./util');

exports.step = (state, c) => {
  const F = (c && c.food) || D.food;
  const cap = ((c && c.caps) || D.caps).food;
  const powered = state.power > 0;
  const prod = powered ? F.farmIfPowered * state.farm : 0;
  let cons = F.usePerPop * state.population;
  if (state.rationing) cons = floorDiv(cons, 2);
  state.food = clamp(state.food + prod - cons, 0, cap);
  if (state.food <= F.lowAlert) state.alerts.push('FOOD_LOW');
  return state;
};
