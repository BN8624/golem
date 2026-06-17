# Planning A/B/C 비교

- 아이디어: 작은 텍스트 로그라이크: 타일 이동 + 적 전투 + 아이템 획득
- API 호출: 0회

| arm | 모드 | total | unique | dup_rate | blocking |
|---|---|---|---|---|---|
| A | self-review | 2 | 2 | 0.0 | 0 |
| B | 3 independent reviewers | 6 | 6 | 0.0 | 0 |
| C | 10 independent reviewers | 13 | 12 | 0.077 | 1 |

## 판정(§19 PENDING-004)
- B vs A: unique 2->6 (gain=2.0) → 독립리뷰 채택 근거 있음
- C vs B: unique 6->12 (gain=1.0) → 10리뷰어 채택 근거 있음

> 주의: `unique_issue_count`는 토큰 Jaccard 기반 **lexical heuristic**이지 의미(semantic) 중복제거가 아니다. near-dup 표현이 unique로 셈해져 특히 reviewer 많은 arm의 수치가 부풀 수 있다. arm 간 **방향성**(리뷰어↑→이슈↑)만 신뢰하고 **격차 크기**는 과신하지 말 것.
