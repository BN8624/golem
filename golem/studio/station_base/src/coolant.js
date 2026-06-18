// 정거장 냉각 루프 — 목표온도 편차와 방열판에서 냉각 여유를 산출해 점검 스케줄에 기록하고 여유 부족을 경보한다
//
// 모델:
//   delta  = |temperature - thermal.target|
//   margin = coolant.marginBase - coolant.perDelta * delta + coolant.radiatorGain * thermal.radiators
//   margin' = clamp(margin, 0, 100)
//
// 불변식:
//   - temperature는 읽기 전용(thermal step이 이미 갱신). margin은 파생값으로 보관하지 않는다.
//   - 승패 판정과 무관(경보/로그 전용). 점검은 결정적 스케줄(난수 0).
//
// 경보/로그:
//   - COOLANT_LOW: 냉각 여유가 경보선 이하.
//   - 'COOLANT <여유>': 냉각 점검 스케줄 턴의 현재 여유.
const D = require('./constants').constants;
const { clamp } = require('./util');
const { COOLANT_CHECK_SCHEDULE } = require('./tables');

exports.step = (state, c) => {
  const CL = (c && c.coolant) || D.coolant;
  const TH = (c && c.thermal) || D.thermal;

  const delta = state.temperature >= TH.target
    ? state.temperature - TH.target
    : TH.target - state.temperature;
  const margin = clamp(
    CL.marginBase - CL.perDelta * delta + CL.radiatorGain * TH.radiators,
    0,
    100
  );

  if (margin <= CL.lowAlert) {
    state.alerts.push('COOLANT_LOW');
  }

  if (COOLANT_CHECK_SCHEDULE.indexOf(state.turn) !== -1) {
    state.log.push('COOLANT ' + margin);
  }
  return state;
};
