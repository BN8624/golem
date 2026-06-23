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
- **좌표계(고정·필수)**: PLAYING의 셀 크기는 `cell_size = 640.0 / state.gridSize`, 보드 원점은 화면 `(0,0)`.
  클릭→셀은 `gx = int(event.position.x / cell_size)`, `gy = int(event.position.y / cell_size)`.
  프로브가 정확히 이 좌표계(640/grid, 원점 0)로 클릭한다 — **고정 cell(예: 32)이나 offset(예: 100) 금지.** 보드는 640×640을 꽉 채운다.

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

## 에셋 사양 (반드시 이 경로를 load — 클로드가 준비·동결한 CC0 에셋)
- **폰트(필수)**: `font = load("res://assets/fonts/NanumGothic-Regular.ttf")`. 모든 `draw_string`에 이 font를 써라.
  `ThemeDB.get_fallback_font()` 금지 — 웹 빌드엔 한글 글리프가 없어 □로 깨진다.
- **픽셀 필터**: `_ready`에서 `texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST` (16px 타일이 뭉개지지 않게).
- **타일(Tiny Dungeon, 16x16)** — `res://assets/tinydungeon/Tiles/tile_XXXX.png`:
  - 바닥: `tile_0048`(흙). 바닥 변주(드물게 섞기): `tile_0049`, `tile_0050`, `tile_0051`.
  - 아군 근접(range 없음/1): `tile_0096`(은색 기사). 아군 원거리(range>1): `tile_0084`(마법사).
  - 적: `tile_0108`(초록 몬스터).
  - 더 필요하면 `godot/assets/tinydungeon/Tiles/`에서 골라 써도 된다(같은 16x16).

## 맵·이펙트 요구 (게임답게 — 이번 단계 목표)
- **맵(미션별 지형 톤)**: 바닥은 `tile_0048`을 깔되 `current_mission_idx`별로 색조(tone)를 다르게
  (예: 0=기본, 1=청회색, 2=보라어둠, 3=황금). 칸 위치 해시로 변주 타일을 드물게 섞어 단조롭지 않게.
  - 색조는 **반드시** `draw_texture_rect(tex, rect, false, tone)`의 **4번째 인자**로 준다.
    `draw_set_transform`은 변환 행렬(pos,rot,scale)용이라 색을 못 준다 — 거기에 Color를 넣지 마라(인자 4개 금지).
- **이펙트(시간 기반 — `set_process(true)` + `_process(delta)`로 갱신, `queue_redraw`)**:
  - **데미지/회복 플로팅 텍스트**: 액션 후 hp 변화량을 그 유닛 칸 위에 "-N"(빨강)/"+N"(초록)으로 띄우고 위로 떠오르며 페이드아웃.
  - **타격 플래시**: 피해 받은 유닛을 짧게(≈0.2s) 흰/빨강으로 깜빡(modulate).
  - **선택 하이라이트**: 아군 선택 시 이동 가능 빈 인접칸=초록 반투명, 사거리 내 적 칸=빨강 테두리.
  - 이펙트 상태는 멤버 배열/딕셔너리로 들고 `_process`에서 수명 감소·만료 제거. 룰/상태(state)는 절대 안 건드린다(표시 전용).
- hp 변화 계산: `update_state` 호출 **전** 모든 유닛 hp를 스냅샷 → 호출 후 비교 → 변한 유닛에 플로터/플래시.
- **⚠ 유닛 dict 키 함정(필수)**: 아군과 적은 **id가 겹친다**(양쪽 다 1,2,…). hp 스냅샷·flash·이펙트 등 유닛을
  dict 키로 들 때 **반드시 진영을 합쳐라**(예: `"a"+str(id)` / `"e"+str(id)`). id만 키로 쓰면 같은 id의
  아군·적이 섞여 **엉뚱한 유닛이 빨개지고(flash) 데미지 계산이 틀린다**(2026-06-23 실제 버그).
- 바닥 변주 타일은 **2D 해시**(`(x*7 + y*13) % N`)로 드물게(≈10%) 섞어라. 행/열 단일 해시는 가로 띠가 진다.
  - ⚠ **변주는 "바닥 결"이어야 한다 — 떠다니는 갈색 막대처럼 튀면 안 된다(2026-06-23 캡처 실측).** tile_0049~0051을 풀셀 틴트로 깔면 바닥이 아니라 잔해/가로띠로 읽혔다. 변주는 **같은 바닥 톤 안의 미세 명도 변화**(예: tone을 칸별로 ±0.05 흔들기)로 주거나, 변주 타일을 쓰더라도 바닥 계열로만 골라 톤을 본 바닥과 거의 맞춰라. 변주가 본 바닥보다 눈에 띄면 실패다.

## 플레이 입력 (`screen=="PLAYING"`, 좌클릭)
- 클릭 셀에 살아있는 내 아군 → 그 아군 선택.
- 아군 선택 상태에서, **클릭한 칸의 내용으로 분기**(occupied 여부 하나로 뭉뚱그리지 마라):
  - 클릭 칸에 살아있는 적이 있고 맨해튼 dist가 `1 <= dist <= range`(기본 range 1) → `update_state(state, {"unit":선택id,"type":"attack"})`.
  - 클릭 칸이 비었고 직교 인접(dist==1) → `update_state(state, {"unit":선택id,"type":"move","dir":[dx,dy]})`.
- 매 액션 후: 반환 status를 `state.status`에 반영, `queue_redraw()`. VICTORY/DEFEAT면 `screen="RESULT"`.
- 키(데스크톱 보조): `R` 현재 미션 리셋(load_mission), `N` 메뉴로. (폰엔 키 없음 → 화면 버튼이 정답.)

### ⚠ 좌표 비교 함정 (반드시 지킬 것)
- `pos`는 JSON에서 와서 **float**(`[0.0,0.0]`), 클릭 셀 `gx,gy`는 `int(...)`라 **int**다.
- GDScript에서 `[0.0,0.0] == [0,0]`은 **false**(배열 비교는 원소 타입까지 엄격). 스칼라 `0.0==0`만 true.
- **배열째 `pos == [gx,gy]` 비교 금지.** 반드시 원소별 `pos[0]==gx and pos[1]==gy`.

## 렌더 (`_draw`) — screen별 분기
- 공통: 화면 ~640px 기준 좌표.
- **MENU**: 제목 + 4미션 버튼(사각형 + name/desc 텍스트). 버튼 위치를 `_unhandled_input`의 히트 판정과 동일 좌표로.
- **BRIEFING**: 반투명 박스 + briefing 본문(여러 줄 wrap) + 하단 "탭하여 시작".
- **PLAYING**: 모든 그리기가 **같은 좌표계**(cell=640.0/gridSize, 원점 (0,0)). 각 칸 rect는 정확히 `Rect2(x*cell, y*cell, cell, cell)`.
  - 바닥: 칸마다 바닥 타일을 **그 칸의 정사각 rect**에 `draw_texture_rect`(rect를 화면 폭으로 늘리지 마라 — 한 칸=cell×cell).
  - 유닛: **원이 아니라 스프라이트**를 칸 중앙에 칸의 ~0.8 크기로. 텍스처 선택은 진영으로 고정 —
    **아군만 기사(range 없음/1)·마법사(range>1), 적은 무조건 `tex_monster`(tile_0108).** 적에 기사/마법사 텍스처를 쓰면 안 된다.
  - 유닛 칸에 `"HP %d"`(int) 라벨. hp<=0는 흐리게+✕. 선택 아군 하이라이트, [맵·이펙트]의 이동/사거리 표시도 **같은 cell/원점**. 상단에 "미션명 · 턴".
- **RESULT**: 보드 위 반투명 오버레이 + victory/defeat 본문 + 버튼.

### ⚠ draw_string 시그니처 함정 (반드시 지킬 것)
- Godot 4: `draw_string(font, pos:Vector2, text, alignment, width, font_size, modulate)`.
  색을 주려면 `draw_string(font, pos, text, HORIZONTAL_ALIGNMENT_LEFT, -1, 16, color)`.
- `draw_string(font, 0, pos, text, color)`처럼 쓰면 인자가 밀려 **실렌더 시 깨진다**(헤드리스 스모크/프로브는
  `_draw`를 호출 안 해 못 잡으니 렌더 캡처 게이트로 잡는다. 2026-06-23 실제 버그).
- `draw_string`은 `\n`을 무시한다. 여러 줄은 줄 단위로 나눠 그리거나 `draw_multiline_string`.

## 불변식
1. **rules.gd 수정·재구현 금지.** 룰 판정은 전부 update_state 경유. 씬은 표시·입력만.
2. 결정적 — RNG 금지.
3. 죽은 유닛도 그리되 흐리게.
4. 순수 표시/입력 — 파일 IO·네트워크 없음(레벨 JSON 로드 제외).
5. 위 [자동 검증 계약]의 멤버/메서드 시그니처를 절대 바꾸지 마라.

## 다듬기 v3 (2026-06-23 G96 — 아이폰/캡처 피드백 반영, 좌표계 계약은 불변)
아래는 **좌표계 계약(cell=640/grid·원점 0·보드 640 꽉 채움)을 깨지 않는 표시 레이어 변경**이다. 프로브가 의존하는 클릭 좌표계는 그대로 둔다 — HUD·바·라인은 전부 보드 위 **오버레이**로 그린다.

1. **상단 잘림·겹침 제거(최우선 버그)**: 현재 HP 라벨이 스프라이트 위(`rect.position.y - 5`)라 gy=0 유닛이 화면 밖으로 잘리고, 타이틀이 좌상단 유닛과 겹친다.
   - HP는 **스프라이트 위 텍스트를 버리고 셀 안쪽 하단의 HP 바**로 바꾼다(아래 2번). 화면 밖으로 나갈 일이 없게 셀 경계 안에만 그린다.
   - 타이틀("미션명 · 턴")은 화면 **최상단 반투명 띠**(예: `Rect2(0,0,640,36)` 알파 0.5) 안에 그려 유닛과 안 겹치게. 좌상단 (0,0)칸 유닛은 이 띠 아래로 살짝 가려도 된다(HUD가 우선).
2. **HP 바(텍스트→막대)**: 유닛 스프라이트 칸 안쪽 하단에 가는 막대. 배경 어두운 막대 + hp/maxhp 비율만큼 채움(아군=초록, 적=빨강). maxhp는 `initialState`의 시작 hp를 멤버에 스냅샷해 둔다(state엔 안 박는다 — 표시 전용). 숫자는 바 위에 작게(외곽선, 4번 참고) 선택적. hp<=0는 빈 바 + ✕.
3. **그리드 라인(전술 가독성 — 근본)**: 바닥 타일을 깐 뒤 각 셀 경계에 **은은한 라인**(예: `draw_rect(rect, Color(0,0,0,0.12), false, 1.0)`)을 그어 칸을 셀 수 있게. 솔리드 바닥 한 장으로 보이면 거리·위치 판단이 안 된다. 라인은 바닥 위·유닛 아래.
4. **데미지/플로팅 텍스트 가독성**: 주황 배경에 묻힌다. **외곽선/그림자**를 줘라 — 같은 텍스트를 검정으로 4방향(±1px) 먼저 그리고 그 위에 색 텍스트. 크기 ≈22, 상승거리 ≈60px(life 동안), 페이드아웃 유지. 스프라이트 정중앙 말고 칸 위쪽에서 떠오르게.
5. **이동/넉백 트윈(표시 전용)**: 유닛이 순간이동하지 않게, `pos` 변화 시 직전 픽셀좌표→현재 픽셀좌표를 짧게(≈0.15s) 보간해 그린다. **state/룰은 즉시 갱신(트윈은 그리기 좌표만)** — 결정적 검증·프로브에 영향 없어야 한다. 트윈 진행 상태는 멤버 dict(`"a"+id`/`"e"+id` 키, [id 충돌 함정] 준수)로 들고 `_process`에서 감쇠.
6. **죽은 유닛**: 회색 반투명 + ✕는 유지하되, 살아있는 유닛과 한눈에 구분되게(틴트를 충분히 어둡게). 사망이 "맞은 직후 빨강 플래시"와 헷갈리지 않게.

> 못 고치는 것(사양 밖, 골렘 레벨 데이터): 유닛이 좌상단에 몰리고 나머지가 빈 보드인 건 `squad_levels.json` 배치·gridSize 문제다. 그리드 라인으로 휑함은 줄지만 근본은 레벨 생성기 몫이다.

## 검증 (모두 통과해야 채택)
1. 헤드리스 스모크: `--quit-after 30` 가 SCRIPT ERROR/Parse Error 없이 뜸.
2. 입력 프로브: `--script res://test/run_input_probe.gd` 가 `PROBE RESULT: 입력 로직 동작함` + `PROBE ATTACK RESULT: 공격 동작함`.
   (프로브는 `load_mission(0)`로 메뉴를 우회 → 클릭 선택·이동·공격을 결정적 검증.)
3. **렌더 캡처(windowed)**: `--script res://test/capture_attack.gd` 가 _draw(MENU+PLAYING)를 실제로 그리며
   SCRIPT ERROR/Parse Error 없이 `test/cap_menu.png`·`test/cap_after.png`를 생성해야 한다.
   (헤드리스 스모크/프로브가 `_draw`를 호출 안 해 못 잡는 draw_string 시그니처·폰트·텍스처 로드 에러를 여기서 잡는다.)
4. 최종 미관(예쁜지)과 실제 터치는 사람이 확인(0-diff 범위 밖).
