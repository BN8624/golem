# 미션 선택, 브리핑, 전투 플레이 및 결과를 관리하는 메인 보드 스크립트
extends Node2D

var state = {}
var selected_unit_id = null
var screen = "MENU"
var pending_idx = 0
var current_mission_idx = 0
var rules = null
var levels = []
var font = null
var tex_floor
var tex_knight
var tex_mage
var tex_goblin

func _ready():
	rules = load("res://scripts/rules.gd").new()
	font = ThemeDB.get_fallback_font()
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	tex_floor = load("res://assets/tinydungeon/Tiles/tile_0048.png")
	tex_knight = load("res://assets/tinydungeon/Tiles/tile_0096.png")
	tex_mage = load("res://assets/tinydungeon/Tiles/tile_0084.png")
	tex_goblin = load("res://assets/tinydungeon/Tiles/tile_0108.png")

	var file = FileAccess.open("res://data/squad_levels.json", FileAccess.READ)
	if file:
		var json_text = file.get_as_text()
		levels = JSON.parse_string(json_text)

	screen = "MENU"
	queue_redraw()

func load_mission(idx: int) -> void:
	current_mission_idx = idx
	var level_data = levels[idx]
	var initial_state = level_data["initialState"]

	# Deep clone
	state = JSON.parse_string(JSON.stringify(initial_state))
	state["turn"] = 0
	state["status"] = "PLAYING"

	selected_unit_id = null
	screen = "PLAYING"
	queue_redraw()

func _unhandled_input(event):
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		var mouse_pos = event.position

		if screen == "MENU":
			for i in range(levels.size()):
				var rect = Rect2(50, 100 + i * 80, 540, 60)
				if rect.has_point(mouse_pos):
					pending_idx = i
					screen = "BRIEFING"
					queue_redraw()
					return

		elif screen == "BRIEFING":
			load_mission(pending_idx)
			return

		elif screen == "PLAYING":
			var grid_size = state.get("gridSize", 0)
			var cell_size = 640.0 / grid_size
			var gx = int(mouse_pos.x / cell_size)
			var gy = int(mouse_pos.y / cell_size)

			if gx >= 0 and gx < grid_size and gy >= 0 and gy < grid_size:
				_handle_grid_click(gx, gy)
			return

		elif screen == "RESULT":
			if state.status == "VICTORY":
				var next_rect = Rect2(220, 400, 200, 50)
				if next_rect.has_point(mouse_pos):
					if current_mission_idx < levels.size() - 1:
						pending_idx = current_mission_idx + 1
						screen = "BRIEFING"
					else:
						screen = "MENU"
					queue_redraw()
					return
			else:
				var retry_rect = Rect2(150, 400, 140, 50)
				var menu_rect = Rect2(350, 400, 140, 50)
				if retry_rect.has_point(mouse_pos):
					load_mission(current_mission_idx)
					return
				if menu_rect.has_point(mouse_pos):
					screen = "MENU"
					queue_redraw()
					return

	elif event is InputEventKey and event.pressed:
		if screen == "PLAYING":
			if event.keycode == KEY_R:
				load_mission(current_mission_idx)
			elif event.keycode == KEY_N:
				screen = "MENU"
			queue_redraw()
		elif screen == "BRIEFING":
			if event.keycode == KEY_ENTER or event.keycode == KEY_SPACE:
				load_mission(pending_idx)

func _handle_grid_click(gx: int, gy: int):
	# 1. Select Ally
	var clicked_ally = null
	for a in state["allies"]:
		if a["hp"] > 0 and a["pos"][0] == gx and a["pos"][1] == gy:
			clicked_ally = a
			break

	if clicked_ally:
		selected_unit_id = clicked_ally["id"]
		queue_redraw()
		return

	# 2. Action with selected ally
	if selected_unit_id != null:
		var ally = null
		for a in state["allies"]:
			if a["id"] == selected_unit_id:
				ally = a
				break

		if not ally or ally["hp"] <= 0:
			selected_unit_id = null
			queue_redraw()
			return

		# Move check (Manhattan 1, empty)
		var dx = gx - int(ally["pos"][0])
		var dy = gy - int(ally["pos"][1])
		var dist = abs(dx) + abs(dy)

		if dist == 1:
			var occupied = false
			for u in state["allies"] + state["enemies"]:
				if u["hp"] > 0 and u["pos"][0] == gx and u["pos"][1] == gy:
					occupied = true
					break

			if not occupied:
				var action = {"unit": selected_unit_id, "type": "move", "dir": [dx, dy]}
				_execute_action(action)
				return

		# Attack check
		var enemy_here = null
		for e in state["enemies"]:
			if e["hp"] > 0 and e["pos"][0] == gx and e["pos"][1] == gy:
				enemy_here = e
				break

		if enemy_here:
			var range_val = ally.get("range", 1)
			if dist <= range_val and dist >= 1:
				var action = {"unit": selected_unit_id, "type": "attack"}
				_execute_action(action)
				return

	selected_unit_id = null
	queue_redraw()

func _execute_action(action):
	var status = rules.update_state(state, action)
	state["status"] = status
	if status == "VICTORY" or status == "DEFEAT":
		screen = "RESULT"
	queue_redraw()

func _draw():
	if screen == "MENU":
		_draw_menu()
	elif screen == "BRIEFING":
		_draw_briefing()
	elif screen == "PLAYING":
		_draw_playing()
	elif screen == "RESULT":
		_draw_result()

func _draw_menu():
	draw_rect(Rect2(0, 0, 640, 640), Color(0.12, 0.1, 0.14))
	draw_string(font, Vector2(50, 64), "전술 미션 선택", HORIZONTAL_ALIGNMENT_LEFT, -1, 28, Color.WHITE)
	for i in range(levels.size()):
		var rect = Rect2(50, 100 + i * 80, 540, 60)
		draw_rect(rect, Color(0.2, 0.2, 0.24))
		draw_rect(rect, Color(0.6, 0.6, 0.7), false, 2.0)
		draw_string(font, Vector2(64, 128 + i * 80), str(levels[i]["name"]), HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Color.WHITE)
		draw_string(font, Vector2(64, 150 + i * 80), str(levels[i]["desc"]), HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Color.LIGHT_GRAY)

func _draw_briefing():
	draw_rect(Rect2(0, 0, 640, 640), Color(0.08, 0.07, 0.1))
	var rect = Rect2(50, 120, 540, 320)
	draw_rect(rect, Color(0, 0, 0, 0.7))
	draw_rect(rect, Color(0.6, 0.6, 0.7), false, 2.0)
	draw_string(font, Vector2(70, 108), str(levels[pending_idx]["name"]), HORIZONTAL_ALIGNMENT_LEFT, -1, 20, Color.YELLOW)
	_draw_wrapped(str(levels[pending_idx]["story"]["briefing"]), Vector2(72, 168), 496, 18, Color.WHITE)
	draw_string(font, Vector2(250, 412), "탭하여 시작", HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Color.YELLOW)

func _draw_playing():
	var grid_size = state.get("gridSize", 0)
	var cell_size = 640.0 / grid_size

	# 바닥 타일
	for x in range(grid_size):
		for y in range(grid_size):
			draw_texture_rect(tex_floor, Rect2(x * cell_size, y * cell_size, cell_size, cell_size), false)
	# 격자선(옅게)
	for i in range(grid_size + 1):
		draw_line(Vector2(i * cell_size, 0), Vector2(i * cell_size, grid_size * cell_size), Color(0, 0, 0, 0.2))
		draw_line(Vector2(0, i * cell_size), Vector2(grid_size * cell_size, i * cell_size), Color(0, 0, 0, 0.2))

	# 유닛
	for u in state["allies"]:
		_draw_unit(u, cell_size, true)
	for e in state["enemies"]:
		_draw_unit(e, cell_size, false)

	# 헤더 바
	draw_rect(Rect2(0, 0, 640, 26), Color(0, 0, 0, 0.55))
	var header = "%s   턴 %d" % [str(levels[current_mission_idx]["name"]), int(state["turn"])]
	draw_string(font, Vector2(10, 19), header, HORIZONTAL_ALIGNMENT_LEFT, -1, 15, Color.WHITE)

func _draw_unit(u, cell_size, is_ally):
	var alive = u["hp"] > 0
	var gx = u["pos"][0]
	var gy = u["pos"][1]

	if is_ally and alive and u["id"] == selected_unit_id:
		var hl = Rect2(gx * cell_size + 2, gy * cell_size + 2, cell_size - 4, cell_size - 4)
		draw_rect(hl, Color(1, 1, 0, 0.22))
		draw_rect(hl, Color.YELLOW, false, 3.0)

	var tex
	if is_ally:
		tex = tex_mage if int(u.get("range", 1)) > 1 else tex_knight
	else:
		tex = tex_goblin
	var modc = Color.WHITE if alive else Color(0.4, 0.4, 0.4, 0.5)
	var rect = Rect2(gx * cell_size + cell_size * 0.1, gy * cell_size + cell_size * 0.05, cell_size * 0.8, cell_size * 0.8)
	draw_texture_rect(tex, rect, false, modc)

	if not alive:
		draw_line(rect.position, rect.position + rect.size, Color.RED, 2)
		draw_line(rect.position + Vector2(rect.size.x, 0), rect.position + Vector2(0, rect.size.y), Color.RED, 2)
		return

	var label = "HP %d" % int(u["hp"])
	var lw = font.get_string_size(label, HORIZONTAL_ALIGNMENT_LEFT, -1, 12).x
	var lx = gx * cell_size + cell_size / 2 - lw / 2
	var ly = gy * cell_size + cell_size - 6
	draw_rect(Rect2(lx - 3, ly - 11, lw + 6, 14), Color(0, 0, 0, 0.6))
	draw_string(font, Vector2(lx, ly), label, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color.WHITE if is_ally else Color(1, 0.82, 0.82))

func _draw_result():
	_draw_playing()
	draw_rect(Rect2(0, 0, 640, 640), Color(0, 0, 0, 0.62))
	var status = state["status"]
	var title = "승리" if status == "VICTORY" else "패배"
	draw_string(font, Vector2(268, 196), title, HORIZONTAL_ALIGNMENT_LEFT, -1, 34, Color.YELLOW if status == "VICTORY" else Color(0.95, 0.4, 0.4))
	var story_text = str(levels[current_mission_idx]["story"]["victory"]) if status == "VICTORY" else str(levels[current_mission_idx]["story"]["defeat"])
	_draw_wrapped(story_text, Vector2(100, 248), 440, 18, Color.WHITE)

	if status == "VICTORY":
		var label = "다음 미션" if current_mission_idx < levels.size() - 1 else "메뉴로"
		draw_rect(Rect2(220, 400, 200, 50), Color(0.2, 0.5, 0.2))
		draw_string(font, Vector2(258, 432), label, HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Color.WHITE)
	else:
		draw_rect(Rect2(150, 400, 140, 50), Color(0.5, 0.2, 0.2))
		draw_string(font, Vector2(186, 432), "다시", HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Color.WHITE)
		draw_rect(Rect2(350, 400, 140, 50), Color(0.3, 0.3, 0.3))
		draw_string(font, Vector2(386, 432), "메뉴", HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Color.WHITE)

func _draw_wrapped(text: String, pos: Vector2, max_width: float, font_size: int, color: Color):
	var y = pos.y
	for raw in text.split("\n"):
		var line = ""
		for word in raw.split(" "):
			var test = line + (" " if line != "" else "") + word
			if font.get_string_size(test, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size).x > max_width:
				draw_string(font, Vector2(pos.x, y), line, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size, color)
				y += font_size * 1.4
				line = word
			else:
				line = test
		draw_string(font, Vector2(pos.x, y), line, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size, color)
		y += font_size * 1.4
