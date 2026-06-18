// 정거장 축전지 — 전력 잉여를 충전하고 부족하면 방전하며 잔량 등급에 따라 경보·충방전 사이클을 기록한다
//
// 모델:
//   demand = power.usePerPop * population + battery.reserveFloor   (유지 부하 추정)
//   surplus면 charge += chargePerSurplus, 적자면 charge -= dischargePerDeficit
//   charge' = clamp(charge, 0, battery.cap)
//
// 불변식:
//   - charge는 항상 [0, battery.cap] 정수. 출력 계약에는 들어가지 않는 내부 비축 지표다.
//   - 핵심 자원(전력·인구)은 읽기만 하고 바꾸지 않는다. 승패 판정에 영향 없음(경보/로그 전용).
//
// 경보/로그:
//   - BATTERY_CRITICAL / BATTERY_LOW: 잔량이 임계선 이하.
//   - 'CHARGE_CYCLE <등급>': 충방전 사이클 스케줄 턴에 현재 잔량 등급을 기록.
const D = require('./constants').constants;
const { clamp, band } = require('./util');
const { CHARGE_CYCLE_SCHEDULE, CHARGE_BANDS } = require('./tables');

exports.step = (state, c) => {
  const B = (c && c.battery) || D.battery;
  const P = (c && c.power) || D.power;

  const demand = P.usePerPop * state.population + B.reserveFloor;
  if (state.power > demand) {
    state.charge = clamp(state.charge + B.chargePerSurplus, 0, B.cap);
  } else {
    state.charge = clamp(state.charge - B.dischargePerDeficit, 0, B.cap);
  }

  if (state.charge <= B.criticalAlert) {
    state.alerts.push('BATTERY_CRITICAL');
  } else if (state.charge <= B.lowAlert) {
    state.alerts.push('BATTERY_LOW');
  }

  if (CHARGE_CYCLE_SCHEDULE.indexOf(state.turn) !== -1) {
    state.log.push('CHARGE_CYCLE ' + band(state.charge, CHARGE_BANDS));
  }
  return state;
};
