// 정거장 선체 무결성 — 매 턴 미세보수하고, 충돌 위험(미소운석·잔해) 발생 시 피해를 입으며 화물로 보강한다
const D = require('./constants').constants;
const { clamp, min2, scheduledAt } = require('./util');
const { HAZARD_SCHEDULE } = require('./tables');

const IMPACT_KINDS = ['MICROMETEORITE', 'DEBRIS_FIELD'];

exports.step = (state, c) => {
  const H = (c && c.hull) || D.hull;
  const cap = ((c && c.caps) || D.caps).hull;

  // 자동 미세보수.
  state.hull = clamp(state.hull + H.autoRepair, 0, cap);

  // 이번 턴 충돌 위험이면 피해.
  const hz = scheduledAt(HAZARD_SCHEDULE, state.turn);
  if (hz && IMPACT_KINDS.indexOf(hz.kind) !== -1) {
    const dmg = H.micrometeoriteDamage * hz.severity;
    state.hull = clamp(state.hull - dmg, 0, cap);
  }

  // 화물로 선체를 보강(소모량만큼 무결성 회복).
  if (state.hull < cap && state.cargo > 0) {
    const patch = min2(state.cargo, 2);
    state.cargo -= patch;
    state.hull = clamp(state.hull + patch * H.repairPerCargo, 0, cap);
  }

  if (state.hull <= H.breachAlert) {
    state.alerts.push('HULL_BREACH');
  }
  return state;
};
