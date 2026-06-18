const fs = require('fs');
const { runScenario } = require('./src/engine');

function main() {
  const args = process.argv.slice(2);
  const scenarioIdxArg = args.indexOf('--scenario');
  
  if (scenarioIdxArg === -1 || !args[scenarioIdxArg + 1]) {
    return;
  }

  const scenarioIdx = parseInt(args[scenarioIdxArg + 1], 10);
  
  let scenarios;
  try {
    const data = fs.readFileSync('scenarios.json', 'utf8');
    scenarios = JSON.parse(data);
  } catch (e) {
    return;
  }

  const scenario = scenarios[scenarioIdx - 1];
  if (!scenario) return;

  const finalState = runScenario(scenario);

  process.stdout.write(`turn: ${finalState.turn}\n`);
  process.stdout.write(`fuel: ${finalState.fuel}\n`);
  process.stdout.write(`stage: ${finalState.stage}\n`);
  process.stdout.write(`events: ${JSON.stringify(finalState.events)}\n`);
  process.stdout.write(`log: ${JSON.stringify(finalState.log)}\n`);
  process.stdout.write(`gameStatus: ${finalState.gameStatus}\n`);
  process.stdout.write(`logs: ${JSON.stringify(finalState.log)}\n`);
}

main();
