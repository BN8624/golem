// 정거장 서브시스템 공용 산술·헬퍼 — 정수 클램프, 바닥나눗셈, 밴드분류 등 결정적 유틸 모음
exports.clamp = (v, lo, hi) => (v < lo ? lo : v > hi ? hi : v);

exports.floorDiv = (a, b) => Math.floor(a / b);

// 값 v가 thresholds(오름차순) 중 몇 번째 밴드에 드는지 반환(0..len). 경보 등급 분류에 쓴다.
exports.band = (v, thresholds) => {
  let i = 0;
  while (i < thresholds.length && v >= thresholds[i]) i += 1;
  return i;
};

// 배열 정수 합(빈 배열은 0). 파생 지표 계산에 쓴다.
exports.sum = (arr) => {
  let t = 0;
  for (let i = 0; i < arr.length; i += 1) t += arr[i];
  return t;
};

// 0..max 범위의 정수 백분율(바닥). max<=0이면 0.
exports.pct = (v, max) => (max > 0 ? Math.floor((v * 100) / max) : 0);

// a와 b 중 작은/큰 값(Math 의존 최소화한 결정적 버전).
exports.min2 = (a, b) => (a < b ? a : b);
exports.max2 = (a, b) => (a > b ? a : b);

// 주기 sched의 turn에 해당하는 항목을 반환(없으면 null). 결정적 이벤트 스케줄 조회.
exports.scheduledAt = (sched, turn) => {
  for (let i = 0; i < sched.length; i += 1) {
    if (sched[i].turn === turn) return sched[i];
  }
  return null;
};
