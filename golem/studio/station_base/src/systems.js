// 정거장 틱 파이프라인 — 한 턴 동안 모든 서브시스템 step을 고정 순서로 차례차례 적용한다
const power = require('./power');
const oxygen = require('./oxygen');
const water = require('./water');
const food = require('./food');
const population = require('./population');
const morale = require('./morale');
const research = require('./research');
const economy = require('./economy');

// 고정 순서: 전력 → 산소 → 물 → 식량 → 인구 → 사기 → 연구 → 경제.
const ORDER = [power, oxygen, water, food, population, morale, research, economy];

exports.tick = (state, c) => {
  for (const sys of ORDER) {
    state = sys.step(state, c);
  }
  return state;
};
