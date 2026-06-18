// 정거장 카드의 기본 설정 테이블 — 시나리오가 constants를 생략하면 이 값이 기본값으로 쓰인다
exports.constants = {
  caps: {
    power: 100,
    oxygen: 100,
    water: 100,
    food: 100,
    population: 12,
    morale: 100,
    research: 99999,
    credits: 99999,
  },
  power: {
    genPerSolar: 8,   // 태양광 패널 1레벨당 발전량
    usePerPop: 2,     // 인구 1명당 전력 소비
  },
  oxygen: {
    genIfPowered: 10, // 전력 있을 때 산소 발생기 생산
    decayIfDark: 6,   // 정전 시 산소 손실
    usePerPop: 2,
    lowAlert: 20,
  },
  water: {
    recycleIfPowered: 9, // 재활용기 1레벨당 정수량
    usePerPop: 2,
    lowAlert: 20,
  },
  food: {
    farmIfPowered: 7,    // 농장 1레벨당 식량 생산
    usePerPop: 2,
    lowAlert: 15,
  },
  population: {
    growEvery: 3,        // N턴마다 1명 증가(생존 조건 충족 시)
    lowAlert: 3,
  },
  morale: {
    comfort: 30,         // 자원이 이 값 초과면 쾌적
    up: 2,
    down: 3,
    rationPenalty: 1,    // 배급제 시 추가 사기 하락
    lowAlert: 25,
  },
  research: {
    perPopIfPowered: 1,  // 전력 있을 때 인구 1명당 연구점수
    goal: 40,            // 이 점수 도달 시 WON
  },
  economy: {
    incomePerPop: 3,     // 매 턴 인구 1명당 크레딧
  },
  build: {
    solar: 20,
    farm: 25,
    recycler: 22,
  },
  start: {
    power: 20,
    oxygen: 60,
    water: 60,
    food: 50,
    population: 4,
    morale: 60,
    research: 0,
    credits: 30,
    solar: 2,
    farm: 2,
    recycler: 2,
  },
};
