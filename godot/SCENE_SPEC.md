# 씬 사양서 — 플레이 가능한 전술 씬 (골렘이 Phase 2에서 작성)

골렘은 검증된 `res://scripts/rules.gd`(절대 수정 금지)를 호출만 하는 **플레이 씬 스크립트**
`res://scripts/board.gd`를 만든다. 클로드가 래퍼 씬 `res://scenes/main.tscn`(루트 Node2D에 board.gd 부착)과
헤드리스 스모크를 제공한다.

## 산출물
`godot/scripts/board.gd` 단 하나. 아래를 지킨다.

## 인터페이스·로딩
- `extends Node2D`. 첫 줄은 역할을 적은 한 줄 한국어 주석.
- `_ready()`에서:
  - 룰 로드: `var rules = load("res://scripts/rules.gd").new()` — 모든 룰 결과는 `rules.update_state(state, action)`로만.
  - 레벨 로드: `res://data/squad_levels.json` = Array. 각 원소 `{ "name", "desc", "teaches", "initialState" }`.
    `initialState` = `{ "gridSize":int, "allies":[...], "enemies":[...] }`. 유닛 = `{ "id","hp","atk","pos":[x,y], 카드필드(range/knockback/...) }`.
  - 현재 미션 인덱스 0부터. 상태 = 미션 initialState 깊은 복제 + `turn=0`.

## 렌더 (`_draw`)
- 정사각 격자 gridSize×gridSize, 화면 ~640px에 맞춤.
- 아군 = 파란 원, 적 = 빨간 원, 각 원에 id와 hp 텍스트. hp<=0(죽음)은 흐리게 + ✕.
- 선택된 아군은 테두리 강조.
- `_ready`에서 Label 하나 add_child 해서 "미션명 · 턴 · 상태(PLAYING/VICTORY/DEFEAT)" 표시. 상태 바뀌면 갱신.

## 입력 (`_unhandled_input`, 좌클릭)
- 클릭한 셀에 살아있는 내 아군 → 그 아군 선택.
- 아군이 선택된 상태에서:
  - 빈 셀이 직교 인접(맨해튼 1) → `update_state(state, {"unit":선택id, "type":"move", "dir":[dx,dy]})`.
  - 적이 선택 아군 사거리 내(맨해튼 <= range, 기본 1, >=1) → `update_state(state, {"unit":선택id, "type":"attack"})`.
- 매 액션 후: 반환 status로 Label 갱신, `queue_redraw()`. VICTORY/DEFEAT면 입력 잠금.
- 키: `R` 현재 미션 리셋, `N` 다음 미션(끝이면 처음으로).

## 불변식
1. **rules.gd 수정·재구현 금지.** 룰 판정은 전부 update_state 경유. 씬은 표시·입력만.
2. 결정적 — RNG 금지.
3. 죽은 유닛도 그리되 흐리게(로스터 유지는 룰이 함).
4. 순수 표시/입력 — 파일 IO·네트워크 없음(레벨 JSON 로드 제외).

## 검증
헤드리스 스모크: `godot --headless --path godot --quit-after 30` 가 SCRIPT ERROR/Parse Error 없이 떠야 채택
(플레이 가능·UI 정확성은 사용자가 F5로 확인 — 0-diff 범위 밖).
