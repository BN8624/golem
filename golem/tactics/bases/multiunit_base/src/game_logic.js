function getManhattanDist(p1, p2) {
    return Math.abs(p1[0] - p2[0]) + Math.abs(p1[1] - p2[1]);
}

exports.applyAction = (state, action) => {
    const { hero, enemies, gridSize } = state;

    if (action.type === 'move') {
        const nx = hero.pos[0] + action.dir[0];
        const ny = hero.pos[1] + action.dir[1];

        if (nx >= 0 && nx < gridSize && ny >= 0 && ny < gridSize) {
            const isOccupied = enemies.some(e => e.hp > 0 && e.pos[0] === nx && e.pos[1] === ny);
            if (!isOccupied) {
                hero.pos = [nx, ny];
            }
        }
    } else if (action.type === 'attack') {
        let target = null;
        for (const enemy of enemies) {
            if (enemy.hp > 0 && getManhattanDist(hero.pos, enemy.pos) === 1) {
                if (!target || enemy.id < target.id) {
                    target = enemy;
                }
            }
        }
        if (target) {
            target.hp -= hero.atk;
        }
    }
    return state;
};

exports.updateState = (state, action) => {
    // 1. Hero Phase
    state = exports.applyAction(state, action);

    // 2. Check if all enemies defeated (skip enemy phase if so)
    const aliveEnemies = state.enemies.filter(e => e.hp > 0);
    if (aliveEnemies.length > 0) {
        // 3. Enemy Phase
        const sortedEnemies = state.enemies
            .filter(e => e.hp > 0)
            .sort((a, b) => a.id - b.id);

        for (const enemy of sortedEnemies) {
            const dist = getManhattanDist(enemy.pos, state.hero.pos);
            if (dist === 1) {
                state.hero.hp -= enemy.atk;
            } else {
                const moves = [
                    [enemy.pos[0] + 1, enemy.pos[1]],
                    [enemy.pos[0] - 1, enemy.pos[1]],
                    [enemy.pos[0], enemy.pos[1] + 1],
                    [enemy.pos[0], enemy.pos[1] - 1],
                ];

                const candidates = moves.filter(([nx, ny]) => {
                    if (nx < 0 || nx >= state.gridSize || ny < 0 || ny >= state.gridSize) return false;
                    if (nx === state.hero.pos[0] && ny === state.hero.pos[1]) return false;
                    if (state.enemies.some(e => e.hp > 0 && e.pos[0] === nx && e.pos[1] === ny)) return false;
                    return true;
                }).filter(([nx, ny]) => {
                    return getManhattanDist([nx, ny], state.hero.pos) < dist;
                });

                if (candidates.length > 0) {
                    const xMoves = candidates.filter(([nx, ny]) => nx !== enemy.pos[0]);
                    const yMoves = candidates.filter(([nx, ny]) => ny !== enemy.pos[1]);
                    const selection = xMoves.length > 0 ? xMoves : yMoves;
                    selection.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
                    enemy.pos = selection[0];
                }
            }
        }
    }

    state.turn += 1;
    return state;
};

exports.checkGameState = (state) => {
    const aliveEnemies = state.enemies.filter(e => e.hp > 0);
    if (aliveEnemies.length === 0) return 'VICTORY';
    if (state.hero.hp <= 0) return 'DEFEAT';
    return 'PLAYING';
};
