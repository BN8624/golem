// 정거장 전력망 — 현재 전력이 추정 수요에 못 미치면 브라운아웃 플래그를 세우고 경보를 낸다
const D = require('./constants').constants;

exports.step = (state, c) => {
  const P = (c && c.power) || D.power;
  // 수요 = 인구 부하 + 생명유지 기본 부하(고정 5). 결정적.
  const demand = P.usePerPop * state.population + 5;
  state.brownout = state.power < demand;
  if (state.brownout) {
    state.alerts.push('GRID_BROWNOUT');
  }
  return state;
};
