// 정거장 화물 — 매 턴 인구가 소모품을 소비하고, 보급 스케줄에 맞춰 화물이 보충된다
const D = require('./constants').constants;
const { clamp } = require('./util');
const { RESUPPLY_SCHEDULE } = require('./tables');
const labels = require('./labels');

exports.step = (state, c) => {
  const CG = (c && c.cargo) || D.cargo;
  const cap = ((c && c.caps) || D.caps).cargo;

  state.cargo = clamp(state.cargo - CG.consumePerPop * state.population, 0, cap);

  if (RESUPPLY_SCHEDULE.indexOf(state.turn) !== -1) {
    state.cargo = clamp(state.cargo + CG.resupplyAmount, 0, cap);
    state.log.push(labels.milestone('RESUPPLY'));
  }

  if (state.cargo <= CG.lowAlert) {
    state.alerts.push('CARGO_LOW');
  }
  return state;
};
