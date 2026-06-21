# golem 체크리스트

## Golem Studio 파이프라인 §13 (Step 1~7 완주, 2026-06-17)
세부 측정·결정은 context-notes G25~G44, 현재상태·다음할일은 HANDOFF.md.
- [x] Step1 Contract Microkernel Replay (`contract_validator.py`·`replay.py`, replay 5/5, 키0)
- [x] Step2 Planning (`planning.py`, A/B/C + synthesis, FROZEN 계약)
- [x] Step3 Design (`design.py`, 4모듈 분해 + traceability)
- [x] Step4 Spec QA (`specqa.py`, 시나리오 구체화. SCN-006 오라클오류 G36 교정. BLOCKING 추적은 backlog)
- [x] Step5 Build v1 (`build_graded.py`, 합의 채점. 사다리 0.36→0.66→0.98→1.0)
- [x] Step6 Adversarial QA (`adversarial.py`, edge_cases 능동탐색 → EDGE-011/012 발견 → 계약 명문화로 소거)
- [x] logs 채점 갭 해소 (출력계약에 logs 줄 추가, RULE-07 로그 6/6 수렴)
- [x] Step7 Integration (`integration.py`, 최종 workspace 선정+static_gate+golden 채점+final_report. 방치형 24/24)
- [x] 장르확장 다리실험 — 발열/과열(결합) 카드: 합의 1.0, 골든 13/13. "결합=어렵다" 기각, 난이도는 틱 모호성·oracle 버그로 이동
- [x] 하네스 일반화 — build_graded·integration 계약구동(출력키=state_shape, 입력=시나리오 예시). 새 카드 코드변경 0
- [x] 자동 해소 루프 (`reconcile.py`) — 합의-vs-oracle 자동 diff + 31B 진단(AMBIGUOUS/ORACLE_BUG/BUILD_BUG)·AUTO/ESCALATE. diff/resolve/apply 검증 + 실측 1건
- [x] 외부 지적 수용분 하드닝(G45, 키0) — 합의-vs-oracle 자동diff wired / fixture 6종(replay 11/11) /
      module.exports.prop 미인식 버그 수정 / unique_issue_count lexical 라벨 / validator 정본+schema drift 경고 /
      path escape guard / assumptions·backlog 영속화 / FAILURE_TAXONOMY 통합 인벤토리(난립 방지, 매핑표 아님)
- [x] T0 reconcile 자동연결(G47, 코드 키0) — build_graded --reconcile/--apply: diff→resolve→AUTO적용→ESCALATE/BUILD_BUG 리포트. ESCALATE 자동적용 금지, BUILD_BUG는 재빌드 권장만
- [x] (T1 전, 키0) AUTO 정확률 검증 로그 + 실패 사전분류(HARNESS/INFRA vs 카드/계약)를 reconcile/build_graded에 추가(G49) — `verify_auto_fixes`(다운스트림 일관성·needs_rebuild·카드별 ledger 되돌림감지) + `classify_attempt_failure`(INFRA/HARNESS/CARD, 기존 라벨 재사용·난립 없음). worker가 하네스 크래시 잡아 HARNESS로 기록(런 안 깨짐). 단위검증 PASS, replay 무회귀
- [~] **T1 일반화 실험(설계=G48)** — 첫 N=3 정성 스모크 완료(G51, ★키). 저(방치형 9/11·합의1.0)·중(발열 8/11·합의1.0) baseline diff 0. 고(턴제전투 신규 `*_packet_combat` 6/11·**합의 0.567**) 붕괴 → confidently-wrong AUTO 실측 → **저합의 가드(G50)** 추가·라이브 검증(저합의 AUTO 3건 ESCALATE 강등). 근본=계약 종료조건 부재(reconcile ESCALATE가 지목). 남은 것 ↓
- [ ] (새 세션, ★키) **B: 고결합 카드에 계약 종료조건 박고 + oracle 교정 후 재빌드** — 합의 0.567 오르나(사다리 수렴 검증). specqa 재생성으로 `*_packet_combat` oracle 원복부터. **측정 본질로 우선.**
- [ ] (새 세션, 키0) 저합의 가드 임계 강화 — 과반(>0.5)→절대다수(2/3↑). SCN-009(0.6) 같은 무한루프값 통과 빈틈 차단(G50)
- [x] 정량 1단계 — B카드 multi-seed N=6 → 합의 0.633±0.044, **G52의 0.762는 +2.9σ 단발(재현X)**(G53, `studio/multiseed.py`). 곁다리: 승격 누락 `key_usage.py` 복사.
- [x] 정량 2단계 — baseline(RULE-10 전) multi-seed N=6 → **RULE-10 효과 확립**: base 0.421±0.102 vs post 0.633±0.044, t=4.69 p≈0.002, d=2.71, 분포 분리, 분산 5.3배↓(G54). 사다리 방향 맞고 G52 두 숫자는 고점 운빨. baseline 패킷=`studio/planning_packet_combat_baseline`.
- [x] 정량 3단계 — 새 고결합 카드(eco 생태계) 풀 파이프라인+multiseed → **결합도 가설 기각**: eco는 고결합인데 컴파일된 빌드 0.98 수렴(combat과 정반대). 합의를 정하는 건 결합도 아닌 계약 빡빡함(G55). 단 측정함정 2건(표본수 오염·repr 재발)으로 0.98은 잠정.
- [x] (키0) 하네스 fix — `_canon`으로 스칼라+구조적출력 repr 통일(build_graded·reconcile, B) + consensus min-voter 가드/표본수 병기(A). reconcile replay 회귀 통과(G55).
- [x] (★키) eco cap=22 재측정 — 평균 7표로 맞춰 **결합도 가설 기각 확정**: eco 0.925±0.054 vs combat 0.633±0.044, t=10.2 d=5.89 분포 분리. cap11 0.983→0.925로 작은표본 인플레+0.057 잡힘(하네스 fix 실증)(G55).
- [ ] (★키) Step3 결합도(=계약 타이트) 스윕 — 계약 빡빡함 축으로 합의 곡선·붕괴 임계
- [ ] (백로그) eco 잔차 분해(0.925≠1.0, SCN-004 번식) / 자율 oracle(31B가 골든까지)
- [ ] 코어 다음 frontier = 자율 oracle × 고결합 카드 × reconcile calibration (UI/Asset는 별도 트랙, 결정적 렌더 채점법 선결)
- [ ] (backlog) levels 등 출력표면 확장 / adversarial BLOCKING 추적 / 발열 Adversarial QA·Integration 정식 완주

## (완료 기록) Golem Studio v0.1 Contract Microkernel Replay (2026-06-17)
- [x] `GolemStudioMode.md` 13장 구현 우선순위와 19장 Pending Decisions 재확인
- [x] `static_gate.py` 현재 CLI/함수 구조 확인 (평면 glob → src/ 못 봄 확인)
- [x] `golem/studio/schemas/module_manifest.schema.json` 작성 (v0.1 최소 필드, stdlib 손검증)
- [x] `golem/studio/fixtures/demo_pass/module_manifest.json` 작성 (runs/는 gitignore라 fixtures/로)
- [x] demo workspace CommonJS fake files 작성 (main.js + src/engine·state·movement.js)
- [x] import/export validator 작성 (`contract_validator.py`, checks 4종)
- [x] static_gate bridge 연결 (PENDING-003 I/O 계약)
- [x] static_gate.py src/ 지원 확장 (rglob+경로해소, 하위호환)
- [x] 음성 픽스처 4종 (export불일치·파일누락·순환·bare default)
- [x] `replay_result.json` 생성
- [x] `contract_validation_report.md` 생성
- [x] Gemini/Gemma API 호출 0회 확인
- [x] 검증: replay 5/5 통과, static_gate 무회귀(기존 평면 게임 ok:true 유지)

## Step 2 — Planning A/B/C 측정 (하니스 빌드+replay 완료, 실키 발사만 go 대기)
- [x] `planning.py` — A(self-review)/B(1+3)/C(1+10) arm, 리뷰어 키 병렬, dedup 메트릭(unique/dup_rate/blocking)
- [x] A안 정의 = lead 자기검토(self-review, 편향) → A/B/C가 "독립리뷰가 self-review 이기나" 측정
- [x] 리뷰 스키마(§6)·10축(§2.2)·PENDING-004 판정(§19) 반영
- [x] fake 픽스처 replay 검증 — 의도적 중복으로 dedup 작동 확인(A2<B6<C12 unique, dup 0.077), API 0회
- [x] (★키) `planning.py --idea 방치형게임` 실측 — A6<B11<C27 unique, 독립리뷰>self·10>3 둘 다 임계 통과(G27)
- [x] (★키) synthesis 추가 + 실발사 — BLOCKING 11→0, 부동소수점 floor() 못박음, 계약 FROZEN(G28). 패킷=planning_packet/
- [x] (키X) dedup 토큰 Jaccard 클러스터링 — 결론 강건성 확인(임계 무관 A<B<C). 진짜 의미 dedup은 보류(G29)
- [x] (★키) Build v0 `build.py` — FROZEN 계약 → gemma 구현 → static_gate+v0.1 정합+스모크. 방치형 cracked@4 10/11(G30)
- [x] (점검) §13 순서 어긋남 발견 — 1,2 후 5(Build)로 점프, 3·4 건너뜀. design.py import 버그 수정. 순서 복원(G31)
- [x] (★키) Step 3 Design `design.py` — 방치형 4모듈 분해(utils←state_manager←engine←main), RULE 6개 traceability, §7·§8.2 PASS. design_packet/

## §13 순서 — 남은 단계
- [x] (★키) Step 4 Spec QA `specqa.py` — 11 시나리오 구체화·RULE 6개 커버·오라클위험 표시. 단 초안(결함: ACTIVE 오라클오류·float경로 미검·BLOCKING 추적안됨 G32). 사용자: 초안으로 두고 진행
- [x] (★키) Step 5 Build v1 `build_graded.py` — design 4모듈 + specqa 시나리오 + 합의 채점. contract_validator에 strict 모드 추가(빌드=느슨, v0.1 5/5 무회귀). 게이트 3/11, **합의 0.36**(G33)
- [x] 발견: 출력 계약 미고정 → 빌드가 무슨 key 찍을지 제각각(undefined 버그 포함). 합의 채점이 "스펙 안 빡빡"을 특권golden 없이 잡음
- [x] (★키) 한 변수 실험 — 출력 계약 고정(4 key) → 합의 0.36→0.66, 게이트 3→8/11(G34). 방향 확인
- [x] 점검: 0.66 반쪽 — 빌드가 시나리오 actions 미실행(turn:0/undefined). 입력 스키마 미고정이 남은 원인
- [ ] (다음, ★키) 입력(시나리오) 스키마 고정 → 빌드가 actions 실행 → 합의 재측정(0.66→?)
- [ ] (★키) Step 6 Adversarial QA — edge_cases.json + acceptance draft 다듬기(ACTIVE)
- [ ] (backlog) specqa validator 강화(계약 외 상태값 거부+BLOCKING 해소 추적) / 측정 N≥10 장르확장

## 과거 히스토리

### Phase 0 — 셋업
- [x] 이름·폴더 확정 (golem, `arag/golem/`)
- [x] node 가용성 확인 (v24.15.0)
- [x] 플랜/체크리스트/컨텍스트노트 생성
- [x] 스케줄러 스펙 한 장 (후속 실험에서 대체됨)

### Phase 1 — 전투엔진 JS 스파이크 (T-000012 JS판, 4 고정 시나리오) — 완료
- [x] make_golden.py — game/로 시나리오 파티+정답 생성·검증 (4/4 골든 일치)
- [x] grade.py — node main.js --scenario N 출력 vs 골든 정확일치 + 첫불일치 (스모크 검증)
- [x] worker_prompt.py — PAMPHLET 규칙+고정파티+출력계약 (정답 비노출)
- [x] driver.py — 키 11개 병렬 select-best(워커=키) + --replay 점검모드 (plumbing 검증)
- [x] 스파이크 실행 — 런 20260616-130305, **cracked@10, 11시도 중 5통과**, 총 $0.031
- [x] 통과본 독립 재채점 — attempt01·10 둘 다 4/4 정확일치 (우연 아님 확인)
- [x] 통과본 검수 — 4파일 304줄, 껍데기·미사용 import 없음, 스케줄러 레퍼런스 일치 → 재작성 불필요

### 판단 기준 — 결과
- gemma JS 엔진이 4 시나리오 골든 정확일치하나 → **됨**. cracked@10 (Python T-000012 cracked@2 대비 더 어렵게 걸림, 통과율 5/11).
- Claude가 packet/diff만으로 얕게 끝내나 → **아니오**. 4파일 전부 읽고 로직 추적, 품질 양호 확인.
- 실패 6개 패턴: 시나리오1 턴 카운트 ±오차 4개(턴 스케줄러 frontier 동일) + require 경로 깨짐 2개.

### Phase 2 — 표현층 바인딩 (사용자 선택: 실용)
- [x] `golem/web/engine.browser.js` — 검증엔진(attempt10) 무수정 로직 + trace. 공유 모듈(browser+node).
      **표현층(스킨)이 갈아끼우는 단일 진실원.** 룩이 바뀌어도 이 파일은 안 바뀜.
- [x] `golem/web/battle.html` — 공유엔진 + **이모지 스킨**. 캐릭터 이모지·공격 들썩·피격 흔들림·
      데미지 숫자 플로팅·스킬 아이콘·HP/gauge바·상태배지·승자배너. 폰 세로. 스킨=SKIN 객체 한 곳.
- [x] `golem/web/samples.html` — 룩 비교 목업(A 이모지 / B 레트로도트 / C 네온). 사용자가 **A 이모지** 선택.
- [x] `golem/web/_verify.js` — 공유엔진 vs 골든 무회귀 가드. **4/4 PASS** (이모지 개편 후 재확인).
- [x] 아이폰 확인 — 테일스케일 `http://100.89.73.83:8731/golem/web/battle.html`로 폰 접속 OK.
- [ ] (선택) 다른 스킨(레트로/네온) 추가 시 SKIN을 스킨객체 배열로 승격 + 셀렉터. 지금은 이모지 1종.
- [ ] (선택) 인터랙티브화 — 스킬 선택 플레이는 엔진 변경(메카닉 확장)이라 골든 재검증 필요.

### Phase 3 — Game Bank + A 오라클 (검증엔진 라이브러리)
방향(사용자 2026-06-16): A 방식(Claude 레퍼런스 오라클)으로 여러 게임을 만들어 DB(은행)에 쌓고,
베이스로 확장. 단계 = 1)은행+A골격(키X) 2)새 게임 1개 생성(런·go필요) 3)확장 루프(런).
#### 1단계 — 은행 + A 파이프라인 골격 (키 안 씀) — 완료
- [x] `game_bank.py` — sqlite 카드 은행(스키마 + save/get/list). 카드 = 규칙·시나리오·골든·솔루션·레퍼런스.
- [x] `oracle.py` — JS 레퍼런스 impl → 골든 생성(grade 러너 재사용). **game/ 의존 제거 = A경로 핵심.**
- [x] `bank_init.py` — 카드 #1 "tempo-combat" 적재(규칙=RULES, 시나리오=golden/, 솔루션=attempt10).
- [x] 무회귀: oracle로 솔루션에서 골든 재생성 → 저장 골든 4/4 일치(game/ 없이 골든 나옴 증명).
- [x] driver/worker_prompt/grade 카드 파라미터화(`--card slug`, 기본값 유지). replay 양쪽 PASS, 프롬프트 동일.
- [x] `game_bank.sqlite` gitignore(바이너리·재생성 가능).
#### 2단계 — 새 게임(2048류 합치기 퍼즐) A 생성 (준비=키X 완료, 런=go필요)
- [x] 입출력 일반화 — 골든=평면 `key:value` dict 정확일치(전투의 winner/turns/hp도 자연 포함),
      입력=임의 JSON. grade/oracle/worker_prompt/driver 게임-중립화. **새 게임이 강제한 일반화.**
- [x] 카드#1 무회귀 — 일반화 후 bank_init 재적재, 솔루션 여전히 4/4 PASS.
- [x] 카드#2 "merge-2048" — Claude 결정적 2048 레퍼런스(board/moves/main.js)+규칙+4시나리오 →
      oracle 골든 → 적재. 레퍼런스 self-채점 PASS. 골든 손검산 OK(sc1 L→4·sc2 L→12 등).
- [x] **생성 런** `driver.py --card merge-2048` (런 20260616-143058) — **cracked@4, 11/11 전부 통과**,
      $0.027. attempt04 독립 재채점 4/4 정확일치(멀티파일 board/moves/main 157줄). 통과본=카드 solution 갱신.
      → **A 방식이 처음 보는 게임(2048)에도 됨 확정.** 전투(5/11)보다 깔끔 — 규칙이 명확할수록 잘 됨.

#### 3단계 — 확장 루프 (준비=키X 완료, 런=go필요)
선택 메카닉 = 2048 + 벽(장애물). 베이스 solution을 워커에 줘 "맨바닥 대비 확장이 싸게 되나" 측정.
- [x] 베이스 주입 경로 — worker_prompt.build_prompt(base_files=), driver `--base <slug>`.
- [x] 카드#3 "merge-2048-walls" — 확장 레퍼런스(moves.js만 벽 세그먼트화)+전체 규칙+4 벽시나리오 →
      oracle 골든. self-채점 PASS, 골든 손검산 OK(sc1 [2,-1,2,2]L→2,-1,4,2 등).
- [x] 확장 프롬프트 점검 — BASE IMPLEMENTATION(베이스 코드)+벽 규칙 포함(8966자).
- [x] **확장 런** `driver.py --card merge-2048-walls --base merge-2048` (런 20260616-144906) —
      **cracked@7, 11/11 전부 통과**($0.030). 맨바닥 2048(11/11)만큼 깔끔. 통과본=카드#3 solution.
      **재사용 증거**: attempt07이 board.js를 베이스 그대로(24줄 동일) 두고 moves.js만 벽 세그먼트로
      키움(67→99) + main.js 벽시나리오. = 맨바닥 재작성 아닌 진짜 확장. → **확장 루프 됨 확정.**

### Phase 4 — 자율 오라클: 31B가 골든까지 만든다 — 작동 입증
지금은 Claude가 오라클을 짰다. 사용자 제안 = 주제+최소규격만 주고 31B가 오라클 설계. 핵심 리스크 =
오라클 신뢰(출제=응시 같은 모델). 해결 = 오라클도 게이트(독립 gemma 합의).
- [x] `oracle_design.py` — 31B에 [주제+메타규격(META)] → 규칙·레퍼런스·시나리오 설계. 파싱+정적점검
      (멀티파일·Math.random없음·node실행·key:value)+oracle 골든화+카드 적재.
- [x] **자율 설계 런** (theme=Snake) — 31B 첫 시도 성공: game.js/main.js, 골든 생성. $0.003.
      규칙 2342자(좌표계·벽/자기충돌·먹이 리스폰·꼬리순서 명세). 카드 'snake-auto'.
- [x] **합의 검증 게이트** `driver --card snake-auto` — 독립 11개 중 **10/11 합의**(31B 골든과 정확일치).
      실패 1 = 출력형식 실수(규칙 해석 아님). 죽는 시나리오 포함 일치 → 모호점도 합의 안 깸. $0.021.
      → **자율 오라클 작동 확정**(강신뢰 과반 크게 넘음). 통과본=snake-auto solution.
- 결론: 31B가 게임+오라클을 스스로 설계 + 독립 합의 게이트가 신뢰 보증. golem 자율화 핵심 입증.

### Phase 5 — 랜덤 주제 대량 측정 캠페인 후보
메커니즘 입증됐으니 주제를 계속 바꿔 대량으로 돌려 측정. 측정축 = 주제별 오라클 생성 성공률 /
합의율 분포(명확↔모호) / 자율 신뢰 통과율 = **무료모델×자율오라클 한계 지도**. ⚠️대량 키 소비 =
사용자 명시 지시+사전 점검 필수. 현재 다음 작업은 아님.

## Golem Studio Mode 문서 정리 (2026-06-17)
- [x] `11명/팀원` 표현을 `11 worker slots/병렬 샘플링 슬롯`으로 재정의
- [x] v0.1 구현 범위를 Contract Microkernel Replay로 축소
- [x] 질문 등급, 변경 등급, deprecation, Spec QA/Adversarial QA, JSON traceability, 롤백 분류 반영
- [x] 문서 내부 충돌 표현 재검색
- [x] 문서 검증 결과 보고

## Golem Studio v0.1 Pending 기본값 정리 (2026-06-17)
- [x] v0.1 JS module format을 CommonJS only로 고정
- [x] module_manifest v0.1 최소 필드 예시 추가
- [x] static_gate bridge 입력/출력 JSON 기본값 추가
- [x] A/B/C 비교 provisional threshold 추가

## Golem Studio 선회 핸드오프 정리 (2026-06-17)
- [x] HANDOFF의 예전 생산 분할 Step 1 예정분 폐기 표시
- [x] 다음 작업순서를 Contract Microkernel Replay 기준으로 재작성
- [x] CLAUDE.md와 GolemStudioMode.md 충돌 여부 점검
- [x] 필요한 CLAUDE.md 우선순위 규칙 최소 반영
- [x] 문서 재검색 및 커밋

## 외부 코드리뷰 12항목 분류·수행 (2026-06-17, 키0) — 결정이유 context-notes G57
P0 (지금, 완료):
- [x] #1 build.py LEGACY 경고 배너(라이브 금지, build_graded.py 정본)
- [x] #3 AUTO suspect 롤업(`summarize_auto_verification`) + Green 게이트(`auto_suspect>0→green_blocked`) — reconcile.py·build_graded.py
- [x] #7 planning_compare.md lexical heuristic 경고 배너
- [x] #9 schema 정본 — `_schema_drift()`로 이미 구현됨 확인(추가작업 불필요)
- [x] 검증: import OK + 헬퍼 스모크 + reconcile replay 회귀 통과

P1 (다음 실험 전):
- [~] #8 실측 실패 fixture — `demo_fail_syntax_error` 추가(스윕 최다 실측 실패=구문오류, replay 11→12 green). 고아·미도달은 기존 unreachable_module/missing_file이 이미 커버. 남음: output-surface-skip(consensus 채점 fixture = replay 밖 별도 하네스)
- [ ] #6 failure taxonomy 인벤토리(기존 라벨 정리 후에만 신규도입 + 라벨별 액션)
- [ ] #4 Integration final_report 위험지표(auto_suspect·low_consensus_guarded·output_surface_skip) — frontier 부를 때
- [ ] #5 Spec QA expected_confidence — 소비처 동시 배선 조건
- [ ] #10 ASSUMED/DEFERRED 소비처 배선 — 생산자 확인 후

기각·보류:
- [x] #11 전면 포맷 커밋 — 기각(병리적 아님, blame 파괴 비용>효용)
- [x] #2 build_graded 분해 — 보류(363줄, 성장 금지 가드레일만)
- [x] #12 package화 — 보류(둥지 구조는 의도된 선택, P2)

## 자율 oracle frontier (2026-06-18, ★키) — 결정이유 context-notes G60~G62
도구 `studio/auto_oracle.py`(31B가 빌드 0줄로 rules+입력만으로 골든 자율 생성 → 키별 _canon 대조).
- [x] G60 프로브 1차(방치형): 정확률 0.879, 두 실패 다 계약-모호(enum·빈dict) = 공짜 모호탐지기
- [x] G61 사다리: 어휘 RULE-08 한 줄 박으니 0.879→1.0 수렴(변형 패킷 planning_packet_idle_vocab)
- [x] G62 고결합(eco): 결합 무관(entities 7/8 무결), 실패는 또 계약-모호(status enum 8/8 + SCN-004 번식)
- [x] 하네스: key_accuracy_by_name 추가(시나리오단위 0.0은 uniform 모호키 아티팩트)
- [x] G63 eco 어휘+번식 박고 재측정: 0.875/0.0 → 1.0/8/8(변형 패킷 planning_packet_eco_vocab), 원문 PHASE4↔골든 모순까지 탐지
- [x] G64 self-suggest: 31B가 자기 불일치 읽고 계약 자율 처방 → 1.0/8/8(도구 self_suggest.py, 패킷 eco_selfsug), 루프 종결
- [ ] (다음) 트랙 A: reconcile에 자율oracle+self-suggest 배선(=실질 마무리) / combat 자율oracle(곁)

## 확장 방향 — 큰 게임/서사/밸런스 (2026-06-18, 대화 G) — 정본 GolemStudioMode.md §21, 이유 context-notes 대화 G
- [x] 방향 합의: 큰 게임=결정적 시뮬/전략(코에이식), 서사 2겹(A겹 발동로직/B겹 텍스트), 밸런스=config분리, 스케일=모듈+선택적컨텍스트
- [x] 로켓 카드 키0 준비(planning_packet_rocket+specqa_packet_rocket, A겹=BEAT-N), 골든 로컬 시뮬 자가검증
- [x] 로켓 A겹 가능성 입증: 0.945, events 키 6/6 전부 1.0(fuel·stage·gameStatus도 1.0). 손계산 스케일 한계 실측(150틱 붕괴→18틱 재설계로 회복)
- [x] SCN-003 turn 0.667 파보니 산술지터 아니라 계약모호(ADVANCE도 turn 올리나 미명세) → RULE-05에 turn 정의 핀 → 1.0/6/6 완전수렴
- [x] 모호성 종류 사전 신설(GolemStudioMode §6.1): G60~64 실측 6종(enum·컬렉션·경계·순서/타이밍·카운터·빈입력) — 반응적 핀→사전 차단
- [x] 트랙 A reconcile 자율 oracle 배선: `--auto-oracle`로 oracle 다리=31B 자율생성(손golden 대체). 검증 replay 회귀(키0)+fill_auto_oracle 라이브 로켓 6/6. 잔여=풀 E2E는 graded 빌드런 필요
- [x] (트랙 C 본선, G65) 로켓 실빌드 1단계 design 완료: 배관 픽스(planning_packet_rocket/acceptance_tests.json 복사) + design_packet_rocket 생성(4모듈·validator PASS·COMPLETE, BLOCKING=2는 정보용 비게이트)
- [ ] (트랙 C 다음 ★키) 로켓 build_graded --reconcile: 누적빌드 첫 graded 카드 + reconcile 풀 E2E(Build합의 vs 자율oracle)
- [x] (트랙 C 다음 ★키) 로켓 build_graded --reconcile: 누적빌드 첫 graded 카드(게이트 7/11·합의 0.881·합의vs oracle 일치) + Node 실측 게임 작동(G65)
- [x] (트랙 C 2단계) 로켓 B겹 → StoryForge: storyforge.py 신규, 4비트 대사+바이블, 구조검증 3/3 PASS, 서사 2겹 닫힘(G66)

## 누적 빌드 4레버 (트랙 C 본선, §21.2, G67~)
방향 재확인: 게임별 룰코어 생성(O)·범용엔진(X)·그릇=웹(G2). 실증질문=검증된 기존코드 주입받아 scratch 아닌 수정으로 기능 얹고 기존기능 안 깨나.
- [x] (Phase1) 베이스 스냅샷 `studio/rocket_base/`(graded attempt01 4파일, 6시나리오 키0 재현 확인)
- [x] UPGRADE 카드 패킷 v2(planning/specqa_packet_rocket_v2): RULE-06 연료5→fuelRate 1→2, state_shape 불변. 골든 자가검증=기존6 회귀 불변 PASS + 새 SCN-007/008 손계산 일치
- [x] build_graded `--base` 편집모드: `_EDIT_HEADER`(코드주입+수정/보존) + design=base manifest. 키0 프롬프트 조립 검증 통과
- [x] 누적 회귀(레버3): 채점 시나리오에 기존6+새2 동시 포함(자동 채점)
- [x] **(★키) 누적 빌드 런 + 검증(G68)**: graded-20260618-180934 합의 1.0, 회귀(SCN-001~006)6/6·새 UPGRADE(SCN-007/008)2/2, 합의vs oracle 일치. 배관 픽스=Node stdout UTF-8(cp949 차단)
- [x] 레버4 선택적 컨텍스트 배선(G69): `--inject-modules`(touched만 본문+재생성, 나머지 시그니처만+verbatim). `_validate_l4_keyless` ALL PASS(가림+병합+골든8/8)

## 레버4 ★키 런 + 31solo + 외부리뷰 (G70~G71)
- [x] **(★키) 레버4 첫 런(G70)**: graded-20260618-191818 게이트 11/11·합의 8/8 1.0·oracle 일치. 31B가 logic 본문 못 본 채 engine만 편집→회귀+ABORT 둘 다 1.0(logic verbatim·engine ABORT 핸들러 대조). **누적 빌드 4레버 전부 닫힘**
- [x] 31solo 강제(G70): config generator 26b→31B(스튜디오 3도구가 실제 26B 돌던 잔재 제거). 이유=26B 구글 서버 1주일+ 불능. vocab 핀 3패킷 31B 확인런 1.0 재현(재실험 불필요)
- [x] 외부 코드리뷰 반영(G71): #2 게이트 전 시나리오 종료코드 검사·#1 FROZEN BLOCKING 흡수수 확인 픽스+키0 회귀잠금(`_gate_allscenarios_keyless`·`_freeze_blocking_keyless`). #6 CI=`run_keyless.py`+GitHub Actions 그린. #3·#4=정답앵커 실Node 골든으로 정리
- [x] **(★키) 스케일 확장 1차 A/B(G73)**: 정거장 30모듈로 A전체주입(graded-222413,≈14.6k)·B선택주입(graded-223623,≈5k) 두 런. 둘 다 게이트 11/11·합의 1.0·golden_diff 0. EOL 정규화 대조=engine.js만 변경·29모듈 바이트동일. **레버4 천장 ~14.6k에선 미포착** → 확장 분기
- [x] **(키0) 카드 스케일 확장(G73)**: station_base 30→46모듈(본문 35.7KB→63.5KB, 1.77x). 신규 16서브시스템 전부 turn결정적·alerts/log+bounded morale만 → 게이팅 불변·다양성 보존(PLAYING×4·WON×2·LOST×1·EVACUATED×3). 회귀7 base==ref 바이트동일·16모듈 전부 골든 기여(죽은코드0)·strict 게이트 46모듈·run_keyless ALL PASS. 목표 73KB의 ~87%(중복 회피로 멈춤). 커밋 9131978
- [x] **확장 카드 A 재측정→사후채집(G73 후속)**: graded-232623 attempt03 소켓 무한행(llm.py 타임아웃 부재)→킬. **10 attempt 사후 node채점=A @ 63.5KB 1.0**(정확도 100/100·전원합의, 재런 불필요). 충실도 드리프트 발견(tables 주석 패러프레이즈 10/10·EVACUATE actions.js 재배치 2/10)=B 우위 증거. **A 전체주입 측정 보류**(출력바운드·자기모순).
- [x] **출력한도 재프레이밍(사용자 지적, 방향 전환)**: 진짜 제약=컨텍스트(256k,10%) 아니라 출력 32k(추론 포함). A는 키울수록 못 뱉음. B(선택출력/패치)는 모델 출력 수백 토큰·게임크기와 분리(build_graded:90·370-374)=유일 스케일링 길. 측정 B 중심 전환.
- [x] **(★키) 확장 카드 B 측정(graded-20260619-005137)**: 게이트 11/11·합의 1.0·golden_diff 0·held-out 드리프트 0(A의 tables 드리프트와 대조)·engine EVACUATE 정상·콜≈6k. B가 63.5KB/~26k서 정확도+충실도 둘 다 1.0이면서 출력 작게 유지 = 재프레이밍 실증. 레버4 천장 B에선 미포착.
- [x] **llm.py 타임아웃 안전망(키0, 커밋 466a5cb)**: per-request 30분 타임아웃(REQUEST_TIMEOUT_MS) + httpx 타임아웃 type명 분류 → 좀비 소켓 무한행 차단. 정상 콜(최대 24분) 안 끊음. 클라생성·분류·run_keyless ALL PASS 검증.
- [x] **(★키) B 입력 lost-in-the-middle 프로브(graded-20260619-011018)**: 생성기 gen_station_xl.py로 546모듈 XL(sensor 500·입력~24k·시그니처545). 게이트 11/11·합의 1.0·golden_diff 0·held-out 드리프트 0/545·engine EVACUATE 정상. 묻힌 engine도 정확 편집=B 천장 미포착. B는 모듈 수 무관 1.0. (XL gitignore, 생성기만 추적)
- [x] **(키0) 패치빌드 §21.2 레버2 배선(G74)**: 레버4 위 `--patch` 모드. touched 모듈도 통째 재출력 대신 안2(앵커/search-replace) FIND/REPLACE diff만 출력 → 하네스가 base에 적용(`patch_apply.py`). 출력을 모듈 크기와도 분리(B는 게임 크기와만 분리). FIND 0회/2회+/없는파일/쌍없음 = PatchError → CARD 실패(통째 재출력 폴백 없음, ★키 비교 깨끗). `_validate_l4_patch_keyless` ALL PASS(단위6 + 프롬프트4 + e2e등가: 패치복원==B참조본 바이트동일·게이트·골든8/8). run_keyless 편입
- [x] **(★키) 패치모드 3방식 비교(G74, rocket)**: 같은 로켓 l4 카드를 A(전체주입 cmp_a)·B(통째출력 cmp_b)·patch(diff cmp_patch) ★키 런. **셋 다 게이트 11/11·합의 1.0·golden_diff 0·failure 0.** 핵심=patch 11/11 전부 유효 FIND/REPLACE diff(patch 실패 0) → **31B가 diff를 안정적으로 뱉음 실증.** engine.js 셋 다 base 35줄 중 33줄 verbatim 보존·동일 최소편집. 한계=로켓이 작아 A/B 드리프트 미발생(G73 A 주석 패러프레이즈는 63.5KB tables서 나온 것) → patch 충실도 우위는 구조적 보장이나 이 카드선 미응력. raw 응답 미저장이라 출력토큰 사후측정 불가(다음 측정 때 raw 저장 추가)
- [x] **(키0) raw 응답 저장 추가(G74)**: build_graded 워커가 attempt별 `_raw_response.txt`, 런당 `_prompt.txt` 저장 → 출력/입력토큰 사후 정량. run_keyless ALL PASS.
- [x] **(★키) patch를 61.2KB station 카드로(G74, st_a/st_b/st_patch)**: 46모듈 카드 A·B·patch ★키 런. **셋 다 게이트 11/11·합의 1.0·golden_diff 0**(행동 동일). **출력 raw: A 51.1KB vs B 0.7KB vs patch 0.5KB** = 출력이 게임크기와 분리(A 전체재출력, B/patch sub-KB) 실증. **충실도: A held-out 드리프트 11/11**(tables.js 주석 패러프레이즈 + EVACUATE를 계약상 engine 아닌 actions.js에 재배치 = G73 재현), **B·patch 0/11**(하네스 verbatim 강제). A는 행동 1.0이어도 코드·모듈경계 보존 실패, B/patch는 충실도까지 안전 → §21.5 재프레이밍 61KB서 완전 실증. patch vs B 출력격차는 작음(touched engine이 작아서) = patch>B는 큰 touched 모듈서만.
- [x] **(키0) patch 폴백=touched 미패치 파일은 base verbatim(G74)**: 모델이 안 바꾸기로 한 touched 파일은 PATCH 블록 없음 → 하네스가 base 유지(`files.setdefault`). 프롬프트도 "변경 없으면 블록 내지 마라" 명시. `_validate_l4_patch_keyless`에 폴백 케이스 추가, run_keyless ALL PASS.
- [x] **(★키) patch>B 출력우위 응력(G74, st2_b/st2_patch)**: station에 engine+**tables(3.3KB)** 둘 다 touched 주입, EVACUATE 카드(tables 미변경). **둘 다 게이트 11/11·합의 1.0·golden_diff 0·tables verbatim.** **출력 raw B 4.06KB vs patch 0.47KB(~8.6x)** — B는 안 바뀐 tables까지 통째 재출력, patch는 engine diff만(tables 블록 없음→base). **patch가 출력을 touched 모듈 크기와도 분리** 실증. patch는 tables 구조적 보존, B는 재출력이라 큰 모듈선 드리프트 위험(A가 그랬듯).
- [x] **(★키) §21.2 레버3 누적 완주(G74, l2_patch)**: 카드2(PING) patch 빌드를 **카드1(EVACUATE) 출력 위에**(B1=station_base+카드1 engine) 얹음. 누적 13시나리오(카드1 10+PING 3) **전원 게이트 11/11·합의 1.0·golden_diff 0.** 결과 engine에 **EVACUATE 보존+PING 추가**(이미 편집된 모듈 위 재패치)·held-out verbatim·SCN-013(PING→EVACUATE 합성) 통과. 누적회귀 무결 = 이전 카드 기능 안 깨짐 실증. 골든=REF_V2(EVACUATE+PING) node 역산(`gen_station_l2_golden.py`, v1==v2 바이트동일 10/10 검증). B1·임시ref gitignore·생성기로 키0 재현. 패킷=`planning_packet_station_l2`·`specqa_packet_station_l2`.
- [x] **(★키) 레버3 3장 체인 + 서사 A겹 통합(G74, l3_patch)**: 카드3(서사 비트 RULE-10, turn 2→BEAT-1·3→BEAT-2 log에)을 **카드2(EVACUATE+PING) 출력 위에**(B2) patch로 누적. 누적 15시나리오(카드2까지 13+비트 2) **전원 게이트 11/11·합의 1.0·golden_diff 0.** 결과 engine에 **EVACUATE+PING+BEAT 셋 다**(세 번 누적편집)·held-out verbatim·SCN-015(PING+BEAT-1+BEAT-2 합성) 통과·비트 미발동 기존 시나리오 누적회귀 무결. 골든=REF_V3 node 역산(`gen_station_l3_golden.py`). B2 gitignore·생성기로 키0 재현. 패킷=`planning_packet_station_l3`·`specqa_packet_station_l3`. **= 결정적 시뮬(레버1~4)+누적(레버3)+서사 발동(A겹)이 한 카드 체인에 다 올라간 첫 통합. 측정 프로그램 사실상 닫힘.**
- [x] **(★키) 고결합 도메인 일반성 검증 — combat에 patch(G74, combat_l_patch)**: 저결합 자원시뮬(eco·로켓·station)서 본 1.0이 **고결합 턴제전투**(독·게이지·에너지·위치·스턴이 서로 먹임, G52서 합의 0.633로 제일 안 모이던 모양)서도 유지되나. 새 `combat_base`(6모듈 결정적 전투, RULE-01~10) 골격 + 카드 RULE-11 FATIGUE(에너지0→hp-3, engine 루프 편집)를 patch로. **게이트 11/11·합의 1.0(8시나리오)·golden_diff 0.** 모델이 고결합 루프에 FATIGUE 정확 패치(`if energy===0 hp-=3`)+독·게이지·우선순위·종료 결합코어 보존·held-out verbatim. 골든=REF(베이스+FATIGUE) node 역산(`gen_combat_l_golden.py`, 회귀 5 바이트동일·FATIGUE 3 발동). **patch 메커니즘이 도메인 모양에 무관함 입증 — 측정 프로그램의 마지막 미지수(일반성) 닫힘.**
- [ ] **(다음) 본선 쇼케이스 또는 combat 누적/B겹**: 측정 다 갚음. ① 보여줄 게임 1편(B겹 대사·밸런스 config) ② combat에 카드 더 누적(레버3을 고결합서도) ③ combat 서사 A겹. 곁=다모듈 동시편집 / XL 1000+ / 외부리뷰 P1(#10)

## 본선 쇼케이스 — 텍스트 어드벤처(느와르 탐정 IF) (G75~)
- [x] **(키0) 장르·무대 결정**: 안 해본 새 장르 중 텍스트 어드벤처/인터랙티브 픽션 선택(기존은 전부 자원/시스템 시뮬). 서사 2겹(A겹 비트+B겹 대사)을 곁가지가 아닌 본체로 세우는 쇼케이스. 무대=느와르 탐정(대사·분기가 가장 자연스러운 무대, 사용자 추천 위임).
- [x] **(키0) detective_base 저작**: 7모듈 결정적 IF 엔진(`detective_base/`). 선택 순서 입력 → 장면 전이·단서 수집·조건부 비트 발동·결말 분기. scenes.js=B겹 콘텐츠 데이터, beats.js=A겹 발동 로직(단서 3개=DEDUCTION), engine.js=루프(카드 편집 대상). 출력계약=turn/scene/clues/beats/ending/isGameOver/log.
- [x] **(키0) 결정성 검증**: 시나리오 5종(분기·비트 다 건드림) node 실행 → golden 스냅샷 → 재실행 diff 0/5. SCN-1 단서3→DEDUCTION→TRUTH, SCN-5 단서3 모았으나 침묵→COLD_CASE(비트 떴어도 결말은 선택으로 분기), SCN-3/4 단서부족→오답.
- [x] **(키0) 카드1~3 파이프라인 저작·검증**: 누적 3장 — 카드1(집사 ALIBI+FALSE_ALIBI), 카드2(금고 MOTIVE+MOTIVE_REVEALED), 카드3(5단서 CASE_CLOSED, beats만). 각 카드 contract/concept + 골든 생성기(`gen_detective_l1/2/3_golden.py`, REF node 역산, 회귀 prev==cur 바이트동일·신규 발동) + `_validate_detective_keyless.py`(게이트+골든 일치) ALL PASS.
- [x] **(키0) 무인 드라이버**: `driver_showcase.py` — 카드 순차 패치빌드→그린판정(게이트·합의1.0·골든diff0)→통과 워크스페이스를 다음 base로 누적→리포트. 실패 시 1회 재시도 후 중단·마지막 그린 보존·시간 상한 가드.
- [x] **(★키) 무인 쇼케이스 3장 완주(20260619-0414, 610s)**: l1/l2/l3 **전부 11/11 게이트·합의 1.0·골든 diff 0** (8→11→12 누적 시나리오). 최종 게임 `build_runs/showcase/l3_built`(이때 드라이버는 단일 경로 사용, 이후 G76서 게임별 `showcase_<game>`로 일반화). **engine·state·format·constants·main 5모듈 3장 내내 held-out verbatim(EOL만 차이, 내용 동일)** = "엔진 불변, 콘텐츠+비트만 누적"으로 게임 성장 실증. SCN-012=5단서·비트4개(MOTIVE_REVEALED·FALSE_ALIBI·DEDUCTION·CASE_CLOSED) 전부 발동·TRUTH. **자율 루프가 새 장르(IF)에서 처음부터 게임을 지어 키움.**

## 본선 쇼케이스 2 — 격자 퍼즐(소코반) (G76~)
- [x] **(키0) 새 장르 = 격자 퍼즐(소코반)**: 자원시뮬·IF와 다른 2D 공간·이동 모양. `sokoban_base` 7모듈 결정적 엔진(이동→상자 밀기→전 상자 목표 위면 승리). state.js가 비표준 타일을 일반 tiles맵으로 파싱(프로즌) → 카드는 move_logic+levels만 패치, engine·state·format·constants·main 프로즌. 시나리오 6종 결정성 검증 drift 0/6.
- [x] **(키0) 카드1~3 + 골든 + 검증**: 카드1(열쇠K/문D), 카드2(텔레포트T), 카드3(구덩이O) 누적. `gen_sokoban_l1/2/3_golden.py`(REF node 역산, 회귀 prev==cur 바이트동일·신규 발동) + `_validate_sokoban_keyless.py` ALL PASS. 전부 move_logic+levels만 touched.
- [x] **(키0) 드라이버 일반화**: `driver_showcase.py`에 GAMES 레지스트리 추가(detective/sokoban) — `python driver_showcase.py sokoban`. 새 게임은 레지스트리 한 줄 + 패킷/골든이면 무인 빌드.
- [x] **(★키) 1차 시도서 설계결함 발견·수정**: 첫 런(0844) l1이 게이트11/11·합의1.0이나 **골든 diff 3건**으로 드라이버 자동 중단. 원인=시나리오가 `L_key`/`L_locked` 참조하나 계약이 레벨 id/레이아웃 미지정 → 모델이 `L4`/`L5` 자작(메커니즘 로직은 정확). **합의만 봤으면 속았을 것 — 모델독립 골든이 잡음(외부리뷰 #3 규율의 실증).** 수정=쇼케이스 레벨 전부 base levels.js에 고정(frozen 데이터), 카드는 move_logic만 패치. 키0 재검증 3장 통과.
- [x] **(★키) 소코반 무인 3장 완주(20260619-0857, 694s)**: l1(열쇠/문)·l2(텔레포트)·l3(구덩이) **전부 11/11·합의 1.0·골든 diff 0**(9→11→13 누적 시나리오). 최종 게임 `build_runs/showcase_sokoban/l3_built`. **engine·state·format·constants·levels·main 6모듈 내용 동일(frozen), move_logic.js만 3장 내내 누적** — 데이터 고정·로직만 성장. SCN-007 열쇠+문 통과·SCN-010 텔레포트·SCN-012 구덩이 메워 승리. **자율 루프가 두 번째 새 장르(격자 퍼즐)도 처음부터 지어 키움.**

## 북극성 — 다작·선별 퍼널 (G77, 정본 §1.5)
목표: `생성→[싼 사전필터]→사람 판단→[실노출 신호]→더블다운`. 병목=선별+품질(생성 아님). 골렘이 "안 깨졌나" 공짜 검증→사람은 "재미있나"만. 모든 작업은 이 목표에 종속.
- [x] **(키0) 북극성 정본화**: GolemStudioMode.md §1.5 + HANDOFF 목표줄 + context-notes G77.
- [x] **(★키 2콜) 싼 사전필터 조각 ① 닫힘(G78)**: `card_proposer.py`에 레저(RAG, `cardgen_ledger.py`+`cardgen/` L-001~005·E-001/002) 주입 + 사전필터 신호층(static_gate·직전 골든 회귀·발동 커버리지·결정성·구조 스코프). 소코반 card4로 **FLAG·PASS 두 판정 실증**(Spring/Crumbling 커버리지 자동 FLAG → 워크드 격자 few-shot 보강 후 Crumbling Floor PASS). 부수발견=산문교훈 vs few-shot 교훈종류 차이. 한계=PASS도 '그럴듯하게 틀린' REF는 사람 대조 필요. 커밋 7cbccc4·141d138.
- [~] **소설→게임 브리지 첫 실증(G79)**: 아뜰리에 "에테르노의 그림자"(12장면) → 내러티브 IF 뼈대 + 턴제 전투 카드 하이브리드. 골렘=구조화+건전성검증, 각색충실도=사람. (아뜰리에 읽기전용.)
  - [x] (키0) 구조 설계 `bridge_eterno/STRUCTURE.md` — 12장면→노드 매핑·상태 스키마·4대 메커니즘 직역·선형→분기 발명. 커밋 fc07178.
  - [x] (키0) Card1 패킷화 + 전수검사·A1 재작성(G80) — `eterno_base`(7모듈 IF 엔진, static_gate 통과) + planning/specqa 패킷. 빌드 전 전수검사서 1차 설계 결함(스텁 base+줄거리 앞으로 확장=누적 회귀 깨짐) 잡아 **허브형 완결 base + add-only 곁가지 카드**로 재작성(Card1=scenes.js만, 타이머 always-on). 누적 8시나리오(회귀5+잠입3) 회귀 base 골든과 바이트동일. B(허위 RULE-04)·C(eclipse off-by-one) 해소, D=키0 검증기 `_validate_eterno_keyless.py`(gate+골든+회귀 예행, 빌드 성공 사전보증). run_keyless ALL PASS. driver에 eterno 등록(inject=scenes.js). 커밋 81963f3·3da5e15·c194bde·dfabb2b.
  - [x] **(★키) 무인 빌드 `driver_showcase.py eterno` 그린 완주(G81)** — 139.7s, 게이트 11/11·합의 1.0·골든 diff 0(8시나리오), touched=scenes.js만·frozen 6. 최종=`build_runs/showcase_eterno/l1_built`. **소설→게임 IF 브리지 첫 실증 닫힘.**
  - [x] **(키0) 이모지 웹 외형 1호(G81)** — `golem/studio/eterno_play/server.js`. 검증 엔진 require·읽기전용 렌더(룰 복제 안 함). 아이폰 테일스케일 접속(방화벽 인바운드 8765 테일넷대역만 허용). 사용자 플레이 확인.
  - [-] (취소) Card2 변칙검술 — IF 라인은 l1로 닫고 전술 SRPG로 피벗(아래). 변칙검술은 전술 카드로 이어감.
- [ ] **(나중) 실노출 신호 조각 ②**: 살아남은 후보를 작게 내보내 실제 반응 측정 → 더블다운.

## 장르 피벗 — 전술 SRPG(영걸전형) + 운영 모델 정형화 (G81, 2026-06-19) — 이유 context-notes G81
- [x] **운영 모델 정형화** — 골렘=설계+빌드+검증 / 클로드=하네스+외형(게임 설계 직접X) / 사용자=아이디어·취향(맨끝). 작게 시작→점진 검증, 단계마다 끊어 보고 하네스 조임, 보조는 한시적·골렘 완전자율이 목표. 메모리 3종(golem-labor-division·golem-incremental-small-first·golem-user-intervenes-last).
- [x] **장르 결정** — IF 취향 아님 → 전술 SRPG. 정사각 상하좌우 2D부터(검증·이미지추출·고도렌더 floor 정렬), 쿼터뷰/iso 나중. 비주얼=에셋팩+이미지→타일맵(결정CV·레이아웃만)+고도. 가챠=시드RNG로 검증가능.
- [x] **(키0) 파이프라인 plumbing 점검** — `run_keyless.py` ALL PASS(compileall·replay·레버4·게이트#2·FROZEN#1).
- [x] **(★키) 전술 커널 planning 첫 런 → OPEN** — `planning.py --synthesize --idea "…전술 그리드…영웅1·인접공격·처치=승리·결정적" --out planning_packet_tactics_kernel`. 골렘 설계 양호(BLOCKING 19→흡수 16: 결정11·가정3·보류2, 턴사이클·적AI·결정이동·충돌·데미지). FROZEN 못 박음.
- [x] **(키0) 하네스 fix #1 — planning FROZEN 게이트(커밋 1f223f8)** — `planning.py:262` n_block을 `_dedup`로 distinct 카운트. 중복 BLOCKING 분모 인플레 차단. `_freeze_blocking_keyless.py` 회귀 4건. run_keyless ALL PASS.
- [x] **(★키) 전술 커널 풀 파이프라인 — 골렘이 설계·빌드** — planning(FROZEN)→design(4모듈 main/engine/actions/state, validator PASS)→specqa→build. **사다리 합의 0.35→0.846**: 1차 0.35(출력계약 미고정, G33 재현) → 출력계약+공허승리 핀 → 0.846(게이트 6/11). 패킷=`*_tactics_kernel`, 빌드=`build_runs/tactics_kernel`(v1)·`tactics_kernel_v2`(0.846).
- [x] **(진단) 남은 golden_diff 3종** — (a)적 출력 shape(빌드 full vs oracle partial) (b)승리 타이밍(빈 적→VICTORY/FINISHED 빌드 분열) (c)SCN-010 specqa 오라클버그(적을 영웅칸 스폰).
- [x] **(★키) 3핀 재파생 planning FROZEN** — 출력 5키 고정·enemies{id,hp,pos}만·승패 액션직후만·위치 유일성 → REQ-005/007/008로 핀. 단 specqa v3 환각(TAKE_DAMAGE·좌표MOVE 지어냄, REQ-007 위반) → 빌드 전 손검산이 잡음.
- [x] **(키0) 하네스 fix #2 — specqa 환각 차단(미커밋)** — `specqa.py` lead·synth 프롬프트에 FROZEN CONTRACT 전문 주입(명령·출력 모델) + "계약 밖 명령/키 금지" + 옛 `prints key:value` 줄 제거. **사후 validator 2종은 기각**(어휘 substring·키일관성 둘 다 정상 런 막는 false positive — specqa_demo fixture 깨짐 실증). specqa replay·run_keyless ALL PASS. 효과는 ★키 재런으로만 확인.
- [x] **(★키) specqa 재런 → 환각 멈춤 확인 → build v6 합의 1.0·golden_diff 0 → 커널 닫힘 → `tactics_kernel_base` 동결(G81).**

## 전술 카드 9장 누적 + 자율 완결-후보 파이프라인 (G82, 2026-06-19~20) — 이유 context-notes G82
- [x] **카드 l1~l5 손그래프트 누적 — 전부 게이트 11/11·합의 1.0·golden_diff 0.** l1 변칙검술(마나방패+ANOMALY)·l2 사거리·l3 지형(Wall/Conductive)·l4 유닛(Hardened/Glass/Resonant)·l5 루트맵. 각 골렘 planning ★키 설계 → base 관례 그래프트(직전 REQ 이월+새 REQ) → 확장 참조(직전 순수 슈퍼셋) 골든 → `_validate_tactics_lN_keyless` → `build_graded --inject src/game_logic.js`. engine/main/scenarios 불변·출력 5필드 고정.
- [x] **운영 교정** — 카드마다 취향 안 묻고 골렘 자율·키 안 멈추고 끝까지(메모리 golem-no-taste-questions). 종착점=골렘 완전자율, 지금은 하네스 컨트롤.
- [x] **"다 하기" 4트랙** — ①외형 `gen_tactics_play.py`(정사각 탑다운 렌더러, 키0) ②카드더 l6 상태이상(Corrosion DoT) ③밸런스 l7 config(atkMult/recMult/anomMult) ④캠페인 루트맵 6전투+서사. l6 합의 첫 1.0 미달(0.971)이나 golden_diff 0.
- [x] **patch-누적 base 빌드(스케일링 fix)** — 전체재작성 l8=0.718 붕괴(8카드 깊이) → l7 참조 `tactics_base_l7` 동결 후 l8 `--patch`=1.0·golden 0·출력 ~1.3KB. go-forward=`tactics_base_lN` 동결 후 `--patch`.
- [x] **자율 인프라 4조각** — (a)`card_delta.py`(골렘 base-델타)+`graft.py`(조립·키0검증·교차검산) / 빌드 patch-누적 / (b)`gen_tactics_story.py`(골렘 서사·구조검증) / (c)`gen_tactics_play.py --level` 일반화.
- [x] **종착점 `driver_autocard.py`** — idea→설계→base동결→patch빌드(그린)→스토리→렌더 한 바퀴 무인. 시연 l9 처형: gate 11/11·합의1.0·golden0(34세계)·손번역 0·5.7분. REPORT.json.
- [x] **견고화** — graft 신규세계 "≥1 발동"으로 완화(l3식 비발동 유효) / patch_apply 줄끝공백 폴백(`_locate`, l8 3/11 CARD 흡수). 단위테스트+run_keyless 그린.
- [x] **외형 호평·아이폰 서버** — 서사 한 겹에 사용자 "느낌이 확 달라"(메모리 golem-story-layer-matters). 테일스케일 서버 확인 후 내림.
- [x] **(3·4·5)** (4)선별 퍼널 `propose_cards.py`(골렘 카드 제안)→driver_autocard `--ideas-file` / (3)card_delta 피드백 루프(자가수정 1패스율↑) / (5)StoryForge 보강("변칙의 잔향" 카엘).

## 외부리뷰 대응 + 정본화·운영안전·분해 (G82, 이유 context-notes G82 (10~12))
- [x] **정본 선언** — 루트 `README.md` 신설(본선 전술 9카드·stable=`tactics_base_l8`·실험 l9·tactics_play 생성산출물 수정금지·디렉토리 경계·live vs legacy), `golem/README` 포인터.
- [x] **검증 정본 `verify_tactics.py`** — 9카드 골든회귀(l1~l9)+l8 strict 승격+run_keyless 한 명령. 정본: `python golem/studio/verify_tactics.py`.
- [x] **promotion gate** — 후보 strict False / base 승격 strict True(l8 구조부패 차단).
- [x] **llm 재시도 상한** — `SLOW_RETRY_MAX=12`(무한대기→관측가능 종료, env override).
- [x] **디커플 + legacy 이동** — `parse_write.py` 분리·importer 재지정 → 21개 `golem/legacy/`로(driver/bank flow/probe류). 루트 live=parse_write·static_gate·oracle·grade.
- [x] **build_graded 분해** — gate_runner·grading(키0)·build_prompt(프롬프트 바이트동일로 검증) 분리, 596→294줄, re-export로 호출부 무변경.
- [x] **전체 코드 점검** — compileall(legacy 포함) exit0·live 17모듈 import·verify_tactics ALL PASS·고아참조 0·워킹트리 클린.
- [x] **실노출 신호 `play_signals.py`** — solvable/min_turns(BFS)·지배전략·카드영향. 퍼널 마지막 칸.
- [x] **레벨 시스템 `propose_levels.py`** — 골렘 생성+play_signals 검증+커브, 단일-attempt 채택. 8레벨(min 3~8) 라이브.
- [x] **인터랙티브 플레이 `gen_tactics_interactive.py`→play.html** — 검증 l9 embed, 탭 이동/공격, 모바일 좌표·탭이동 fix. server /play.
- [x] **장르 시드(propose_cards --ref)·card_delta 피드백 루프·StoryForge 보강(카엘).**
- [x] **외부리뷰 대응·정본화·legacy 분리·build_graded 분해** (context-notes G82 10~12).
- [x] **비주얼**: SVG 에셋팩(sprites.py) → CC0 픽셀팩(Kenney Tiny Dungeon, 다운로드·검증)+llm 이미지 입력+Gemma 비전 선택(gen_assets.py)→픽셀 스프라이트(play.html). 자족(tile_sprites.json).
- [x] **볼륨↑** 레벨 8 + 운영원칙(다 자동화·노브 몇 개, 메모리).
- [ ] **(다음 세션)** 볼륨 더(레벨↑/카드 누적 driver_autocard/캠페인↑) · 뷰어 index.html도 픽셀 · 스프라이트 슬롯/이펙트.
