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
  - 텍스트 주의: id/hp는 JSON에서 **float**라 `%d`+`int(...)`로 정수 표시(안 그러면 `2.0`). 여러 줄은
    `draw_string`이 `\n`을 무시하므로 **`draw_multiline_string`** 사용(예: `"%d\nHP %d"`). hp는 또렷이.
- 선택된 아군은 테두리 강조.
- `_ready`에서 Label 하나 add_child 해서 "미션명 · 턴 · 상태(PLAYING/VICTORY/DEFEAT)" 표시. 상태 바뀌면 갱신.

## 입력 (`_unhandled_input`, 좌클릭)
- 클릭한 셀에 살아있는 내 아군 → 그 아군 선택.
- 아군이 선택된 상태에서:
  - 빈 셀이 직교 인접(맨해튼 1) → `update_state(state, {"unit":선택id, "type":"move", "dir":[dx,dy]})`.
  - 적이 선택 아군 사거리 내(맨해튼 <= range, 기본 1, >=1) → `update_state(state, {"unit":선택id, "type":"attack"})`.
- 매 액션 후: 반환 status로 Label 갱신, `queue_redraw()`. VICTORY/DEFEAT면 입력 잠금.
- 키: `R` 현재 미션 리셋, `N` 다음 미션(끝이면 처음으로).

### ⚠ 좌표 비교 함정 (반드시 지킬 것)
- `pos`는 JSON에서 와서 **float**(`[0.0, 0.0]`)다. 클릭 셀 `gx,gy`는 `int(...)`라 **int**다.
- GDScript에서 `[0.0,0.0] == [0,0]`은 **false**다(배열 비교는 원소 타입까지 엄격). 스칼라 `0.0==0`만 true.
- 그래서 **배열째 `pos == [gx,gy]` 비교 금지.** 반드시 원소별로: `pos[0] == gx and pos[1] == gy`.
- 이걸 어기면 스모크는 통과하지만 클릭이 전부 무반응이 된다(2026-06-23 실제 버그).

## 불변식
1. **rules.gd 수정·재구현 금지.** 룰 판정은 전부 update_state 경유. 씬은 표시·입력만.
2. 결정적 — RNG 금지.
3. 죽은 유닛도 그리되 흐리게(로스터 유지는 룰이 함).
4. 순수 표시/입력 — 파일 IO·네트워크 없음(레벨 JSON 로드 제외).

## 검증
1. 헤드리스 스모크: `godot --headless --path godot --quit-after 30` 가 SCRIPT ERROR/Parse Error 없이 떠야 함.
2. **입력 프로브**: `godot --headless --path godot --script res://test/run_input_probe.gd` 가
   `PROBE RESULT: 입력 로직 동작함`(선택+이동 반영)을 찍어야 채택.
   스모크만으론 위 좌표 비교 함정 같은 입력 무반응 버그를 못 잡는다 — 프로브로 클릭 경로를 결정적으로 검증한다.
3. UI 미관·실제 터치는 사용자가 확인(0-diff 범위 밖).
