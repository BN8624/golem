// 소코반 진행 루프 — 레벨을 로드해 이동을 순서대로 적용하고 승리(전 상자 목표 위)를 판정한다. 카드는 이 모듈을 건드리지 않는다
const C = require('./constants');
const { LEVELS } = require('./levels');
const { createInitialState } = require('./state');
const { resolveMove } = require('./move_logic');

// 승리 = 모든 상자가 목표 칸 위에 있음
function checkWin(state) {
  if (state.boxes.length === 0) return false;
  for (const b of state.boxes) {
    if (!state.targets[b[0] + ',' + b[1]]) return false;
  }
  return true;
}

exports.runScenario = (scenario) => {
  const input = (scenario && scenario.input) || {};
  const lines = LEVELS[input.level_id] || input.level || [];
  const moves = input.moves || [];
  const state = createInitialState(lines);

  for (let i = 0; i < moves.length && i < C.MAX_MOVES; i++) {
    state.logs.push(resolveMove(state, moves[i]));
    state.moves += 1;
    if (checkWin(state)) {
      state.isWon = true;
      state.isGameOver = true;
      break;
    }
  }
  if (!state.isGameOver && checkWin(state)) {
    state.isWon = true;
    state.isGameOver = true;
  }
  return state;
};
