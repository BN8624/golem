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
const battery = require('./battery');
const medical = require('./medical');
const inventory = require('./inventory');
const telemetry = require('./telemetry');
const thermalzones = require('./thermalzones');
const structural = require('./structural');
const science = require('./science');
const safety = require('./safety');
const navlog = require('./navlog');
const radlog = require('./radlog');
const habitat = require('./habitat');
const airlock = require('./airlock');
const coolant = require('./coolant');
const attitude = require('./attitude');
const waste = require('./waste');
const derive = require('./derive');
const report = require('./report');

// 고정 순서: 핵심 자원 → 위험/전력망 → 환경(열·방사선·선체) → 운영(정비·통신·화물·승무원·항법) →
// 2차 진단(축전지·의무실·재고·텔레메트리·구역열·구조·과학·안전·항법기록·피폭·거주성) → 파생 지표 → 종합보고.
// 진단·보고 모듈은 앞 단계가 갱신한 상태를 읽기만 하므로(report는 derive 뒤) 핵심 계산을 바꾸지 않는다.
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
  battery,
  medical,
  inventory,
  telemetry,
  thermalzones,
  structural,
  science,
  safety,
  navlog,
  radlog,
  habitat,
  airlock,
  coolant,
  attitude,
  waste,
  derive,
  report,
];

exports.tick = (state, c) => {
  for (const sys of ORDER) {
    state = sys.step(state, c);
  }
  return state;
};
