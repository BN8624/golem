# 전술 씬 컨트롤러 - 룰 모듈 연동 및 시각화
extends Node2D

var rules
var levels = []
var current_mission_idx = 0
var state = {}
var selected_unit_id = null
var ui_label = Label.new()

func _ready():
	rules = load("res://scripts/rules.gd").new()
	
	var file = FileAccess.open("res://data/squad_levels.json", FileAccess.READ)
	if file:
		var json_text = file.get_as_text()
		levels = JSON.parse_string(json_text)
	
	add_child(ui_label)
	ui_label.position = Vector2(10, 10)
	
	load_mission(0)

func load_mission(idx):
	current_mission_idx = idx
	var mission = levels[current_mission_idx]
	# Deep copy of initialState
	state = JSON.parse_string(JSON.stringify(mission["initialState"]))
	state["turn"] = 0
	state["status"] = "PLAYING"
	selected_unit_id = null
	update_ui()
	queue_redraw()

func update_ui():
	var mission = levels[current_mission_idx]
	ui_label.text = "%s · Turn: %d · %s" % [mission["name"], state["turn"], state["status"]]

func _unhandled_input(event):
	if state["status"] != "PLAYING":
		if event is InputEventKey and event.pressed:
			if event.keycode == KEY_N:
				load_mission((current_mission_idx + 1) % levels.size())
			elif event.keycode == KEY_R:
				load_mission(current_mission_idx)
		return

	if event is InputEventKey and event.pressed:
		if event.keycode == KEY_R:
			load_mission(current_mission_idx)
		elif event.keycode == KEY_N:
			load_mission((current_mission_idx + 1) % levels.size())
		return

	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and event.pressed:
		var cell_size = 640.0 / state["gridSize"]
		var gx = int(event.position.x / cell_size)
		var gy = int(event.position.y / cell_size)
		
		if gx < 0 or gx >= state["gridSize"] or gy < 0 or gy >= state["gridSize"]:
			return

		# Check if clicking an ally
		var clicked_ally = null
		for a in state["allies"]:
			if a["hp"] > 0 and a["pos"] == [gx, gy]:
				clicked_ally = a
				break
		
		if clicked_ally:
			selected_unit_id = clicked_ally["id"]
			queue_redraw()
			return

		# Action phase if ally selected
		if selected_unit_id != null:
			var ally = null
			for a in state["allies"]:
				if a["id"] == selected_unit_id:
					ally = a
					break
			
			if ally and ally["hp"] > 0:
				var dx = gx - ally["pos"][0]
				var dy = gy - ally["pos"][1]
				var dist = abs(dx) + abs(dy)
				
				# Try move to empty adjacent cell
				if dist == 1:
					var occupied = false
					for u in state["allies"] + state["enemies"]:
						if u["hp"] > 0 and u["pos"] == [gx, gy]:
							occupied = true
							break
					if not occupied:
						var res = rules.update_state(state, {"unit": selected_unit_id, "type": "move", "dir": [dx, dy]})
						state["status"] = res
						update_ui()
						queue_redraw()
						return
				
				# Try attack enemy in range
				var clicked_enemy = null
				for e in state["enemies"]:
					if e["hp"] > 0 and e["pos"] == [gx, gy]:
						clicked_enemy = e
						break
				
				if clicked_enemy:
					var range_val = ally.get("range", 1)
					if dist <= range_val and dist >= 1:
						var res = rules.update_state(state, {"unit": selected_unit_id, "type": "attack"})
						state["status"] = res
						update_ui()
						queue_redraw()
						return
			
			selected_unit_id = null
			queue_redraw()

func _draw():
	var gridSize = state["gridSize"]
	var cell_size = 640.0 / gridSize
	var font = ThemeDB.get_fallback_font()

	# Grid
	for i in range(gridSize + 1):
		draw_line(Vector2(i * cell_size, 0), Vector2(i * cell_size, 640), Color.DARK_GRAY)
		draw_line(Vector2(0, i * cell_size), Vector2(640, i * cell_size), Color.DARK_GRAY)

	var draw_unit = func(u, color):
		var pos = Vector2(u["pos"][0] * cell_size + cell_size/2, u["pos"][1] * cell_size + cell_size/2)
		var is_dead = u["hp"] <= 0
		var final_color = color if not is_dead else Color(1, 1, 1, 0.3)
		
		draw_circle(pos, cell_size * 0.35, final_color)
		
		if is_dead:
			draw_line(pos + Vector2(-10, -10), pos + Vector2(10, 10), Color.WHITE, 2)
			draw_line(pos + Vector2(10, -10), pos + Vector2(-10, 10), Color.WHITE, 2)
		
		var txt = "%s\n%d" % [u["id"], u["hp"]]
		draw_string(font, pos + Vector2(-10, 0), txt, HORIZONTAL_ALIGNMENT_CENTER, -1, 12)

	for a in state["allies"]:
		draw_unit.call(a, Color.CORNFLOWER_BLUE)
		if selected_unit_id == a["id"] and a["hp"] > 0:
			var pos = Vector2(a["pos"][0] * cell_size + cell_size/2, a["pos"][1] * cell_size + cell_size/2)
			draw_arc(pos, cell_size * 0.4, 0, TAU, 32, Color.YELLOW, 3.0)

	for e in state["enemies"]:
		draw_unit.call(e, Color.INDIAN_RED)
