// 에테르노 IF CLI 진입점 — scenarios.json에서 N번째 시나리오를 읽어 엔진을 돌리고 최종 상태를 출력한다
const fs = require('fs');
const { runScenario } = require('./src/engine');
const { render } = require('./src/format');

function main() {
  const args = process.argv.slice(2);
  const i = args.indexOf('--scenario');
  if (i === -1 || !args[i + 1]) return;
  const idx = parseInt(args[i + 1], 10);

  let scenarios;
  try {
    scenarios = JSON.parse(fs.readFileSync('scenarios.json', 'utf8'));
  } catch (e) {
    return;
  }

  const scenario = scenarios[idx - 1];
  if (!scenario) return;

  process.stdout.write(render(runScenario(scenario)) + '\n');
}

main();
