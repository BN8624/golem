# JS↔GDScript 차등 퍼징 러너 — 시드 생성된 _fuzz_cases.json(JS 정답 trace)을 rules.gd로 재생해 0-diff 대조, 불일치 시 quit(1)
# 실행: godot --headless --path godot --script res://test/run_fuzz_diff.gd  (godot_fuzz_diff.py가 호출)
extends SceneTree


func _initialize():
	quit(_run())


func _run() -> int:
	var cases_path := "res://test/_fuzz_cases.json"
	if not FileAccess.file_exists(cases_path):
		print("SKIP: _fuzz_cases.json 미존재 — godot_fuzz_diff.py 가 먼저 생성해야 함")
		return 2
	var rules_script = load("res://scripts/rules.gd")
	var rules = rules_script.new()

	var cases = JSON.parse_string(FileAccess.get_file_as_string(cases_path))
	if cases == null:
		push_error("_fuzz_cases.json 파싱 실패")
		return 2

	var total := 0
	var failed := 0
	var first_fail := {}
	for c in cases:
		var state = JSON.parse_string(JSON.stringify(c["initialState"]))
		if not state.has("turn"):
			state["turn"] = 0
		var step_i := 0
		for step in c["steps"]:
			total += 1
			var status = rules.update_state(state, step["action"])
			var ok_status: bool = str(status) == str(step["status"])
			var ok_state: bool = _deep_equal(state, step["state_after"])
			if not (ok_status and ok_state):
				failed += 1
				if first_fail.is_empty():
					first_fail = {"case": c["name"], "step": step_i, "action": step["action"],
						"got_status": str(status), "want_status": str(step["status"]),
						"got_state": state, "want_state": step["state_after"]}
				print("FUZZ FAIL [%s] 스텝%d status got=%s want=%s state_match=%s" % [
					str(c["name"]), step_i, str(status), str(step["status"]), str(ok_state)])
			step_i += 1
	var passed := total - failed
	print("FUZZ DIFF: %d/%d 스텝 일치, %d 불일치 (%d 케이스)" % [passed, total, failed, cases.size()])
	if not first_fail.is_empty():
		# 최초 불일치 케이스를 파일로 보존(시드 재현 가능) — godot_fuzz_diff.py 가 출력
		var f = FileAccess.open("res://test/_fuzz_fail.json", FileAccess.WRITE)
		if f:
			f.store_string(JSON.stringify(first_fail, "  "))
			f.close()
	return 0 if failed == 0 else 1


func _deep_equal(a, b) -> bool:
	if a is Dictionary and b is Dictionary:
		if a.size() != b.size():
			return false
		for k in a:
			if not b.has(k):
				return false
			if not _deep_equal(a[k], b[k]):
				return false
		return true
	if a is Array and b is Array:
		if a.size() != b.size():
			return false
		for i in a.size():
			if not _deep_equal(a[i], b[i]):
				return false
		return true
	if (a is int or a is float) and (b is int or b is float):
		return float(a) == float(b)
	return a == b
