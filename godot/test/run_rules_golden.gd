# 골든 대조 테스트 러너(하네스) — JS 룰에서 뽑은 rules_golden.json을 GDScript 포팅(rules.gd)으로 재생해 0-diff 확인
# 실행: godot --headless --path godot --script res://test/run_rules_golden.gd
# 주의: 이건 커스텀 러너다(엔진 C++ 테스트용 --test 아님). rules.gd는 골렘이 Phase 1에서 생성.
extends SceneTree


func _initialize():
	var code := _run()
	quit(code)


func _run() -> int:
	var rules_path := "res://scripts/rules.gd"
	if not FileAccess.file_exists(rules_path):
		print("SKIP: rules.gd 미존재 — Phase 1에서 골렘이 res://scripts/rules.gd 생성해야 함")
		return 2
	var rules_script = load(rules_path)
	var rules = rules_script.new()

	var golden_text := FileAccess.get_file_as_string("res://test/rules_golden.json")
	var golden = JSON.parse_string(golden_text)
	if golden == null:
		push_error("rules_golden.json 파싱 실패")
		return 2

	var total := 0
	var failed := 0
	for c in golden:
		var state = _dup(c["initialState"])
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
				print("FAIL [%s] %s 스텝%d  status got=%s want=%s  state_match=%s" % [
					c["category"], c["name"], step_i, str(status), str(step["status"]), str(ok_state)])
			step_i += 1
	var passed := total - failed
	print("골든 대조: %d/%d 통과, %d 실패 (%d 케이스)" % [passed, total, failed, golden.size()])
	return 0 if failed == 0 else 1


func _dup(v):
	return JSON.parse_string(JSON.stringify(v))  # 순수 데이터 깊은 복제


# 숫자는 값으로 비교(JSON float vs int 차이 흡수), 컨테이너는 재귀
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
