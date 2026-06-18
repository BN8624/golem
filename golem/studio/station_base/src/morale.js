// 정거장 사기 서브시스템 — 모든 생존 자원이 쾌적선을 넘으면 오르고 아니면 내리며 배급제는 추가로 깎는다
const D = require('./constants').constants;
const { clamp } = require('./util');

exports.step = (state, c) => {
  const M = (c && c.morale) || D.morale;
  const cap = ((c && c.caps) || D.caps).morale;
  const comfortable =
    state.food > M.comfort && state.oxygen > M.comfort && state.water > M.comfort;
  state.morale += comfortable ? M.up : -M.down;
  if (state.rationing) state.morale -= M.rationPenalty;
  state.morale = clamp(state.morale, 0, cap);
  if (state.morale <= M.lowAlert) state.alerts.push('MORALE_LOW');
  return state;
};
