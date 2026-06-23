# fixture 기반 입력 계약 검증 — test/fixtures/*.json 을 미션0과 무관하게 로드해 기능 단위로 board.gd 입력을 검증, 불일치 시 quit(1)
extends SceneTree

var board
var done = false
var failures = 0
var total = 0


func _initialize():
	board = load("res://scenes/main.tscn").instantiate()
	get_root().add_child(board)


func _click(gx, gy) -> void:
	var ev = InputEventMouseButton.new()
	ev.button_index = MOUSE_BUTTON_LEFT
	ev.pressed = true
	ev.position = board.cell_to_screen(int(gx), int(gy))
	board._unhandled_input(ev)


func _find_unit(kid: String) -> Variant:
	var arr = board.state["allies"] if kid.begins_with("a") else board.state["enemies"]
	var want := int(kid.substr(1))
	for u in arr:
		if int(u["id"]) == want:
			return u
	return null


func _pos_eq(a, b) -> bool:
	return int(a[0]) == int(b[0]) and int(a[1]) == int(b[1])


func _check_fixture(fx: Dictionary) -> void:
	total += 1
	board.levels = [fx]
	board.load_mission(0)
	board.auto_mode = false
	for click in fx["clicks"]:
		_click(click[0], click[1])

	var exp = fx["expect"]
	var mism := []

	if exp.has("selected_unit_id"):
		var want = exp["selected_unit_id"]
		if want == null:
			if board.selected_unit_id != null:
				mism.append("selected_unit_id got=%s want=null" % str(board.selected_unit_id))
		elif board.selected_unit_id == null or int(board.selected_unit_id) != int(want):
			mism.append("selected_unit_id got=%s want=%s" % [str(board.selected_unit_id), str(want)])

	if exp.has("turn") and int(board.state["turn"]) != int(exp["turn"]):
		mism.append("turn got=%s want=%s" % [str(board.state["turn"]), str(exp["turn"])])

	if exp.has("status") and str(board.state["status"]) != str(exp["status"]):
		mism.append("status got=%s want=%s" % [str(board.state["status"]), str(exp["status"])])

	if exp.has("screen") and str(board.screen) != str(exp["screen"]):
		mism.append("screen got=%s want=%s" % [str(board.screen), str(exp["screen"])])

	if exp.has("units"):
		for kid in exp["units"].keys():
			var u = _find_unit(kid)
			var want_u = exp["units"][kid]
			if u == null:
				mism.append("%s 유닛 없음" % kid)
				continue
			if want_u.has("pos") and not _pos_eq(u["pos"], want_u["pos"]):
				mism.append("%s.pos got=%s want=%s" % [kid, str(u["pos"]), str(want_u["pos"])])
			if want_u.has("hp") and int(u["hp"]) != int(want_u["hp"]):
				mism.append("%s.hp got=%s want=%s" % [kid, str(u["hp"]), str(want_u["hp"])])

	var passed: bool = mism.size() == 0
	if not passed:
		failures += 1
	print("FIXTURE_JSON ", JSON.stringify({"test": fx["name"], "passed": passed, "mismatches": mism}))


func _process(_d):
	if done:
		return true
	done = true

	var dir = DirAccess.open("res://test/fixtures")
	if dir == null:
		print("FIXTURE_RESULT no fixtures dir (res://test/fixtures 없음)")
		quit(2)
		return true

	var files := []
	dir.list_dir_begin()
	var f := dir.get_next()
	while f != "":
		if f.ends_with(".json"):
			files.append(f)
		f = dir.get_next()
	dir.list_dir_end()
	files.sort()

	for name in files:
		var txt := FileAccess.get_file_as_string("res://test/fixtures/" + name)
		var fx = JSON.parse_string(txt)
		if fx == null:
			print("FIXTURE_JSON ", JSON.stringify({"test": name, "passed": false, "mismatches": ["JSON 파싱 실패"]}))
			failures += 1
			total += 1
			continue
		_check_fixture(fx)

	print("FIXTURE_RESULT total=%d failures=%d" % [total, failures])
	quit(0 if failures == 0 else 1)
	return true
