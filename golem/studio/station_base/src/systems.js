// 정거장 틱 파이프라인 — 한 턴 동안 모든 서브시스템 step을 고정 순서로 차례차례 적용한다
const power = require('./power');
const oxygen = require('./oxygen');
const water = require('./water');
const food = require('./food');
const population = require('./population');
const morale = require('./morale');
const research = require('./research');
const economy = require('./economy');
const hazards = require('./hazards');
const grid = require('./grid');
const thermal = require('./thermal');
const radiation = require('./radiation');
const hull = require('./hull');
const maintenance = require('./maintenance');
const comms = require('./comms');
const cargo = require('./cargo');
const crew = require('./crew');
const navigation = require('./navigation');
const lifesupport = require('./lifesupport');
const derive = require('./derive');

// 고정 순서: 핵심 자원 → 위험/전력망 → 환경(열·방사선·선체) → 운영(정비·통신·화물·승무원·항법) → 파생 지표.
const ORDER = [
  power,
  oxygen,
  water,
  food,
  population,
  morale,
  research,
  economy,
  hazards,
  grid,
  thermal,
  radiation,
  hull,
  maintenance,
  comms,
  cargo,
  crew,
  navigation,
  lifesupport,
  derive,
];

exports.tick = (state, c) => {
  for (const sys of ORDER) {
    state = sys.step(state, c);
  }
  return state;
};
