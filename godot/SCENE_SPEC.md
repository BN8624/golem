# 씬 사양서 v2 — 미션선택 + 서사 + 플레이 (골렘이 Phase 3에서 재작성)

골렘은 검증된 `res://scripts/rules.gd`(절대 수정 금지)를 호출만 하는 **씬 스크립트** `res://scripts/board.gd`를
만든다. 클로드가 래퍼 씬 `res://scenes/main.tscn`(루트 Node2D에 board.gd 부착)과 헤드리스 검증을 제공한다.

## 산출물
`godot/scripts/board.gd` 단 하나. 아래를 지킨다.

## ★ 자동 검증 계약 (이걸 어기면 채택 안 됨 — 최우선)
헤드리스 프로브가 메뉴/브리핑을 건너뛰고 플레이를 검증한다. 다음 공개 인터페이스를 **정확히** 유지하라.
- 멤버 `var state = {}` : 현재 미션 상태 dict. 키 `gridSize`, `allies`, `enemies`, `turn`, `status`.
- 멤버 `var selected_unit_id` : 선택된 아군 id 또는 null.
- 메서드 `func load_mission(idx) -> void` : **미션 idx의 initialState로 즉시 플레이 상태를 구성하고 화면을 PLAYING으로 전환**한다.
  (메뉴/브리핑을 거치지 않는다. 프로브가 이걸 직접 호출해 곧장 플레이한다.)
  내부에서 `state = 깊은복제(initialState)`, `state.turn=0`, `state.status="PLAYING"`, `selected_unit_id=null`, `screen="PLAYING"`.
- 메서드 `func _unhandled_input(event)` : `screen=="PLAYING"`일 때 좌클릭으로 아래 [플레이 입력]을 처리.

## 화면 모드 (`var screen`)
`"MENU" → "BRIEFING" → "PLAYING" → "RESULT"`. `_ready()`는 `screen="MENU"`로 시작.
- **MENU**: 4미션 목록. 각 항목 `levels[i].name` + `levels[i].desc`를 세로 버튼으로. 클릭한 항목 i → `screen="BRIEFING"`, `pending_idx=i`.
- **BRIEFING**: `levels[pending_idx].story.briefing` 본문 + "탭하여 시작" 안내. 클릭 또는 Enter/Space → `load_mission(pending_idx)`(→PLAYING).
- **PLAYING**: 보드. 좌클릭 [플레이 입력]. 액션 후 status가 VICTORY/DEFEAT면 `screen="RESULT"`.
- **RESULT**: status==VICTORY면 `levels[현재].story.victory`, DEFEAT면 `story.defeat` 표시.
  버튼: 승리=「다음 미션」(다음 idx BRIEFING; 마지막이면 「메뉴로」) / 패배=「다시」(같은 미션 load_mission) + 「메뉴로」(screen=MENU).

## 로딩 (`_ready`)
- `extends Node2D`. 첫 줄은 역할을 적은 한 줄 한국어 주석.
- 룰: `rules = load("res://scripts/rules.gd").new()` — 모든 룰 판정은 `rules.update_state(state, action)`로만.
- 레벨: `res://data/squad_levels.json` = Array. 각 원소 `{ "name","desc","teaches","initialState","story" }`.
  - `initialState = { "gridSize":int, "allies":[...], "enemies":[...] }`. 유닛 `{ "id","hp","atk","pos":[x,y], 카드필드(range/knockback/...) }`.
  - `story = { "briefing":str, "victory":str, "defeat":str }`.
- 깊은 복제는 `JSON.parse_string(JSON.stringify(initialState))`.

## 플레이 입력 (`screen=="PLAYING"`, 좌클릭)
- 클릭 셀에 살아있는 내 아군 → 그 아군 선택.
- 아군 선택 상태에서:
  - 빈 셀이 직교 인접(맨해튼 1) → `update_state(state, {"unit":선택id,"type":"move","dir":[dx,dy]})`.
  - 적이 사거리 내(맨해튼 <= range, 기본 1, >=1) → `update_state(state, {"unit":선택id,"type":"attack"})`.
- 매 액션 후: 반환 status를 `state.status`에 반영, `queue_redraw()`. VICTORY/DEFEAT면 `screen="RESULT"`.
- 키(데스크톱 보조): `R` 현재 미션 리셋(load_mission), `N` 메뉴로. (폰엔 키 없음 → 화면 버튼이 정답.)

### ⚠ 좌표 비교 함정 (반드시 지킬 것)
- `pos`는 JSON에서 와서 **float**(`[0.0,0.0]`), 클릭 셀 `gx,gy`는 `int(...)`라 **int**다.
- GDScript에서 `[0.0,0.0] == [0,0]`은 **false**(배열 비교는 원소 타입까지 엄격). 스칼라 `0.0==0`만 true.
- **배열째 `pos == [gx,gy]` 비교 금지.** 반드시 원소별 `pos[0]==gx and pos[1]==gy`.

## 렌더 (`_draw`) — screen별 분기
- 공통: 화면 ~640px 기준 좌표.
- **MENU**: 제목 + 4미션 버튼(사각형 + name/desc 텍스트). 버튼 위치를 `_unhandled_input`의 히트 판정과 동일 좌표로.
- **BRIEFING**: 반투명 박스 + briefing 본문(여러 줄은 `draw_multiline_string`, 박스 폭으로 wrap) + 하단 "탭하여 시작".
- **PLAYING**: 정사각 격자 gridSize×gridSize. 아군=파란 원, 적=빨간 원, 각 원에 `"%d\nHP %d" % [int(id),int(hp)]`를 **`draw_multiline_string`**(draw_string은 `\n` 무시). hp<=0는 흐리게+✕. 선택 아군은 테두리 강조. 상단 Label에 "미션명 · 턴 · 상태".
- **RESULT**: 보드 위 반투명 오버레이 + victory/defeat 본문 + 버튼.

## 불변식
1. **rules.gd 수정·재구현 금지.** 룰 판정은 전부 update_state 경유. 씬은 표시·입력만.
2. 결정적 — RNG 금지.
3. 죽은 유닛도 그리되 흐리게.
4. 순수 표시/입력 — 파일 IO·네트워크 없음(레벨 JSON 로드 제외).
5. 위 [자동 검증 계약]의 멤버/메서드 시그니처를 절대 바꾸지 마라.

## 검증 (모두 통과해야 채택)
1. 헤드리스 스모크: `--quit-after 30` 가 SCRIPT ERROR/Parse Error 없이 뜸.
2. 입력 프로브: `--script res://test/run_input_probe.gd` 가 `PROBE RESULT: 입력 로직 동작함` + `PROBE ATTACK RESULT: 공격 동작함`.
   (프로브는 `load_mission(0)`로 메뉴를 우회 → 클릭 선택·이동·공격을 결정적 검증. 스모크만으론 입력 무반응을 못 잡음.)
3. 메뉴/브리핑/결과 미관과 실제 터치는 사용자가 확인(0-diff 범위 밖).
