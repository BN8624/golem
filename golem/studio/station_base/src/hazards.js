// 정거장 위험 이벤트 — 결정적 스케줄에서 이번 턴의 우주환경 위험을 찾아 경보·로그로 기록한다
// 실제 피해(방사선/선체)는 각 서브시스템이 같은 스케줄을 읽어 독립 적용한다. 여기선 통지만 한다.
const { HAZARD_SCHEDULE } = require('./tables');
const { scheduledAt } = require('./util');
const labels = require('./labels');

exports.step = (state, c) => {
  const hz = scheduledAt(HAZARD_SCHEDULE, state.turn);
  if (hz) {
    state.alerts.push(labels.alert('HAZARD', hz.kind));
    state.log.push(labels.hazardLine(hz.kind, hz.severity));
  }
  return state;
};
