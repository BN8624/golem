# 시스템 설계 — 다중유닛(능동적 적 AI) 전술 격자 커널

결정적 턴제. 영웅 1명과 적 N명이 정사각 격자(gridSize)에서 싸운다. Math.random 금지·시나리오 구동·CommonJS.

## 모듈
- main.js: `--scenario N` 파싱 → `getScenario(N)`로 {initialState, actions} 획득 → `runScenario` 실행 → 최종 상태를 출력계약 5필드로 stdout 출력.
- src/scenarios.js: 하네스가 계약 세계로 써넣음(getScenario(n)=1-based n번째 {initialState, actions}). 직접 만들지 말 것.
- src/engine.js: `runScenario(initialState, actionSequence)` — turn=0에서 시작, 매 영웅 액션마다 `updateState` 후 `checkGameState`. 결과 있으면 그 status로 종료, 없으면 액션 소진 후 status='FINISHED'. `{state, status}` 반환.
- src/game_logic.js: `applyAction`(영웅 1액션 적용)·`updateState`(영웅 액션 → 적 페이즈 → turn+1)·`checkGameState`(승패).

## 상태
hero {hp, atk, pos:[x,y]}, enemies [{id, hp, atk, pos:[x,y]}], gridSize, turn.

## 규칙(결정적)
1. 영웅 MOVE: pos+dir. 격자 밖(0..gridSize-1) 또는 살아있는 적이 점유한 칸이면 이동 실패(턴은 소비).
2. 영웅 ATTACK: 맨해튼 거리 1인 살아있는 적 중 **가장 작은 id**를 target_hp -= hero.atk.
3. updateState: 영웅 액션 적용 → 적이 모두 죽지 않았으면 적 페이즈 실행 → turn += 1. (영웅이 마지막 적을 처치하면 적 페이즈 생략.)
4. 적 페이즈(매 영웅 액션 직후): 살아있는 적을 **id 오름차순**으로, 각 적이 1행동.
   - 영웅과 맨해튼 거리 1이면 이동 대신 공격(hero.hp -= enemy.atk).
   - 아니면 4방향(상하좌우) 중 **영웅과의 맨해튼 거리를 줄이는** 칸들(격자 안·영웅/다른 살아있는 적 미점유)만 후보. 후보 중 타이브레이크로 하나 선택해 이동: ① X축 이동 우선(상하보다 좌우) ② 결과 x 작은 쪽 ③ 결과 y 작은 쪽. 후보 없으면 정지.
5. 승패(checkGameState, 매 영웅 액션+적 페이즈 후): 적 전멸=VICTORY, 영웅 hp<=0=DEFEAT, 그 외 진행.

## 출력계약(정확히 5필드, 그 외 출력 금지)
status: <PLAYING|VICTORY|DEFEAT|FINISHED>, turn: <int>, hero_hp: <int>, hero_pos: [x,y], enemies: [{id,hp,pos:[x,y]} ascending id, atk 제외].

## turn 카운터(핀)
적용된 모든 영웅 액션마다 turn += 1 — VICTORY/DEFEAT를 유발하는 액션도 포함한다. 액션1에 즉시 승리해도 turn=1.
