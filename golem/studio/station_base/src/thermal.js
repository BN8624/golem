// 정거장 열관리 — 전력 부하·태양광 노출의 발열에서 방열판 냉각을 빼고 목표온도로 회귀시킨다
const D = require('./constants').constants;
const { clamp, floorDiv, band } = require('./util');
const { TEMP_BANDS } = require('./tables');

exports.step = (state, c) => {
  const T = (c && c.thermal) || D.thermal;
  const heat = T.heatPerLoad * floorDiv(state.power, 10) + T.solarHeat * state.solar;
  const cool = T.coolPerRadiator * T.radiators;
  let temp = state.temperature + heat - cool;
  // 목표온도로의 자연 회귀(난방/냉방 보정).
  if (temp > T.target) temp -= T.drift;
  else if (temp < T.target) temp += T.drift;
  state.temperature = clamp(temp, -50, 150);

  const level = band(state.temperature, TEMP_BANDS);
  if (state.temperature >= T.hotAlert) {
    state.alerts.push('THERMAL_HOT');
  } else if (state.temperature <= T.coldAlert) {
    state.alerts.push('THERMAL_COLD');
  }
  // 극단 온도는 사기에도 영향(밴드 0 또는 4).
  if (level === 0 || level >= TEMP_BANDS.length) {
    const cap = ((c && c.caps) || D.caps).morale;
    state.morale = clamp(state.morale - 1, 0, cap);
  }
  return state;
};
