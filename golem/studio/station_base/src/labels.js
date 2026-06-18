// 정거장 경보·로그 메시지 카탈로그 — 코드를 일관된 문자열로 조립하는 순수 헬퍼(상태 변경 없음)
const { SEVERITY_LABEL } = require('./tables');

// 서브시스템 경보 코드를 표준 형식으로 만든다. 예: alert('THERMAL','HOT') -> 'THERMAL_HOT'.
exports.alert = (system, condition) => system + '_' + condition;

// 등급 숫자를 라벨로(범위 밖이면 UNKNOWN).
exports.severity = (level) => SEVERITY_LABEL[level] || 'UNKNOWN';

// 위험 이벤트 로그 라인. 예: hazardLine('SOLAR_FLARE',2) -> 'HAZARD SOLAR_FLARE WARNING'.
exports.hazardLine = (kind, sev) => 'HAZARD ' + kind + ' ' + exports.severity(sev);

// 단계 전환 로그(주로 종료/마일스톤). 예: milestone('RESUPPLY') -> 'EVENT RESUPPLY'.
exports.milestone = (code) => 'EVENT ' + code;

// 수치 경보를 등급과 함께. 예: graded('RAD',3) -> 'RAD_CRITICAL'.
exports.graded = (system, level) => system + '_' + exports.severity(level);
