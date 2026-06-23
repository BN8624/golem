# 씬 사양서 v2 — 미션선택 + 서사 + 플레이 (골렘이 Phase 3에서 재작성)

골렘은 검증된 `res://scripts/rules.gd`(절대 수정 금지)를 호출만 하는 **씬 스크립트** `res://scripts/board.gd`를
만든다. 클로드가 래퍼 씬 `res://scenes/main.tscn`(루트 Node2D에 board.gd 부착)과 헤드리스 검증을 제공한다.

## 산출물
`godot/scripts/board.gd` 단 하나. 아래를 지킨다.

## ★ 자동 검증 계약 (이걸 어기면 채택 안 됨 — 최우선)
헤드리스 프로브가 메뉴/브리핑을 건너뛰고 플레이를 검증한다. 다음 공개 인터페이스를 **정확히** 유지하라.
- 멤버 `var state = {}` : 현재 미션 상태 dict. 키 `gridSize`, `allies`, `enemies`, `turn`, `status`.
- 멤버 `var selected_unit_id` : 선택된 아군 id 또는 null.
- 멤버 `var pending_idx` : BRIEFING/SQUAD_SELECT가 보여줄 미션 인덱스(int). 캡처 하네스가 메뉴 클릭을 우회해 `pending_idx=N; screen="BRIEFING"`/`"SQUAD_SELECT"`로 화면을 직접 띄워 렌더를 검증하므로 **이 이름·의미를 유지하라**(메뉴 버튼 픽셀 좌표에 게이트가 의존하지 않게 — 좌표는 골렘 자유).
- 메서드 `func load_mission(idx) -> void` : **미션 idx의 initialState로 즉시 플레이 상태를 구성하고 화면을 PLAYING으로 전환**한다.
  (메뉴/브리핑을 거치지 않는다. 프로브가 이걸 직접 호출해 곧장 플레이한다.)
  내부에서 `state = 깊은복제(initialState)`, `state.turn=0`, `state.status="PLAYING"`, `selected_unit_id=null`, `screen="PLAYING"`.
- 메서드 `func _unhandled_input(event)` : `screen=="PLAYING"`일 때 좌클릭으로 아래 [플레이 입력]을 처리.
- 메서드 `func cell_to_screen(gx:int, gy:int) -> Vector2` (**공개·필수**): 칸 (gx,gy)의 **화면 픽셀 중심**을 아이소 투영으로 반환한다. `_draw`(타일·유닛 배치)와 `_unhandled_input`의 클릭 히트판정이 **이 한 함수를 단일 진실원천으로** 쓴다. 프로브·캡처 하네스가 이 함수를 직접 호출해 클릭 위치를 잡으므로 **시그니처를 절대 바꾸지 마라.**
- 멤버 `var auto_mode = true` : 자동 전투 on/off. 메서드 `func auto_step() -> void` (**공개·필수**): `screen=="PLAYING"`이면 아군 1명의 자동 액션을 골라 `rules.update_state` 1회 적용(엔진이 적 반응 처리), 종료면 `screen="RESULT"`. 자동 플레이아웃 프로브가 이걸 반복 호출해 결정적 종료를 검증한다 — [★v7 자동 전투] 참조. **시그니처 고정.**
- ⚠ **`load_mission(idx)`는 위 동작 그대로 절대 불변**이다(메뉴/브리핑/덱편성을 모두 건너뛰고 미션의 **고정 allies**로 PLAYING 직행). 입력 프로브·fixture·test_bridge가 이 계약에 의존한다. 덱 편성(아래 [★v10])은 load_mission을 **건드리지 않고** 그 위에 얹는 **새 진입 경로**다.
- **좌표계(아이소메트릭 2.5D·필수)**: 보드는 다이아몬드 격자다. 투영 =
  `cell_to_screen(gx,gy) = origin + Vector2((gx-gy)*TILE_W/2.0, (gx+gy)*TILE_H/2.0)` (2:1 아이소 → `TILE_H = TILE_W/2.0`).
  `TILE_W`·`origin`은 GxG 보드가 가로로 화면 폭(≈600, 좌우 여백 둠)에 맞고 **가로·세로 모두 가운데 정렬**되게 골렘이 정한다. 권장 `TILE_W = 600.0/state.gridSize`(→ `TILE_H = TILE_W/2`), `origin.x = 320`. **세로 중앙정렬**: 다이아몬드의 세로 픽셀 높이는 `(gridSize-1)*TILE_H`이므로 `origin.y = (640 + HUD높이)/2 - (gridSize-1)*TILE_H/2`로 둬서 보드가 화면 세로 가운데(HUD 아래)에 오게 한다 — 위로 쏠려 아래가 휑하면 안 된다(2026-06-24 캡처 실측).
  - **클릭→칸은 위 투영의 정확한 역변환**이어야 한다: `rx=(px-origin.x)/(TILE_W/2.0)`, `ry=(py-origin.y)/(TILE_H/2.0)` → `gx=int(round((rx+ry)/2.0))`, `gy=int(round((ry-rx)/2.0))`. 즉 `cell_to_screen(gx,gy)` 위치를 클릭하면 정확히 칸 (gx,gy)가 잡혀야 한다(프로브가 이 왕복을 검증).
  - **탑다운 `int(x/cell)` 좌표계 금지.** 고정 cell·고정 offset 금지. origin/TILE_W는 위 식으로 gridSize에서 유도.

## 화면 모드 (`var screen`)
`"MENU" → "BRIEFING" → "SQUAD_SELECT" → "PLAYING" → "RESULT"`. `_ready()`는 `screen="MENU"`로 시작.
- **MENU**: 4미션 목록. 각 항목 `levels[i].name` + `levels[i].desc`를 세로 버튼으로. 클릭한 항목 i → `screen="BRIEFING"`, `pending_idx=i`.
- **BRIEFING**: `levels[pending_idx].story.briefing` 본문 + "탭하여 시작" 안내. 클릭 또는 Enter/Space → `screen="SQUAD_SELECT"`(덱 편성으로. **load_mission 직행 아님** — 사람 진입 경로엔 편성 단계가 들어간다).
- **SQUAD_SELECT**: 덱 편성. 로스터에서 유닛을 골라 출전. 상세는 [★v10]. "출전" → `start_battle_with(고른유닛들)`(→PLAYING).
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
- 로스터(덱 편성용): `res://data/roster.json` = `{ "cost_budget":int, "units":[...] }`. 각 유닛 `{ "id":str, "name":str, "role":str, "cost":int, "hp":int, "atk":int, 카드필드(range/knockback/reflect_dmg/...), "desc":str }`. `roster = parse(...)["units"]`, `cost_budget = parse(...)["cost_budget"]`로 멤버에 보관. `cost`는 편성 예산용 메타(룰 미사용). [★v10]에서 SQUAD_SELECT가 쓴다.

## 에셋 사양 (반드시 이 경로를 load — 클로드가 준비·동결한 CC0 에셋)
- **폰트(필수)**: `font = load("res://assets/fonts/NanumGothic-Regular.ttf")`. 모든 `draw_string`에 이 font를 써라.
  `ThemeDB.get_fallback_font()` 금지 — 웹 빌드엔 한글 글리프가 없어 □로 깨진다.
- **픽셀 필터**: `_ready`에서 `texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST` (16px 타일이 뭉개지지 않게).
- **타일(Tiny Dungeon, 16x16)** — `res://assets/tinydungeon/Tiles/tile_XXXX.png`:
  - 바닥: **아이소 2.5D 전환으로 바닥 타일은 안 쓴다 — 바닥은 절차적 다이아몬드로 그린다(아래 ★v4).** `tile_0048~0051` 폐기(탑다운 정사각 타일은 다이아몬드에 안 맞고, 갈색 가로띠 문제도 이로써 사라진다). **유닛 스프라이트(기사/마법사/몬스터)는 그대로 쓴다 — 다이아몬드 위에 빌보드로 세운다.**
  - 아군 근접(range 없음/1): `tile_0096`(은색 기사). 아군 원거리(range>1): `tile_0084`(마법사).
  - 적: `tile_0108`(초록 몬스터).
  - 더 필요하면 `godot/assets/tinydungeon/Tiles/`에서 골라 써도 된다(같은 16x16).

## 맵·이펙트 요구 (게임답게 — 이번 단계 목표)
- **맵(미션별 지형 톤)**: 미션별 색조(tone)는 `tones[current_mission_idx%n]`로 다르게(0=기본, 1=청회색, 2=보라어둠, 3=황금). **아이소 전환 후 바닥은 타일이 아니라 절차적 다이아몬드 fill에 이 tone을 준다(★v4 1번).** 즉 `draw_colored_polygon(pts, tone*명도변화)`. (구 탑다운 `draw_texture_rect(tex, rect, false, tone)` 4번째 인자 방식은 바닥엔 폐기 — 단, **유닛 스프라이트 modulate**(플래시·사망 틴트)엔 여전히 `draw_texture_rect`의 4번째 Color 인자를 쓴다.)
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
- **SQUAD_SELECT**: 제목("출전 부대 편성") + 로스터 유닛 카드 세로 목록(이름·역할·**cost**·hp/atk·desc, 고른 유닛은 강조 테두리/체크) + **예산 표시 "코스트 N/한도"**(초과면 빨강) + 하단 "출전" 버튼(편성 규칙 불만족이면 흐리게/비활성 표시). 상세·히트판정은 [★v10].
- **PLAYING**: **아래 [★v4 아이소메트릭]이 PLAYING 렌더의 정본이다.** 모든 칸·유닛·하이라이트 위치는 `cell_to_screen(gx,gy)`로 잡는다(정사각 `Rect2(x*cell,...)` 격자는 아이소 전환으로 폐기).
  - 유닛 텍스처 선택은 진영으로 고정 — **아군만 기사(range 없음/1)·마법사(range>1), 적은 무조건 `tex_monster`(tile_0108).** 적에 기사/마법사 텍스처를 쓰면 안 된다.
  - 상단에 "미션명 · 턴"(최상단 반투명 HUD 띠).
- **RESULT**: 보드 위 반투명 오버레이 + victory/defeat 본문 + 버튼.

### ⚠ draw_string 시그니처 함정 (반드시 지킬 것)
- Godot 4: `draw_string(font, pos:Vector2, text, alignment, width, font_size, modulate)`.
  색을 주려면 `draw_string(font, pos, text, HORIZONTAL_ALIGNMENT_LEFT, -1, 16, color)`.
- `draw_string(font, 0, pos, text, color)`처럼 쓰면 인자가 밀려 **실렌더 시 깨진다**(헤드리스 스모크/프로브는
  `_draw`를 호출 안 해 못 잡으니 렌더 캡처 게이트로 잡는다. 2026-06-23 실제 버그).
- `draw_string`은 `\n`을 무시한다. 여러 줄은 줄 단위로 나눠 그리거나 `draw_multiline_string`.

### ⚠ GDScript 다중변수 선언 함정 (반드시 지킬 것)
- **`var a, b = ...` 같은 한 줄 다중 변수 선언 금지** — GDScript는 안 된다(`Parse Error: Expected end of statement after variable declaration, found ","`, 2026-06-24 실제 3회 실패). 변수마다 `var`를 따로: `var dx = ...` 다음 줄 `var dy = ...`. 베지어/방향/타원 계산에서 특히 주의.

## 불변식
1. **rules.gd 수정·재구현 금지.** 룰 판정은 전부 update_state 경유. 씬은 표시·입력만.
2. 결정적 — RNG 금지.
3. 죽은 유닛도 그리되 흐리게.
4. 순수 표시/입력 — 파일 IO·네트워크 없음(레벨 JSON 로드 제외).
5. 위 [자동 검증 계약]의 멤버/메서드 시그니처를 절대 바꾸지 마라.
6. **MENU/BRIEFING에서 `state`는 비어 있다(`{}`).** `_process`·`_draw`·`cell_to_screen` 등이 `state.allies`/`state.enemies`/`state.gridSize`에 접근하려면 **반드시 `screen=="PLAYING"` 가드 안에서만**. MENU 화면에서 `state.allies`를 읽으면 `Invalid access to property 'allies' on Dictionary` 크래시(2026-06-24 실제). 스모크는 MENU로 부팅하므로 이게 바로 터진다.

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

## ★ v4 아이소메트릭 2.5D (2026-06-24 — PLAYING 렌더의 정본, 위 좌표계 계약과 한 몸)
탑다운 정사각 격자를 **아이소 다이아몬드 격자**로 바꾼다. 모든 위치는 `cell_to_screen(gx,gy)`(위 계약)로 잡는다. 룰·검증·입력 의미는 불변 — **순수 표시 변경**이다.

1. **바닥 = 절차적 다이아몬드(타일 폐기)**: 각 칸을 `cell_to_screen(gx,gy)` 중심의 마름모로 그린다. 네 꼭짓점 =
   `c+Vector2(0,-TILE_H/2)`(위), `c+Vector2(TILE_W/2,0)`(오른), `c+Vector2(0,TILE_H/2)`(아래), `c+Vector2(-TILE_W/2,0)`(왼).
   `draw_colored_polygon(pts, fill)`로 채우고, 테두리(=그리드)는 **닫힌 점 배열을 직접 만들어** `draw_polyline`한다 — `draw_polyline(PackedVector2Array([top, right, bottom, left, top]), 격자선색, 1.0)`(첫 점을 끝에 한 번 더). ⚠ **`pts + [pts[0]]`처럼 PackedVector2Array에 Array를 `+`로 붙이지 마라(GDScript 에러 `Invalid operands ... operator '+'`, 2026-06-24 실제 4회 실패).** **갈색 막대 변주 금지** — fill은 미션 톤(`tones[current_mission_idx%n]`) 기반, 칸별 미세 명도 변화는 `(gx*7+gy*13)%5`로 ±0.04 정도만(바닥 결, 튀지 않게). 격자선은 은은하게(알파 ~0.15).
2. **깊이 정렬(필수)**: 유닛·이펙트는 **뒤→앞**으로 그린다. `gx+gy`(=화면 아래로 내려갈수록 큰 값) 오름차순 정렬 후 그려, 앞 칸 유닛이 뒤 칸 유닛/타일을 가린다. 바닥 전체를 먼저 다 깔고, 그 위에 정렬된 유닛.
3. **유닛 = 빌보드 + 그림자(2.5D 핵심)**: 스프라이트는 눕히지 말고 **똑바로 세운다**. **밑변 중앙이 칸 중심 `c`에 닿게** 위로 올려 그린다(`Rect2(c.x - w/2, c.y - h, w, h)`, **w ≈ TILE_W*1.1**(타일보다 약간 크게 — 작으면 그림자에 묻힌다), h는 텍스처 비율 유지).
   - ⚠ **그림자는 작고 납작하고 은은하게 — 큰 어두운 원 절대 금지(2026-06-24 캡처 실측: 유닛이 어두운 구덩이에 빠진 것처럼 보였다).** 칸 중심 `c`에 **납작한 타원**: 가로 반지름 `rx ≈ TILE_W*0.22`, 세로 반지름 `ry ≈ TILE_H*0.18`(폭의 ~1/3로 눌린 타원), 색 `Color(0,0,0,0.22)`. 그림자는 스프라이트보다 작아야 한다.
   - **만드는 법(정확히 이대로 — `draw_set_transform` 절대 쓰지 마라)**: 타원 점들을 직접 계산해 `draw_colored_polygon`으로 그린다.
     ```
     var pts = PackedVector2Array()
     for i in range(16):
         var t = TAU * i / 16.0
         pts.append(c + Vector2(cos(t) * rx, sin(t) * ry))
     draw_colored_polygon(pts, Color(0, 0, 0, 0.22))
     ```
     `draw_circle`(정원이라 안 눌림)도, **`draw_set_transform`(시그니처 함정 — 2026-06-24 그림자에 쓰려다 5회 연속 스모크 실패의 원인. `draw_set_transform(pos:Vector2, rot, scale:Vector2)`라 인자 수·타입을 계속 틀렸다)**도 쓰지 마라.
4. **HP 바**: v3의 "셀 하단 바"를 **빌보드 머리 위 가는 바**로 옮긴다(스프라이트 top 위 ~4px). 어두운 배경 + 비율 채움(아군 초록/적 빨강), hp<=0는 빈 바+✕. maxhp 스냅샷은 v3대로.
5. **하이라이트(이동/사거리)**: v3 정사각 대신 그 칸의 **다이아몬드**를 칠한다 — 이동 가능 빈 인접칸=초록 반투명 마름모(fill), 사거리 내 적 칸=빨강 테두리 마름모. 선택 아군 칸도 노랑 테두리 마름모. (**사거리 영역 전체 표시는 G98에서 추가 — 아래 ★v9.**)
6. **트윈·데미지텍스트·죽은유닛**: v3의 5·4·6 그대로 유지하되 좌표만 `cell_to_screen` 기반(트윈은 직전칸 `cell_to_screen`→현재칸 `cell_to_screen` 픽셀 보간). 플로팅 텍스트는 칸 중심 위쪽에서 떠오른다. **데미지 숫자는 정수로 표시**(`str(int(round(diff)))` — hp가 JSON float라 "-3.0"으로 나오면 안 된다, "-3").
7. **HUD 띠**: v3의 상단 반투명 띠 + "미션명 · 턴" 유지(아이소 보드는 origin.y만큼 내려가 있어 더 안전).
8. **공격 화살표(근접 직선/원거리 포물선)** — ✅ **이번 증분(G97). 아래 ★v8 사양대로 추가하라.**

## ★ v7 자동 전투 모드 (AUTO — 2026-06-24 사용자 요청, 브라운더스트2/트릭컬식)
플레이어가 매 턴 안 누른다. 아군도 정책이 자동 구동되고, 사람은 관전한다(이동 트윈·HP 변화·데미지 텍스트로 보임). **수동 조작(`_unhandled_input`·`cell_to_screen`)은 그대로 유지**한다 — 검증·향후 덱 편성에 쓴다. AUTO는 그 위에 자동 진행만 얹는다.

- **멤버**: `var auto_mode = true`(기본 on), `var auto_ally_idx = 0`(라운드로빈 커서), `var auto_accum = 0.0`(틱 누적시간).
- **`func auto_step() -> void`(공개·필수)**: `screen!="PLAYING"`이면 즉시 return. 아니면 **아군 1명**을 골라 그 액션 1개를 만들어 `state.status = rules.update_state(state, action)` 1회 호출. 데미지/플로터/플래시 fx는 manual `execute_action`과 동일하게 생성(hp 스냅샷 비교). status가 PLAYING이 아니면 `screen="RESULT"`. **`selected_unit_id`는 안 건드린다(수동과 독립).**
- **아군 선택(라운드로빈·결정적)**: 살아있는 아군을 id 오름차순 리스트로 만들고 `auto_ally_idx % 산 아군수`로 한 명 고른 뒤 `auto_ally_idx += 1`. (산 아군이 없으면 return — 곧 DEFEAT 처리됨.)
- **그리디 정책(결정적·RNG 금지)**: 고른 아군 `u`에 대해
  1. **공격 우선**: 사거리(`1 <= dist <= u.range`, range 없으면 1) 안에 살아있는 적이 있으면 **가장 가까운(동률은 낮은 id)** 적을 향해 `{"unit":u.id,"type":"attack"}`.
  2. **없으면 이동**: 가장 가까운 적(동률 낮은 id) 쪽으로 맨해튼 거리를 줄이는 **직교 한 칸**으로 `{"unit":u.id,"type":"move","dir":[dx,dy]}`. 후보 방향 우선순위 고정(예: 가로 먼저[적이 x로 더 멀면 ±x], 그다음 세로), **빈 칸·격자 안**일 때만. 막혔으면 다른 축으로, 그래도 막혔으면 그 아군은 패스(아무 액션 안 하고 return — 다음 틱에 다른 아군).
- **타이머(관전 속도)**: `_process(delta)`에서 `if auto_mode and screen=="PLAYING": auto_accum += delta; if auto_accum >= 0.6: auto_accum = 0; auto_step()`. (0.6s/틱. 이동 트윈이 그 사이 보인다.)
- **종료**: status가 VICTORY/DEFEAT면 `screen="RESULT"`(기존 RESULT 화면·버튼 그대로). RESULT에서 자동 진행 멈춤.
- ⚠ **결정성**: 같은 미션을 두 번 자동 플레이하면 **턴 수·결과가 동일**해야 한다(RNG·시간의존 분기 금지 — 정책은 state만 보고 결정). 프로브가 2회 돌려 일치를 검증한다.
- **수동과의 공존**: load_mission은 기존 계약대로(수동 가능)에 더해 **`auto_ally_idx=0`·`auto_accum=0`도 리셋**한다(미션 재시작 시 자동 전투가 동일하게 재현되게). 입력 프로브는 `load_mission` 직후 `auto_mode=false`로 꺼 수동을 깨끗이 검증한다. 자동 프로브는 `auto_step()`을 직접 반복 호출(타이머 무관)하고, 같은 미션을 2회 돌려 턴 수·결과 일치를 본다.

> v3 항목과의 관계: v3의 **HP바·데미지외곽선·트윈·죽은유닛·HUD띠는 그대로 유효**하다. v3의 "정사각 그리드라인(3번)"과 "셀 하단 HP바 위치"만 위 v4 1·4번(다이아몬드 격자·머리 위 바)으로 **대체**된다.

## ★ v8 공격 화살표 (2026-06-23 G97 — 이번 증분, v4·v7 위에 표시만 얹음)
공격 액션이 적에게 피해를 줄 때, 공격자 칸에서 **피해 입은 적 칸**으로 향하는 화살표를 짧게 띄운다. 근접(range<=1)은 직선, 원거리(range>1)는 포물선. **순수 표시 — state/룰/`selected_unit_id`/turn 불변.** 결정적 검증·프로브·골든·퍼징에 0 영향이어야 한다.

- **발생 시점**: manual `execute_action`·auto `auto_step` 공통. `action.type=="attack"`일 때만. board가 이미 데미지 FX용으로 들고 있는 **공격 전 hp 스냅샷**을 재사용해 **이번 액션에 hp가 준 적**을 target으로 잡고(여럿이면 각각), 공격자(=`action.unit`인 아군)에서 그 적 칸으로 화살표 effect를 spawn한다. **이동 액션엔 화살표 없음.** 적이 0데미지(보호막 등)면 화살표 생략 가능.
- **range 판정**: 공격자 아군의 `get("range",1)`. `>1`이면 `ranged=true`(포물선), 아니면 직선.
- **effect 데이터(표시 전용)**: 기존 `effects` 배열에 `{ "type":"arrow", "from_cell":[ax,ay], "to_cell":[ex,ey], "ranged":bool, "life":0.4, "max_life":0.4 }` 추가. `_process(delta)`에서 `life -= delta`, 만료 시 제거(데미지 텍스트와 동일 수명 관리). **state엔 절대 안 박는다.**
- **그리기(`_draw`, 유닛보다 위 레이어 — 데미지 텍스트 직전쯤)**: 끝점은 `cell_to_screen`로 잡고 유닛 가슴 높이로 올린다.
  - `var a = cell_to_screen(int(fx["from_cell"][0]), int(fx["from_cell"][1])) + Vector2(0, -TILE_H * 0.4)`
  - `var b = cell_to_screen(int(fx["to_cell"][0]), int(fx["to_cell"][1])) + Vector2(0, -TILE_H * 0.4)`
  - `var alpha = clamp(fx["life"] / fx["max_life"], 0.0, 1.0)`
  - **근접(`ranged==false`)**: `draw_line(a, b, Color(1, 1, 0.3, alpha), 3.0)`.
  - **원거리(`ranged==true`)**: 포물선. `t`를 0..1로 16분할, 각 점 = `a.lerp(b, t) + Vector2(0, -TILE_H * 1.2 * (4.0 * t * (1.0 - t)))`(위로 솟는 아치). 점들을 `PackedVector2Array`에 **append로** 모아 `draw_polyline(pts, Color(0.6, 0.9, 1, alpha), 3.0)`. ⚠ **PackedVector2Array에 Array를 `+`로 붙이지 마라**(함정 — append만).
  - **화살촉(옵션·간단)**: `var dir = (b - a).normalized()`; 그 반대 방향으로 좌우 약간 벌린 짧은 선 2개를 `b`에서 그린다. 한 줄 다중변수 선언 금지(`var` 따로따로).
- ⚠ **함정 재확인**: `draw_set_transform` 금지(점 직접 계산). `var p1, p2 = ...` 다중선언 금지. 색은 `draw_line`/`draw_polyline`의 마지막 인자.
- **검증 불변(필수)**: 화살표는 `effects`(표시 전용)라 입력 프로브·fixture 프로브·자동 프로브·골든·차등 퍼징이 **전부 그대로 통과**해야 한다. 하나라도 깨지면 화살표가 state를 건드린 것이니 표시 전용으로 되돌려라.

## ★ v9 사거리 영역 표시 (2026-06-23 G98 — 이번 증분, v4 하이라이트 5번 확장)
선택한 아군의 **공격 사거리 영역 전체**를 칠해 어디까지 때릴 수 있는지 한눈에 보인다(현 기본형은 적 칸 테두리만). **순수 표시 — state/룰/`selected_unit_id`/turn 불변.** 프로브·골든·퍼징·시각 게이트에 0 영향이어야 한다.

- 선택 아군 `actor`(`selected_unit_id`로 찾은 살아있는 아군)의 `range = actor.get("range", 1)`.
- 보드 모든 칸 (gx,gy)에 대해 `dist = abs(actor.pos[0]-gx) + abs(actor.pos[1]-gy)`. **`1 <= dist <= range`이면 사거리 영역** — 그 칸 다이아몬드를 **옅은 빨강 반투명 fill**(`Color(1, 0.3, 0.3, 0.12)` 정도, 바닥이 비치게 옅게)로 칠한다.
  - 그 칸에 **살아있는 적**이 있으면 v4대로 **빨강 테두리 마름모**를 위에 덧그려 타겟 강조.
  - **이동 가능 빈 인접칸=초록 반투명·선택 아군 칸=노랑 테두리**는 v4대로 유지(영역 fill과 공존).
- **레이어 순서**: 바닥 → **사거리 영역 fill(옅은 빨강)** → 이동 초록 → 적 빨강 테두리 → 유닛 → (v8 화살표·데미지텍스트). 영역 fill이 유닛이나 적 테두리를 가리면 안 된다(유닛보다 아래).
- ⚠ 다이아몬드 꼭짓점은 `cell_to_screen` 기반(네 점 `draw_colored_polygon`, **PackedVector2Array에 Array `+` 금지 — append만**). 한 줄 다중변수 선언 금지.
- **auto_mode와 무관**: 자동전투 중엔 `selected_unit_id`가 없어 영역이 안 그려질 수 있고 정상(수동 선택 시 보인다). 표시 전용이라 auto_step·결정성에 영향 0.
- **검증 불변(필수)**: 입력 프로브·fixture·자동 프로브·골든·차등 퍼징·시각 게이트(MENU/BRIEFING는 안 바뀜)가 **전부 그대로 통과**해야 한다. 하나라도 깨지면 영역 표시가 state를 건드렸거나 다른 화면을 바꾼 것.

## ★ v10 덱 편성 단계 SQUAD_SELECT (2026-06-23 G100 — 이번 증분, "선택→자동전투" 루프를 닫음)
브리핑 다음에 **전투 전 유닛 선택** 단계를 끼운다. 플레이어가 로스터에서 부대를 고르면 그 선택이 battle의 `allies`가 된다. **enemies는 미션 고정.** 룰·골든·rules.gd 불변 — 입력 진입만 바뀐다.

- **멤버**: `var roster = []`(로딩서 채움), `var cost_budget = 0`(로딩서 채움), `var picked_ids = []`(현재 고른 로스터 id들). `screen=="SQUAD_SELECT"` 진입(BRIEFING 클릭) 시 `picked_ids.clear()`.
- **편성 규칙**: 정확히 `squad_size`명을 고르되 **고른 유닛 cost 합 ≤ `cost_budget`**. `squad_size = levels[pending_idx].initialState.allies.size()`(=미션이 기대하는 아군 수, 현재 전부 2). 강한 유닛은 cost가 높아 "아무나 N명"이 아니라 트레이드오프가 생긴다(예산 7·squad 2면 kael4+ria4=8은 막힘). 두 조건을 모두 만족하기 전엔 "출전" 비활성(클릭 무시).
- **헬퍼**: `func picked_cost() -> int`(고른 유닛 cost 합). 유닛 cost는 `roster`에서 id로 찾아 `u.get("cost", 0)`.
- **선택 입력(`screen=="SQUAD_SELECT"`, 좌클릭)**: 유닛 카드 클릭 → 토글. 안 골랐으면 추가(단 이미 `squad_size`명이면 무시 — **cost 초과는 추가는 허용하고 "출전"에서 막는다**, 그래야 무엇을 빼야 할지 보인다), 골랐으면 제거. "출전" 버튼 클릭 → `picked_ids.size()==squad_size and picked_cost()<=cost_budget`일 때만 `start_battle_with(picked_ids)`.
- **메서드 `func start_battle_with(ids: Array) -> void`(공개·새 진입 경로)**: 주어진 ids로 전투를 구성한다(예산·count 게이트는 위 "출전" 클릭 경로의 책임). 캡처 하네스가 **예산 내 유효 부대**로 이걸 직접 불러 PLAYING 진입을 검증한다.
  - `var picked_allies = []`. `ids` 순서대로 `i`(0부터): 로스터 유닛을 깊은복제(`JSON.parse_string(JSON.stringify(u))`)하고 **전투용으로 정규화** — `id = i+1`(**정수 id 1..N, 미션 allies와 동일 의미** → 적 AI 타이브레이크가 기존과 동일하게 동작), `pos = [0, i]`(0열에 세로 배치). `name/role/desc/_comment`는 전투엔 불필요하니 떨궈도 되고 남겨도 무방(룰은 안 읽음). 카드필드(range/knockback/...)는 그대로 보존.
  - `var init = JSON.parse_string(JSON.stringify(levels[pending_idx].initialState))`. `init.allies = picked_allies`(enemies·gridSize는 미션 그대로). 
  - 그 다음은 **load_mission과 동일한 마감**: `state = init`, `state.turn=0`, `state.status="PLAYING"`, `selected_unit_id=null`, `auto_ally_idx=0`, `auto_accum=0`, `screen="PLAYING"`. (load_mission 본체를 복제하지 말고, 공통 마감을 `_enter_battle(init_state)` 헬퍼로 빼서 load_mission도 그걸 부르게 하면 중복이 없다 — 단 **load_mission의 외부 동작·시그니처는 불변**.)
- **불변(필수)**: `load_mission(idx)`는 그대로 미션 고정 allies로 PLAYING 직행(프로브·fixture·test_bridge 의존). SQUAD_SELECT/start_battle_with는 **순수 추가** — 골든·입력프로브·fixture·자동프로브·차등퍼징·시각게이트(MENU/BRIEFING)가 **전부 그대로 통과**해야 한다. 적 AI가 정수 id를 타이브레이크에 쓰므로 start_battle_with가 `id=1..N` 정수로 재부여하는 게 핵심(로스터 문자열 id를 그대로 넣지 마라).

## 검증 (모두 통과해야 채택)
1. 헤드리스 스모크: `--quit-after 30` 가 SCRIPT ERROR/Parse Error 없이 뜸.
2. 입력 프로브: `--script res://test/run_input_probe.gd` 가 **종료코드 0**(미션0 통합 — 선택·이동·공격을 구조화 비교, 불일치 시 `quit(1)`. 출력은 `PROBE_JSON`의 expected vs actual). `load_mission(0)`로 메뉴 우회 후 검증.
3. fixture 프로브: `--script res://test/run_fixture_probe.gd` 가 **종료코드 0**(미션0 비의존 기능 단위 계약 — `test/fixtures/*.json`, `board.levels=[fixture]` 주입). 불일치 시 `quit(1)`.
4. 자동 전투 프로브: `--script res://test/run_auto_probe.gd` 가 `자동 전투 동작함`(결정적 종료·2회 재현 일치).
5. **렌더 캡처(windowed)**: `--script res://test/capture_attack.gd` 가 _draw(MENU+PLAYING)를 실제로 그리며
   SCRIPT ERROR/Parse Error 없이 `test/cap_menu.png`·`test/cap_after.png`를 생성해야 한다.
   (헤드리스 스모크/프로브가 `_draw`를 호출 안 해 못 잡는 draw_string 시그니처·폰트·텍스처 로드 에러를 여기서 잡는다. **v8 화살표의 draw_line/draw_polyline 에러도 여기서 잡힌다.**)
6. 차등 퍼징: `python golem/tools/godot_fuzz_diff.py` 가 `ALL MATCH`(rules.gd ≡ JS 엔진 — 화살표는 표시 전용이라 영향 0이어야 한다).
7. **SQUAD_SELECT 화면 캡처·검사(G99식 화면별 게이트, board.gd 재생성 증분서 추가)**: 캡처 하네스가 `screen="SQUAD_SELECT"`로도 `_draw`를 그려 SCRIPT ERROR 없이 PNG 생성 + MENU/BRIEFING과 픽셀차이로 새 화면이 실제로 다르게 그려지는지 검사(브리핑 회귀 차단과 동형). `start_battle_with([로스터 앞 2개 id])` 호출 후 PLAYING 상태가 `allies.size()==2`·`status=="PLAYING"`인지 키0 브리지로 확인.
8. 최종 미관(예쁜지)과 실제 터치는 사람이 확인(0-diff 범위 밖).
