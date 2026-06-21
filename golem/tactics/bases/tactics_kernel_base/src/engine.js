const gameLogic = require('./game_logic');

exports.runScenario = (initialState, actionSequence) => {
  let state = {
    ...initialState,
    hero: { ...initialState.hero },
    enemies: initialState.enemies.map(e => ({ ...e })),
    turn: 0
  };

  const initialEnemyCount = state.enemies.length;
  let status = 'READY';

  for (const action of actionSequence) {
    state = gameLogic.updateState(state, action);
    
    // REQ-005: Win/Lose checks occur strictly post-action
    const result = gameLogic.checkGameState(state, initialEnemyCount);
    if (result) {
      status = result;
      break;
    }
  }

  // REQ-009: Actions exhausted without VICTORY/DEFEAT -> FINISHED
  if (status === 'READY') {
    status = 'FINISHED';
  }

  return { state, status };
};
