const { applyAction, updateState, checkGameState } = require('./game_logic');

function runScenario(initialState, actionSequence) {
  // Create a deep copy of initialState to avoid mutating the scenario data
  const state = {
    gridSize: initialState.gridSize,
    allies: initialState.allies.map(u => ({ ...u, pos: [...u.pos] })),
    enemies: initialState.enemies.map(u => ({ ...u, pos: [...u.pos] })),
    turn: 0
  };

  for (const action of actionSequence) {
    const status = updateState(state, action);
    if (status === 'VICTORY' || status === 'DEFEAT') {
      return { state, status };
    }
  }

  return { state, status: 'FINISHED' };
}

module.exports = { runScenario };
