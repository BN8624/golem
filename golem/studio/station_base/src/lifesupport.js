// 정거장 생명유지 지수 — 산소·물·식량의 평균에 여유 보너스를 더한 파생 지표를 계산하고 경보를 낸다
const D = require('./constants').constants;
const { clamp, floorDiv, band } = require('./util');
const { LIFE_BANDS } = require('./tables');
const labels = require('./labels');

exports.step = (state, c) => {
  const LS = (c && c.lifesupport) || D.lifesupport;

  let idx = floorDiv(state.oxygen + state.water + state.food, 3);
  if (state.oxygen > 50 && state.water > 50 && state.food > 50) {
    idx += LS.redundancyBonus;
  }
  state.lifeIndex = clamp(idx, 0, 100);

  if (state.lifeIndex <= LS.indexAlert) {
    state.alerts.push(labels.graded('LIFE', band(state.lifeIndex, LIFE_BANDS)));
  }
  return state;
};
