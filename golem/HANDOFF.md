# HANDOFF.md — golem 현재 위치와 다음 액션

## ▶ 새 세션 여기부터
- **▶ 트랙 C 본선 다음 동작 (G65, 로켓 실빌드 1단계 완료)**: build_graded --reconcile 완주 — 로켓 게임 코어 실제 생성·작동 확인. 산출물 `golem/studio/build_runs/graded-20260618-161312`(누적빌드 **첫 graded 카드**, .gitignore). 결과 = 게이트 7/11, 합의 0.881(SCN-001~005 6/7·SCN-006 7/7), **합의 vs oracle 전부 일치**(불일치 0→reconcile 진단 없음). Node 실측(키0)으로 6시나리오 직접 실행 = 대기권→궤도→달→화성, A겹 BEAT-1~4 발동·한국어 로그, SCN-004/005 WON. **트랙 C 1단계 세 목표(첫 graded·reconcile E2E·B겹 토대) 충족.** 배관 픽스(키0, 커밋됨): `specqa_packet_rocket/oracle_risk_review.json`(`risky_scenarios:[]`, build_graded.load_all 필수, 프로브 패킷에 빠져 있던 것).
- **▶ 트랙 C 2단계 — 서사 B겹(StoryForge) 완료 (G66)**: `storyforge.py` 신규 — concept→비트추출(키0)→바이블 생성(31B)→비트 대사 일괄(31B, 바이블 고정컨텍스트)→구조검증(키0). 로켓 4비트(대기권/궤도/달/화성) 대사 다 채움, **검증 3/3 PASS**, STORY_STATUS=COMPLETE. 바이블 일관(선장 에이든+AI 오리온, 지구→화성 이주). 산출물 `studio/storyforge_packet_rocket/`. **서사 2겹 닫힘**(A겹 발동 G65 + B겹 대사 G66). 규율 준수=텍스트 출력전용·검증 구조만.
- **▶▶ 새 세션 첫 동작 = 누적 빌드 첫 ★키 런 (G67, 배선 완료·키만 남음)**. 방향 확정(사용자 대화): "엔진 만드는 것 아니냐" 의문 정리 → 게임별 룰코어(O)·범용엔진 Godot(X)·그릇=웹(G2)·JS 한계는 비주얼/3D(범위 밖)뿐 → 누적 빌드로. **다음 명령(키 직전까지 키0 검증 다 통과)**:
  ```
  python golem/studio/build_graded.py --base golem/studio/rocket_base --packet golem/studio/planning_packet_rocket_v2 --specqa golem/studio/specqa_packet_rocket_v2 --reconcile
  ```
  실증 3가지: ① 편집 수렴(빌더가 scratch 아닌 *기존 코드 수정*으로 UPGRADE 얹나) ② **회귀 무결**(기존 SCN-001~006 출력 불변=안 깨졌나) ③ 새 기능(SCN-007/008 UPGRADE 골든 합의). 배선 = 레버1(코드주입)+2(편집모드 `_EDIT_HEADER`)+3(회귀=기존6+새2 동시채점). 키0 검증: 8시나리오 로드·편집헤더·기존코드 주입·RULE-06·출력계약 유지(새키 없음) 전부 OK.
- **▶ 누적 빌드 산출물(키0 준비 완료, 커밋됨)**: `studio/rocket_base/`(검증된 로켓 코어 4파일 스냅샷=영속 베이스) · `studio/planning_packet_rocket_v2/`(UPGRADE 카드 contract+concept, RULE-06=연료5→fuelRate 1→2, **state_shape 불변**) · `studio/specqa_packet_rocket_v2/`(8시나리오, 기존6 회귀 골든 불변 PASS 자가검증 + 새 SCN-007 turn8/fuel4/stage1·SCN-008 turn4/fuel4). `build_graded.py`에 `--base` 편집모드 추가.
- **▶ 누적 빌드 이후**: 레버4 선택적 컨텍스트(모듈만 주입=큰 게임 진짜 천장, §21.2-④). 곁 = combat 자율oracle / 외부리뷰 P1(#6·#4·#5·#10) / B겹 viewer 연결(완료, `rocket_viewer.html` 데모·미커밋). 설계 정본 = `GolemStudioMode.md` §21.
- **참고 — 로켓 게임성 한계(사용자 실플레이 피드백)**: 로켓 카드는 A겹 검증용 최소 프로브라 선택·트레이드오프·실패·idle 곡선이 0("연료 충전만 반복하면 화성"). 재미는 이 카드의 목적 아님 = 검증용으로 보존 합의. *재밌게* 만들려면 룰(contract)에 선택을 박아 재빌드해야 함(B겹 서사만으론 밋밋). 데모 산출물 `studio/rocket_viewer.html`(미커밋) = 빌드 산출물 엔진 로직 그대로의 이모지 모바일 뷰어, `python -m http.server`로 Tailscale 폰 접속 검증. 다음 카드 뷰어 템플릿으로 재활용 가능.
- 읽는 순서: 이 파일 → **context-notes 대화 G(방향 합의: 큰 게임·서사2겹·밸런스·스케일 — 정본 `GolemStudioMode.md` §21)·G64(self-suggest: 자율 oracle 루프 종결)·G63(eco 사다리 1.0·계약버그 탐지)·G62(고결합 자율oracle)·G61(사다리 0.879→1.0)·G60(프로브 0.879)·G57(외부리뷰 P0)·G50(저합의 가드)** → 필요할 때만 `context-notes.md` 나머지(G25~G64) / `GolemStudioMode.md` §21(확장 방향)·전체(설계 정본) / `checklist.md`(진행).
- **지금 할 일 한 줄**: 두 트랙 진전. **(A) 정량 트랙 종결(G53~58)**: 합의를 정하는 건 결합도 아니라 *계약 빡빡함, 단 규칙 종류 의존*(종료조항 올림 d≈3 4회재현 / PHASE 순서 안 올림 / 결합도 가설 기각 eco0.925 vs combat0.633). **(B) 자율 oracle frontier(G60~64) — 루프 닫힘**: 31B가 빌드 0줄로 골든 자율 생성(G60) → 어휘 박으니 1.0(G61) → 고결합 eco도 어휘+번식 박으니 1.0(G63, idle 동형) → **31B가 자기 불일치를 읽고 계약을 자율 처방, 박으니 1.0(G64)**. **생성→탐지→처방→수렴 = self-correcting 완결.** 핵심 = 결합도는 계산 안 깨뜨림(저/고 무관 1.0), 실패는 항상 계약 모호이고 박으면 닫힘. 도구 `studio/auto_oracle.py`·`studio/self_suggest.py`(키별 `key_accuracy_by_name` 봐야 함, 시나리오단위 0.0은 아티팩트). **(C) 서사 레이어 — 현재 라이브**: 큰 게임=결정적 시뮬/전략, 서사 2겹(A겹 발동로직=결정적 golden검증, B겹 텍스트=저작데이터), 텍스트는 출력전용. **로켓 카드 A겹 입증 완료**(auto_oracle events 6/6 1.0, turn 모호성도 RULE-05 핀으로 1.0/6/6 — 정본 §6.1 모호성 사전 등재). **트랙 A reconcile 자율 oracle 배선도 완료**(`reconcile.py --auto-oracle`, 손golden 대신 31B 자율생성, replay+라이브 6/6 검증). **다음(★키) = 트랙 C 본선: 로켓 실빌드(build_graded, design_packet 필요) → 이 한 런으로 ①누적빌드 첫 카드 ②reconcile 풀 E2E(Build합의 vs 자율oracle) ③B겹 대사 토대 동시 해결 → StoryForge 일관 바이블. 곁 = combat 자율oracle / 외부리뷰 P1(#6·#4·#5·#10)**.
- 정량 1단계(G53): combat 카드 multi-seed N=6 → 합의 **0.633±0.044**(min 0.565 max 0.685). G52의 0.762는 분포 밖 **+2.9σ 단발**. min 0.565 ≈ "RULE-10 박기 전" baseline 0.567 → **"0.567→0.762 상승" 서사는 과장, 상승 통계적 미확립**. 도구 `studio/multiseed.py`. 곁다리: 승격 누락된 `key_usage.py` 복사(코드0).
- B 결과(G52, ★N=1 주의): 계약 종료조건(RULE-10: tick 1000 무승부) 박고 oracle 비종료 7개를 draw로 손교정 → 합의 0.762 측정**(단발, G53서 +2.9σ 운빨로 판명)**. 2/3 저합의 가드가 SCN-003·008(0.6) 라이브 강등. **하네스 repr 버그**(oracle None/bool이 빌드 JS null/true와 거짓불일치) 발견·수정(`_js_scalar`).
- **프로젝트 승격 완료(2026-06-17)**: golem을 arag에서 독립 저장소로 분리(`C:\Users\USER\golem`). 둥지 구조(루트에 config 등 **5파일**[config·llm·observability·run_index·**key_usage**]+.env, 그 밑 `golem/`)라 코드 0수정. 셋업·구조·정본 규칙은 루트 `README.md`. arag/golem은 레거시로 남음(원본 삭제는 사용자 확인 후). 공유 파일은 **이 저장소가 정본**, arag와 따로 진화.
- T1 계측은 빌드 후 자동 기록: 실패 사전분류→`consensus.json`(failure_classes), AUTO 검증·되돌림→`reconcile_report.json`(auto_verification/**auto_summary**/low_consensus_guarded) + 카드별 `auto_fix_ledger.jsonl`. SUSPECT=confidently-wrong 후보, needs_rebuild=계약수정은 재빌드로만 검증. **auto_summary.green_blocked(=auto_suspect>0)면 ESCALATE 수와 무관하게 Green 금지**(G57 외부리뷰 #3).
- 키 사용은 사용자 명시 go 뒤에만(메모리 no-autostart-runs).
- 운영 가드레일은 context-notes **G46** 참조: v0.1 동결 아님(확장 유지) / 우선순위 T0→T1→T2(T2가 T0/T1 안 막음) / live build=build_graded.py / reconcile=Build↔oracle 슬라이스 / unique_issue_count는 lexical(방향성만) / --apply는 AUTO만.

## 지금 어디 (2026-06-18)

**현재 핵심(2026-06-18)**: 자율 oracle frontier 종결(G60~64, 루프 닫힘) → 서사 트랙 개시. 로켓 카드로 A겹(서사 발동층) 결정적 검증 입증, reconcile에 자율 oracle 배선 완료(트랙 A). **트랙 C 본선 착수(G65)**: 로켓 실빌드 1단계 design 완료(`design_packet_rocket` 4모듈·validator PASS), 다음 ★키 = build_graded --reconcile(위 ▶ 다음 동작 참조). 방향 정본 = `GolemStudioMode.md` §21(확장)·§6.1(모호성 사전). 아래는 그 이전 §13 파이프라인 배경.

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
2. ~~(★키) 정량 2단계 baseline multi-seed(G54)~~ — **완료. RULE-10 효과 확립**(d=2.71, p≈0.002, 분포 분리, 분산 5.3배↓). baseline 패킷 = `studio/planning_packet_combat_baseline`(RULE-10만 뺀 9 rules).
3. ~~(★키) Step2 새 고결합 카드 eco(G55)~~ — **완료. 결합도 가설 기각**: eco는 고결합인데 컴파일된 빌드 0.98 수렴(combat과 정반대). 단 표본수 오염으로 잠정. 패킷 `studio/*_eco`.
4. ~~(키0) 하네스 fix(G55)~~ — **완료**: `_canon`으로 스칼라+구조적 출력 repr 통일(build_graded·reconcile), consensus min-voter 가드(1표 자명합의 제외, 표본수 병기). reconcile replay 회귀 통과.
5. ~~(★키) eco cap=22 재측정(G55)~~ — **완료. 결합도 가설 기각 확정**: eco 0.925±0.054 vs combat 0.633±0.044(t=10.2, d=5.89, 분포 분리). cap11 0.983→0.925로 작은표본 인플레 잡힘(하네스 fix 실증).
6. ~~(★키) Step3 계약-타이트 스윕 1차(G56)~~ — **완료. 합의 곡선 단조 상승 재확인**: L0 0.37→L1 0.65→L2 0.80(같은 combat 카드, 현재 하네스 동일조건). 도구 `studio/sweep.py`, 럽 = baseline/combat/`*_combat_phased`(RULE-11 PHASE 순서). L0→L1(RULE-10) p=0.004 3번째 재현. **L1→L2(RULE-11)는 미확립**(p=0.148, L2 투표수↓ 소표본 인플레).
7. ~~(★키) Step3 스윕 cap↑ 재측정(G58)~~ — **완료. L1→L2 상승 아님으로 결판**: cap=22로 L2 투표수 5.71표(자명합의 소거)로 매칭하자 합의 0.640→0.607(Δ−0.03, p=0.69, 분포 겹침). G56의 0.80은 cap=11 소표본 인플레였음 확정. L0→L1(RULE-10)은 11표로 더 강한 4번째 재현(d=2.98). thesis 정정 = 사다리는 규칙 종류 의존(종료조항 올림, PHASE 순서 안 올림).
8. ~~(키0) 외부 코드리뷰 P0 4건(G57)~~ — **완료**: #1 build.py legacy 경고·#3 AUTO suspect 롤업+Green게이트·#7 planning_compare 경고·#9 schema(이미 됨). P1 5건(#8·#6·#4·#5·#10)은 다음 실험 전 백로그(checklist).
9. ~~(★키) 자율 oracle 프로브 1차(G60)~~ — **완료. 31B 자율 oracle 정확률 0.879**(완전정확 9/11, 안정성 0.94). 결정적 산술 11/11 무결, **두 실패 다 계약-모호(enum 라벨·빈 dict 관례)** = reconcile CONTRACT_AMBIGUOUS 표면. 자율 oracle 가능 + 불일치=공짜 모호탐지기. 도구 `studio/auto_oracle.py`.
10. ~~(★키) 자율 oracle 사다리 — 어휘 박고 재측정(G61)~~ — **완료. 0.879→1.0 수렴**: G60이 짚은 두 모호성(gameStatus enum·levels 빈dict)을 RULE-08 한 줄로 박으니 11/11 완전정확·안정성 1.0(골든 무변경=1변수). 빌드합의 사다리(G33~38)의 자율-oracle 판 확립 — 자율 oracle은 viable + self-correcting. 변형 패킷 `studio/planning_packet_idle_vocab`.
11. ~~(★키) 고결합(eco) 자율 oracle(G62)~~ — **완료. 결합 무관, 실패는 또 전부 계약-모호.** 키별 entities 0.875(다개체 시뮬 7/8 완벽)·status 0.0(enum 어휘, 골든 'FINISHED' vs 31B success/completed…). SCN-004만 entities 0/3=번식 규칙 모호(빌드합의 잔차 재발견). **결합도는 계산 안 깨뜨림, 미명세 계약만 깨뜨림**(G60~62 통합). 하네스에 `key_accuracy_by_name` 추가(시나리오단위 0.0은 아티팩트).
12. ~~(★키) eco 어휘+번식 박고 재측정(G63)~~ — **완료. 0.875/0.0 → 1.0 완전수렴**: G62가 짚은 status enum·SCN-004 번식 두 모호성을 변형 패킷 `studio/planning_packet_eco_vocab`(골든 무변경=1변수)에 박으니 8/8 완전정확·안정성 1.0. 고결합서도 사다리 닫힘 = G61(idle) 동형. 부수: 원문 PHASE4가 골든과 모순이었음(자격=tick시작 energy, 자식 energy=부모 cost차감 후)을 골든 역산으로 잡아 자율 oracle이 enum 너머 계약버그까지 탐지함을 실증. 키0 로컬 시뮬로 8/8 골든 재현 자가검증 후 측정.
13. ~~(★키) 31B self-suggest(G64)~~ — **완료. 자율 oracle 루프 완전히 닫힘**: 31B가 자기 불일치(G62 eco 런)를 읽고 세 모호성(status·movement클램프·번식) 다 진단 + 처방 자율생성 → 박은 패킷 `studio/planning_packet_eco_selfsug` auto_oracle 1.0/8/8. 번식은 사람(G63)보다 우아하게 PHASE 순서만 바꿔 해결. 도구 `studio/self_suggest.py`. 생성(G60)→탐지(G62)→처방(G64)→수렴 = self-correcting 완결.
14. ~~(★키) 로켓 A겹 가능성 프로브~~ — **거의 완료. A겹 작동 입증**: 방치형 로켓 카드(`studio/planning_packet_rocket`+`specqa_packet_rocket`) auto_oracle에서 **events(BEAT-N 발동) 키 전 시나리오 3/3** — 결정적 엔진에 서사 발동층 붙여도 31B가 정확 계산. 부수발견: 첫판 SCN-004/005(WAIT×150=154스텝)가 전키 0.0 붕괴 → **손계산 스케일 한계**(oracle가 머리로 150틱 못 셈, 게임 결함 아님). cost 축소로 18/22스텝 재설계하니 0.945, **events 키 6/6 전부 1.0**(fuel·stage·gameStatus도 1.0) = A겹 가능성 입증. 유일 흠 SCN-003 turn 0.667을 파보니 **또 계약 모호**(한 시드가 turn=7=ADVANCE도 카운트 — RULE-01/02가 "ADVANCE는 turn 안 올림" 미명세) — 산술지터 아님. RULE-05에 turn 정의 박으니 **1.0/6/6 완전수렴**(turn 3/3 회복) — 로켓 위 미니 사다리(탐지→진단→핀→수렴). 종류는 모호성 사전(GolemStudioMode §6.1) "카운터 증가 의미"로 등재 = 반응적 핀→사전 차단 전환.
15. ~~(★키) 트랙 A — reconcile 자율 oracle 배선~~ — **코어 완료**: `reconcile.py`에 `--auto-oracle` 추가 — oracle 다리를 손golden(`sc["expected"]`) 대신 31B 자율생성(`fill_auto_oracle`→`auto_oracle._ask_oracle`)으로. 손-oracle 없이 Build합의 vs 자율oracle로 모호성 탐지. `--apply`는 자율 모드서 ORACLE_BUG 미적용(생성값을 golden으로 안 박음), CONTRACT_AMBIGUOUS 핀만. report에 `oracle_source`. 검증: replay 회귀(키0) 그린 + `fill_auto_oracle` 라이브 로켓 6/6 골든 일치. **잔여 = 풀 E2E(Build합의 vs 자율oracle)는 graded 빌드 런 필요**(현재 build_runs에 graded 0개) → 트랙 C에서 카드 실빌드할 때 자연 합류. combat 자율oracle은 곁.
16. ~~(★키) 트랙 C 본선 — 로켓 실빌드(build_graded --reconcile)~~ — **완료(G65)**: 게이트 7/11, 합의 0.881, 합의 vs oracle 전부 일치. Node 실측으로 게임 실작동(A겹 BEAT-1~4 발동, 대기권→화성, SCN-004/005 WON). 첫 graded 카드 `build_runs/graded-20260618-161312`. 트랙 C 1단계 세 목표 충족.
17. **(다음, ★키) 트랙 C 2단계 — 서사 B겹**: 로켓 B겹(대사 텍스트, BEAT-N 키에 별도 파일) → StoryForge 일관 바이블. + 누적 빌드 레버(코드 주입·편집·누적회귀·선택적 컨텍스트). **설계 정본 = `GolemStudioMode.md` §21·§6.1(모호성 사전)**, 결정 이유 = context-notes 대화 G. 사람 몫=아트·텍스트 질·재미 취향, 진짜 천장=선택적 컨텍스트. UI/Asset/Renderer는 별도 트랙.
18. (backlog) levels 등 출력표면 확장 / adversarial validator BLOCKING 추적 / 발열 Adversarial QA·Integration 정식 완주.
