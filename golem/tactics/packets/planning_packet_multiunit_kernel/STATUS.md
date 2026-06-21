# STATUS

- 아이디어: 최소 전술 격자 커널 + 능동적 적(적 AI). 정사각 격자에 영웅 1명과 적 N명이 있고 각 유닛은 {id, hp, atk, pos}. 결정적 라운드제 — 시나리오가 영웅 액션 시퀀스(상하좌우 이동 또는 인접한 적 공격)를 주고, 매 영웅 액션 직후 살아있는 모든 적이 결정적 AI로 1행동한다: 영웅과 인접(맨해튼 거리 1)이면 이동 대신 영웅을 공격해 영웅 hp를 적 atk만큼 깎고, 인접이 아니면 영웅에게 가장 가까워지는 방향으로 1칸 이동한다(여러 후보가 같은 거리면 결정적 타이브레이크: 격자 차원 순서·좌표 작은 쪽). 막힌 칸(격자 밖·다른 유닛 점유)으로는 못 간다. 적 전멸=VICTORY, 영웅 hp<=0=DEFEAT, 액션 소진되고 미결=FINISHED. 완전 결정적(Math.random 금지)·시나리오 구동·stdin/네트워크/파일시스템 금지·CommonJS. 출력은 평면 5필드(status, turn, hero_hp, hero_pos, enemies는 [{id,hp,pos}] 배열). 적이 능동적으로 이동·공격하는 것이 이전 정적-적 커널과의 핵심 차이다.
- 리뷰어 BLOCKING 원본 17 → distinct 14(중복 제거)
- 흡수: decisions 9 / assumed 2 / deferred 0
- 미해소 BLOCKING(흡수 부족분): 3
- interface_contract 파일 수: 2
- acceptance_tests 수: 3

CONTRACT_STATUS: OPEN (BLOCKING 미해소)
