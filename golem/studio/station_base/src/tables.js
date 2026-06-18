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

// --- 2차 확장 서브시스템 스케줄·밴드(전부 turn 기반 결정적) ---

// 부품 재주문(보급) 스케줄: 이 턴들에 inventory가 부품을 보충한다.
exports.REORDER_SCHEDULE = [5, 10, 15, 20];

// 안전 훈련 스케줄: 이 턴들에 safety가 훈련 로그를 남긴다.
exports.DRILL_SCHEDULE = [2, 8, 14, 20];

// 정기 건강검진 스케줄: 이 턴들에 medical이 현재 건강 등급을 검진 로그로 남긴다.
exports.MED_CHECK_SCHEDULE = [3, 9, 15, 21];

// 선체 정밀점검 스케줄: 이 턴들에 structural이 점검 로그를 남긴다.
exports.INSPECTION_SCHEDULE = [4, 11, 18];

// 정기 상태 스냅샷 스케줄: 이 턴들에 report가 종합 상태 로그를 남긴다.
exports.STATUS_SCHEDULE = [3, 6, 9, 12, 15, 18];

// 열 균형 점검 스케줄: 이 턴들에 thermalzones가 균형 로그를 남긴다.
exports.THERMAL_BALANCE_SCHEDULE = [5, 13, 21];

// 궤도요소 기록 스케줄: 이 턴들에 navlog가 궤도 로그를 남긴다.
exports.ORBIT_LOG_SCHEDULE = [4, 9, 16];

// 축전지 충방전 사이클 기록 스케줄.
exports.CHARGE_CYCLE_SCHEDULE = [7, 14, 21];

// 선외활동(EVA) 스케줄: 이 턴들에 airlock이 EVA 로그를 남긴다.
exports.EVA_SCHEDULE = [4, 10, 16];

// 냉각 루프 점검 스케줄: 이 턴들에 coolant가 여유 로그를 남긴다.
exports.COOLANT_CHECK_SCHEDULE = [2, 7, 12, 17];

// 자세제어 점검 스케줄: 이 턴들에 attitude가 이탈 로그를 남긴다.
exports.ATTITUDE_SCHEDULE = [5, 11, 19];

// 폐기물 처리 스케줄: 이 턴들에 waste가 적체를 처리한다.
exports.WASTE_SCHEDULE = [6, 12, 18];

// 실험 마일스톤(누적 연구점수 경계 → 코드). research가 이 값 이상이 되면 한 번씩 로그한다.
exports.EXPERIMENT_MILESTONES = [
  { at: 5, code: 'ASSAY' },
  { at: 12, code: 'SYNTHESIS' },
  { at: 22, code: 'TRIAL' },
  { at: 34, code: 'BREAKTHROUGH' },
];

// 피폭 누적 마일스톤(누적 방사선 경계 → 코드). radiation이 이 값 이상이 되면 한 번씩 로그한다.
exports.DOSE_MILESTONES = [
  { at: 10, code: 'TRACE' },
  { at: 30, code: 'ELEVATED' },
  { at: 60, code: 'SERIOUS' },
  { at: 100, code: 'SEVERE' },
];

// 건강 등급 밴드(오름차순 경계). util.band로 0..4 등급(낮을수록 위험).
exports.HEALTH_BANDS = [25, 50, 70, 90];

// 응력 등급 밴드(오름차순 경계, 높을수록 위험).
exports.STRESS_BANDS = [30, 60, 90, 120];

// 축전지 충전 등급 밴드.
exports.CHARGE_BANDS = [4, 12, 30, 50];

// 거주성 등급 밴드(높을수록 쾌적).
exports.HABITAT_BANDS = [20, 35, 55, 75];
