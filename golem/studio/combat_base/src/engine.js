// 전투 틱 루프 — 독→게이지→행동(player 우선 enemy)→stun감소를 maxTicks까지. 카드는 이 모듈을 편집한다
const C = require('./constants');
const { createInitialState } = require('./state');
const L = require('./unit_logic');

function endCheck(state) {
  const pd = state.player.hp <= 0;
  const ed = state.enemy.hp <= 0;
  if (!pd && !ed) return false;
  state.isGameOver = true;
  state.winner = pd && ed ? 'draw' : pd ? 'enemy' : 'player';
  return true;
}

exports.runScenario = (scenario) => {
  const input = (scenario && scenario.input) || {};
  const commands = input.commands || {};
  const state = createInitialState(input.setup);

  while (!state.isGameOver && state.tick < C.maxTicks) {
    state.tick += 1;

    state.player = L.applyPoison(state.player); // RULE-01
    state.enemy = L.applyPoison(state.enemy);
    if (endCheck(state)) break;

    state.player = L.gainGauge(state.player); // RULE-02
    state.enemy = L.gainGauge(state.enemy);

    if (state.player.gauge >= C.gaugeThreshold) { // RULE-03 player 우선
      const r = L.calculateAction(state.player, state.enemy, commands.player, 'PLAYER');
      state.player = r.actor;
      state.enemy = r.target;
      state.gameLog.push(r.log);
      if (endCheck(state)) break;
    }
    if (state.enemy.gauge >= C.gaugeThreshold) {
      const r = L.calculateAction(state.enemy, state.player, commands.enemy, 'ENEMY');
      state.enemy = r.actor;
      state.player = r.target;
      state.gameLog.push(r.log);
      if (endCheck(state)) break;
    }

    state.player = L.decStun(state.player); // RULE-08
    state.enemy = L.decStun(state.enemy);
  }

  if (!state.isGameOver && state.tick >= C.maxTicks) { // RULE-10
    state.isGameOver = true;
    state.winner = 'draw';
  }
  return state;
};
