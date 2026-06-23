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
- 메서드 `func cell_to_screen(gx:int, gy:int) -> Vector2` (**공개·필수**): 칸 (gx,gy)의 **화면 픽셀 중심**을 아이소 투영으로 반환한다. `_draw`(타일·유닛 배치)와 `_unhandled_input`의 클릭 히트판정이 **이 한 함수를 단일 진실원천으로** 쓴다. 프로브·캡처 하네스가 이 함수를 직접 호출해 클릭 위치를 잡으므로 **시그니처를 절대 바꾸지 마라.**
- **좌표계(아이소메트릭 2.5D·필수)**: 보드는 다이아몬드 격자다. 투영 =
  `cell_to_screen(gx,gy) = origin + Vector2((gx-gy)*TILE_W/2.0, (gx+gy)*TILE_H/2.0)` (2:1 아이소 → `TILE_H = TILE_W/2.0`).
  `TILE_W`·`origin`은 GxG 보드가 가로로 화면 폭(≈600, 좌우 여백 둠)에 맞고 **가로·세로 모두 가운데 정렬**되게 골렘이 정한다. 권장 `TILE_W = 600.0/state.gridSize`(→ `TILE_H = TILE_W/2`), `origin.x = 320`. **세로 중앙정렬**: 다이아몬드의 세로 픽셀 높이는 `(gridSize-1)*TILE_H`이므로 `origin.y = (640 + HUD높이)/2 - (gridSize-1)*TILE_H/2`로 둬서 보드가 화면 세로 가운데(HUD 아래)에 오게 한다 — 위로 쏠려 아래가 휑하면 안 된다(2026-06-24 캡처 실측).
  - **클릭→칸은 위 투영의 정확한 역변환**이어야 한다: `rx=(px-origin.x)/(TILE_W/2.0)`, `ry=(py-origin.y)/(TILE_H/2.0)` → `gx=int(round((rx+ry)/2.0))`, `gy=int(round((ry-rx)/2.0))`. 즉 `cell_to_screen(gx,gy)` 위치를 클릭하면 정확히 칸 (gx,gy)가 잡혀야 한다(프로브가 이 왕복을 검증).
  - **탑다운 `int(x/cell)` 좌표계 금지.** 고정 cell·고정 offset 금지. origin/TILE_W는 위 식으로 gridSize에서 유도.

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
   `draw_colored_polygon(pts, fill)`로 채우고 `draw_polyline(pts+[pts[0]], 격자선색, 1.0)`로 마름모 테두리(=그리드). **갈색 막대 변주 금지** — fill은 미션 톤(`tones[current_mission_idx%n]`) 기반, 칸별 미세 명도 변화는 `(gx*7+gy*13)%5`로 ±0.04 정도만(바닥 결, 튀지 않게). 격자선은 은은하게(알파 ~0.15).
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
5. **하이라이트(선택 시 — 이동/공격 사거리 분리 표시)**: v3 정사각 대신 그 칸의 **다이아몬드**로 칠한다. 선택 아군 기준:
   - **이동 가능 칸**(`dist==1` 빈 칸): 초록 반투명 마름모 **fill**(`draw_colored_polygon`).
   - **공격 사거리 칸**(`1 <= dist <= range`, range 없으면 1): **빨강 테두리 마름모**(`draw_polyline`로 마름모 외곽). `range>1`(마법사)이면 **2칸까지 빈 칸도 전부** 테두리가 떠 reach가 보인다 — 이게 '공격 사거리 타일 표시'의 핵심(2026-06-24 사용자 요청).
   - **사거리 안에 적이 올라간 칸**: 더 진한 빨강(테두리 두껍게 + fill 살짝)으로 때릴 수 있는 적 강조.
   - 선택 아군 자기 칸: 노랑 테두리 마름모.
   - ⚠ **이동(초록 fill) vs 공격사거리(빨강 테두리)가 색·표현으로 구분**돼야 한다(겹치는 인접칸은 둘 다 보이게).
6. **트윈·데미지텍스트·죽은유닛**: v3의 5·4·6 그대로 유지하되 좌표만 `cell_to_screen` 기반(트윈은 직전칸 `cell_to_screen`→현재칸 `cell_to_screen` 픽셀 보간). 플로팅 텍스트는 칸 중심 위쪽에서 떠오른다. **데미지 숫자는 정수로 표시**(`str(int(round(diff)))` — hp가 JSON float라 "-3.0"으로 나오면 안 된다, "-3").
7. **HUD 띠**: v3의 상단 반투명 띠 + "미션명 · 턴" 유지(아이소 보드는 origin.y만큼 내려가 있어 더 안전).
8. **공격 화살표(2026-06-24 사용자 요청 — 근접 직선 / 원거리 포물선)**: 공격 액션 시(`execute_action`의 attack 분기) 공격자 칸→대상 칸으로 **짧게 날아가는 화살표** 이펙트(시간 기반, `_process` 수명 감소, state 불건드림).
   - 멤버 `attack_fx` 배열: `{from: Vector2, to: Vector2, ranged: bool, life: float}`(from/to는 `cell_to_screen`, 수명 ~0.3s, 만료 제거).
   - **근접(range<=1): 직선** — `from`→`to` `draw_line` + 끝에 화살촉(작은 삼각형 `draw_colored_polygon`).
   - **원거리(range>=2): 포물선 호** — 2차 베지어. 제어점 `ctrl = (from+to)/2 + Vector2(0, -호높이)`(호높이 ≈ `from.distance_to(to)*0.3`, 위로 솟게). `t`를 0..1로 ~12등분 `p = (1-t)*(1-t)*from + 2*(1-t)*t*ctrl + t*t*to` 점들을 `draw_polyline`로 잇고 끝점에 화살촉.
   - 화살표는 깊이정렬된 유닛보다 **위**(최상단 오버레이). 잘 보이게 노랑/흰 + 외곽선. **`draw_set_transform` 쓰지 마라**(베지어·삼각형은 점 계산으로). 표시 전용 — 룰/상태·프로브에 영향 없음.

> v3 항목과의 관계: v3의 **HP바·데미지외곽선·트윈·죽은유닛·HUD띠는 그대로 유효**하다. v3의 "정사각 그리드라인(3번)"과 "셀 하단 HP바 위치"만 위 v4 1·4번(다이아몬드 격자·머리 위 바)으로 **대체**된다.

## 검증 (모두 통과해야 채택)
1. 헤드리스 스모크: `--quit-after 30` 가 SCRIPT ERROR/Parse Error 없이 뜸.
2. 입력 프로브: `--script res://test/run_input_probe.gd` 가 `PROBE RESULT: 입력 로직 동작함` + `PROBE ATTACK RESULT: 공격 동작함`.
   (프로브는 `load_mission(0)`로 메뉴를 우회 → 클릭 선택·이동·공격을 결정적 검증.)
3. **렌더 캡처(windowed)**: `--script res://test/capture_attack.gd` 가 _draw(MENU+PLAYING)를 실제로 그리며
   SCRIPT ERROR/Parse Error 없이 `test/cap_menu.png`·`test/cap_after.png`를 생성해야 한다.
   (헤드리스 스모크/프로브가 `_draw`를 호출 안 해 못 잡는 draw_string 시그니처·폰트·텍스처 로드 에러를 여기서 잡는다.)
4. 최종 미관(예쁜지)과 실제 터치는 사람이 확인(0-diff 범위 밖).
