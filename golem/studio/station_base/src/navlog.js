// 정거장 항법기록 — 궤도 이탈을 결정적 스케줄에 기록하고 추진제 잔량이 낮으면 경보한다
//
// 불변식:
//   - navDrift·navFuel은 읽기 전용(navigation step이 이미 갱신). 이 모듈은 항법값을 바꾸지 않는다.
//   - 승패 판정과 무관(경보/로그 전용). 기록은 결정적 스케줄(난수 0).
//
// 경보/로그:
//   - NAV_RESERVE_LOW: 추진제 잔량이 경보선 이하.
//   - 'ORBIT_LOG <이탈>': 궤도요소 기록 스케줄 턴의 현재 이탈량.
const D = require('./constants').constants;
const { ORBIT_LOG_SCHEDULE } = require('./tables');

exports.step = (state, c) => {
  const NL = (c && c.navlog) || D.navlog;

  if (ORBIT_LOG_SCHEDULE.indexOf(state.turn) !== -1) {
    state.log.push('ORBIT_LOG ' + state.navDrift);
  }

  if (state.navFuel <= NL.reserveLowAlert) {
    state.alerts.push('NAV_RESERVE_LOW');
  }
  return state;
};
