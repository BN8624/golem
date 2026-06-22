# l1 참조 game_logic(골렘 base-델타 산출, card_delta.py) — graft 체인용
REF_GAME_LOGIC = r"""
function manhattan(p1, p2) {
  return Math.abs(p1[0] - p2[0]) + Math.abs(p1[1] - p2[1]);
}

function isOccupied(state, x, y) {
  const allyOccupied = state.allies.some(u => u.hp > 0 && u.pos[0] === x && u.pos[1] === y);
  const enemyOccupied = state.enemies.some(u => u.hp > 0 && u.pos[0] === x && u.pos[1] === y);
  return allyOccupied || enemyOccupied;
}

function applyAction(state, action) {
  const ally = state.allies.find(a => a.id === action.unit);
  if (!ally || ally.hp <= 0) return;

  if (action.type === 'move') {
    const [dx, dy] = action.dir || [0, 0];
    const nx = ally.pos[0] + dx;
    const ny = ally.pos[1] + dy;

    if (
      nx >= 0 && nx < state.gridSize &&
      ny >= 0 && ny < state.gridSize &&
      !isOccupied(state, nx, ny)
    ) {
      ally.pos = [nx, ny];
    }
  } else if (action.type === 'attack') {
    const range = ally.range || 1;
    const target = state.enemies
      .filter(e => e.hp > 0 && manhattan(ally.pos, e.pos) <= range && manhattan(ally.pos, e.pos) >= 1)
      .sort((a, b) => a.id - b.id)[0];
    if (target) {
      target.hp -= ally.atk;
    }
  }
}

function executeEnemyAI(state, enemy) {
  const livingAllies = state.allies.filter(a => a.hp > 0);
  if (livingAllies.length === 0) return;

  const target = livingAllies.sort((a, b) => {
    const distA = manhattan(enemy.pos, a.pos);
    const distB = manhattan(enemy.pos, b.pos);
    return distA - distB || a.id - b.id;
  })[0];

  const distToTarget = manhattan(enemy.pos, target.pos);

  if (distToTarget === 1) {
    target.hp -= enemy.atk;
  } else {
    const possibleMoves = [[1, 0], [-1, 0], [0, 1], [0, -1]];
    const candidates = [];

    for (const [dx, dy] of possibleMoves) {
      const nx = enemy.pos[0] + dx;
      const ny = enemy.pos[1] + dy;

      if (
        nx >= 0 && nx < state.gridSize &&
        ny >= 0 && ny < state.gridSize &&
        !isOccupied(state, nx, ny)
      ) {
        if (manhattan([nx, ny], target.pos) < distToTarget) {
          candidates.push([nx, ny]);
        }
      }
    }

    if (candidates.length > 0) {
      candidates.sort((a, b) => {
        const aIsX = a[0] !== enemy.pos[0];
        const bIsX = b[0] !== enemy.pos[0];
        if (aIsX !== bIsX) return aIsX ? -1 : 1;
        if (a[0] !== b[0]) return a[0] - b[0];
        return a[1] - b[1];
      });
      enemy.pos = candidates[0];
    }
  }
}

function checkGameState(state) {
  const enemiesAlive = state.enemies.some(e => e.hp > 0);
  const alliesAlive = state.allies.some(a => a.hp > 0);

  if (!enemiesAlive) return 'VICTORY';
  if (!alliesAlive) return 'DEFEAT';
  return 'PLAYING';
}

function updateState(state, action) {
  applyAction(state, action);

  const statusAfterAlly = checkGameState(state);
  if (statusAfterAlly === 'VICTORY') {
    state.turn++;
    return 'VICTORY';
  }

  const livingEnemies = state.enemies
    .filter(e => e.hp > 0)
    .sort((a, b) => a.id - b.id);

  for (const enemy of livingEnemies) {
    executeEnemyAI(state, enemy);
    const statusDuringEnemy = checkGameState(state);
    if (statusDuringEnemy === 'DEFEAT') {
      state.turn++;
      return 'DEFEAT';
    }
  }

  state.turn++;
  return 'PLAYING';
}

module.exports = { applyAction, checkGameState, updateState };
"""
