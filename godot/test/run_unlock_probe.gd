# 로스터 언락 검증 — 기본 해금 셋·unlock_for_mission·is_unlocked·중복방지를 헤드리스로 확인(영속은 web E2E 별도)
extends SceneTree

var board

func _initialize():
	board = load("res://scenes/main.tscn").instantiate()
	get_root().add_child(board)

func _has(uid) -> bool:
	return uid in board.unlocked_ids

func _process(_d):
	var fails = []

	# 1) 기본 해금 = unlock=="start" 인 유닛(헤드리스는 영속 안 하니 항상 기본)
	var expect_start = []
	for u in board.roster:
		if u.get("unlock", "") == "start":
			expect_start.append(u.id)
	for uid in expect_start:
		if not _has(uid):
			fails.append("기본 해금 누락: " + str(uid))
	# 잠긴 유닛은 기본에 없어야
	if _has("thorn"):
		fails.append("thorn 이 처음부터 해금됨(잘못)")

	# 2) is_unlocked 계약
	if expect_start.size() > 0 and not board.is_unlocked(expect_start[0]):
		fails.append("is_unlocked(start유닛)=false")
	if board.is_unlocked("thorn"):
		fails.append("is_unlocked(thorn) 초기 true(잘못)")

	# 3) 미션 클리어 해금
	board.unlock_for_mission("V1-E01")
	if not _has("thorn"):
		fails.append("V1-E01 클리어 후 thorn 미해금")
	if _has("vire"):
		fails.append("V1-E01 클리어로 vire 까지 해금됨(잘못)")

	# 4) 중복 방지(같은 미션 두 번 클리어해도 id 한 번만)
	board.unlock_for_mission("V1-E01")
	var thorn_count = 0
	for uid in board.unlocked_ids:
		if uid == "thorn":
			thorn_count += 1
	if thorn_count != 1:
		fails.append("thorn 중복 해금(count=" + str(thorn_count) + ")")

	print("UNLOCK_JSON ", JSON.stringify({"unlocked": board.unlocked_ids, "fails": fails}))
	if fails.is_empty():
		print("UNLOCK_RESULT 통과")
		quit(0)
	else:
		print("UNLOCK_RESULT 실패 ", fails)
		quit(1)
	return true
