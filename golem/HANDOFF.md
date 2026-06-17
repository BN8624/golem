# HANDOFF.md — golem 현재 위치와 다음 액션

## ▶ 새 세션 여기부터
- 읽는 순서: 이 파일 → **context-notes G53(정량1단계: B 0.762는 +2.9σ 단발)·G52(B완료+repr픽스)·G50(저합의 가드)** → 필요할 때만 `context-notes.md` 나머지(G25~G53) / `GolemStudioMode.md`(설계 정본) / `checklist.md`(진행).
- **지금 할 일 한 줄**: 정량 1단계 완료 = **B의 0.762는 재현 안 됨(N=1 운빨, +2.9σ). 진짜 B합의 = 0.63±0.04(N=6)**. 다음은 **baseline도 multi-seed**(RULE-10 상승 확립 여부) → Step2 동결합 다수 카드(재현성) → Step3 결합도 스윕(임계곡선).
- 정량 1단계(G53): combat 카드 multi-seed N=6 → 합의 **0.633±0.044**(min 0.565 max 0.685). G52의 0.762는 분포 밖 **+2.9σ 단발**. min 0.565 ≈ "RULE-10 박기 전" baseline 0.567 → **"0.567→0.762 상승" 서사는 과장, 상승 통계적 미확립**. 도구 `studio/multiseed.py`. 곁다리: 승격 누락된 `key_usage.py` 복사(코드0).
- B 결과(G52, ★N=1 주의): 계약 종료조건(RULE-10: tick 1000 무승부) 박고 oracle 비종료 7개를 draw로 손교정 → 합의 0.762 측정**(단발, G53서 +2.9σ 운빨로 판명)**. 2/3 저합의 가드가 SCN-003·008(0.6) 라이브 강등. **하네스 repr 버그**(oracle None/bool이 빌드 JS null/true와 거짓불일치) 발견·수정(`_js_scalar`).
- **프로젝트 승격 완료(2026-06-17)**: golem을 arag에서 독립 저장소로 분리(`C:\Users\USER\golem`). 둥지 구조(루트에 config 등 **5파일**[config·llm·observability·run_index·**key_usage**]+.env, 그 밑 `golem/`)라 코드 0수정. 셋업·구조·정본 규칙은 루트 `README.md`. arag/golem은 레거시로 남음(원본 삭제는 사용자 확인 후). 공유 파일은 **이 저장소가 정본**, arag와 따로 진화.
- T1 계측은 빌드 후 자동 기록: 실패 사전분류→`consensus.json`(failure_classes), AUTO 검증·되돌림→`reconcile_report.json`(auto_verification/low_consensus_guarded) + 카드별 `auto_fix_ledger.jsonl`. SUSPECT=confidently-wrong 후보, needs_rebuild=계약수정은 재빌드로만 검증.
- 키 사용은 사용자 명시 go 뒤에만(메모리 no-autostart-runs).
- 운영 가드레일은 context-notes **G46** 참조: v0.1 동결 아님(확장 유지) / 우선순위 T0→T1→T2(T2가 T0/T1 안 막음) / live build=build_graded.py / reconcile=Build↔oracle 슬라이스 / unique_issue_count는 lexical(방향성만) / --apply는 AUTO만.

## 지금 어디 (2026-06-17)

Golem Studio = `GolemStudioMode.md` §13 파이프라인을 실모델로 구축. 아이디어 한 줄로 **Step 1~7 전부 실제 완주**(방치형·발열 두 카드). 하네스는 계약구동으로 일반화돼 새 카드는 코드변경 0. 합의-vs-oracle 자동 해소(`reconcile.py`)+저합의 가드(G50)까지 갖춤. 산출물은 `golem/studio/`(패킷: 방치형=`*_packet`, 발열=`*_packet_heat`, **턴제전투(고결합)=`*_packet_combat`** 신규).

**B 도달점(G52)**: 고결합 카드에 계약 종료조건(RULE-10: tick 1000 무승부)을 박고 oracle 비종료 7개를 draw(tick=1000)로 손교정 → 합의 **0.567→0.762**, 비종료 tick 완전수렴(oracle 대비 tick 불일치 0). **frontier 핵심 질문("고결합도 계약 박으면 수렴하나")에 긍정 답** = 사다리 원리(G33~38) 재확인. 부수: 2/3 저합의 가드가 SCN-003·008(0.6) 라이브 강등(곁다리 실증), 하네스 repr 버그(oracle None/bool vs 빌드 JS null/true 거짓불일치) 발견·수정(`_js_scalar`). 잔여: 0.762는 완전수렴 아님(통과 5빌드 logs/winner 표기 잔차) + 게이트 5/11(JS 구문오류 6=생성품질 별개).

**T1 첫 측정(G51) 경위**: 결합밀도 저/중/고 3카드 측정 → 저·중 1.0, 고결합 0.567 붕괴(무한루프 타임아웃) + confidently-wrong AUTO 실측 → 저합의 가드 추가. 그 붕괴를 B(G52)가 해소.

| §13 단계 | 코드 | 산출/상태 |
|---|---|---|
| Step1 v0.1 Contract Microkernel | `contract_validator.py`·`replay.py` | replay 5/5(키0). `static_gate.py` src/ 확장(strict 모드 보유). |
| Step2 Planning | `planning.py` | A/B/C 측정 + synthesis. 방치형 FROZEN 계약 → `planning_packet/`. A6<B11<C27(독립리뷰>self·10>3). |
| Step3 Design | `design.py` | 4모듈 분해(utils←state_manager←engine←main)+traceability, §7·§8.2 PASS → `design_packet/`. |
| Step4 Spec QA | `specqa.py` | 11 시나리오 구체화 → `specqa_packet/`. SCN-006 오라클오류는 G36에서 교정(ACTIVE→PLAYING). 남은 결함: BLOCKING 해소 추적 안 됨(backlog). |
| Step5 Build v1 | `build_graded.py` | design 4모듈+시나리오+**합의 채점**(특권 golden 아님). `build.py`는 v0 스파이크로 잔존. |
| Step6 Adversarial QA | `adversarial.py` | 팀(lead+리뷰어8+synth)이 edge_cases 13+acceptance 5 → `adversarial_packet/`. 실측으로 EDGE-011(빈입력)·EDGE-012(미지id) 크래시 발견 → 계약 명문화(RULE-07+actions []디폴트, rung5)로 **둘 다 소거**, 유효빌드 edge 7/7 수렴. |
| Step7 Integration | `integration.py` | 수렴 빌드 재사용(키0) → 최종 workspace 선정+static_gate+golden 채점+final_report. **계약구동 일반화**(출력키=state_shape, adversarial 옵셔널). 방치형 24/24·발열 13/13. |
| 자동해소 | `reconcile.py` | Build 합의 vs golden **자동 diff(키0)** + 31B 진단(CONTRACT_AMBIGUOUS/ORACLE_BUG/BUILD_BUG)·AUTO/ESCALATE 분류 + `--apply`(AUTO만) + **저합의 가드(G50, 과반미달 AUTO→ESCALATE)** + AUTO검증/실패 사전분류(G49). T1 고결합서 confidently-wrong 차단 라이브 검증. |

**장르확장(다리실험, G41~44)**: 방치형 v1 → **발열/과열(결합 시스템)** 카드(`*_packet_heat`). 결과: ① 맞물림이 빌드 합의를 안 떨어뜨림(첫 런 1.0) — "결합=어렵다" 기각. ② 난이도가 *틱 순서 모호성*(관성·즉시)+*oracle 버그*로 이동 — 합의 1.0은 필요조건이지 충분조건 아님(독립 oracle 대조 필수). ③ 계약 한 줄 명문화로 완전수렴 합의를 의도값으로 이동시킴(B1→B2). 최종 발열 골든 13/13. ④ 하네스(build_graded·integration) 계약구동 일반화 → 새 카드 코드변경 0. ⑤ 수작업 diff/진단을 `reconcile.py`로 자동화.

**핵심 측정(G33·G34·G35)** — Build 합의(특권 golden 아닌 다수합의)로 "계약이 얼마나 빡빡한가"를 잰다. 한 번에 한 변수.
- 출력계약 미고정 → 합의 **0.36**.
- 출력계약 고정 → 합의 **0.66**, 게이트 3/11→8/11. 단 반쪽(빌드가 actions 미실행, turn:0 no-op 합의).
- 입력 스키마 고정(액션 키 `action`/`id`·`costMultiplier`·캐노니컬 디폴트) → 합의 **0.98**, 게이트 9/11. 진짜 수렴.
- 평가시점 명문화(RULE-05/06 시작+액션후 체크, WON시 중단) + SCN-006 ACTIVE→PLAYING → 합의 **1.0**, 게이트 11/11, 11빌드 expected 완전 수렴(G36). **사다리 0.36→0.66→0.98→1.0 = 계약 한 칸 박을 때마다 한 칸 수렴.**
- Step6 실측(G37): 수렴 빌드가 edge 대부분 일치하나 EDGE-011(빈 {})·EDGE-012(미지 id)에서 깨짐 → 두 구멍 지목.
- rung5(G38): 두 구멍 계약 명문화(RULE-07 + actions []디폴트) → acceptance 합의 **1.0 유지**, EDGE-011/012 **크래시 둘 다 0**, 유효빌드 edge 7/7 수렴. **adversarial이 찾은 구멍을 계약에 박을 때마다 싼 모델이 그 엣지에서도 수렴 — 사다리 검증 완결.**
- logs 채점(G39): 출력계약에 `logs:` 줄 추가 → acceptance 1.0 유지, EDGE-012 미지id 로그 2/11→**6/6 골든 수렴**. RULE-07 상태+로그 모두 채점·수렴. 교훈: 채점 표면(output contract)이 곧 측정 가능 범위.
- Step7 Integration(G40): 수렴 빌드 재사용(키0) E2E 완주 — 최종 attempt01(4모듈), static_gate PASS, **golden 24/24 PASS**(levels는 출력표면밖 표기). **아이디어 한 줄→Step1~7 전 파이프라인 실제 완주 도달.**

주의: Step4는 초안(결함 있음). `build_runs/`는 .gitignore(생성물). 결정·반박 로그는 context-notes G25~G51.

## 다음 액션

1. ~~(키0) AUTO검증+실패분류(G49)~~ · ~~T1 첫 스모크(G51)~~ · ~~저합의 가드(G50)~~ · ~~2/3 가드 강화~~ · ~~B 고결합(G52)~~ · ~~repr 픽스(G52)~~ · ~~프로젝트 승격(2026-06-17)~~ · ~~정량 1단계 B multi-seed(G53, 0.633±0.044)~~ — **전부 완료**.
2. **(★키, 1순위) 정량 판정 — baseline multi-seed** — RULE-10 박기 전 계약으로도 N=6 돌려, 0.633±0.044(박은후)와 **분포 비교**. G53서 min 0.565≈baseline 0.567이라 "상승" 미확립 → 두 분포 겹치나/갈리나로 RULE-10 효과를 정량 판정. (이게 G52 사다리 정성 결론의 운명 결정.)
3. (★키, 2순위) **Step2 동결합 다수 카드** — 새 고결합 카드 N장으로 0.633이 카드별 재현되나(분포 vs 우연).
4. (★키, 3순위) **Step3 결합도 스윕** — 저·중·고 각 다수 카드로 합의-vs-결합도 곡선·붕괴 임계.
5. (선택, 키0) B 잔차 분해 — 통과 빌드 logs/winner 표기 차이 들여다보기.
5. **코어 다음 frontier**(★키) — 자율 oracle(31B가 골든까지) × 고결합 카드 × reconcile calibration. UI/Asset/Renderer는 채점기반을 바꾸므로 **별도 트랙**(결정적 렌더 채점법 선결).
6. (backlog) levels 등 출력표면 확장 / adversarial validator BLOCKING 추적 / 발열 Adversarial QA·Integration 정식 완주.
