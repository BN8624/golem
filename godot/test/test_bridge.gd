# 테스트 전용 상태 브리지 — web export ?test=1 에서만 board 상태를 window.GOLEM_TEST로 노출(증거 수집) + window.GOLEM_NAV로 화면 직접 전환(시각 게이트가 메뉴 버튼 좌표에 결합 안 되게). board.gd·룰 미변경
extends Node

var _enabled := false
var _checked := false
var _last := ""


func _ready() -> void:
	# web 외(헤드리스 프로브·데스크톱)에선 process 자체를 끈다 → 프로덕션·골든·프로브에 0 영향.
	# 헤드리스 프로브는 extends SceneTree라 autoload를 아예 로드하지 않으므로 이중 안전.
	set_process(OS.has_feature("web"))


func _process(_d) -> void:
	if not _checked:
		_checked = true
		var search = str(JavaScriptBridge.eval("window.location.search", true))
		_enabled = search.find("test=1") != -1
	if not _enabled:
		return

	var board = get_tree().current_scene
	if board == null:
		return

	# 테스트 전용 화면 네비게이션 — 게이트가 메뉴/카드 버튼 픽셀 좌표(골렘 자유)에 결합되지 않게 화면을 직접 띄운다.
	# 형식: window.GOLEM_NAV = "BRIEFING" / "SQUAD_SELECT" / "PLAY". 적용 후 비운다.
	#   BRIEFING·SQUAD_SELECT: 미션0 화면을 직접 세팅(렌더 검증용). PLAY: load_mission(0) 계약 경로로 곧장 PLAYING(자동전투 검증용, 계약 불변).
	var nav = str(JavaScriptBridge.eval("window.GOLEM_NAV || ''", true))
	if nav != "":
		JavaScriptBridge.eval("window.GOLEM_NAV = '';", true)
		if nav == "PLAY":
			board.load_mission(0)
		elif nav == "BRIEFING" or nav == "SQUAD_SELECT":
			board.set("pending_idx", 0)
			if nav == "SQUAD_SELECT":
				board.set("picked_ids", [])
			board.set("screen", nav)
			board.queue_redraw()

	# 아래는 전부 읽기 전용 — board 상태를 수정하지 않는다.
	var payload := {}
	payload["screen"] = board.get("screen")
	payload["selectedUnitId"] = board.get("selected_unit_id")
	payload["mission"] = board.get("current_mission_idx")
	var st = board.get("state")
	if st is Dictionary:
		payload["turn"] = st.get("turn", null)
		payload["status"] = st.get("status", null)
		payload["allies"] = st.get("allies", [])
		payload["enemies"] = st.get("enemies", [])

	var js := JSON.stringify(payload)
	if js == _last:
		return
	_last = js
	JavaScriptBridge.eval("window.GOLEM_TEST = " + js + ";", true)
