# STATUS

- 아이디어: 다중 아군 전술 격자 커널(squad) — 능동적 적 AI 위에 아군을 1명에서 여럿으로 일반화. 정사각 격자에 아군 유닛 여럿(allies)과 적 유닛 여럿(enemies)이 있고 각 유닛은 {id, hp, atk, pos}. 시나리오가 액션 시퀀스를 주는데 각 액션은 어느 아군이 행동하는지 지정한다: {unit: 아군id, type: "move"(dir 상하좌우) 또는 "attack"}. 매 아군 액션 직후, 살아있는 모든 적이 적 id 오름차순으로 결정적 AI 1행동을 한다: 자신에게 맨해튼 거리가 가장 가까운 살아있는 아군을 목표로 고르고(거리 동률이면 아군 id 작은 쪽), 그 목표 아군과 인접(맨해튼 1)이면 이동 대신 공격해 목표 아군 hp를 적 atk만큼 깎는다. 인접이 아니면 목표 아군에게 맨해튼 거리를 줄이는 칸들(격자 0..gridSize-1 안·다른 살아있는 유닛 미점유) 중에서 타이브레이크로 한 칸 이동한다(X축 이동 우선→결과 x 작은 쪽→결과 y 작은 쪽). 거리 줄이는 이동이 다 막히면 정지. 아군 MOVE는 격자 밖이거나 다른 살아있는 유닛이 점유한 칸이면 실패(턴은 소비). 아군 ATTACK은 자신과 인접한 살아있는 적 중 id 최소를 골라 그 적 hp를 아군 atk만큼 깎는다. 적 전멸=VICTORY, 아군 전멸=DEFEAT, 액션 소진되고 미결=FINISHED. turn은 적용된 모든 아군 액션마다 +1(VICTORY/DEFEAT를 유발하는 액션도 포함). 완전 결정적(Math.random 금지)·시나리오 구동·stdin/네트워크/파일시스템 금지·CommonJS. 출력은 평면 필드: status, turn, allies는 [{id,hp,pos:[x,y]}] (id 오름차순), enemies는 [{id,hp,pos:[x,y]}] (id 오름차순). 이전 커널은 아군이 영웅 1명이었고, 이번 핵심 차이는 아군이 여럿이고 액션이 어느 아군인지 지정하는 것이다.
- 리뷰어 BLOCKING 원본 8 → distinct 7(중복 제거)
- 흡수: decisions 9 / assumed 2 / deferred 2
- 미해소 BLOCKING(흡수 부족분): 0
- interface_contract 파일 수: 2
- acceptance_tests 수: 4

CONTRACT_STATUS: FROZEN
