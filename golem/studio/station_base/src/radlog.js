// 정거장 피폭기록 — 누적 방사선이 피폭 마일스톤을 넘을 때마다 기록하고 차폐 저하를 경보한다
//
// 모델:
//   radiation이 DOSE_MILESTONES[i].at 이상이 되면 코드를 로그하고 doseLevel 카운터 +1(순서대로, 1회씩).
//
// 불변식:
//   - radiation·hull은 읽기 전용. doseLevel은 단조 증가 내부 카운터.
//   - 승패 판정과 무관(경보/로그 전용).
//
// 경보/로그:
//   - 'DOSE <코드>': 피폭 마일스톤 최초 도달.
//   - SHIELD_DEGRADED: 선체가 낮은 상태에서 방사선이 높을 때(차폐 약화).
const D = require('./constants').constants;
const { DOSE_MILESTONES } = require('./tables');

exports.step = (state, c) => {
  const RL = (c && c.radlog) || D.radlog;
  const DM = DOSE_MILESTONES;

  while (state.doseLevel < DM.length && state.radiation >= DM[state.doseLevel].at) {
    state.log.push('DOSE ' + DM[state.doseLevel].code);
    state.doseLevel += 1;
  }

  if (state.hull <= RL.shieldBreachHull && state.radiation >= RL.shieldBreachRad) {
    state.alerts.push('SHIELD_DEGRADED');
  }
  return state;
};
