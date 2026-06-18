// 정거장 항법 — 매 턴 궤도가 이탈하고 추진제가 남아 있으면 자동 보정 분사로 이탈을 줄인다
const D = require('./constants').constants;
const { clamp, min2 } = require('./util');

exports.step = (state, c) => {
  const N = (c && c.navigation) || D.navigation;
  const cap = ((c && c.caps) || D.caps).navFuel;

  state.navDrift += N.driftPerTurn;

  if (state.navFuel > 0) {
    const burn = min2(state.navFuel, N.fuelPerBurn);
    state.navFuel = clamp(state.navFuel - burn, 0, cap);
    state.navDrift -= N.burnReduces;
  }
  if (state.navDrift < 0) state.navDrift = 0;

  if (state.navDrift >= N.decayAt) {
    state.alerts.push('ORBIT_DECAY');
  } else if (state.navDrift >= N.driftAlert) {
    state.alerts.push('NAV_DRIFT');
  }
  return state;
};
