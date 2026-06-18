// 정거장 연구 서브시스템 — 전력이 있을 때 인구에 비례해 연구점수를 누적한다(승리 판정의 입력)
//
// 모델:
//   powered -> research += perPopIfPowered * population
//   research' = clamp(research, 0, cap)
//
// 불변식:
//   - research는 단조 증가한다(감소 규칙 없음). 전력이 없으면 그 틱은 정체.
//   - state.checkEnd가 research >= goal 일 때 gameStatus='WON'으로 종료시킨다(승리 판정의 유일 입력).
//   - 인구가 많을수록·정전이 적을수록 빨리 목표에 도달한다 → 생명유지를 잘 굴리는 게 곧 승리 경로.
//
// 경보: 없음(연구는 항상 좋은 방향이며 임계 위험이 아니므로 경보를 내지 않는다).
const D = require('./constants').constants;
const { clamp } = require('./util');

exports.step = (state, c) => {
  const R = (c && c.research) || D.research;
  const cap = ((c && c.caps) || D.caps).research;
  if (state.power > 0) {
    state.research = clamp(state.research + R.perPopIfPowered * state.population, 0, cap);
  }
  return state;
};
