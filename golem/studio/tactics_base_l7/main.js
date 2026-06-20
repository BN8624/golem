const engine = require('./src/engine');
const scenarios = require('./src/scenarios');

function main() {
  const args = process.argv.slice(2);
  const scenarioIdxArg = args[args.indexOf('--scenario') + 1];
  
  if (!scenarioIdxArg) return;

  const scenario = scenarios.getScenario(parseInt(scenarioIdxArg, 10));
  if (!scenario) return;

  const { state, status } = engine.runScenario(scenario.initialState, scenario.actions);

  // REQ-008: Exact output format
  process.stdout.write(`status: ${status}\n`);
  process.stdout.write(`turn: ${state.turn}\n`);
  process.stdout.write(`hero_hp: ${state.hero.hp}\n`);
  process.stdout.write(`hero_pos: ${JSON.stringify(state.hero.pos)}\n`);
  
  const filteredEnemies = state.enemies.map(e => ({
    id: e.id,
    hp: e.hp,
    pos: e.pos
  }));
  process.stdout.write(`enemies: ${JSON.stringify(filteredEnemies)}\n`);
}

main();
