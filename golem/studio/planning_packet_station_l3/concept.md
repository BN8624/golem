# 정거장 OS 대형카드 l3 — 서사 비트 A겹 (레버3 누적빌드 카드 3)

이전 카드 둘(l EVACUATE, l2 PING)이 이미 얹힌 정거장 코드베이스 **위에** 서사 비트(A겹)를 더 얹는
누적 빌드 카드다. 빌더가 받는 engine.js엔 EVACUATE·PING 분기가 이미 들어 있고, 이번엔 RULE-10만 추가한다.

서사 2겹 중 **A겹 = 결정적 발동 로직**이다("상태 조건 → 비트 발동"). 골든으로 채점 가능한 뼈대이며,
실제 대사(B겹)는 이 카드 범위 밖이다(출력 전용·정확일치 안 잼). 이번 카드도 engine.js **한 곳만** 건드린다.

- RULE-10: WAIT 틱이 끝난 직후 gameStatus가 'PLAYING'이면, turn이 처음 2가 될 때 log에 'BEAT-1',
  처음 3이 될 때 'BEAT-2'를 한 번씩 덧붙인다. 그 turn 값에서만(각 1회)·PLAYING일 때만 발동하고
  BUILD/RATION/PING/EVACUATE에는 발동하지 않는다. 비트는 해당 턴 서브시스템 틱 로그 뒤에 붙는다.
- EVACUATE·PING 분기와 WAIT/BUILD/RATION 디스패치는 그대로 보존한다(이전 카드 정본).
- turn이 2·3에 안 닿는 시나리오는 글자 하나 안 바뀐다(이전 PING 카드 출력과 바이트동일 = 누적회귀 무결).
- 핵심 검증: 빌더가 **두 번 편집된 engine.js 위에** 비트 발동을 정확히 패치로 얹으면서 EVACUATE·PING과
  나머지 디스패치를 보존하나. card1(EVACUATE)+card2(PING)+card3(BEAT)을 누적으로 다 통과하나.
- A겹 비트 키(BEAT-1/BEAT-2)는 엔진 마일스톤과 공유하는 계약이다(B겹 대사가 나중에 이 키로 붙는다).
