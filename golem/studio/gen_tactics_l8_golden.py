# l8 참조 game_logic(골렘 base-델타 산출, card_delta.py) — graft 체인용
REF_GAME_LOGIC = r"""
function dmgToEnemy(enemy, base, source) {
  let d = base;
  if (source === 'melee' && enemy.unit_type === 'Hardened') d = Math.max(0, d - 1);
  if (enemy.unit_type === 'Glass') d *= 2;
  return d;
}
function mults(state) {
  const c = state.config || {};
  return {
    atk: c.atkMult != null ? c.atkMult : 1,
    rec: c.recMult != null ? c.recMult : 1,
    anom: c.anomMult != null ? c.anomMult : 1
  };
}

exports.applyAction = (state, action) => {
  const newState = {
    ...state,
    hero: { ...state.hero, pos: [...state.hero.pos] },
    enemies: state.enemies.map(e => ({ ...e, pos: [...e.pos] })),
    turn: state.turn
  };
  const m = mults(newState);

  if (action.type === 'move') {
    const [dx, dy] = action.dir;
    const [cx, cy] = newState.hero.pos;
    const nx = cx + dx, ny = cy + dy;
    const isOffGrid = nx < 0 || ny < 0;
    const isOccupied = newState.enemies.some(e => e.hp > 0 && e.pos[0] === nx && e.pos[1] === ny);
    const isWall = !!(newState.terrain && newState.terrain[nx + ',' + ny] === 'Wall');
    if (!isOffGrid && !isOccupied && !isWall) newState.hero.pos = [nx, ny];
  } else if (action.type === 'attack') {
    const target = newState.enemies.find(e => e.id === action.target);
    if (target && target.hp > 0) {
      const dist = Math.abs(newState.hero.pos[0] - target.pos[0]) + Math.abs(newState.hero.pos[1] - target.pos[1]);
      if (dist === 1) {
        const dmgDealt = dmgToEnemy(target, Math.floor(newState.hero.atk * m.atk), 'melee');
        target.hp -= dmgDealt;
        const incoming = Math.floor(target.atk * m.rec);
        const manaBefore = newState.hero.mana || 0;
        const absorbed = Math.min(incoming, manaBefore);
        newState.hero.mana = manaBefore - absorbed;
        newState.hero.hp -= (incoming - absorbed);
        if (manaBefore > 0 && newState.hero.mana <= 0) {
          const [ahx, ahy] = newState.hero.pos;
          let base = Math.floor((newState.hero.anomaly_dmg || 0) * m.anom);
          if (newState.terrain && newState.terrain[ahx + ',' + ahy] === 'Conductive') base *= 2;
          for (const e of newState.enemies) {
            if (e.hp > 0 && Math.abs(ahx - e.pos[0]) + Math.abs(ahy - e.pos[1]) === 1) {
              e.hp -= dmgToEnemy(e, base, 'anomaly');
              if (e.unit_type === 'Resonant') newState.hero.hp -= Math.floor(1 * m.rec);
            }
          }
        }
        if (newState.hero.lifesteal != null) {
          newState.hero.hp += Math.floor(dmgDealt * newState.hero.lifesteal);
        }
      }
    }
  } else if (action.type === 'ranged_attack') {
    const target = newState.enemies.find(e => e.id === action.target);
    if (target && target.hp > 0) {
      const dist = Math.abs(newState.hero.pos[0] - target.pos[0]) + Math.abs(newState.hero.pos[1] - target.pos[1]);
      if (dist >= 2 && dist <= 3) {
        target.hp -= dmgToEnemy(target, Math.floor(newState.hero.atk * m.atk), 'ranged');
        if (newState.hero.corrosion) {
          target.status = { type: 'Corrosion', duration: newState.hero.corrosion.duration, dmg: newState.hero.corrosion.dmg };
        }
      }
    }
  }

  return newState;
};

exports.updateState = (state, action) => {
  const nextState = exports.applyAction(state, action);
  nextState.turn += 1;
  const m = mults(nextState);

  for (const e of nextState.enemies) {
    if (e.hp > 0 && e.status && e.status.type === 'Corrosion' && e.status.duration > 0) {
      e.hp -= Math.floor(e.status.dmg * m.atk) * (e.unit_type === 'Glass' ? 2 : 1);
      e.status = { ...e.status, duration: e.status.duration - 1 };
      if (e.status.duration <= 0) delete e.status;
    }
  }

  if (nextState.hero.hp > 0 && Array.isArray(nextState.route)) {
    const idx = nextState.route_index || 0;
    const allDead = nextState.enemies.every(e => e.hp <= 0);
    if (allDead && idx < nextState.route.length) {
      const battle = nextState.route[idx];
      nextState.enemies = battle.enemies.map(e => ({ ...e, pos: [...e.pos] }));
      nextState.terrain = battle.terrain || undefined;
      nextState.hero = { ...nextState.hero, pos: [0, 0] };
      nextState.route_index = idx + 1;
    }
  }
  return nextState;
};

exports.checkGameState = (state, initialEnemyCount) => {
  const heroDead = state.hero.hp <= 0;
  const allEnemiesDead = state.enemies.every(e => e.hp <= 0);
  const routeRemaining = Array.isArray(state.route) && (state.route_index || 0) < state.route.length;
  if (heroDead && allEnemiesDead) return 'DEFEAT';
  if (allEnemiesDead && !routeRemaining && initialEnemyCount > 0) return 'VICTORY';
  if (heroDead) return 'DEFEAT';
  return null;
};
"""
