# GDScript 함정 — 골렘이 GDScript를 생성할 때 반드시 지키는 공통 규칙

이 파일은 `godot_port_scene.py`가 **모든 board.gd 생성 프롬프트에 자동 주입**한다(omc skills auto-inject 패턴 차용).
씬별 사양(SCENE_SPEC)과 별개로, 어떤 Godot 4 GDScript에도 공통으로 적용되는 함정만 모은다.
새 함정을 발견하면 SCENE_SPEC이 아니라 **여기에** 추가한다 — 그래야 board.gd 한 파일 너머로 재사용된다.

## 1. `var a, b = ...` 한 줄 다중 선언 금지
GDScript는 한 `var`에 변수 하나만. `Parse Error: Expected end of statement after variable declaration, found ","`.
- 틀림: `var dx, dy = 0, 0`
- 맞음: `var dx = 0` 다음 줄 `var dy = 0`

## 2. `PackedVector2Array + Array` 금지 (`+` 연산자)
`Invalid operands 'PackedVector2Array' and 'Array' in operator '+'`. 닫힌 폴리라인은 점 배열을 직접 만든다.
- 틀림: `draw_polyline(pts + [pts[0]], col, 1.0)`
- 맞음: `draw_polyline(PackedVector2Array([p0, p1, p2, p3, p0]), col, 1.0)` (첫 점을 끝에 한 번 더)

## 3. `draw_string` 시그니처
Godot 4: `draw_string(font, pos:Vector2, text, alignment, width, font_size, modulate)`.
- 색을 주려면: `draw_string(font, pos, text, HORIZONTAL_ALIGNMENT_LEFT, -1, 16, color)`.
- `draw_string(font, 0, pos, text, color)`처럼 쓰면 인자가 밀려 **실렌더 시 깨진다**(헤드리스 스모크/프로브는 `_draw`를 호출 안 해 못 잡으니 렌더 캡처로만 잡힌다).
- `draw_string`은 `\n`을 무시한다 — 여러 줄은 줄 단위로 나눠 그리거나 `draw_multiline_string`.

## 4. `draw_set_transform`은 변환 행렬 전용 — 색·인자수 함정
시그니처 `draw_set_transform(pos:Vector2, rot:float, scale:Vector2)`. 인자 수·타입을 자주 틀린다(`Too many arguments`, `argument 1 should be Vector2 but is int`).
- 여기에 Color를 넣지 마라(색은 그리기 함수의 modulate 인자로).
- 납작한 타원이 필요하면 `draw_set_transform`로 누르지 말고 **타원 점들을 직접 계산해 `draw_colored_polygon`**: `for i in range(16): pts.append(c + Vector2(cos(t)*rx, sin(t)*ry))`.
- `draw_circle`는 정원이라 못 누른다 — 타원은 위 폴리곤으로.

## 5. JSON 좌표는 float, 클릭 셀은 int — 배열 비교 함정
JSON에서 온 `pos`는 float `[0.0, 0.0]`, 계산한 셀은 int. GDScript에서 `[0.0,0.0] == [0,0]`은 **false**(배열은 원소 타입까지 엄격 비교).
- 틀림: `if u.pos == [gx, gy]:`
- 맞음: `if int(u.pos[0]) == gx and int(u.pos[1]) == gy:` (원소별 + int 캐스트)

## 6. 아군·적 id 겹침 — dict 키는 진영을 합쳐라
아군과 적은 id가 겹친다(양쪽 다 1,2,…). hp 스냅샷·flash·이펙트 등을 dict 키로 들 때 id만 쓰면 같은 id의 아군·적이 섞여 **엉뚱한 유닛이 빨개지고 데미지 계산이 틀린다**.
- 맞음: 키를 `"a" + str(id)` / `"e" + str(id)`로.

## 7. 플레이 전 `state`는 비어 있다 — 가드
MENU/BRIEFING에서 `state == {}`. `_process`·`_draw`가 `state.allies`/`state.enemies`/`state.gridSize`에 접근하려면 **반드시 `screen=="PLAYING"` 가드 안에서만**. 안 그러면 `Invalid access to property 'allies' on Dictionary` 크래시(스모크가 MENU 부팅이라 바로 터진다).
