# 포팅 사양서 — squad 룰(JS) → Godot GDScript (골렘이 Phase 1에서 작성)

이 문서는 **골렘에게 줄 작업 지시**다(클로드가 작성한 하네스). 골렘은 검증된 JS 룰을 GDScript로
포팅해 `res://scripts/rules.gd`를 만든다. 정답은 `test/rules_golden.json`(JS 엔진이 생성)이고,
`test/run_rules_golden.gd`가 0-diff로 대조한다.

## 산출물
`godot/scripts/rules.gd` 단 하나. 아래 인터페이스·불변식을 정확히 지켜야 한다.

## 인터페이스 (러너가 이렇게 호출함)
```gdscript
extends RefCounted
# state, action 은 JSON에서 온 Dictionary. update_state 는 state 를 제자리 변경하고 status 문자열 반환.
func update_state(state: Dictionary, action: Dictionary) -> String   # "VICTORY" | "DEFEAT" | "PLAYING"
func check_game_state(state: Dictionary) -> String
func apply_action(state: Dictionary, action: Dictionary) -> void
```
- `state` = `{ "gridSize": int, "allies": Array, "enemies": Array, "turn": int }`.
  유닛 = `{ "id", "hp", "atk", "pos":[x,y], 그리고 카드 필드(range/knockback/flank_bonus/reflect_dmg/...) 옵션 }`.
- `action` = `{ "unit": int, "type": "move"|"attack", "dir":[dx,dy](move일 때) }`.

## 불변식 (반드시)
1. **순수 모듈이다 — Node 상속·씬 참조·get_node·_process 금지.** RefCounted만. 씬은 나중에 이걸 호출만 한다.
2. **결정적 — RNG·시간·난수 금지.** 동률 타이브레이크까지 JS와 동일(적 AI: 가장 가까운 아군, 거리 동률은 id 작은 쪽; 이동 후보 정렬은 X축 우선→작은 x→작은 y).
3. **state 제자리 변경 + status 반환** (JS updateState와 동일 흐름: 아군 액션 → 승리 체크 → 적 AI id오름차순 → 패배 체크 → turn++).
4. **죽은 유닛도 로스터에 유지**(hp 음수로 남김, 배열에서 제거 금지). 렌더러/골든 호환.
5. JSON 숫자가 float로 와도 좌표·hp 계산이 JS 정수 결과와 값이 같아야 한다.

## 검증
`godot --headless --path godot --script res://test/run_rules_golden.gd` →
`골든 대조: N/N 통과, 0 실패` 가 나와야 채택. 실패 라인(케이스·스텝·status/state)을 골렘에 되먹여 재포팅.

## 참조 — 포팅 원본(JS, 변경 금지·동치로 옮길 것)
원본 파일: `golem/tactics/bases/squad_base_l8/src/game_logic.js`. 핵심 규칙:
- `manhattan`, `isOccupied`(살아있는 유닛이 점유).
- `applyAction`: move=경계·점유 검사 후 이동 / attack=사거리내(>=1,<=range) 적 중 id최소 타깃, 데미지=atk(+flank_bonus×인접아군수, +asymmetric_strike 조건), 적 aura_shield·phalanx_defense 감산, reflect_dmg 반사(아군 aura_shield 감산), knockback(타깃을 같은 방향 한 칸, 경계·점유·unmovable 검사).
- `executeEnemyAI`: 가장 가까운 아군(거리 동률 id) 타깃, 인접이면 공격(대칭 룰), 아니면 거리 줄이는 칸으로 이동(정렬 X우선→작은x→작은y).
- `checkGameState`: 적 전멸=VICTORY, 아군 전멸=DEFEAT, 아니면 PLAYING.
- `updateState`: applyAction → VICTORY면 turn++ 반환 / 적 AI 루프(중 DEFEAT면 turn++ 반환) → turn++ PLAYING.
