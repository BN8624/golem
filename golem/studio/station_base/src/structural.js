// 정거장 구조응력 — 선체 손상과 장비 마모에서 누적 응력을 산출하고 등급 경보와 정밀점검 로그를 남긴다
//
// 모델:
//   stress = floor(wear / structural.stressPerWear) + structural.hullWeight * (caps.hull - hull)
//   stress' = clamp(stress, 0, caps.wear)
//
// 불변식:
//   - hull·wear는 읽기 전용(각 step이 이미 갱신). stress는 [0, caps.wear] 정수 내부 지표.
//   - 승패 판정과 무관(경보/로그 전용).
//
// 경보/로그:
//   - STRUCT_CRITICAL / STRUCT_HIGH: 응력이 임계선 이상.
//   - 'INSPECTION <응력등급>': 정밀점검 스케줄 턴 기록.
const D = require('./constants').constants;
const { clamp, floorDiv, band } = require('./util');
const { INSPECTION_SCHEDULE, STRESS_BANDS } = require('./tables');

exports.step = (state, c) => {
  const ST = (c && c.structural) || D.structural;
  const caps = (c && c.caps) || D.caps;

  const s = floorDiv(state.wear, ST.stressPerWear) + ST.hullWeight * (caps.hull - state.hull);
  state.stress = clamp(s, 0, caps.wear);

  if (state.stress >= ST.criticalAlert) {
    state.alerts.push('STRUCT_CRITICAL');
  } else if (state.stress >= ST.highAlert) {
    state.alerts.push('STRUCT_HIGH');
  }

  if (INSPECTION_SCHEDULE.indexOf(state.turn) !== -1) {
    state.log.push('INSPECTION ' + band(state.stress, STRESS_BANDS));
  }
  return state;
};
