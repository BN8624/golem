exports.applyAction = (state, action) => {
  const newState = {
    ...state,
    hero: { ...state.hero, pos: [...state.hero.pos] },
    enemies: state.enemies.map(e => ({ ...e, pos: [...e.pos] })),
    turn: state.turn
  };

  if (action.type === 'move') {
    const [dx, dy] = action.dir;
    const [cx, cy] = newState.hero.pos;
    const nx = cx + dx;
    const ny = cy + dy;

    // REQ-010: Blocked if negative coordinates OR occupied by living enemy
    const isOffGrid = nx < 0 || ny < 0;
    const isOccupied = newState.enemies.some(e => e.hp > 0 && e.pos[0] === nx && e.pos[1] === ny);

    if (!isOffGrid && !isOccupied) {
      newState.hero.pos = [nx, ny];
    }
  } else if (action.type === 'attack') {
    const target = newState.enemies.find(e => e.id === action.target);
    if (target && target.hp > 0) {
      const [hx, hy] = newState.hero.pos;
      const [ex, ey] = target.pos;
      const dist = Math.abs(hx - ex) + Math.abs(hy - ey);

      // REQ-011: Valid attack only if orthogonally adjacent
      if (dist === 1) {
        // REQ-003: Simultaneous mutual damage
        const heroAtk = newState.hero.atk;
        const enemyAtk = target.atk;
        target.hp -= heroAtk;
        newState.hero.hp -= enemyAtk;
      }
    }
  }

  return newState;
};

exports.updateState = (state, action) => {
  const nextState = exports.applyAction(state, action);
  // REQ-002: turn = turn + 1 after every action attempt
  nextState.turn += 1;
  return nextState;
};

exports.checkGameState = (state, initialEnemyCount) => {
  const heroDead = state.hero.hp <= 0;
  const allEnemiesDead = state.enemies.every(e => e.hp <= 0);

  // REQ-006: Both dead -> DEFEAT
  if (heroDead && allEnemiesDead) return 'DEFEAT';
  // REQ-007: Initial enemies 0 -> FINISHED, not VICTORY
  if (allEnemiesDead && initialEnemyCount > 0) return 'VICTORY';
  // Only hero dead -> DEFEAT
  if (heroDead) return 'DEFEAT';

  return null;
};
