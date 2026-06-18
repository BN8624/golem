
## 레버4 — 선택적 컨텍스트 (G69 배선 → G70 ★키 런으로 닫힘 ✅)
- [x] 하네스: `build_graded --inject-modules` (touched=full주입+재생성 / held-out=시그니처 스텁+verbatim 복사)
- [x] 인터페이스 스텁 추출 `_iface_stub` (exports 시그니처만, 본문 숨김)
- [x] held-out 모듈 워크스페이스 verbatim 복사 (재생성 안 함)
- [x] 셀렉티브 EDIT 헤더 (touched만 출력하라)
- [x] l4 프로브 패킷 `planning_packet_rocket_l4` (ABORT=RULE-07, engine.js만 touched)
- [x] l4 specqa `specqa_packet_rocket_l4` (회귀6 + ABORT 2, 골든은 rocket_base 실행 역산)
- [x] 키0 검증: 프롬프트에 engine 본문 O / logic 본문 X·시그니처 O / held-out verbatim 복사 / 골든 로컬재현
- [x] (★키) build_graded 실행 → 회귀무결+ABORT 합의 1.0 (G70 graded-20260618-191818, 레버4 메커니즘 닫힘)

## 스케일 확장 — 레버4 소프트 천장 측정 (리뷰 #5, 키0 카드제작 ✅ → ★키 A/B 대기)
설계: 대형 카드 "정거장 OS"(30모듈), 신기능 EVACUATE(engine.js만 touched)=로켓 l4 ABORT의 규모확장판. 변수=컨텍스트 크기 하나.
- [x] station_base 30모듈 작성 (코어 8 + 확장 12 서브시스템 + util·tables·labels·grid 등)
- [x] module_manifest.json (require 그래프 무순환·전부 main 도달, 30모듈)
- [x] node로 베이스 결정적 실행 확인 (WON/LOST/회귀 결정적)
- [x] static_gate + contract_validator(strict) 통과
- [x] planning_packet_station_l (concept.md + contract.json, RULE-07 EVACUATE 포함)
- [x] 참조 engine(EVACUATE) → node 역산으로 골든 생성 (gen_station_l_golden.py)
- [x] specqa_packet_station_l (회귀7 + EVACUATE3, 시나리오 10, expected=참조 역산)
- [x] 회귀 시나리오 base==참조 바이트동일 확인 (7/7)
- [x] 베이스 토큰량 측정 — A(전체주입)≈14.6k·B(선택주입)≈5k 콜토큰 (로켓 3배). 30k는 1차 저하시 추가확장
- [x] 레버4 프롬프트 키0 검증 (engine 본문O / 나머지29 시그니처+verbatim / 채점10)
- [x] (★키) 1차 A/B @ ~14.6k: 둘 다 게이트11/11·합의1.0·golden_diff0(graded-222413/223623). 천장 미포착(G73)
- [x] 카드 1.77x 확장(46모듈, 신규16 진단서브시스템): 다양성 보존·죽은코드0·strict46통과·run_keyless ALL PASS(커밋9131978)
- [x] A 재측정 소켓행→킬→사후채집: A@63.5KB=정확도100/100·1.0. 단 verbatim 드리프트(tables주석10/10·EVACUATE재배치2/10)
- [x] **출력 32k 재프레이밍**: 진짜 벽=컨텍스트(256k,10%) 아니라 출력. A는 자기모순, B(선택출력)가 스케일링 길(GolemStudioMode §21.5 정정)
- [x] (★키) 확장 카드 B @ 46모듈: 게이트11/11·합의1.0·golden_diff0·held-out 드리프트0(graded-005137)
- [x] (★키) B 입력 lost-in-the-middle 프로브: gen_station_xl.py로 546모듈(입력~24k)·B=1.0·drift0/545(graded-011018). B는 모듈 수 무관
- [x] llm.py per-request 타임아웃 안전망(30분)·좀비소켓 무한행 차단(커밋466a5cb)
- [ ] (다음) 패치빌드(파일별/diff) 라인을 §21 대형게임 정본과 정합 — B로 진짜 큰 게임 짓기
