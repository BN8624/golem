// 정거장 승무원 — 매 턴 피로가 쌓이고 교대 로테이션에서 역할 보너스만큼 회복하며 과로는 사기를 깎는다
const D = require('./constants').constants;
const { clamp } = require('./util');
const { CREW_ROLES } = require('./tables');

exports.step = (state, c) => {
  const CR = (c && c.crew) || D.crew;
  const caps = (c && c.caps) || D.caps;

  state.fatigue = clamp(state.fatigue + CR.fatiguePerTurn, 0, caps.fatigue);

  if (state.turn % CR.rotateEvery === 0) {
    const idx = Math.floor(state.turn / CR.rotateEvery) % CREW_ROLES.length;
    const role = CREW_ROLES[idx];
    const rest = CR.restPerRotation + role.restBonus;
    state.fatigue = clamp(state.fatigue - rest, 0, caps.fatigue);
    state.log.push('SHIFT ' + role.id);
  }

  if (state.fatigue >= CR.overworkAt) {
    state.morale = clamp(state.morale - 2, 0, caps.morale);
    state.alerts.push('CREW_OVERWORK');
  } else if (state.fatigue >= CR.highAlert) {
    state.alerts.push('CREW_TIRED');
  }
  return state;
};
