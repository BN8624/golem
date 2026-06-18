// 정거장 방사선 — 기본 우주방사선에 플레어 이벤트 배수를 곱하고 선체 차폐를 빼 누적 피폭을 갱신한다
const D = require('./constants').constants;
const { clamp, floorDiv, band, max2, scheduledAt } = require('./util');
const { HAZARD_SCHEDULE, RAD_BANDS } = require('./tables');
const labels = require('./labels');

const FLARE_KINDS = ['SOLAR_FLARE', 'CORONAL_EJECTION'];

exports.step = (state, c) => {
  const R = (c && c.radiation) || D.radiation;
  const cap = ((c && c.caps) || D.caps).radiation;

  let influx = R.influxPerTurn;
  const hz = scheduledAt(HAZARD_SCHEDULE, state.turn);
  if (hz && FLARE_KINDS.indexOf(hz.kind) !== -1) {
    influx += R.influxPerTurn * R.flareMultiplier * hz.severity;
  }
  // 선체 무결성이 차폐를 제공한다(10단위당 shieldPerHull).
  const shield = R.shieldPerHull * floorDiv(state.hull, 10);
  const net = max2(0, influx - shield);
  state.radiation = clamp(state.radiation + net, 0, cap);

  // 피폭은 승무원 피로로도 환산된다.
  state.fatigue = clamp(state.fatigue + R.crewDosePerInflux * floorDiv(net, 4), 0, ((c && c.caps) || D.caps).fatigue);

  if (state.radiation >= R.doseAlert) {
    state.alerts.push(labels.graded('RAD', band(state.radiation, RAD_BANDS)));
  }
  return state;
};
