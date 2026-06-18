// 정거장 서브시스템 공용 산술 헬퍼 — 정수 클램프와 바닥나눗셈(결정적)
exports.clamp = (v, lo, hi) => (v < lo ? lo : v > hi ? hi : v);

exports.floorDiv = (a, b) => Math.floor(a / b);
