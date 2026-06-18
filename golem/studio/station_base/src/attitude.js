// 정거장 자세제어 — 궤도 이탈량을 자세제어 점검 스케줄에 기록하고 이탈이 크면 지향 오차를 경보한다
//
// 불변식:
//   - navDrift는 읽기 전용(navigation step이 이미 갱신). 이 모듈은 항법값을 바꾸지 않는다.
//   - 승패 판정과 무관(경보/로그 전용). 점검은 결정적 스케줄(난수 0).
//
// 경보/로그:
//   - ATTITUDE_OFF: 이탈량이 경보선 이상(자세 지향 오차).
//   - 'ATTITUDE <이탈>': 자세제어 점검 스케줄 턴의 현재 이탈량.
const D = require('./constants').constants;
const { ATTITUDE_SCHEDULE } = require('./tables');

exports.step = (state, c) => {
  const AT = (c && c.attitude) || D.attitude;

  if (state.navDrift >= AT.offAlert) {
    state.alerts.push('ATTITUDE_OFF');
  }

  if (ATTITUDE_SCHEDULE.indexOf(state.turn) !== -1) {
    state.log.push('ATTITUDE ' + state.navDrift);
  }
  return state;
};
