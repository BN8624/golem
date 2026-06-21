const engine = require('./src/engine');
const scenarios = require('./src/scenarios');

function main() {
    const args = process.argv.slice(2);
    const scenarioIdxArg = args[args.indexOf('--scenario') + 1];
    if (!scenarioIdxArg) return;

    const n = parseInt(scenarioIdxArg, 10);
    const scenario = scenarios.getScenario(n);
    if (!scenario) return;

    const { initialState, actions } = scenario;
    const { state, status } = engine.runScenario(initialState, actions);

    process.stdout.write(`status: ${status}\n`);
    process.stdout.write(`turn: ${state.turn}\n`);
    process.stdout.write(`hero_hp: ${state.hero.hp}\n`);
    process.stdout.write(`hero_pos: ${JSON.stringify(state.hero.pos)}\n`);

    const enemiesFormatted = state.enemies
        .slice()
        .sort((a, b) => a.id - b.id)
        .map(e => ({
            id: e.id,
            hp: e.hp,
            pos: e.pos
        }));
    process.stdout.write(`enemies: ${JSON.stringify(enemiesFormatted)}\n`);
}

main();
