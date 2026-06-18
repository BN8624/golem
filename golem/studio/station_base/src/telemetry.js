// 정거장 텔레메트리 — 데이터버퍼와 인구에서 패킷을 적립하고 접속 윈도우에 다운링크하며 링크 품질을 경보한다
//
// 모델:
//   packets += telemetry.packetPerData * dataBuffer + telemetry.packetPerPop * population
//   접속 윈도우(CONTACT_WINDOWS) 턴이면 전량 다운링크(로그 'DOWNLINK <수량>'), packets=0
//   packets' = clamp(packets, 0, telemetry.cap)
//
// 불변식:
//   - packets는 [0, cap] 정수 내부 누적. comms·dataBuffer·population은 읽기 전용.
//   - 승패 판정과 무관. 접속 윈도우는 결정적 스케줄(난수 0).
//
// 경보/로그:
//   - LINK_LOW: 통신 링크 품질이 경보선 이하.
//   - 'DOWNLINK <수량>': 접속 윈도우에서 적립 패킷을 비운 기록.
const D = require('./constants').constants;
const { clamp } = require('./util');
const { CONTACT_WINDOWS } = require('./tables');

exports.step = (state, c) => {
  const TM = (c && c.telemetry) || D.telemetry;

  state.packets = clamp(
    state.packets + TM.packetPerData * state.dataBuffer + TM.packetPerPop * state.population,
    0,
    TM.cap
  );

  if (CONTACT_WINDOWS.indexOf(state.turn) !== -1) {
    state.log.push('DOWNLINK ' + state.packets);
    state.packets = 0;
  }

  if (state.comms <= TM.linkLowAlert) {
    state.alerts.push('LINK_LOW');
  }
  return state;
};
