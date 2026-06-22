# board.gd 입력 로직 헤드리스 검증 — 가짜 마우스 이벤트로 선택→이동이 되는지 확인(터치/웹 무관, 순수 로직)
extends SceneTree

var board
var done = false

func _initialize():
	board = load("res://scenes/main.tscn").instantiate()
	get_root().add_child(board)

func _process(_d):
	if done:
		return true
	done = true
	# 여기선 board._ready 가 이미 실행됨(미션0 로드)
	var grid = board.state["gridSize"]
	var cell = 640.0 / grid
	var ally = board.state["allies"][0]
	var ax = ally["pos"][0]
	var ay = ally["pos"][1]
	print("PROBE grid=", grid, " cell=", cell, " ally0=", ally["id"], " pos=", [ax, ay])

	# 1) 아군 셀 중앙 클릭 → 선택돼야 함
	var ev = InputEventMouseButton.new()
	ev.button_index = MOUSE_BUTTON_LEFT
	ev.pressed = true
	ev.position = Vector2(ax * cell + cell / 2, ay * cell + cell / 2)
	board._unhandled_input(ev)
	print("PROBE [select] selected_unit_id=", board.selected_unit_id, " (기대=", ally["id"], ")")

	# 2) 빈 인접칸으로 이동 → turn 증가 기대
	var before_turn = board.state["turn"]
	var tx = ax
	var ty = ay
	for d in [[1, 0], [-1, 0], [0, 1], [0, -1]]:
		var nx = ax + d[0]
		var ny = ay + d[1]
		if nx < 0 or nx >= grid or ny < 0 or ny >= grid:
			continue
		var occ = false
		for u in board.state["allies"] + board.state["enemies"]:
			if u["hp"] > 0 and u["pos"] == [nx, ny]:
				occ = true
				break
		if not occ:
			tx = nx
			ty = ny
			break
	var ev2 = InputEventMouseButton.new()
	ev2.button_index = MOUSE_BUTTON_LEFT
	ev2.pressed = true
	ev2.position = Vector2(tx * cell + cell / 2, ty * cell + cell / 2)
	board._unhandled_input(ev2)
	print("PROBE [move] target=", [tx, ty], " turn ", before_turn, "->", board.state["turn"], " status=", board.state["status"])

	if board.selected_unit_id != null or board.state["turn"] != before_turn:
		print("PROBE RESULT: 입력 로직 동작함")
	else:
		print("PROBE RESULT: 무반응 — board.gd 문제")
	quit()
	return true
