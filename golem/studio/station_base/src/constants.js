// 정거장 카드의 기본 설정 테이블 — 시나리오가 constants를 생략하면 이 값이 기본값으로 쓰인다
// 모든 수치는 정수이며 결정적이다. 서브시스템마다 자기 구역의 설정을 읽고 없으면 이 기본값으로 폴백한다.
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
    hull: 100,
    comms: 100,
    cargo: 200,
    navFuel: 100,
    radiation: 1000,
    wear: 1000,
    fatigue: 100,
  },
  power: {
    genPerSolar: 8, // 태양광 패널 1레벨당 발전량
    usePerPop: 2, // 인구 1명당 전력 소비
  },
  oxygen: {
    genIfPowered: 10, // 전력 있을 때 산소 발생기 생산
    decayIfDark: 6, // 정전 시 산소 손실
    usePerPop: 2,
    lowAlert: 20,
  },
  water: {
    recycleIfPowered: 9, // 재활용기 1레벨당 정수량
    usePerPop: 2,
    lowAlert: 20,
  },
  food: {
    farmIfPowered: 7, // 농장 1레벨당 식량 생산
    usePerPop: 2,
    lowAlert: 15,
  },
  population: {
    growEvery: 3, // N턴마다 1명 증가(생존 조건 충족 시)
    lowAlert: 3,
  },
  morale: {
    comfort: 30, // 자원이 이 값 초과면 쾌적
    up: 2,
    down: 3,
    rationPenalty: 1, // 배급제 시 추가 사기 하락
    lowAlert: 25,
  },
  research: {
    perPopIfPowered: 1, // 전력 있을 때 인구 1명당 연구점수
    goal: 40, // 이 점수 도달 시 WON
  },
  economy: {
    incomePerPop: 3, // 매 턴 인구 1명당 크레딧
  },
  build: {
    solar: 20,
    farm: 25,
    recycler: 22,
  },
  // --- 확장 서브시스템 설정 ---
  thermal: {
    target: 21, // 목표 선체 온도
    heatPerLoad: 1, // 전력 부하(소비)당 발열
    solarHeat: 2, // 태양광 노출당 발열
    coolPerRadiator: 3, // 방열판 1단위 냉각
    radiators: 4,
    hotAlert: 35, // 이 온도 이상이면 과열 경보
    coldAlert: 5, // 이 온도 이하이면 동결 경보
    drift: 1, // 매 턴 목표온도로의 자연 회귀량
  },
  radiation: {
    influxPerTurn: 4, // 매 턴 기본 우주방사선 유입
    shieldPerHull: 1, // 선체 무결성 단위당 차폐
    flareMultiplier: 5, // 플레어 이벤트 시 유입 배수
    doseAlert: 200, // 누적 피폭 경보선
    crewDosePerInflux: 1,
  },
  hull: {
    repairPerCargo: 2, // 화물 1단위로 수리하는 무결성
    autoRepair: 1, // 매 턴 자동 미세보수
    breachAlert: 40, // 이 무결성 이하면 균열 경보
    micrometeoriteDamage: 8,
  },
  maintenance: {
    wearPerTurn: 3, // 매 턴 장비 마모 누적
    wearPerPop: 1, // 인구 활동에 따른 추가 마모
    serviceReduces: 12, // 정비 1회 감소량(자동)
    backlogAlert: 60, // 마모 적체 경보선
    breakdownAt: 120, // 이 적체 이상이면 고장(전력 페널티)
  },
  comms: {
    baseQuality: 100,
    degradePerTurn: 5, // 매 턴 링크 품질 저하
    restoreInWindow: 30, // 접속 윈도우에서 회복
    bufferPerPop: 1, // 인구당 데이터 생성
    bufferDrainInWindow: 8,
    lowAlert: 25,
  },
  cargo: {
    consumePerPop: 1, // 인구당 소모품 소비
    resupplyEvery: 6, // N턴마다 보급(결정적)
    resupplyAmount: 30,
    lowAlert: 20,
  },
  crew: {
    fatiguePerTurn: 4, // 매 턴 누적 피로
    restPerRotation: 10, // 교대 시 회복
    rotateEvery: 4, // N턴마다 교대
    highAlert: 70, // 피로 경보선
    overworkAt: 90, // 이 이상이면 사기 페널티
  },
  navigation: {
    driftPerTurn: 2, // 매 턴 궤도 이탈
    burnReduces: 6, // 자동 보정 분사 감소량
    fuelPerBurn: 2,
    driftAlert: 20, // 이탈 경보선
    decayAt: 40, // 이 이상 이탈이면 고도 손실
  },
  lifesupport: {
    redundancyBonus: 5, // 모든 자원 여유 시 보너스
    indexAlert: 30, // 생명유지 지수 경보선
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
    temperature: 21,
    radiation: 0,
    hull: 100,
    wear: 0,
    comms: 100,
    dataBuffer: 0,
    cargo: 40,
    fatigue: 0,
    navDrift: 0,
    navFuel: 30,
  },
};
