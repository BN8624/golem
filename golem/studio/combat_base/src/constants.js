// 턴제 전투 밸런스 상수 — 규칙(로직)과 분리된 숫자만(밸런스는 여기서 튜닝, 엔진 정확성은 불변)
module.exports = {
  maxTicks: 50,
  poisonDmg: 5,
  attackDmg: 20,
  attackCost: 20,
  attackRange: 1,
  moveCost: 10,
  waitGain: 20,
  energyCap: 100,
  posMin: 0,
  posMax: 10,
  gaugeThreshold: 100,
};
