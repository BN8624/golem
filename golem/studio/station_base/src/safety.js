// 정거장 안전 — 사기와 건강에서 대비태세를 산출해 경보하고 결정적 훈련 스케줄에 훈련 로그를 남긴다
//
// 모델:
//   readiness = floor((morale*moraleWeight + health*healthWeight) / (moraleWeight + healthWeight))
//
// 불변식:
//   - morale·health는 읽기 전용(각 step이 이미 갱신). readiness는 파생값으로 보관하지 않는다.
//   - 승패 판정과 무관(경보/로그 전용). 훈련은 결정적 스케줄(난수 0).
//
// 경보/로그:
//   - READINESS_LOW: 대비태세가 경보선 이하.
//   - 'DRILL': 훈련 스케줄 턴 기록.
const D = require('./constants').constants;
const { floorDiv } = require('./util');
const { DRILL_SCHEDULE } = require('./tables');

exports.step = (state, c) => {
  const SF = (c && c.safety) || D.safety;

  const readiness = floorDiv(
    state.morale * SF.moraleWeight + state.health * SF.healthWeight,
    SF.moraleWeight + SF.healthWeight
  );

  if (readiness <= SF.readinessFloor) {
    state.alerts.push('READINESS_LOW');
  }

  if (DRILL_SCHEDULE.indexOf(state.turn) !== -1) {
    state.log.push('DRILL');
  }
  return state;
};
