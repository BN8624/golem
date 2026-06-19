# HANDOFF.md — golem 현재 위치와 다음 액션

## ▶ 새 세션 여기부터

**현재 상태 (2026-06-19, G81) — IF 브리지 닫힘 + 장르 피벗(전술 SRPG) + 운영 모델 정형화 + 골렘이 전술 커널 풀 파이프라인 설계·빌드(합의 0.35→0.846, 사다리) + 하네스 fix 2건(planning FROZEN·specqa 환각).**
- **(★키) eterno IF 브리지 l1 무인 빌드 그린 완주** — `driver_showcase.py eterno` 139.7s, 게이트 11/11·합의 1.0·골든 diff 0(8시나리오), touched=scenes.js만·frozen 6. **소설 "에테르노의 그림자"→게임 IF 브리지 첫 실증 닫힘.** 최종=`build_runs/showcase_eterno/l1_built`. + **이모지 웹 외형 1호**(아이폰 테일스케일 플레이, `golem/studio/eterno_play/server.js`, 검증 엔진 require·읽기전용 렌더).
- **장르 피벗 결정(사용자)** — IF는 취향 아님 → **전술 SRPG(영걸전형): 정사각 격자 이동·공격, 짜여진 루트.** 에테르노는 **캠페인 루트로 재구성**(엔진=전술 결정적 / 스토리=데이터 레이어라 교체가능 — 10권 풀스토리 내일 도착 예정, 오늘은 있는 12장면으로 시운전). **정사각 상하좌우 2D부터**(골렘검증·이미지추출·고도렌더 셋 다 이산구조에서 floor — 한 줄 정렬), 쿼터뷰/iso는 나중. 비주얼 로드맵=에셋팩+이미지→타일맵(결정적 CV, 레이아웃만·스펙X)+고도. 가챠=시드RNG로 검증가능(Math.random만 금지).
- **운영 모델 정형화** — **골렘=설계+빌드+검증 / 클로드=하네스+외형(게임 설계·base를 손으로 안 씀) / 사용자=아이디어·장르·취향(맨 끝 개입).** **작게 시작→검증하며 점진 확장(누적 빌드)**, **단계마다 끊어 보고 하네스 조임.** 지금 보조는 한시적 발판이고 **골렘 완전자율이 종착점**(매 보조=하네스로 흡수할 후보). (메모리 3종에 박음.)
- **(키0) 하네스 fix #1 — planning FROZEN 게이트(커밋됨)** — `planning.py:262` n_block을 `_dedup`(A/B/C와 동일 토큰 Jaccard)로 distinct 카운트. 리뷰어 중복 BLOCKING이 분모를 부풀려 FROZEN 산술 불가하던 결함 차단. `_freeze_blocking_keyless.py` 회귀 4건. 첫 "하네스 조이기" 케이스 — 골렘 출력 안 건드리고 게이트만.
- **(★키) 전술 커널 풀 파이프라인 완주 — 골렘이 설계·빌드(planning→design→specqa→build)** — `*_tactics_kernel` 패킷. 사다리로 합의 **0.35→0.846** 끌어올림: ①최소 커널 idea(영웅1·인접공격·처치=승리·결정적·시나리오구동·stdin금지) FROZEN → design 4모듈(main/engine/actions/state) → specqa → build 0.35(출력계약 미고정=빌드마다 형식 제각각, G33 재현). ②**출력계약+공허승리 핀** 박아 재파생 → **0.846**(게이트 6/11). 남은 golden_diff 진단: (a)적 출력 shape(빌드 full {id,hp,atk,pos} vs oracle partial) (b)승리 타이밍(빈 적→VICTORY vs FINISHED, 빌드 3:3 분열) (c)SCN-010 specqa 오라클버그(적을 영웅칸에 스폰). ③**3핀 재파생**(출력 5키 고정·enemies {id,hp,pos}만·승패는 액션 직후만·위치 유일성) → planning FROZEN, REQ-005/007/008로 핀 박힘. 단 **specqa v3가 환각**(없는 명령 TAKE_DAMAGE·좌표MOVE 지어냄, REQ-007 위반 expected) → **빌드 전 손검산이 잡음(11키 낭비 방지).**
- **(키0) 하네스 fix #2 — specqa 환각 근본 차단(미커밋, 이 세션)** — 진단=`specqa.py`가 모델에 rules 텍스트만 주고 **interface_contract(명령·출력 모델)를 안 먹였음** + 옛 `"prints key: value lines"`(계약과 모순). fix=lead·synth 프롬프트에 **FROZEN CONTRACT 전문 주입** + "계약에 없는 명령/출력키 금지" 명시 + 옛 줄 제거. **사후 validator는 기각**(어휘 substring=false pos/neg, 키일관성=정상 패턴 specqa_demo 깨는 false positive — 정상 런 막는 가드는 병보다 나쁨). specqa replay·run_keyless ALL PASS. **효과(환각 멈춤)는 ★키 specqa 재런으로만 확인 가능 — 미검증.**
- **(★키) 전술 커널 1.0 닫힘 — specqa fix 검증 + 출력계약·세계 하네스 주입(이 세션 완료).** ①specqa 재런(★키) → 손검산 환각 멈춤 확인(명령어휘·출력shape·REQ-007 클린). ②build_graded v4 0.633 진단=하네스↔계약 불일치(제네릭 `_output_lines` key:value+logs vs REQ-008 평면 hero_hp/pos·enemies id/hp/pos) + 세계 미고정(main.js가 주입 scenarios.json 무시·src/scenarios.js 자체 하드코딩). ③**하네스 fix(하위호환)**: 계약 `output_contract`(평면 5필드·logs없음·atk제외)+`scenario_data`(골든 역산 6세계) 추가, `_output_block`/`_provided_block`/`_gen_scenarios_module`로 출력지시 계약구동·`src/scenarios.js` 고정세계 verbatim 주입, golden_diff가 hero_hp/pos 채점. REQ-009(소진→FINISHED)·010(blocked move)·011(액션스키마·인접공격)·007(post-action 시점) 핀. **참조 엔진이 6세계→골든 6/6 재현(키0).** ④v5 0.958(golden_diff 0!, SCN-004 한 빌드 turn0 단락) → REQ-007 시점 핀 → **v6 합의 1.0·golden_diff 0(전6시나리오 5/5)=깨끗한 닫힘.** 커밋 e37e38e·f58d536. **잔여(정확성 아닌 신뢰도): 게이트 5/11 — 원인 규명됨(과분해 아님): 고아 3건=require 경로 표기 혼동(모델이 manifest 루트상대 `src/game_logic.js`를 src/engine.js의 require에 그대로 복사→`./src/game_logic` 잘못, 통과본은 `./game_logic` 정답). 잘림 3건=출력 중간 truncation(별개). 경로건은 프롬프트 fix(require=모듈상대 명시)로 차단(미커밋이면 이 세션 커밋).**
- **base 동결 완료(이 세션, 키0).** v6 attempt02(6세계 골든일치·결정적)를 `golem/studio/tactics_kernel_base`로 고정(main·engine·game_logic·scenarios 4모듈+manifest). 검증기 `_validate_tactics_keyless.py`(gate+골든+결정성 2회) ALL PASS. 커밋 fd00ee4. 루트 `build_runs/`도 gitignore.
- **다음 세션 첫 동작 = 첫 카드(★키, 골렘이 설계).** 변칙검술 마나방패+ANOMALY를 골렘 planning→design→build로 산출, `build_graded --base golem/studio/tactics_kernel_base`로 add-only 누적(game_logic/engine만 touched, scenarios 세계는 카드 시나리오 추가 시 계약 scenario_data 확장). 단계마다 끊어 보고 골렘 출력 검토. 누적 순서=변칙검술 → 사거리 → 지형 → 유닛 → 루트 맵. 에테르노 스토리(`bridge_eterno/STRUCTURE.md`)는 캠페인 루트 콘텐츠(엔진과 분리). **신뢰도 fix 2건(이 세션): ①require 경로 프롬프트 명료화(고아 3건, 커밋 848a828) ②parse_files 펜스 누출 차단(잘림 3건=모델이 전체를 ```js 한 덩이로 감싸 닫는 ```가 main.js에 누출→SyntaxError, 커밋 aa4d27f). ②는 기존 raw 재파싱으로 키0 검증 완료(node --check 3/3 OK). 합치면 v6 5/11 → 11/11 예상(★키 빌드로 확인, 1.0은 이미 닫혀 급하지 않음).**

**현재 상태 (2026-06-19, G78~G80)**: **북극성 두 트랙 동시 전진 — ① 싼 사전필터 닫힘 + ② 소설→게임 브리지 Card1 패킷화.** (G78, ★키 2콜) `card_proposer.py`에 레저(RAG, `cardgen_ledger.py`+`cardgen/`)를 주입하고 사전필터 신호층(static_gate·직전 골든 회귀·발동 커버리지·결정성·구조 스코프)을 붙여 **FLAG·PASS 두 판정 실증**(소코반 card4: 커버리지 1<2 자동 FLAG → 워크드 격자 few-shot 보강 후 Crumbling Floor PASS). 부수발견=산문교훈만으론 31B 격자 좌표 약점 못 막아 few-shot 필요(교훈 종류 차이). (G79→G80, 키0) 아뜰리에 "에테르노의 그림자"(12장면)를 내러티브 IF로 구조화(`bridge_eterno/STRUCTURE.md`) + `eterno_base`(7모듈 IF 엔진) + Card1 패킷. **빌드 전 전수검사서 1차 설계 결함(스텁 base+줄거리 앞으로 확장=누적 회귀 깨짐) 발견 → A1 재작성**: detective 패턴대로 base를 완결 줄거리(허브에서 5조각→대면→결말, 엔진 기계장치 전부 base가 실행)로, 카드는 허브에 add-only 곁가지. Card1=scenes.js만(검문 잠입 infiltrate→checkpoint, bluff→CAUGHT). 타이머 always-on으로 off-by-one 제거. 누적 8시나리오 회귀 base 골든과 바이트동일·키0 검증기 `_validate_eterno_keyless.py`(gate+골든+회귀 예행)·run_keyless ALL PASS. **다음 첫 동작 = `driver_showcase.py eterno` 무인 빌드(★키).** 커밋 7cbccc4·141d138·fc07178·81963f3·3da5e15·c194bde·dfabb2b. (G76 이전 측정 상세는 아래.)

**현재 상태 (2026-06-19, G76 완료)**: **두 번째 새 장르 — 격자 퍼즐(소코반)도 무인 자율 루프로 처음부터 지어 카드 3장 누적 완주.** `sokoban_base`(7모듈 결정적: 이동→상자밀기→전 상자 목표면 승리, state.js가 비표준 타일을 일반 tiles맵으로 파싱) + 카드3장 l1(열쇠/문)·l2(텔레포트)·l3(구덩이)를 `driver_showcase.py sokoban`으로 무인 빌드. **결과(20260619-0857, 694s): 전부 11/11·합의 1.0·골든 diff 0**(9→11→13 시나리오). 최종 `build_runs/showcase_sokoban/l3_built`. **engine·state·format·constants·levels·main 6모듈 frozen, move_logic.js만 누적** = 데이터 고정·로직만 성장. **1차 시도서 설계결함(시나리오가 참조하는 레벨 id를 계약이 미지정→모델이 자작 레벨)을 골든 diff로 잡아 자동 중단→수정(레벨을 base에 고정)→재실행 성공**: 모델독립 골든이 "합의는 1.0인데 틀린" 케이스를 거른 실증(외부리뷰 #3 규율). 드라이버는 GAMES 레지스트리로 일반화(detective/sokoban, 새 장르는 한 줄+패킷/골든이면 무인). **다음=쇼케이스 더(또 다른 장르 / 기존 게임 카드 확장 / B겹·밸런스) — 사용자와 결정.** (G75 IF·G74까지 측정 상세는 아래.)

**현재 상태 (2026-06-19, G75 완료)**: 측정 종료 후 **본선 쇼케이스 완주 — 새 장르 텍스트 어드벤처(느와르 탐정 IF)를 무인 자율 루프로 처음부터 지어 카드 3장 누적으로 키움.** `detective_base`(7모듈 결정적 IF 엔진: 선택→장면전이·단서수집·조건부 비트발동·결말분기) 저작·결정성 검증(키0) 후, 누적 카드 3장을 `driver_showcase.py`로 무인 패치빌드. **결과(20260619-0414, 610s): l1(집사 ALIBI+FALSE_ALIBI)·l2(금고 MOTIVE+MOTIVE_REVEALED)·l3(5단서 CASE_CLOSED) 전부 11/11 게이트·합의 1.0·골든 diff 0**(8→11→12 누적 시나리오). 최종 게임=`build_runs/showcase/l3_built`. **engine·state·format·constants·main 5모듈은 3장 내내 held-out verbatim(EOL만 차이) = 엔진 불변·콘텐츠+비트만 누적으로 성장 실증.** 골든은 REF node 역산(모델 독립), 키0 검증기 `_validate_detective_keyless.py` 보유. **다음=쇼케이스 확장(카드 더 누적 / B겹 대사·밸런스 / 다른 장르) — 사용자와 방향 결정.** (G74까지 측정 상세는 아래.)

**현재 상태 (2026-06-19, G74)**: 누적 4레버·patch빌드(레버2)·레버3 누적 3장·서사 A겹·**고결합 combat 일반성 검증**까지 전부 닫힘 + CI 그린. 본선은 **31solo**(gemma-4 31B 단독). **측정 프로그램 사실상 종료 — 레버·patch·스케일·누적·서사발동·도메인 일반성 전부 31B로 1.0.** 스케일 확장 1차 A/B ★키 둘 다 1.0 → 카드 1.77x(63.5KB·46모듈) 확장 → A 재측정 소켓행→킬·사후채집 A @ 63.5KB=1.0(충실도 드리프트) → **출력 32k 재프레이밍**(진짜 벽은 컨텍스트 아니라 출력, B가 스케일링 길) → 확장 카드 B=1.0·drift0 → B 입력 프로브 546모듈/입력~24k서도 B 1.0·drift0/545(천장 미포착) → **G74 패치빌드(§21.2 레버2) 배선 + ★키 3방식 비교 + 61KB 응력 완료**: 레버4 위 `--patch` 모드(touched도 통째 대신 FIND/REPLACE diff만 출력) + raw 응답 저장. 로켓 l4·station 61KB 카드 둘 다 A·B·patch ★키 런 = **셋 다 게이트 11/11·합의 1.0·golden_diff 0·patch 실패 0**. **station서 §21.5 완전 실증: 출력 raw A 51.1KB vs B/patch sub-KB(0.7/0.5), A held-out 드리프트 11/11(주석 패러프레이즈+EVACUATE 모듈경계 침범) vs B/patch 0/11.** → patch>B 출력우위(st2: B4.06 vs patch0.47KB) → 레버3 누적(l2: 카드2 PING) → **레버3 3장 체인+서사 A겹(l3_patch): 카드3 비트(turn 2→BEAT-1·3→BEAT-2)를 카드2 출력 위에 patch로, 15시나리오 전원 11/11·1.0·golden_diff0·engine에 EVACUATE+PING+BEAT 셋 다** → **고결합 combat 검증(combat_l_patch): 새 combat_base에 RULE-11 FATIGUE를 patch로 11/11·1.0·golden_diff0 = patch 도메인 결합도 무관 입증.** **측정 프로그램 종료. 다음=본선 쇼케이스(B겹·밸런스, 측정 아닌 산출물).**

**▶▶ 핵심 재프레이밍(G73 후속, 사용자 지적) — 진짜 제약은 컨텍스트가 아니라 출력 32k(추론 포함)**.
- **컨텍스트 창은 한계 아님**: gemma-4 31B 256k 창에 카드 입력 ~26k = 10%. 카드를 더 키워도 창은 안 참.
- **출력 32k(추론 포함)가 진짜 벽** — 단 **A(전체 재출력)에만** 걸림. A는 46모듈 verbatim 재출력 ≈20k 출력토큰·콜당 ~11분(최대 24분 실측). 코드가 실효 출력한도(추론 빼면 ~20–25k토큰≈70–90KB) 넘으면 한 응답에 못 담음 → **카드를 키울수록 A가 더 못 뱉는 자기모순.** 추론이 예산 더 깎음.
- **B(선택출력/패치)는 출력이 게임 크기와 분리됨** — 모델은 touched 파일만 출력([build_graded.py:90]), 하네스가 held-out를 base verbatim 강제([build_graded.py:370-374]) → 모델 출력=수백 토큰. 입력도 ~6k(touched 본문+45 시그니처). **게임이 50KB든 500KB든 콜 출력 일정 = 유일하게 출력한도 안 건드리는 스케일링 길.**
- **결론**: 대형 게임은 "매 턴 전체 재생성(A)"이 아니라 **"선택적 읽기 + 패치 쓰기(B)"**로 짓는 게 필연. 출력 32k가 A를 죽이지 B는 안 죽임. 레버4 측정의 의미 = **B가 스케일에서 정확도 1.0 유지함을 보이는 것**(=스케일링 메커니즘 입증). G73에서 B 1.0이라 청신호.

**▶▶ G74 마지막 검증 — 고결합 combat에 patch도 1.0 (메커니즘 도메인 무관 입증)**.
새 `combat_base`(6모듈 결정적 턴제전투, 독·게이지·에너지·위치·스턴 고결합) 골격 + 카드 RULE-11 FATIGUE를
`--patch`로 → 게이트 11/11·합의 1.0·golden_diff 0(combat_l_patch). G52서 제일 안 모이던(합의 0.633)
도메인서도 patch 1.0 = 측정 프로그램 마지막 미지수(일반성) 닫힘.

**▶▶ 다음 세션 첫 동작 = 본선 쇼케이스 게임 1편 (측정 전부 닫힘 — 이제 산출물)**.
G74에서 patch빌드를 §21.2 4레버 전부 + 레버3 3장 체인 + 서사 A겹까지 닫았다(l3_patch: 카드1 EVACUATE→
카드2 PING→카드3 비트를 patch로 누적, 15시나리오 전원 1.0, engine에 셋 다). **결정적 시뮬+누적+서사 발동이
한 체인에 다 올라갔다.** 레버·patch·스케일·누적·서사 A겹 전부 1.0 → 잴 것은 거의 없다. 남은 본선은
**측정이 아니라 산출물** — ① B겹 대사(StoryForge, 출력전용·구조만 검증, 문장 질은 사람) ② 밸런스 config
(잴 수 있는 페이싱/지배전략은 코드, 취향은 사람) ③ 둘을 patch 누적라인에 붙여 "보여줄 게임 한 편". 측정으론
다 갚았으니 여기서 사용자와 "무엇을 쇼케이스로 지을지" 정하는 게 맞다.
*(곁가지: 다모듈 동시편집·XL 1000+·combat 자율oracle·외부리뷰 P1(#10). 전부 한계효용↓ 또는 별 트랙.)*
- 닫힌 것: 확장 카드(63.5KB·46모듈)서 B = 게이트 11/11·합의 1.0·drift 0(★키 graded-20260619-005137). A는 채집으로 1.0이나 출력바운드+드리프트라 **보류**. 출력 32k는 B를 안 죽이니 B축으로 키운다.
- B 입력 lost-in-the-middle **프로브 닫힘(graded-20260619-011018)**: 생성기 `gen_station_xl.py`로 **546모듈** XL 카드(sensor 더미 500개, B 입력 ~24k·시그니처 545개) → **게이트 11/11·합의 1.0·golden_diff 0·held-out 드리프트 0/545·engine EVACUATE 정상.** engine이 545 시그니처 사이에 묻혀도 **B 천장 미포착.** → B는 모듈 수에 사실상 무관하게 정확도+충실도 1.0(출력은 항상 작음). 레버4 천장은 이 스케일 너머. XL은 gitignore, 생성기만 추적.
- 인프라(완료): `llm.py` per-request 타임아웃 안전망(`REQUEST_TIMEOUT_MS=1800000` 30분). 커밋 466a5cb.
- **다음 후보**: ① 패치빌드(파일별/diff) 라인을 §21 대형게임 정본과 정합 — B가 스케일 입증됐으니 진짜 큰 게임을 B로 짓는 쪽(정도). ② (원하면) XL을 1000+모듈로 더 밀어 천장 계속 추적(한계효용↓, B가 546서 끄떡없음). ③ 곁가지 combat 자율oracle / 외부리뷰 P1.
- 갈림길(곁가지): combat 자율oracle / 외부리뷰 P1(#10 등).

**최근 완료 (역순)**:
- **G74 고결합 도메인 검증 — combat에 patch(combat_l_patch)**: 저결합서 본 1.0이 고결합 턴제전투(독·게이지·에너지·위치·스턴 상호결합, G52서 합의 0.633로 제일 안 모이던 모양)서도 유지되나. 새 `combat_base`(6모듈 결정적 전투 RULE-01~10) 골격 + 카드 RULE-11 FATIGUE를 `--patch`로 → **게이트 11/11·합의 1.0·golden_diff 0**, 결합코어(독·게이지·우선순위·종료) 보존하며 FATIGUE 정확 패치·held-out verbatim. 골든 `gen_combat_l_golden.py`(REF node 역산, 회귀 5 바이트동일·FATIGUE 3 발동). **patch 메커니즘 도메인 무관 입증 = 측정 마지막 미지수 닫힘.** combat_base tracked·_combat_ref_tmp gitignore.
- **G74 패치빌드(§21.2 레버2) 배선 + ★키 3방식 비교 + 61KB 응력**: 레버4 위 `--patch` 모드 — touched 모듈도 통째 재출력 대신 안2(앵커/search-replace) FIND/REPLACE diff만 출력시키고 하네스가 base에 적용(`studio/patch_apply.py`). 포맷=안2(unified diff 줄번호 의존이 31B 최대 실패점이라 기각). 폴백=없음(PatchError→CARD). raw 응답 저장(`_raw_response.txt`/`_prompt.txt`) 추가. `_validate_l4_patch_keyless` ALL PASS. **★키 실측 — 로켓 l4(cmp_*)·station 61KB/46모듈(st_*) 둘 다 A·B·patch 셋 다 게이트 11/11·합의 1.0·golden_diff 0·patch 실패 0.** station서 §21.5 완전 실증: **출력 raw A 51.1KB vs B 0.7KB vs patch 0.5KB**(출력=게임크기 분리), **A held-out 드리프트 11/11**(tables.js 주석 패러프레이즈 + EVACUATE를 계약상 engine 아닌 actions.js에 재배치=모듈경계 침범) **vs B·patch 0/11**(verbatim 강제). A는 행동 1.0이어도 코드·모듈경계 보존 실패. **patch>B 출력우위 응력(st2_*): engine+tables(3.3KB) 둘 다 touched·EVACUATE 카드 → 둘 다 게이트 11/11·합의 1.0·tables verbatim, 출력 raw B 4.06KB vs patch 0.47KB(~8.6x)** — patch가 출력을 touched 모듈 크기와도 분리. patch모드 폴백 추가(touched 미패치=base verbatim). **patch가 B 상위호환 확정.** **+ 레버3 누적(l2_patch): 카드2(PING)를 카드1(EVACUATE) 위에 patch로, 13시나리오 1.0. + 레버3 3장 체인+서사 A겹(l3_patch): 카드3 비트(turn 2/3→BEAT-1/2)를 카드2 출력 위에 patch로, 누적 15시나리오 전원 게이트 11/11·합의 1.0·golden_diff 0, engine에 EVACUATE+PING+BEAT 셋 다·SCN-015 PING+BEAT 합성 통과.** **결정적 시뮬+누적+서사 A겹이 한 카드 체인에 다 올라간 첫 통합 — 측정 프로그램 사실상 닫힘.** 커밋 cfc82f0(배선)·0cb272f(로켓)·632c1e3(station)·0723a75(patch>B)·6d270d9(l2).
- **G73 후속 — A 재측정 행 + 출력 재프레이밍 + 사후채집(★키)**: 확장 카드(63.5KB)로 A 재측정 시도 → attempt03 소켓 무한행(`llm.py` 타임아웃 없음)·킬. **킬한 런 10 attempt를 사후 node채점(`_salvage_a_run.py` 키0)으로 A @ 63.5KB 결과 확보 — 정확도 100/100·전원합의·골든일치 1.0(A 재런 불필요, 행동적 저하 없음)**. 단 충실도 드리프트 발견: A는 verbatim 재출력에서 tables.js 주석 패러프레이즈(10/10)·EVACUATE를 actions.js로 재배치(2/10) — 행동 1.0이어도 코드 보존 못 함. **사용자 지적으로 재프레이밍**: 진짜 제약은 컨텍스트(256k,10%) 아니라 **출력 32k(추론 포함)**. A는 자기모순적 확장, **B(선택출력/패치)가 출력을 게임크기와 분리 + held-out verbatim 강제로 충실도까지 안전한 유일 스케일링 길**(build_graded:90·370-374). 측정 B 중심 전환.
- **G73 스케일 확장 카드 제작(키0)**: `station_base` 30→46모듈(본문 35.7KB→63.5KB, 1.77x). 신규 16(battery·medical·inventory·telemetry·thermalzones·structural·science·safety·navlog·radlog·habitat·report·airlock·coolant·attitude·waste) 전부 turn결정적·게이팅(population·research·credits) 불변·alerts/log+bounded morale만 → **gameStatus 다양성 보존(PLAYING×4·WON×2·LOST×1·EVACUATED×3)**·회귀7 base==ref 바이트동일·16모듈 전부 골든 기여(죽은코드0)·strict 게이트 46모듈 통과·run_keyless ALL PASS. contract RULE-02 ORDER·manifest 동기화. (커밋 9131978)
- **G73 레버4 스케일 1차 A/B(★키)**: 정거장 30모듈 같은 패킷 두 런 — A전체주입(graded-20260618-222413, 콜≈14.6k)·B선택주입(graded-20260618-223623, 콜≈5k). **둘 다 게이트 11/11·overall_agreement 1.0·golden_diffs 0**(회귀7+EVACUATE3 전부 1.0). EOL 정규화 대조 → engine.js만 실제 변경·held-out 29모듈 바이트동일(raw diff의 29모듈 차이는 전부 CRLF↔LF, node 채점이라 무해). **레버4 소프트 천장이 ~14.6k(로켓 3배)에선 안 잡힘** → A 흐려질 거란 가설 기각, ≤14.6k 아님이란 약한 하한만 확정. G72 판단대로 모듈 충실화로 30k 확장 후 재측정 분기.
- **G72 스케일 확장 대형카드 제작(키0)**: `station_base` 정거장 30모듈(코어8+확장12 서브시스템+오케스트레이션+데이터, turn기반 결정적 스케줄·난수0) + `planning_packet_station_l`(RULE-07 EVACUATE=engine만 touched) + `specqa_packet_station_l`(시나리오10=회귀7+EVACUATE3, 골든은 참조engine node역산 `gen_station_l_golden.py`). 게이트 strict 30모듈 통과·회귀7 base==참조 바이트동일·레버4 프롬프트 키0검증(engine본문O/나머지29 시그니처+verbatim). A전체주입≈14.6k vs B선택주입≈5k 콜토큰. **판단: 30~50k 목표지만 과투자 전 ~14.6k(로켓3배)로 1차 ★키 A/B 먼저, 저하 안 보이면 확장**. (gen 버그 1건 node가 잡음: scenarios.json input 래퍼 누락→수정).
- **G71 외부 코드리뷰 반영(키0)**: #2 게이트가 첫 시나리오만 종료코드 검사하던 실버그 → 전 시나리오 거부([build_graded.py:230]) · #1 FROZEN이 BLOCKING 흡수 수 미확인하던 오판 → 흡수 ≥ 질문 수일 때만 동결([planning.py:280]) 둘 다 픽스 + 키0 회귀잠금. #6 CI = `run_keyless.py` + `.github/workflows/keyless.yml`(push/PR마다 스위트, GitHub Actions 그린). #3(합의≠정확)·#4(oracle 동일모델)는 골렘 정답앵커가 합의 아닌 **실Node 골든**(모델독립)이라 규율로 정리 — 31B auto_oracle은 모호성 탐지기로만.
- **G70 레버4 첫 ★키 런**(graded-20260618-191818): 게이트 11/11·합의 8/8 전부 1.0·oracle 일치. 31B가 logic 본문 못 본 채 engine만 편집 → 회귀(SCN-001~006)+ABORT(SCN-007/008) 둘 다 1.0(attempt01 logic byte-identical·engine ABORT 핸들러 확인). **+ 31solo 강제**(config generator→31B, 26B 잔재 제거; G60~G64·G66의 "31B"는 사실 26B였음을 발견·정정) **+ vocab 핀 3패킷 31B 확인런 1.0 재현**(idle/eco_vocab/eco_selfsug, 26B 원본과 동일=재실험 불필요).
- **G68 누적 빌드 레버1~3**(graded-20260618-180934): 편집수렴·회귀무결·새기능 합의 1.0. · **G66 서사 B겹**(StoryForge, 로켓 4비트 대사+바이블, 검증 3/3). · **G65 로켓 첫 graded**(게이트 7/11, 합의 0.881, A겹 BEAT 발동·대기권→화성).
- 그 이전(G33~G64) = 사다리 측정·자율 oracle 루프·정량 트랙 → 아래 "지금 어디"·context-notes.

**불변 규칙**:
- 키 사용은 사용자 명시 go 뒤에만. **31solo**(31B만). 추천은 측정 가치로만 정한다(키 절약 이유로 안 바꿈).
- 정본: 설계 = `GolemStudioMode.md`(§21 확장·§6.1 모호성 사전), 결정 이유 = `context-notes.md`, 진행 = `checklist.md`.
- 프로젝트 구조: 루트(config·llm·observability·run_index·key_usage 5파일 + .env) 밑 `golem/`. `build_runs/`는 .gitignore(생성물).
- 키0 검증 스위트: `python golem/studio/run_keyless.py`(CI와 동일 — compileall + replay + 레버4 + 게이트#2 + FROZEN#1).
- 운영 가드레일 = context-notes G46. T1 계측 자동기록(consensus.json·reconcile_report.json). auto_summary.green_blocked(=auto_suspect>0)면 Green 금지(G57 #3).
- 레버4 재현 명령(참고): `python golem/studio/build_graded.py --base golem/studio/rocket_base --packet golem/studio/planning_packet_rocket_l4 --specqa golem/studio/specqa_packet_rocket_l4 --inject-modules src/engine.js --reconcile`

## 지금 어디 — §13 파이프라인 배경 (2026-06-18)

Golem Studio = `GolemStudioMode.md` §13 파이프라인을 실모델로 구축. 아이디어 한 줄로 **Step 1~7 전부 실제 완주**(방치형·발열 두 카드). 하네스는 계약구동으로 일반화돼 새 카드는 코드변경 0. 합의-vs-oracle 자동 해소(`reconcile.py`)+저합의 가드(G50)까지 갖춤. 산출물은 `golem/studio/`(패킷: 방치형=`*_packet`, 발열=`*_packet_heat`, 턴제전투(고결합)=`*_packet_combat`).

| §13 단계 | 코드 | 산출/상태 |
|---|---|---|
| Step1 v0.1 Contract Microkernel | `contract_validator.py`·`replay.py` | replay 12/12(키0). `static_gate.py` src/ 확장(strict 모드 보유). |
| Step2 Planning | `planning.py` | A/B/C 측정 + synthesis. FROZEN=BLOCKING 흡수수 확인(G71). A6<B11<C27. |
| Step3 Design | `design.py` | 4모듈 분해(utils←state_manager←engine←main)+traceability, §7·§8.2 PASS → `design_packet/`. |
| Step4 Spec QA | `specqa.py` | 11 시나리오 구체화 → `specqa_packet/`. (잔여 결함: BLOCKING 추적은 planning에서 G71 보강.) |
| Step5 Build v1 | `build_graded.py` | design 4모듈+시나리오+**합의 채점**(특권 golden 아님). `--base` 편집모드·`--inject-modules` 선택주입. 게이트=전 시나리오 종료코드(G71). |
| Step6 Adversarial QA | `adversarial.py` | 팀이 edge_cases 13+acceptance 5. EDGE-011/012 크래시 → 계약 명문화로 소거, 유효빌드 edge 7/7 수렴. |
| Step7 Integration | `integration.py` | 수렴 빌드 재사용(키0) → 최종 workspace+static_gate+golden+final_report. 방치형 24/24·발열 13/13. |
| 자동해소 | `reconcile.py` | Build 합의 vs golden 자동 diff(키0) + 31B 진단(CONTRACT_AMBIGUOUS/ORACLE_BUG/BUILD_BUG) + `--apply`(AUTO만) + 저합의 가드(G50) + `--auto-oracle`(손golden 대신 31B 자율). |

**핵심 측정(G33~G40)** — Build 합의(특권 golden 아닌 다수합의)로 "계약이 얼마나 빡빡한가"를 잰다. 한 번에 한 변수.
- 출력계약 미고정 0.36 → 출력 고정 0.66 → 입력 스키마 고정 0.98 → 평가시점 명문화 1.0. **사다리 = 계약 한 칸 박을 때마다 한 칸 수렴.**
- adversarial이 찾은 구멍(EDGE-011/012)을 계약에 박으니 그 엣지도 7/7 수렴(G38). logs 채점 추가로 미지id 로그도 6/6(G39). Step7 E2E golden 24/24(G40) = 아이디어 한 줄→전 파이프라인 완주.

**정량 트랙 결론(G52~G58)**: 합의를 정하는 건 결합도 아니라 **계약 빡빡함 — 단 규칙 종류 의존**. 종료조항(RULE-10) 올림 d≈3 4회 재현 / PHASE 순서(RULE-11) 안 올림 / 결합도 가설 기각(eco 0.925 vs combat 0.633). 도구 `multiseed.py`·`sweep.py`.

**자율 oracle 트랙 결론(G60~G64) — 루프 닫힘**: 31B(당시 실제 26B)가 빌드 0줄로 골든 자율생성(G60 0.879) → 어휘 박으니 1.0(G61) → 고결합 eco도 1.0(G63) → 31B가 자기 불일치 읽고 계약 자율 처방, 박으니 1.0(G64). **생성→탐지→처방→수렴 = self-correcting 완결.** 결합도는 계산 안 깨뜨림, 실패는 항상 계약 모호이고 박으면 닫힘. 도구 `auto_oracle.py`·`self_suggest.py`(키별 `key_accuracy_by_name`로 봐야 함).

**서사 2겹**: A겹=결정적 발동로직(golden 검증, 로켓 BEAT 6/6 1.0) + B겹=텍스트 저작데이터(StoryForge, 출력전용). 모호성 종류는 `GolemStudioMode.md` §6.1 모호성 사전에 등재(반응적 핀→사전 차단).

읽는 순서: 이 파일 → 필요할 때 `context-notes.md`(G73 스케일 측정·출력 재프레이밍·B 프로브 최근, G60~G64 자율oracle, G46 가드레일) / `GolemStudioMode.md` §21.5(출력 천장)·§6.1 / `checklist.md`.

## 다음 액션

**★ 북극성(목표) = `GolemStudioMode.md` §1.5 다작·선별 퍼널.** 단발 게임이 아니라 `생성→[싼 사전필터]→사람 판단→[실노출 신호]→더블다운`. 골렘은 "안 깨졌나"를 공짜로 걸러 사람 판단을 "재미있나"에만 쓰게 한다. 대괄호 두 조각(싼 사전필터·실노출)이 골렘이 지어야 할 미완성 부분. 병목은 생성 아니라 선별+품질. 모든 다음 액션은 이 목표에 종속.

1. **전술 SRPG(영걸전형) — 골렘이 설계하는 새 장르. 작은 커널부터 누적. 다음=하네스 fix→planning 재런(★키).** 에테르노 IF 브리지는 l1 그린으로 닫혔고(G81), 사용자가 IF는 취향 아님→전술 SRPG로 피벗. **핵심 규율(G81): 골렘이 설계한다(planning→design→build), 클로드는 손으로 base 안 씀·하네스만 조임.** 작은 커널(작은 격자·영웅1 vs 적1·상하좌우 이동·인접공격·처치=승리, 결정적)부터 골렘이 산출 → 카드 누적(변칙검술 마나방패+ANOMALY → 사거리 → 지형 → 유닛 → 루트 맵). 에테르노 스토리(`bridge_eterno/STRUCTURE.md` 12장면)는 캠페인 루트 콘텐츠(엔진과 분리, 내일 10권 풀스토리로 교체).
   - **현재 상태: 전술 커널 planning ★키 런 = OPEN(하네스 결함). 패킷=`planning_packet_tactics_kernel`.** 골렘 설계는 양호, FROZEN 못 박은 건 `planning.py:262` 중복 BLOCKING 카운팅 결함(위 G81 블록).
   - **다음 첫 동작 = 하네스 fix(중복 BLOCKING dedup 또는 synthesis unresolved 명시) → `planning.py` 재런 → FROZEN 확인 → `design.py`(★키).** 단계마다 끊어 보고 골렘 출력 검토.
   - 비주얼은 나중(골렘이 룰 소진 후): 정사각 탑다운부터, 에셋팩+이미지→타일맵 추출+고도. 클로드 외형(엔진 읽기전용)·각색충실도·밸런스=사람.
2. **(목표 핵심 인프라) 싼 사전필터 조각 ① — 닫힘(G77).** 카드 자동 제안(B+검토) `card_proposer.py`에 레저(RAG) 주입 + 사전필터 신호(static_gate·직전 골든 회귀·발동 커버리지·결정성·구조 스코프)층. `cardgen_ledger.py` + `cardgen/`(L-001~L-005·E-001/E-002). **소코반 card4로 두 판정 다 실증**: Boost/Crumbling 제안이 "커버리지 1<2"로 자동 FLAG → 워크드 격자 few-shot 보강 후 Crumbling Floor가 발동 4·회귀 0·클린 구조로 PASS_PREFILTER. **부수 발견: 산문 교훈(L-005)만으론 31B 격자 좌표 약점 못 막아 few-shot 예시가 필요(교훈 종류 차이).** 커밋 7cbccc4·141d138. 모델-비평가는 여전히 불완전한 취향 대리(PASS도 '그럴듯하게 틀린' REF는 사람이 대조).
3. (곁가지) XL을 1000+모듈로 더 밀어 천장 계속 추적(한계효용↓) / combat 자율oracle / 외부리뷰 P1(#10).
3. (backlog) levels 등 출력표면 확장 / 발열 Adversarial QA·Integration 정식 완주 / CI actions Node20→최신 버전업(경고만, 실패 아님).

**완료 이력(G49~G73)**: AUTO검증·저합의 가드(G49·G50) → 프로젝트 승격(2026-06-17) → 정량 트랙 multiseed·sweep(G53~G58) → 외부리뷰 P0(G57) → 자율 oracle 루프(G60~G64) → 로켓 A겹(G65 graded)·B겹(G66 StoryForge) → 누적 빌드 레버1~3(G67·G68)·레버4 배선(G69)·레버4 ★키 런+31solo(G70) → 외부리뷰 #1·#2·#6 반영+CI(G71) → 스케일 확장 대형카드(정거장 30모듈)+EVACUATE 패킷·골든 키0(G72) → **G73 스케일 측정 한 묶음**: 1차 A/B ★키(둘 다 1.0, 천장 ~14.6k 미포착) → 카드 1.77x(46모듈) 확장 → A 재측정 소켓행→킬·사후채집 A@63.5KB=1.0(드리프트 발견) → **출력 32k 재프레이밍**(진짜 벽=출력, B=스케일링 길) → 확장 B=1.0·drift0 → **B 입력 프로브 546모듈서도 1.0·drift0(천장 미포착)** → llm.py 타임아웃 안전망. 상세는 context-notes 동일 G번호.
