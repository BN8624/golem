// 정거장 의무실 — 피로와 누적 방사선에서 승무원 건강 지수를 산출하고 위급 시 사기를 깎으며 경보·입원 로그를 남긴다
//
// 모델:
//   health = base - floor(fatigue / fatiguePenalty) - floor(radiation / radPenaltyPer)
//   health' = clamp(health, 0, base)
//   health <= criticalAlert면 morale -= moraleHit (작게·bounded, 게이트 무관)
//
// 불변식:
//   - fatigue·radiation은 읽기 전용. health는 [0, base] 정수 내부 지표.
//   - morale만 조건부로 깎되 clamp로 [0,cap] 유지. 승패 판정(인구·연구)에는 영향 없음.
//
// 경보/로그:
//   - MED_<등급>: 건강 밴드 경보(낮을수록 위험).
//   - 'INFIRMARY ADMIT': 위급 등급으로 처음 떨어진 턴에 입원 로그.
const D = require('./constants').constants;
const { clamp, floorDiv, band } = require('./util');
const { HEALTH_BANDS, MED_CHECK_SCHEDULE } = require('./tables');
const labels = require('./labels');

exports.step = (state, c) => {
  const MD = (c && c.medical) || D.medical;
  const caps = (c && c.caps) || D.caps;

  const prev = state.health;
  let h = MD.base - floorDiv(state.fatigue, MD.fatiguePenalty) - floorDiv(state.radiation, MD.radPenaltyPer);
  state.health = clamp(h, 0, MD.base);

  if (state.health <= MD.criticalAlert) {
    state.morale = clamp(state.morale - MD.moraleHit, 0, caps.morale);
    state.alerts.push(labels.graded('MED', band(state.health, HEALTH_BANDS)));
    if (prev > MD.criticalAlert) {
      state.log.push('INFIRMARY ADMIT');
    }
  } else if (state.health <= MD.lowAlert) {
    state.alerts.push(labels.graded('MED', band(state.health, HEALTH_BANDS)));
  }

  // 정기 건강검진: 스케줄 턴마다 현재 건강 등급을 기록한다(건강 양호 여부와 무관하게 산출값이 출력에 드러남).
  if (MED_CHECK_SCHEDULE.indexOf(state.turn) !== -1) {
    state.log.push('CHECKUP ' + band(state.health, HEALTH_BANDS));
  }
  return state;
};
