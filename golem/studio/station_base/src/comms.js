// 정거장 통신 — 접속 윈도우에서 링크가 회복되고 데이터 버퍼가 빠지며, 윈도우 밖에선 품질이 저하된다
const D = require('./constants').constants;
const { clamp, min2 } = require('./util');
const { CONTACT_WINDOWS } = require('./tables');
const labels = require('./labels');

exports.step = (state, c) => {
  const CM = (c && c.comms) || D.comms;
  const cap = ((c && c.caps) || D.caps).comms;
  const inWindow = CONTACT_WINDOWS.indexOf(state.turn) !== -1;

  if (inWindow) {
    state.comms = clamp(state.comms + CM.restoreInWindow, 0, cap);
    const drain = min2(state.dataBuffer, CM.bufferDrainInWindow);
    state.dataBuffer -= drain;
    if (drain > 0) state.log.push(labels.milestone('DOWNLINK'));
  } else {
    state.comms = clamp(state.comms - CM.degradePerTurn, 0, cap);
  }

  // 운영 데이터는 매 턴 쌓인다.
  state.dataBuffer += CM.bufferPerPop * state.population;

  if (state.comms <= CM.lowAlert) {
    state.alerts.push('COMMS_LOW');
  }
  return state;
};
