// 정거장 상태의 생성·복제·종료판정 — 초기 상태를 만들고 매 단계 승패(WON/LOST)를 확정한다
const D = require('./constants').constants;

exports.createInitialState = (c) => {
  const S = (c && c.start) || D.start;
  return {
    turn: 0,
    power: S.power,
    oxygen: S.oxygen,
    water: S.water,
    food: S.food,
    population: S.population,
    morale: S.morale,
    research: S.research,
    credits: S.credits,
    solar: S.solar,
    farm: S.farm,
    recycler: S.recycler,
    rationing: false,
    // 확장 서브시스템 내부 상태(출력 계약에는 미포함, 경보/로그로만 드러남)
    temperature: S.temperature,
    radiation: S.radiation,
    hull: S.hull,
    wear: S.wear,
    comms: S.comms,
    dataBuffer: S.dataBuffer,
    cargo: S.cargo,
    fatigue: S.fatigue,
    navDrift: S.navDrift,
    navFuel: S.navFuel,
    // 2차 확장 서브시스템 내부 상태(출력 계약 미포함, 경보/로그/사기로만 드러남)
    charge: S.charge,
    health: S.health,
    parts: S.parts,
    packets: S.packets,
    stress: S.stress,
    habitability: S.habitability,
    experiments: S.experiments,
    doseLevel: S.doseLevel,
    waste: S.waste,
    brownout: false,
    lifeIndex: 0,
    sustain: 0,
    alerts: [],
    log: [],
    gameStatus: 'PLAYING',
  };
};

exports.clone = (s) => ({ ...s, alerts: [...s.alerts], log: [...s.log] });

exports.checkEnd = (s, c) => {
  if (s.gameStatus !== 'PLAYING') return s;
  const R = (c && c.research) || D.research;
  if (s.population <= 0) {
    s.gameStatus = 'LOST';
    s.log.push('STATION_LOST');
  } else if (s.research >= R.goal) {
    s.gameStatus = 'WON';
    s.log.push('MISSION_COMPLETE');
  }
  return s;
};
