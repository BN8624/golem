const { constants: defaultConstants } = require('./constants');

exports.createInitialState = () => ({
  turn: 0,
  fuel: 0,
  stage: 0,
  events: [],
  log: [],
  gameStatus: 'PLAYING',
});

exports.applyWait = (state, constants) => {
  const fuelRate = constants.fuelRate !== undefined ? constants.fuelRate : defaultConstants.fuelRate;
  return {
    ...state,
    turn: state.turn + 1,
    fuel: state.fuel + fuelRate,
  };
};

exports.applyAdvance = (state, constants) => {
  const stageCost = constants.stageCost || defaultConstants.stageCost;
  const stageNames = constants.stageNames || defaultConstants.stageNames;

  const newState = {
    ...state,
    events: [...state.events],
    log: [...state.log],
  };

  const cost = stageCost[newState.stage];

  if (newState.fuel >= cost) {
    newState.fuel -= cost;
    newState.stage += 1;
    newState.events.push('BEAT-' + newState.stage);
    newState.log.push(stageNames[newState.stage - 1] + ' 도달');
  } else {
    newState.log.push('Insufficient fuel');
  }

  return newState;
};
