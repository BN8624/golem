# Atelier 체크리스트

## 코어 — 캐논 채점기 (frontier 1)

- [x] `auto_oracle.py` → `canon_check.py` 포팅 (캐논 위반 검출 + N시드·exact·recall·안정성·오탐).
- [x] 픽스처: `bible.json`(캐논 4규칙) + 깨끗한 초고 + 모순 심은 초고(골든 C1·C2) + `cases.json`.
- [x] 키 없는 `--replay`로 채점 배선 검증 → exact/recall/오탐 수학 정확 확인.
- [x] ★실제 31B 런(`--n 3`, atelier 11키) — **exact 1.0, 2/2 완전정확, 안정 1.0, 오탐 0** (canon-20260618-145250).
- [x] 어려운 픽스처(`fixtures_ko_hard`: 함의 위반 + 위반0 함정)로 한계 노출 — canon-20260618-170505 등.
- [x] 캐논/미학 경계 1차 결정: **검출(recall)은 한국어 함의로도 강함(C3·C6 1.0), precision(일치 방향
      판정)이 실한계**(trap "친누이"를 C2 위반으로 3/3 뒤집음). 프롬프트·few-shot 둘 다 불가역. 상세 context-notes.
- [x] rule_id 정규화 버그 픽스(`_norm_id`) + fp 진단 계측(`false_alarm_by_rule/_evidence`).
- [x] precision 한계 2패스 검증(`--verify`)으로 **깨짐**: trap 오탐 1.0→0, hard 검출 1.0 유지,
      전체 exact 1.0(canon-20260618-171503). precision은 모델 한계 아닌 단일콜 프레이밍 한계 — 검출/검증
      분리하면 풀림(콜 약 2배). **경계 재이동: precision도 기계화 가능.** 상세 context-notes.

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

## design 단계 (frontier 3) — setup→payoff 채점기

- [x] `design_check.py` 출범 — canon_check의 거울(모순 검출↔약속 미회수 검출). 추적 설정 목록 +
      비트시트 → 31B가 회수 안 된 설정을 짚나. 검출/검증 2패스 + N시드·exact·recall·오탐·안정성 그대로 재사용.
- [x] 심은 픽스처 `fixtures_design/`: outline.json(설정 S1~S5) + 클린(전부 회수) + 미회수(S2·S4 떨굼,
      골든) + cases.json + replay_demo.json. 미회수는 *언급은 하되 회수만 안 함*(노골적 부재 아님).
- [x] 키 없는 `--replay`로 채점 배선 검증 — exact/fp/fn/recall/안정성 수학 정확(`[S4]`→`S4` 정규화 포함,
      일부러 흔든 시드가 exact 0.67·S4 recall 0.667로 구분됨). design-20260618-192236.
- [x] ★실제 31B 런(`--n 3`·`--verify`) — design-20260618-193115/193408: exact **1.0**, S2·S4 recall 1.0,
      2패스도 1.0 유지(과교정 없음). 단 1패스가 이미 완벽해 2패스 측정 가치 0(canon hard2와 동일 상황) →
      어려운 픽스처 필요.
- [x] 31B 핀 가드 — canon_check·design_check 실콜 경로에 `GENERATOR_MODEL`·`CRITIC_MODEL`=31B 핀 +
      `ROLE!=critic` 가드. 26B 전수조사 호출 0 확인 뒤 잠복 위험 차단. (commit f567e0a)
- [x] design 생산자 `design.py`(planning의 거울): FROZEN 바이블 → lead 비트시트 → 10축 리뷰 → synthesis.
      출력 `outline.json`(premise + setups[{id,text}]) + `beatsheet.md` = design_check 입력 모양. 31B 핀 포함.
      키리스 `--replay` 통과 — BLOCKING 2 흡수, setups 5/beats 11, OUTLINE_STATUS FROZEN.
- [x] ★design 실생산(`--bible runs/bible_packet_ko/bible.json`, runs/outline_ko) — BLOCKING 5 흡수,
      setups 6/beats 10 FROZEN. 생산물을 design_check `--verify` 채점(golden=[]) → exact **1.0**/오탐 0/
      안정 1.0(design-20260618-195923). **생산자가 setup 6개 다 회수 + 채점기 동의 = planning→design→
      design_check end-to-end 닫힘**(canon-162900의 design판).
- [ ] 어려운 픽스처(회수를 정황에만 숨김 / 회수처럼 보이는 함정)로 2패스 한계 깨기.

## 이전 (frontier 2 마무리)

- [x] 2패스 스트레스 픽스처 `fixtures_ko_hard2/3` `--verify` 비교 측정 완료 — 과교정 없음 확정 +
      통사적 부정 한계 발견. HANDOFF·context-notes 참조.
- [ ] 캐논 원장 누적(p0..p4 단계적 확장).
- [ ] 어려운 캐논 픽스처로 채점기 한계 깨기(경계 확정).
