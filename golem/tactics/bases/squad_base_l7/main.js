const { runScenario } = require('./src/engine');
const { getScenario } = require('./src/scenarios');

function main() {
  const args = process.argv.slice(2);
  const scenarioArgIdx = args.indexOf('--scenario');
  if (scenarioArgIdx === -1 || !args[scenarioArgIdx + 1]) {
    return;
  }

  const scenarioNum = parseInt(args[scenarioArgIdx + 1], 10);
  const scenario = getScenario(scenarioNum);
  if (!scenario) return;

  const { initialState, actions } = scenario;
  const { state, status } = runScenario(initialState, actions);

  // Prepare rosters: sorted by id, removing atk
  const formatRoster = (units) => {
    return [...units]
      .sort((a, b) => a.id - b.id)
      .map(({ id, hp, pos }) => ({ id, hp, pos }));
  };

  process.stdout.write(`status: ${status}\n`);
  process.stdout.write(`turn: ${state.turn}\n`);
  process.stdout.write(`allies: ${JSON.stringify(formatRoster(state.allies))}\n`);
  process.stdout.write(`enemies: ${JSON.stringify(formatRoster(state.enemies))}\n`);
}

main();
