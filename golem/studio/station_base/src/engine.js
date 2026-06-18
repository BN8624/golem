// 정거장 시나리오 실행 루프 — 액션을 순서대로 적용하고 매 단계 종료(WON/LOST)를 판정한다
const actions = require('./actions');
const { createInitialState, checkEnd } = require('./state');

exports.runScenario = (scenario) => {
  const input = scenario && scenario.input ? scenario.input : {};
  const c = input.constants || {};
  const acts = input.actions || [];

  let state = createInitialState(c);
  state = checkEnd(state, c); // 액션 적용 전 1회 종료 판정

  for (const a of acts) {
    if (state.gameStatus !== 'PLAYING') break; // 종료 상태면 즉시 중단
    state = actions.apply(state, a, c);
    state = checkEnd(state, c);
  }

  return state;
};
