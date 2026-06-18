// 정거장 정비 — 장비 마모를 누적하고 자동 정비로 일부 상쇄하며, 적체가 한계를 넘으면 고장으로 전력을 깎는다
const D = require('./constants').constants;
const { clamp } = require('./util');

exports.step = (state, c) => {
  const M = (c && c.maintenance) || D.maintenance;
  const caps = (c && c.caps) || D.caps;

  const added = M.wearPerTurn + M.wearPerPop * state.population;
  state.wear = clamp(state.wear + added - M.serviceReduces, 0, caps.wear);

  if (state.wear >= M.breakdownAt) {
    // 고장: 전력 계통 손실.
    state.power = clamp(state.power - 5, 0, caps.power);
    state.alerts.push('EQUIP_BREAKDOWN');
  } else if (state.wear >= M.backlogAlert) {
    state.alerts.push('MAINT_BACKLOG');
  }
  return state;
};
