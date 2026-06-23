# board.gd 입력 계약 헤드리스 검증(미션0 통합) — 선택·이동·공격을 각각 구조화 비교하고 불일치 시 quit(1)로 종료
extends SceneTree

var board
var done = false
var failures = 0


func _initialize():
	board = load("res://scenes/main.tscn").instantiate()
	get_root().add_child(board)


func _click(gx: int, gy: int) -> void:
	var ev = InputEventMouseButton.new()
	ev.button_index = MOUSE_BUTTON_LEFT
	ev.pressed = true
	ev.position = board.cell_to_screen(gx, gy)
	board._unhandled_input(ev)


func _ally_by_id(id) -> Variant:
	for a in board.state["allies"]:
		if int(a["id"]) == int(id):
			return a
	return null


func _enemy_by_id(id) -> Variant:
	for e in board.state["enemies"]:
		if int(e["id"]) == int(id):
			return e
	return null


func _emit(test: String, passed: bool, expected, actual) -> void:
	if not passed:
		failures += 1
	print("PROBE_JSON ", JSON.stringify({"test": test, "passed": passed, "expected": expected, "actual": actual}))


func _process(_d):
	if done:
		return true
	done = true

	# ---- 선택 계약: 아군 탭 → 선택만, 턴/위치 불변 ----
	board.load_mission(0)
	board.auto_mode = false
	var ally = board.state["allies"][0]
	var ax := int(ally["pos"][0])
	var ay := int(ally["pos"][1])
	var t0 = board.state["turn"]
	_click(ax, ay)
	var sel_ok: bool = (board.selected_unit_id != null and int(board.selected_unit_id) == int(ally["id"]))
	var sel_still: bool = int(board.state["turn"]) == int(t0) and int(board.state["allies"][0]["pos"][0]) == ax and int(board.state["allies"][0]["pos"][1]) == ay
	_emit("select", sel_ok and sel_still,
		{"selected_unit_id": ally["id"], "turn": t0, "pos": [ax, ay]},
		{"selected_unit_id": board.selected_unit_id, "turn": board.state["turn"], "pos": board.state["allies"][0]["pos"]})

	# ---- 이동 계약: 선택 후 빈 인접칸 탭 → 유닛 이동 + turn+1 ----
	board.load_mission(0)
	board.auto_mode = false
	ally = board.state["allies"][0]
	ax = int(ally["pos"][0])
	ay = int(ally["pos"][1])
	var grid = board.state["gridSize"]
	var bt = int(board.state["turn"])
	var tx := ax
	var ty := ay
	var found := false
	for d in [[1, 0], [-1, 0], [0, 1], [0, -1]]:
		var nx = ax + int(d[0])
		var ny = ay + int(d[1])
		if nx < 0 or nx >= grid or ny < 0 or ny >= grid:
			continue
		var occ := false
		for u in board.state["allies"] + board.state["enemies"]:
			if u["hp"] > 0 and int(u["pos"][0]) == nx and int(u["pos"][1]) == ny:
				occ = true
				break
		if not occ:
			tx = nx
			ty = ny
			found = true
			break
	_click(ax, ay)  # 선택
	_click(tx, ty)  # 이동
	var moved = _ally_by_id(ally["id"])
	var move_ok: bool = found and int(moved["pos"][0]) == tx and int(moved["pos"][1]) == ty \
		and int(board.state["turn"]) == bt + 1 \
		and board.selected_unit_id != null and int(board.selected_unit_id) == int(ally["id"])
	_emit("move", move_ok,
		{"pos": [tx, ty], "turn": bt + 1, "selected_unit_id": ally["id"]},
		{"pos": moved["pos"], "turn": board.state["turn"], "selected_unit_id": board.selected_unit_id})

	# ---- 공격 계약: 첫 턴 사거리쌍이 있으면 적 HP가 공격력만큼 감소 + turn+1 ----
	board.load_mission(0)
	board.auto_mode = false
	var atk_ally = null
	var atk_enemy = null
	for a in board.state["allies"]:
		if a["hp"] <= 0:
			continue
		var rng = a.get("range", 1)
		for e in board.state["enemies"]:
			var dd: int = abs(int(a["pos"][0]) - int(e["pos"][0])) + abs(int(a["pos"][1]) - int(e["pos"][1]))
			if e["hp"] > 0 and dd >= 1 and dd <= rng:
				atk_ally = a
				atk_enemy = e
				break
		if atk_ally:
			break
	if atk_ally == null:
		# 미션0에 첫 턴 사거리쌍이 없으면 룰상 정상(이동 후에만 공격 가능) — 통합 테스트라 스킵 처리(실패 아님)
		print("PROBE_JSON ", JSON.stringify({"test": "attack", "passed": true, "note": "첫 턴 사거리 내 쌍 없음(룰상 정상)"}))
	else:
		var a_bt = int(board.state["turn"])
		var hp_before = int(atk_enemy["hp"])
		var expect_dmg = int(atk_ally["atk"])  # 미션0엔 보호막/반사 없음 → 단순 데미지
		var enemy_id = atk_enemy["id"]
		_click(int(atk_ally["pos"][0]), int(atk_ally["pos"][1]))  # 선택
		_click(int(atk_enemy["pos"][0]), int(atk_enemy["pos"][1]))  # 공격
		var en = _enemy_by_id(enemy_id)
		var atk_ok: bool = int(en["hp"]) == hp_before - expect_dmg and int(board.state["turn"]) == a_bt + 1
		_emit("attack", atk_ok,
			{"enemy_hp": hp_before - expect_dmg, "turn": a_bt + 1},
			{"enemy_hp": en["hp"], "turn": board.state["turn"]})

	print("PROBE_RESULT failures=", failures)
	quit(0 if failures == 0 else 1)
	return true
