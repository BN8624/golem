# 로켓 우주여정 방치형 l4 — ABORT 중단 (레버4 선택적 컨텍스트 프로브)

베이스 로켓 카드(WAIT 연료 / ADVANCE 단계)에 **ABORT 액션**을 얹는 누적 빌드 카드다.
이번 카드는 액션 루프(engine.js) 한 곳만 건드린다 — 그래서 **레버4(선택적 컨텍스트)** 프로브다.
빌더는 engine.js 본문만 받고, logic.js·constants.js·main.js는 **본문 없이 시그니처(인터페이스)만** 본다.

- ABORT: gameStatus를 'ABORTED'로 바꾸고 즉시 중단(WON과 동형). turn·fuel·stage 불변, 비트 없음.
- 출력 계약 키는 그대로(gameStatus enum에 ABORTED만 추가). ABORT를 안 쓰는 기존 시나리오는 글자 하나 안 바뀐다(회귀 무결).
- 핵심 검증: 빌더가 logic의 createInitialState·applyWait·applyAdvance를 **본문을 못 본 채** 시그니처대로 호출해 engine만 정확히 편집하나. 큰 게임에서 "건드리는 모듈만 컨텍스트에 넣는다"의 토대.
- 텍스트/서사는 이 카드 범위 밖.
