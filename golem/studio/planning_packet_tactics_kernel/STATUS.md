# STATUS

- 아이디어: 에테르노 세계관의 턴제 전술 그리드 전투 게임. 작은 사각 격자에서 영웅 유닛 1명이 상하좌우로 한 칸씩 이동하고, 인접한 적 유닛을 공격한다. 공격하면 적 HP를 영웅 공격력만큼 깎고, 동시에 영웅도 적 공격력만큼 반격 피해를 받는다(HP는 음수까지 내려갈 수 있다). 모든 유닛(영웅과 모든 적)의 초기 위치는 서로 겹치지 않는다. 승리와 패배 판정은 각 액션을 처리한 직후에만 한다. 게임 시작 시점이나 액션 처리 전에는 판정하지 않는다. 처음에 존재한 적이 모두 HP<=0이 되면 status=VICTORY, 영웅이 HP<=0이 되면 DEFEAT(VICTORY보다 우선), 둘 다 아닌 채 액션 시퀀스가 끝나면 FINISHED. 적이 처음부터 0마리여도 시작 즉시 VICTORY가 아니라 시퀀스를 끝까지 처리한 뒤 FINISHED가 된다. 실행은 시나리오 구동이다: 하드코딩된 SCENARIOS를 명령행 인자 --scenario N으로 골라 그 시나리오의 고정 액션 시퀀스를 순서대로 적용한다. 모든 액션 시도마다 성공 실패와 무관하게 turn을 1 증가시킨다. 시나리오를 끝까지 처리한 뒤 프로그램은 정확히 한 줄의 JSON을 stdout에 출력한다. 출력 객체는 정확히 다음 다섯 개의 최상위 키만 가진다: status, turn, hero_hp, hero_pos, enemies. hero_pos는 [x,y] 배열이다. enemies는 배열이며 각 원소는 정확히 id, hp, pos 세 필드만 가진다. pos는 [x,y]이고, atk나 maxHp 같은 다른 필드는 출력하지 않는다. stdin이나 대화형 입력을 쓰지 않으며, 모든 규칙은 결정적이고 난수를 쓰지 않는다.
- 리뷰어 BLOCKING 원본 9 → distinct 9(중복 제거)
- 흡수: decisions 10 / assumed 2 / deferred 1
- 미해소 BLOCKING(흡수 부족분): 0
- interface_contract 파일 수: 3
- acceptance_tests 수: 4

CONTRACT_STATUS: FROZEN
