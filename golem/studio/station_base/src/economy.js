// 정거장 경제 서브시스템 — 매 턴 인구에 비례해 크레딧을 벌어들인다(BUILD 비용의 재원)
//
// 모델:
//   credits' = clamp(credits + incomePerPop * population, 0, cap)
//
// 불변식:
//   - credits는 이 step에서 단조 증가한다. 감소는 actions.BUILD에서만 일어난다(증설 비용 지불).
//   - 따라서 BUILD 가능 여부(credits >= cost)는 누적 수입과 지출 이력의 함수다.
//   - 인구가 곧 수입이므로 인구 손실은 연구·수입 양쪽을 동시에 깎는다(복리 하락 위험).
//
// 경보: 없음(크레딧 부족 자체는 위험이 아니라 BUILD 실패로만 드러난다).
const D = require('./constants').constants;
const { clamp } = require('./util');

exports.step = (state, c) => {
  const E = (c && c.economy) || D.economy;
  const cap = ((c && c.caps) || D.caps).credits;
  state.credits = clamp(state.credits + E.incomePerPop * state.population, 0, cap);
  return state;
};
