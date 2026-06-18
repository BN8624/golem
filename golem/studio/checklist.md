
## 레버4 — 선택적 컨텍스트 (G69, 키0 배선 → ★키 검증)
- [ ] 하네스: `build_graded --inject-modules` (touched=full주입+재생성 / held-out=시그니처 스텁+verbatim 복사)
- [ ] 인터페이스 스텁 추출 `_iface_stub` (exports 시그니처만, 본문 숨김)
- [ ] held-out 모듈 워크스페이스 verbatim 복사 (재생성 안 함)
- [ ] 셀렉티브 EDIT 헤더 (touched만 출력하라)
- [ ] l4 프로브 패킷 `planning_packet_rocket_l4` (ABORT=RULE-07, engine.js만 touched)
- [ ] l4 specqa `specqa_packet_rocket_l4` (회귀6 + ABORT 2, 골든은 rocket_base 실행 역산)
- [ ] 키0 검증: 프롬프트에 engine 본문 O / logic 본문 X·시그니처 O / held-out verbatim 복사 / 골든 로컬재현
- [ ] (★키) build_graded 실행 → 회귀무결+ABORT 합의 1.0이면 레버4 메커니즘 닫힘
