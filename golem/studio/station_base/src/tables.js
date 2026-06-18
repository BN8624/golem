// 정거장 결정적 룩업 테이블 — 턴 기반 이벤트 스케줄과 등급 밴드를 한곳에 모은다(난수 없음)
// 모든 스케줄은 turn 값으로 조회한다. 같은 turn에 여러 이벤트가 걸리지 않도록 설계했다.

// 위험 이벤트 스케줄: 특정 턴에 우주환경 위험이 결정적으로 발생한다.
exports.HAZARD_SCHEDULE = [
  { turn: 2, kind: 'MICROMETEORITE', severity: 1 },
  { turn: 4, kind: 'SOLAR_FLARE', severity: 2 },
  { turn: 5, kind: 'MICROMETEORITE', severity: 1 },
  { turn: 7, kind: 'DEBRIS_FIELD', severity: 2 },
  { turn: 9, kind: 'SOLAR_FLARE', severity: 3 },
  { turn: 11, kind: 'MICROMETEORITE', severity: 2 },
  { turn: 13, kind: 'CORONAL_EJECTION', severity: 3 },
  { turn: 16, kind: 'DEBRIS_FIELD', severity: 2 },
  { turn: 19, kind: 'SOLAR_FLARE', severity: 2 },
];

// 통신 접속 윈도우: 이 턴들에 지상국과 교신이 열려 링크가 회복되고 데이터가 빠진다.
exports.CONTACT_WINDOWS = [3, 6, 9, 12, 15, 18, 21, 24];

// 보급선 도착 스케줄: 이 턴들에 화물 보급이 들어온다(cargo.resupplyEvery와 별개의 명시 스케줄).
exports.RESUPPLY_SCHEDULE = [6, 12, 18, 24];

// 승무원 역할 정의: 교대 로테이션에서 활성 역할을 결정하는 고정 순환.
exports.CREW_ROLES = [
  { id: 'COMMANDER', restBonus: 2 },
  { id: 'ENGINEER', restBonus: 3 },
  { id: 'MEDIC', restBonus: 2 },
  { id: 'SCIENTIST', restBonus: 1 },
];

// 온도 등급 밴드(오름차순 경계). util.band로 0..4 등급을 매긴다.
exports.TEMP_BANDS = [5, 15, 28, 35];

// 방사선 누적 등급 밴드.
exports.RAD_BANDS = [50, 120, 200, 350];

// 생명유지 지수 등급 밴드(높을수록 안전).
exports.LIFE_BANDS = [20, 40, 60, 80];

// 지속가능성 점수 가중치: 파생 지표 derive에서 자원별 기여 가중.
exports.SUSTAIN_WEIGHTS = {
  oxygen: 2,
  water: 2,
  food: 2,
  power: 1,
  hull: 1,
  morale: 1,
};

// 등급 → 사람이 읽는 라벨(경보 메시지 조립용).
exports.SEVERITY_LABEL = ['NOMINAL', 'WATCH', 'WARNING', 'CRITICAL', 'EMERGENCY'];
