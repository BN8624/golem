// 유닛 단위 결정적 로직 — 독·게이지·상태감소 + 한 액션(ATTACK/MOVE/WAIT) 실행. 전투의 고결합 코어
const C = require('./constants');

// 틱 시작 독 데미지(RULE-01): poison 지속틱이 있으면 5 데미지·지속 1 감소.
exports.applyPoison = (u) => {
  if (u.poison > 0) {
    return { ...u, hp: u.hp - C.poisonDmg, poison: u.poison - 1 };
  }
  return u;
};

// 게이지 충전(RULE-02·08): stun이 아니면 speed만큼 증가. stun이면 충전 없음.
exports.gainGauge = (u) => (u.stun > 0 ? u : { ...u, gauge: u.gauge + u.speed });

// 틱 끝 stun 지속 감소(RULE-08).
exports.decStun = (u) => (u.stun > 0 ? { ...u, stun: u.stun - 1 } : u);

// 한 액션 실행(RULE-04~07). 성공/실패 무관히 호출부가 gauge -= 100. {actor,target,log} 반환.
exports.calculateAction = (actor, target, command, who) => {
  let a = { ...actor };
  let t = { ...target };
  let log;
  if (command === 'ATTACK') {
    if (Math.abs(a.pos - t.pos) <= C.attackRange && a.energy >= C.attackCost) {
      t = { ...t, hp: t.hp - C.attackDmg };
      a = { ...a, energy: a.energy - C.attackCost };
      log = who + ' ATTACK hit';
    } else {
      log = who + ' ATTACK fail';
    }
  } else if (command === 'MOVE') {
    const dir = t.pos >= a.pos ? 1 : -1;
    const np = a.pos + dir;
    if (np >= C.posMin && np <= C.posMax && a.energy >= C.moveCost) {
      a = { ...a, pos: np, energy: a.energy - C.moveCost };
      log = who + ' MOVE to ' + np;
    } else {
      log = who + ' MOVE fail';
    }
  } else { // WAIT(RULE-06)
    a = { ...a, energy: Math.min(C.energyCap, a.energy + C.waitGain) };
    log = who + ' WAIT';
  }
  a = { ...a, gauge: a.gauge - C.gaugeThreshold }; // RULE-07
  return { actor: a, target: t, log };
};
