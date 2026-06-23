# 실제 렌더 화면을 PNG로 캡처 — MENU·BRIEFING·공격후를 그려 draw 에러를 잡고, BRIEFING이 메뉴와 다른 화면인지(회귀 차단) 검사
extends SceneTree

var board
var frame = 0
var img_menu
var img_briefing

func _initialize():
	board = load("res://scenes/main.tscn").instantiate()
	get_root().add_child(board)

func _tap(gx, gy):
	var ev = InputEventMouseButton.new()
	ev.button_index = MOUSE_BUTTON_LEFT
	ev.pressed = true
	ev.position = board.cell_to_screen(gx, gy)  # 아이소 투영 — board가 단일 진실원천
	board._unhandled_input(ev)

func _tap_raw(px, py):
	var ev = InputEventMouseButton.new()
	ev.button_index = MOUSE_BUTTON_LEFT
	ev.pressed = true
	ev.position = Vector2(px, py)  # 메뉴 버튼은 원시 화면좌표(보드 투영 아님)
	board._unhandled_input(ev)

func _cap_img():
	return get_root().get_texture().get_image()

# 두 이미지의 다른 픽셀 비율(샘플링) — BRIEFING이 MENU와 거의 같으면(브리핑을 안 그림) 0에 가깝다
func _diff_ratio(a, b) -> float:
	if a == null or b == null:
		return 0.0
	if a.get_width() != b.get_width() or a.get_height() != b.get_height():
		return 1.0
	var w = a.get_width()
	var h = a.get_height()
	var diff = 0
	var total = 0
	var step = 4
	var x = 0
	while x < w:
		var y = 0
		while y < h:
			total += 1
			if a.get_pixel(x, y) != b.get_pixel(x, y):
				diff += 1
			y += step
		x += step
	return float(diff) / float(max(total, 1))

func _process(_d):
	frame += 1
	if frame == 2:
		img_menu = _cap_img()
		img_menu.save_png("res://test/cap_menu.png")  # _ready 직후 screen=MENU
	elif frame == 3:
		_tap_raw(320, 175)  # 미션0 버튼 탭 → MENU에서 BRIEFING으로
	elif frame == 4:
		img_briefing = _cap_img()
		img_briefing.save_png("res://test/cap_briefing.png")
		print("BRIEFING_SCREEN=", board.screen, " BRIEFING_DIFF_RATIO=", _diff_ratio(img_menu, img_briefing))
	elif frame == 5:
		board.load_mission(0)  # v2 계약: 메뉴 우회하고 곧장 플레이 상태로
		board.auto_mode = false  # 렌더 게이트는 수동 시연 — 자동전투 간섭 끔(v7)
	elif frame == 7:
		_cap_img().save_png("res://test/cap_before.png")
		print("BEFORE enemies: ", _enemy_hps())
	elif frame == 9:
		# ally2(range2) 선택 → enemy2[2,1] 공격
		_tap(0, 1)
		_tap(2, 1)
		board.queue_redraw()
		print("AFTER  enemies: ", _enemy_hps())
	elif frame == 12:
		_cap_img().save_png("res://test/cap_after.png")
		quit()
		return true
	return false

func _enemy_hps():
	var out = []
	for e in board.state["enemies"]:
		out.append([e["id"], e["hp"], e["pos"]])
	return out
