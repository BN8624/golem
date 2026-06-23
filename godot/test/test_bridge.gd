# 테스트 전용 읽기전용 상태 브리지 — web export에서 ?test=1 일 때만 board 상태를 window.GOLEM_TEST로 노출(증거 수집용, board.gd·룰 미변경)
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

	# 전부 읽기 전용 — board 상태를 절대 수정하지 않는다.
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
