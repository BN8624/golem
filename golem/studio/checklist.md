
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
- [ ] (★키) A: build_graded --base만 / B: --base --inject-modules src/engine.js → 정확도 대조
