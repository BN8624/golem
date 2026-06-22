# 공격 전/후 실제 렌더 화면을 PNG로 캡처 — 적 hp 텍스트가 화면에 갱신되는지 눈으로 검증(windowed 실행)
extends SceneTree

var board
var frame = 0

func _initialize():
	board = load("res://scenes/main.tscn").instantiate()
	get_root().add_child(board)

func _tap(gx, gy):
	var cell = 640.0 / board.state["gridSize"]
	var ev = InputEventMouseButton.new()
	ev.button_index = MOUSE_BUTTON_LEFT
	ev.pressed = true
	ev.position = Vector2(gx * cell + cell / 2, gy * cell + cell / 2)
	board._unhandled_input(ev)

func _cap(path):
	var img = get_root().get_texture().get_image()
	img.save_png(path)

func _process(_d):
	frame += 1
	if frame == 3:
		_cap("res://test/cap_before.png")
		print("BEFORE enemies: ", _enemy_hps())
	elif frame == 5:
		# ally2(range2) 선택 → enemy2[2,1] 공격
		_tap(0, 1)
		_tap(2, 1)
		board.queue_redraw()
		print("AFTER  enemies: ", _enemy_hps())
	elif frame == 8:
		_cap("res://test/cap_after.png")
		quit()
		return true
	return false

func _enemy_hps():
	var out = []
	for e in board.state["enemies"]:
		out.append([e["id"], e["hp"], e["pos"]])
	return out
