// 전투 초기 상태 생성 — setup의 player/enemy 필드를 기본값 위에 얹어 결정적 시작 상태를 만든다
const DEFAULT_UNIT = { hp: 100, energy: 100, speed: 10, gauge: 0, pos: 0, poison: 0, stun: 0 };

function makeUnit(spec) {
  const s = spec || {};
  // poison은 정수 지속틱. 과거 포맷의 boolean(false)도 0으로 정규화한다.
  const poison = typeof s.poison === 'number' ? s.poison : (s.poison ? 1 : 0);
  return {
    hp: s.hp != null ? s.hp : DEFAULT_UNIT.hp,
    energy: s.energy != null ? s.energy : DEFAULT_UNIT.energy,
    speed: s.speed != null ? s.speed : DEFAULT_UNIT.speed,
    gauge: s.gauge != null ? s.gauge : DEFAULT_UNIT.gauge,
    pos: s.pos != null ? s.pos : DEFAULT_UNIT.pos,
    poison: poison,
    stun: s.stun != null ? s.stun : DEFAULT_UNIT.stun,
  };
}

exports.createInitialState = (setup) => {
  const s = setup || {};
  return {
    tick: 0,
    player: makeUnit(s.player),
    enemy: makeUnit(s.enemy),
    gameLog: [],
    isGameOver: false,
    winner: null,
  };
};
