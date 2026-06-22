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
	board.load_mission(0)  # v2 계약: 메뉴 우회하고 곧장 플레이 상태로
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

	# 3) 공격 — 미션 리셋 후, 사거리 내 적이 있는 아군을 찾아 그 적 칸을 탭 → 적 hp 감소 기대
	board.load_mission(0)
	var atk_ally = null
	var atk_enemy = null
	for a in board.state["allies"]:
		if a["hp"] <= 0:
			continue
		var rng = a.get("range", 1)
		for e in board.state["enemies"]:
			var d = abs(a["pos"][0] - e["pos"][0]) + abs(a["pos"][1] - e["pos"][1])
			if e["hp"] > 0 and d >= 1 and d <= rng:
				atk_ally = a
				atk_enemy = e
				break
		if atk_ally:
			break
	if atk_ally == null:
		print("PROBE [attack] 첫 턴 사거리 내 쌍 없음(이동 후에만 공격 가능 — 룰상 정상)")
	else:
		var ea = atk_ally["pos"][0]
		var eb = atk_ally["pos"][1]
		var sel = InputEventMouseButton.new()
		sel.button_index = MOUSE_BUTTON_LEFT
		sel.pressed = true
		sel.position = Vector2(ea * cell + cell / 2, eb * cell + cell / 2)
		board._unhandled_input(sel)
		var hp_before = atk_enemy["hp"]
		var tap = InputEventMouseButton.new()
		tap.button_index = MOUSE_BUTTON_LEFT
		tap.pressed = true
		tap.position = Vector2(atk_enemy["pos"][0] * cell + cell / 2, atk_enemy["pos"][1] * cell + cell / 2)
		board._unhandled_input(tap)
		print("PROBE [attack] ally=", atk_ally["id"], " range=", atk_ally.get("range", 1),
			" enemy=", atk_enemy["id"], " hp ", hp_before, "->", atk_enemy["hp"])
		if atk_enemy["hp"] < hp_before:
			print("PROBE ATTACK RESULT: 공격 동작함")
		else:
			print("PROBE ATTACK RESULT: 공격 무반응 — board.gd 공격 분기 문제")
	quit()
	return true
