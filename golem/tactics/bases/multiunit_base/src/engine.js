const gameLogic = require('./game_logic');

exports.runScenario = (initialState, actionSequence) => {
    let state = { ...initialState, turn: 0 };
    let status = 'PLAYING';

    for (const action of actionSequence) {
        state = gameLogic.updateState(state, action);
        status = gameLogic.checkGameState(state);
        if (status !== 'PLAYING') break;
    }

    if (status === 'PLAYING') {
        status = 'FINISHED';
    }

    return { state, status };
};
