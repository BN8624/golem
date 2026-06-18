// 정거장 구역 열편차 — 목표온도 대비 선체 온도 편차를 방열판으로 완화한 구역 스프레드를 내고 과열/과냉 구역을 경보한다
//
// 모델:
//   delta  = |temperature - thermal.target|
//   spread = max(0, spreadPerDelta * delta - radiatorDamp * thermal.radiators)
//
// 불변식:
//   - temperature는 읽기 전용(thermal step이 이미 갱신). spread는 파생값으로 상태에 보관하지 않는다.
//   - 승패 판정과 무관(경보/로그 전용).
//
// 경보/로그:
//   - ZONE_HOT / ZONE_COLD: 스프레드가 임계 이상이며 온도가 목표보다 높/낮은 쪽.
//   - 'THERMAL_BALANCE <스프레드>': 균형 점검 스케줄 턴 기록.
const D = require('./constants').constants;
const { max2 } = require('./util');
const { THERMAL_BALANCE_SCHEDULE } = require('./tables');

exports.step = (state, c) => {
  const TZ = (c && c.thermalzones) || D.thermalzones;
  const TH = (c && c.thermal) || D.thermal;

  const delta = state.temperature >= TH.target
    ? state.temperature - TH.target
    : TH.target - state.temperature;
  const spread = max2(0, TZ.spreadPerDelta * delta - TZ.radiatorDamp * TH.radiators);

  if (spread >= TZ.hotZone && state.temperature >= TH.target) {
    state.alerts.push('ZONE_HOT');
  } else if (spread >= TZ.coldZone && state.temperature < TH.target) {
    state.alerts.push('ZONE_COLD');
  }

  if (THERMAL_BALANCE_SCHEDULE.indexOf(state.turn) !== -1) {
    state.log.push('THERMAL_BALANCE ' + spread);
  }
  return state;
};
