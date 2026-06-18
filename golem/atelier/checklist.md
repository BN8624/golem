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
- [x] ★실제 31B 런(영어) — BLOCKING 12 흡수 → canon 8 → FROZEN. 한 줄 아이디어가 실제로 자람.
- [x] ★한국어 출력 — LANGUAGE 프롬프트 박음. **빈 패킷 버그 재현 안 됨: synth 11키 병렬 0/11 빈패킷
      (단발 1 + 병렬 11 = 12/12 FROZEN, canon 5~7).** 코드 수정 없이 통과 → 그때 모델/서버 일시 상태로 판단.
      진단 덤프(`_synth_raw.txt`)는 안전망으로 유지(실패시만 작동, 무해). 측정 2026-06-18.
- [x] ★planning 바이블 → canon_check 실초고 채점 end-to-end(한국어, `fixtures_ko/`, canon-20260618-162900):
      clean exact 1.0/오탐 0, violation C1·C2 모두 1.0. **패러프레이즈 모순(왼손 고삐·피 안 섞인 남남)도 검출.**
      → frontier 1·2가 한 줄→바이블→채점으로 닫힘.

## 다음 (planning 검증 뒤)

- [ ] design 단계: 비트시트 + setup→payoff traceability.
- [ ] 캐논 원장 누적(p0..p4 단계적 확장).
- [ ] 어려운 캐논 픽스처로 채점기 한계 깨기(경계 확정).
