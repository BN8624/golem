# 시스템 설계 — 다중 아군(squad) 전술 격자 커널

결정적 턴제. 아군 유닛 여럿(allies)과 적 유닛 여럿(enemies)이 정사각 격자(gridSize)에서 싸운다. Math.random 금지·시나리오 구동·CommonJS.

## 모듈
- main.js: `--scenario N` 파싱 → `getScenario(N)`로 {initialState, actions} 획득 → `runScenario` → 출력계약 필드를 stdout 출력.
- src/scenarios.js: 하네스가 계약 세계로 써넣음(getScenario(n)=1-based n번째). 직접 만들지 말 것.
- src/engine.js: `runScenario(initialState, actionSequence)` — turn=0 시작, 매 액션마다 `updateState` 후 `checkGameState`. 결과 있으면 그 status로 종료, 없으면 소진 후 'FINISHED'. `{state, status}` 반환.
- src/game_logic.js: `applyAction`(지정 아군 1액션)·`updateState`(아군 액션 → 적 페이즈 → turn+1)·`checkGameState`(승패).

## 상태
allies [{id, hp, atk, pos:[x,y]}], enemies [{id, hp, atk, pos:[x,y]}], gridSize, turn. 점유 = 살아있는 아군/적 누구든 그 칸에 있으면.

## 규칙(결정적)
1. 액션은 어느 아군이 행동하는지 지정: {unit: 아군id, type: "move"(dir) | "attack"}. unit이 죽었거나 없으면 무효(턴 소비).
2. 아군 MOVE: pos+dir. 격자 밖(0..gridSize-1) 또는 살아있는 유닛 점유칸이면 실패(턴 소비).
3. 아군 ATTACK: 맨해튼 1인 살아있는 적 중 가장 작은 id를 target_hp -= 아군.atk.
4. updateState: 아군 액션 적용 → 적이 모두 죽지 않았으면 적 페이즈 → turn += 1.
5. 적 페이즈: 살아있는 적을 id 오름차순으로 1행동.
   - 목표 = 자신에게 맨해튼 거리가 가장 가까운 살아있는 아군(동률은 아군 id 작은 쪽). 살아있는 아군 없으면 행동 종료.
   - 목표와 맨해튼 1이면 이동 대신 공격(목표 아군 hp -= 적.atk).
   - 아니면 목표로 거리 줄이는 칸들(격자 안·점유 안 됨)만 후보. 타이브레이크 ① X축 이동 우선 ② 결과 x 작은 쪽 ③ 결과 y 작은 쪽. 후보 없으면 정지.
6. 승패: 적 전멸=VICTORY, 아군 전멸=DEFEAT, 그 외 진행. turn은 적용된 모든 아군 액션마다 +1(끝내는 액션 포함).

## 출력계약(정확히 4필드, 그 외 출력 금지)
status: <PLAYING|VICTORY|DEFEAT|FINISHED>, turn: <int>, allies: [{id,hp,pos:[x,y]} ascending id], enemies: [{id,hp,pos:[x,y]} ascending id]. atk 제외.

## 출력 로스터(핀)
allies·enemies는 항상 초기 상태의 모든 유닛을 id 오름차순으로 담는다 — hp가 0 이하로 떨어진 죽은 유닛도 제거하지 말고 유지한다(기존 전술 base 관례·렌더러 호환).
