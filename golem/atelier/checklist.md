# Atelier 체크리스트

## 코어 — 캐논 채점기 (frontier 1)

- [x] `auto_oracle.py` → `canon_check.py` 포팅 (캐논 위반 검출 + N시드·exact·recall·안정성·오탐).
- [x] 픽스처: `bible.json`(캐논 4규칙) + 깨끗한 초고 + 모순 심은 초고(골든 C1·C2) + `cases.json`.
- [x] 키 없는 `--replay`로 채점 배선 검증 → exact/recall/오탐 수학 정확 확인.
- [ ] ★실제 31B 런(`--n 3`) — **사용자 go 대기**. 31B가 심은 위반을 실제로 잡나 측정.
- [ ] 결과로 캐논/미학 경계 1차 결정 (뭐가 기계로 잡히나).

## 다음 (코어 검증 뒤)

- [ ] planning 단계: 로그라인 → 바이블 초안 + 다축 ambiguity(연속성) 리뷰.
- [ ] design 단계: 비트시트 + setup→payoff traceability.
- [ ] 캐논 원장 누적(p0..p4 단계적 확장).
