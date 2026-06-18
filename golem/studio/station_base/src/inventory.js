// 정거장 부품 재고 — 매 턴 인구 활동으로 부품이 소모되고 보급 스케줄에 보충되며 부족하면 경보를 낸다
//
// 모델:
//   parts -= inventory.consumePerPop * population
//   재주문 스케줄 턴이면 parts += inventory.reorderAmount (로그 'REORDER <수량>')
//   parts' = clamp(parts, 0, inventory.cap)
//
// 불변식:
//   - parts는 [0, inventory.cap] 정수 내부 재고. cargo·population은 읽기 전용.
//   - 승패 판정과 무관(경보/로그 전용). 보급은 결정적 스케줄(난수 0).
//
// 경보/로그:
//   - PARTS_LOW: 재고가 경보선 이하.
//   - 'REORDER <수량>': 재주문 스케줄 턴의 보충 기록.
const D = require('./constants').constants;
const { clamp } = require('./util');
const { REORDER_SCHEDULE } = require('./tables');

exports.step = (state, c) => {
  const IN = (c && c.inventory) || D.inventory;

  state.parts = clamp(state.parts - IN.consumePerPop * state.population, 0, IN.cap);

  if (REORDER_SCHEDULE.indexOf(state.turn) !== -1) {
    state.parts = clamp(state.parts + IN.reorderAmount, 0, IN.cap);
    state.log.push('REORDER ' + IN.reorderAmount);
  }

  if (state.parts <= IN.lowAlert) {
    state.alerts.push('PARTS_LOW');
  }
  return state;
};
