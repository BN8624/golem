// 정거장 에어록 — 선외활동(EVA) 스케줄에 작업을 기록하고 선체가 약한 상태의 EVA를 위험으로 경보한다
//
// 불변식:
//   - hull은 읽기 전용(hull step이 이미 갱신). 이 모듈은 자원·항법값을 바꾸지 않는다.
//   - 승패 판정과 무관(경보/로그 전용). EVA는 결정적 스케줄(난수 0).
//
// 경보/로그:
//   - 'EVA': 선외활동 스케줄 턴 기록.
//   - AIRLOCK_RISK: EVA 턴인데 선체 무결성이 위험선 이하(작업 중 균열 위험).
const D = require('./constants').constants;
const { EVA_SCHEDULE } = require('./tables');

exports.step = (state, c) => {
  const AL = (c && c.airlock) || D.airlock;

  if (EVA_SCHEDULE.indexOf(state.turn) !== -1) {
    state.log.push('EVA');
    if (state.hull <= AL.riskHull) {
      state.alerts.push('AIRLOCK_RISK');
    }
  }
  return state;
};
