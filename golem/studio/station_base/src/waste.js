// 정거장 폐기물 — 매 턴 인구 활동으로 폐기물이 쌓이고 처리 스케줄에 감소하며 적체가 크면 경보한다
//
// 모델:
//   waste += waste.perPop * population
//   처리 스케줄 턴이면 waste -= waste.processAmount (로그 'WASTE_PROCESS')
//   waste' = clamp(waste, 0, waste.cap)
//
// 불변식:
//   - waste는 [0, waste.cap] 정수 내부 적체. population은 읽기 전용.
//   - 승패 판정과 무관(경보/로그 전용). 처리는 결정적 스케줄(난수 0).
//
// 경보/로그:
//   - WASTE_BACKLOG: 적체가 경보선 이상.
//   - 'WASTE_PROCESS': 처리 스케줄 턴의 처리 기록.
const D = require('./constants').constants;
const { clamp } = require('./util');
const { WASTE_SCHEDULE } = require('./tables');

exports.step = (state, c) => {
  const WS = (c && c.waste) || D.waste;

  state.waste = clamp(state.waste + WS.perPop * state.population, 0, WS.cap);

  if (WASTE_SCHEDULE.indexOf(state.turn) !== -1) {
    state.waste = clamp(state.waste - WS.processAmount, 0, WS.cap);
    state.log.push('WASTE_PROCESS');
  }

  if (state.waste >= WS.backlogAlert) {
    state.alerts.push('WASTE_BACKLOG');
  }
  return state;
};
