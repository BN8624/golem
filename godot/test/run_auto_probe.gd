# 자동 전투 검증 — auto_step()을 반복 호출해 결정적 종료(VICTORY/DEFEAT) + 2회 재현 일치 확인(헤드리스)
extends SceneTree

var board
var done = false

func _initialize():
	board = load("res://scenes/main.tscn").instantiate()
	get_root().add_child(board)

func _play_once() -> Dictionary:
	# 미션0을 자동으로 끝까지 — auto_step 반복(타이머 무관). 최대 200틱 안전망.
	board.load_mission(0)
	var steps = 0
	while board.screen == "PLAYING" and steps < 200:
		board.auto_step()
		steps += 1
	return {"screen": board.screen, "status": board.state.get("status", "?"), "turn": board.state.get("turn", -1), "steps": steps}

func _process(_d):
	if done:
		return true
	done = true

	var r1 = _play_once()
	var r2 = _play_once()
	print("PROBE AUTO run1=", r1)
	print("PROBE AUTO run2=", r2)

	var terminal = r1["screen"] == "RESULT" and (r1["status"] == "VICTORY" or r1["status"] == "DEFEAT")
	var deterministic = r1["status"] == r2["status"] and r1["turn"] == r2["turn"] and r1["steps"] == r2["steps"]

	if terminal and deterministic:
		print("PROBE AUTO RESULT: 자동 전투 동작함")
	elif not terminal:
		print("PROBE AUTO RESULT: 종료 안 함 — auto_step/그리디 정책 문제(PLAYING에서 안 끝남)")
	else:
		print("PROBE AUTO RESULT: 비결정적 — 2회 결과 불일치(RNG/시간의존 의심)")
	quit()
	return true
