# Atelier 체크리스트

## 코어 — 캐논 채점기 (frontier 1)

- [x] `auto_oracle.py` → `canon_check.py` 포팅 (캐논 위반 검출 + N시드·exact·recall·안정성·오탐).
- [x] 픽스처: `bible.json`(캐논 4규칙) + 깨끗한 초고 + 모순 심은 초고(골든 C1·C2) + `cases.json`.
- [x] 키 없는 `--replay`로 채점 배선 검증 → exact/recall/오탐 수학 정확 확인.
- [x] ★실제 31B 런(`--n 3`, atelier 11키) — **exact 1.0, 2/2 완전정확, 안정 1.0, 오탐 0** (canon-20260618-145250).
- [ ] 경계 미정 — 지금 픽스처는 너무 쉽다(노골적 모순 4규칙). 어려운 픽스처로 진짜 한계를 찾아야 함.
- [ ] 결과로 캐논/미학 경계 1차 결정 (뭐가 기계로 잡히나).

## 자족화 (골렘 폴더 비의존 — 나중에 독립 프로젝트로 이전 대비)

- [x] 인프라 vendoring → `lib/`(config·llm·key_usage·jsonutil). golem 폴더 import 0.
- [x] `lib/config.py` PROJECT_ROOT = atelier 루트(.env·runs 따라오게). 이동성 격리 import로 증명.
- [x] 모델 정직화 — `generate("generator")`(26B)를 물려받던 것을 `ROLE="critic"`(31B='머리')로 교정.
      print도 상수 대신 `get_model`로 실제 모델 출력. **주의: 앞 1.0 런은 사실 26B였다.**
- [x] ★31B로 재실행 — exact 1.0 / 2-of-2 / 안정 1.0 / 오탐 0 (canon-20260618-150843). 정직한 31B 수치.

## planning 단계 (frontier 2)

- [x] `golem/studio/planning.py` → `planning.py` 포팅(자족 lib, 31B critic). A/B/C arm + synthesis.
- [x] 소설판 10축(동기·복선·타임라인·지식상태·세계규칙·중복인물·테마·톤·스테이크·핸드오프).
- [x] 출력 = `bible.json`(premise + canon[{id,text}]) — **canon_check 입력 모양과 일치, 루프 닫힘**.
- [x] 키 없는 `--replay`로 A/B/C·synthesize 배선 검증(BLOCKING 흡수→FROZEN, canon 5).
- [ ] ★실제 31B 런(`--idea "..." --synthesize`) — 진짜 로그라인으로 바이블 생성(사용자 go 대기).
- [ ] planning 바이블 → canon_check 실초고 채점까지 end-to-end 1회(키 필요).

## 다음 (planning 검증 뒤)

- [ ] design 단계: 비트시트 + setup→payoff traceability.
- [ ] 캐논 원장 누적(p0..p4 단계적 확장).
- [ ] 어려운 캐논 픽스처로 채점기 한계 깨기(경계 확정).
