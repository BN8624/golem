const { createInitialState, applyWait, applyAdvance } = require('./logic');

function checkWin(state) {
  if (state.stage >= 4) {
    return { ...state, gameStatus: 'WON' };
  }
  return state;
}

exports.runScenario = (scenario) => {
  const config = scenario.input.constants;
  const actions = scenario.input.actions;

  let state = createInitialState();
  
  // RULE-03: Win check BEFORE any action
  state = checkWin(state);

  for (const actionObj of actions) {
    // RULE-04: Stop immediately if WON
    if (state.gameStatus === 'WON') break;

    const action = actionObj.action;
    if (action === 'WAIT') {
      state = applyWait(state, config);
    } else if (action === 'ADVANCE') {
      state = applyAdvance(state, config);
    }

    // RULE-03: Win check AFTER action
    state = checkWin(state);
  }

  return state;
};
