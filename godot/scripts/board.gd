# 미션 선택, 서사, 아이소메트릭 전투를 처리하는 보드 스크립트
extends Node2D

var rules
var levels = []
var font
var tex_knight
var tex_mage
var tex_monster

var state = {}
var screen = "MENU"
var current_mission_idx = 0
var pending_idx = 0
var selected_unit_id = null

var auto_mode = true
var auto_ally_idx = 0
var auto_accum = 0.0

var max_hps = {}
var unit_visual_pos = {}
var effects = []

var tones = [
	Color(0.6, 0.6, 0.6), 
	Color(0.5, 0.6, 0.7), 
	Color(0.5, 0.4, 0.6), 
	Color(0.7, 0.7, 0.5)
]

func _ready():
	rules = load("res://scripts/rules.gd").new()
	var file = FileAccess.open("res://data/squad_levels.json", FileAccess.READ)
	if file:
		levels = JSON.parse_string(file.get_as_text())
	
	font = load("res://assets/fonts/NanumGothic-Regular.ttf")
	tex_knight = load("res://assets/tinydungeon/Tiles/tile_0096.png")
	tex_mage = load("res://assets/tinydungeon/Tiles/tile_0084.png")
	tex_monster = load("res://assets/tinydungeon/Tiles/tile_0108.png")
	
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST

func load_mission(idx: int) -> void:
	current_mission_idx = idx
	var init = levels[idx]["initialState"]
	state = JSON.parse_string(JSON.stringify(init))
	state["turn"] = 0
	state["status"] = "PLAYING"
	
	selected_unit_id = null
	auto_ally_idx = 0
	auto_accum = 0.0
	max_hps.clear()
	unit_visual_pos.clear()
	effects.clear()
	
	for u in state["allies"]:
		max_hps["a" + str(u["id"])] = u["hp"]
	for u in state["enemies"]:
		max_hps["e" + str(u["id"])] = u["hp"]
	
	screen = "PLAYING"
	queue_redraw()

func cell_to_screen(gx: int, gy: int) -> Vector2:
	if screen != "PLAYING" or state.is_empty():
		return Vector2.ZERO
	
	var tw = 600.0 / state["gridSize"]
	var th = tw / 2.0
	var ox = 320.0
	var oy = (640.0 + 40.0) / 2.0 - (state["gridSize"] - 1) * th / 2.0
	
	return Vector2(ox + (gx - gy) * tw / 2.0, oy + (gx + gy) * th / 2.0)

func screen_to_cell(pos: Vector2) -> Vector2:
	if screen != "PLAYING" or state.is_empty():
		return Vector2.ZERO
	
	var tw = 600.0 / state["gridSize"]
	var th = tw / 2.0
	var ox = 320.0
	var oy = (640.0 + 40.0) / 2.0 - (state["gridSize"] - 1) * th / 2.0
	
	var rx = (pos.x - ox) / (tw / 2.0)
	var ry = (pos.y - oy) / (th / 2.0)
	
	var gx = int(round((rx + ry) / 2.0))
	var gy = int(round((ry - rx) / 2.0))
	return Vector2(gx, gy)

func _process(delta):
	if screen != "PLAYING":
		return
	
	# Update effects
	var i = effects.size() - 1
	while i >= 0:
		effects[i]["life"] -= delta
		if effects[i]["life"] <= 0:
			effects.remove_at(i)
		i -= 1
	
	# Update visual positions (twins)
	for uid in state["allies"]:
		var key = "a" + str(uid["id"])
		var target_pos = cell_to_screen(int(uid["pos"][0]), int(uid["pos"][1]))
		if not unit_visual_pos.has(key):
			unit_visual_pos[key] = target_pos
		unit_visual_pos[key] = unit_visual_pos[key].lerp(target_pos, 0.2)
		
	for uid in state["enemies"]:
		var key = "e" + str(uid["id"])
		var target_pos = cell_to_screen(int(uid["pos"][0]), int(uid["pos"][1]))
		if not unit_visual_pos.has(key):
			unit_visual_pos[key] = target_pos
		unit_visual_pos[key] = unit_visual_pos[key].lerp(target_pos, 0.2)
	
	if auto_mode:
		auto_accum += delta
		if auto_accum >= 0.6:
			auto_accum = 0.0
			auto_step()
	
	queue_redraw()

func execute_action(action: Dictionary):
	var hp_snapshot = {}
	for u in state["allies"]: hp_snapshot["a" + str(u["id"])] = u["hp"]
	for u in state["enemies"]: hp_snapshot["e" + str(u["id"])] = u["hp"]
	
	var attacker_id = action["unit"]
	var range_val = 1
	for a in state["allies"]:
		if a["id"] == attacker_id:
			range_val = a.get("range", 1)
			break
			
	state["status"] = rules.update_state(state, action)
	
	# Effects: Damage, Flash, Arrows
	for u in state["enemies"]:
		var key = "e" + str(u["id"])
		var diff = hp_snapshot.get(key, u["hp"]) - u["hp"]
		if diff > 0:
			var c = cell_to_screen(int(u["pos"][0]), int(u["pos"][1]))
			effects.append({"type": "text", "pos": c, "text": "-" + str(int(round(diff))), "color": Color(1, 0.3, 0.3), "life": 0.6, "max_life": 0.6})
			effects.append({"type": "flash", "id": key, "life": 0.2})
			if action["type"] == "attack":
				var attacker = null
				for a in state["allies"]:
					if a["id"] == attacker_id: attacker = a; break
				if attacker:
					effects.append({
						"type": "arrow", 
						"from_cell": attacker["pos"], 
						"to_cell": u["pos"], 
						"ranged": range_val > 1, 
						"life": 0.4, 
						"max_life": 0.4
					})
					
	for u in state["allies"]:
		var key = "a" + str(u["id"])
		var diff = hp_snapshot.get(key, u["hp"]) - u["hp"]
		if diff > 0:
			var c = cell_to_screen(int(u["pos"][0]), int(u["pos"][1]))
			effects.append({"type": "text", "pos": c, "text": "-" + str(int(round(diff))), "color": Color(1, 0.3, 0.3), "life": 0.6, "max_life": 0.6})
			effects.append({"type": "flash", "id": key, "life": 0.2})
			
	if state["status"] != "PLAYING":
		screen = "RESULT"

func auto_step() -> void:
	if screen != "PLAYING": return
	
	var living_allies = []
	for a in state["allies"]:
		if a["hp"] > 0: living_allies.append(a)
	living_allies.sort_custom(func(a, b): return a["id"] < b["id"])
	
	if living_allies.size() == 0:
		screen = "RESULT"
		return
		
	var u = living_allies[auto_ally_idx % living_allies.size()]
	auto_ally_idx += 1
	
	# Greedy Policy
	var u_range = u.get("range", 1)
	var closest_enemy = null
	var min_dist = 999
	
	for e in state["enemies"]:
		if e["hp"] <= 0: continue
		var d = abs(u["pos"][0] - e["pos"][0]) + abs(u["pos"][1] - e["pos"][1])
		if d < min_dist:
			min_dist = d
			closest_enemy = e
		elif d == min_dist:
			if closest_enemy == null or e["id"] < closest_enemy["id"]:
				closest_enemy = e
				
	if closest_enemy == null: return
	
	if min_dist <= u_range and min_dist >= 1:
		execute_action({"unit": u["id"], "type": "attack"})
	else:
		var dir = [0, 0]
		var dx = closest_enemy["pos"][0] - u["pos"][0]
		var dy = closest_enemy["pos"][1] - u["pos"][1]
		
		# Prioritize axis reducing distance
		var tried_dirs = []
		if dx > 0: tried_dirs.append([1, 0])
		elif dx < 0: tried_dirs.append([-1, 0])
		if dy > 0: tried_dirs.append([0, 1])
		elif dy < 0: tried_dirs.append([0, -1])
		
		var moved = false
		for d_vec in tried_dirs:
			var nx = u["pos"][0] + d_vec[0]
			var ny = u["pos"][1] + d_vec[1]
			if nx >= 0 and nx < state["gridSize"] and ny >= 0 and ny < state["gridSize"]:
				var occupied = false
				for a in state["allies"]:
					if a["hp"] > 0 and a["pos"][0] == nx and a["pos"][1] == ny: occupied = true; break
				for e in state["enemies"]:
					if e["hp"] > 0 and e["pos"][0] == nx and e["pos"][1] == ny: occupied = true; break
				if not occupied:
					dir = d_vec
					moved = true
					break
		
		if moved:
			execute_action({"unit": u["id"], "type": "move", "dir": dir})

func _unhandled_input(event):
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		var m_pos = event.position
		if screen == "MENU":
			for i in range(levels.size()):
				var rect = Rect2(220, 150 + i * 80, 200, 60)
				if rect.has_point(m_pos):
					pending_idx = i
					screen = "BRIEFING"
		elif screen == "BRIEFING":
			load_mission(pending_idx)
		elif screen == "PLAYING":
			var cell = screen_to_cell(m_pos)
			var gx = int(cell.x)
			var gy = int(cell.y)
			if gx < 0 or gx >= state["gridSize"] or gy < 0 or gy >= state["gridSize"]: return
			
			var clicked_ally = null
			for a in state["allies"]:
				if a["hp"] > 0 and int(a["pos"][0]) == gx and int(a["pos"][1]) == gy:
					clicked_ally = a
					break
			
			if clicked_ally:
				selected_unit_id = clicked_ally["id"]
			elif selected_unit_id != null:
				var actor = null
				for a in state["allies"]:
					if a["id"] == selected_unit_id: actor = a; break
				
				var clicked_enemy = null
				for e in state["enemies"]:
					if e["hp"] > 0 and int(e["pos"][0]) == gx and int(e["pos"][1]) == gy:
						clicked_enemy = e
						break
				
				if clicked_enemy:
					var dist = abs(actor["pos"][0] - gx) + abs(actor["pos"][1] - gy)
					if dist >= 1 and dist <= actor.get("range", 1):
						execute_action({"unit": actor["id"], "type": "attack"})
				else:
					var dist = abs(actor["pos"][0] - gx) + abs(actor["pos"][1] - gy)
					if dist == 1:
						var dx = gx - actor["pos"][0]
						var dy = gy - actor["pos"][1]
						execute_action({"unit": actor["id"], "type": "move", "dir": [dx, dy]})
		elif screen == "RESULT":
			if state["status"] == "VICTORY":
				var next_idx = (current_mission_idx + 1) % levels.size()
				if next_idx == 0: screen = "MENU"
				else: pending_idx = next_idx; screen = "BRIEFING"
			else:
				load_mission(current_mission_idx)
	
	if event is InputEventKey and event.pressed:
		if event.keycode == KEY_R and screen == "PLAYING": load_mission(current_mission_idx)
		if event.keycode == KEY_N: screen = "MENU"

func _draw():
	if screen == "MENU":
		draw_string(font, Vector2(220, 80), "SQUAD TACTICS", HORIZONTAL_ALIGNMENT_LEFT, -1, 32, Color.WHITE)
		for i in range(levels.size()):
			var rect = Rect2(220, 150 + i * 80, 200, 60)
			draw_rect(rect, Color(0.2, 0.2, 0.2, 0.8), true)
			draw_string(font, rect.position + Vector2(10, 25), levels[i]["name"], HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Color.WHITE)
			draw_string(font, rect.position + Vector2(10, 45), levels[i]["desc"], HORIZONTAL_ALIGNMENT_LEFT, -1, 14, Color.LIGHT_GRAY)
	
	elif screen == "BRIEFING":
		draw_rect(Rect2(120, 120, 400, 300), Color(0, 0, 0, 0.7), true)
		var story = levels[pending_idx]["story"]["briefing"]
		var lines = story.split("\n")
		for i in range(lines.size()):
			draw_string(font, Vector2(140, 160 + i * 30), lines[i], HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Color.WHITE)
		draw_string(font, Vector2(260, 380), "Tap to Start", HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color.YELLOW)
		
	elif screen == "PLAYING":
		var gs = state["gridSize"]
		var tw = 600.0 / gs
		var th = tw / 2.0
		var tone_base = tones[current_mission_idx % tones.size()]
		
		# Floor
		for gx in range(gs):
			for gy in range(gs):
				var c = cell_to_screen(gx, gy)
				var top = c + Vector2(0, -th / 2.0)
				var right = c + Vector2(tw / 2.0, 0)
				var bottom = c + Vector2(0, th / 2.0)
				var left = c + Vector2(-tw / 2.0, 0)
				
				var var_color = tone_base
				var v = (gx * 7 + gy * 13) % 5 * 0.02 - 0.02
				var_color = Color(var_color.r + v, var_color.g + v, var_color.b + v)
				
				var pts = PackedVector2Array([top, right, bottom, left])
				draw_colored_polygon(pts, var_color)
				
				var border_pts = PackedVector2Array([top, right, bottom, left, top])
				draw_polyline(border_pts, Color(0, 0, 0, 0.15), 1.0)
				
		# Range Fill
		if selected_unit_id != null:
			var actor = null
			for a in state["allies"]:
				if a["id"] == selected_unit_id: actor = a; break
			if actor:
				var r_val = actor.get("range", 1)
				for gx in range(gs):
					for gy in range(gs):
						var d = abs(actor["pos"][0] - gx) + abs(actor["pos"][1] - gy)
						if d >= 1 and d <= r_val:
							var c = cell_to_screen(gx, gy)
							var pts = PackedVector2Array([c + Vector2(0, -th/2), c + Vector2(tw/2, 0), c + Vector2(0, th/2), c + Vector2(-tw/2, 0)])
							draw_colored_polygon(pts, Color(1, 0.3, 0.3, 0.12))
				
				# Movement Green
				for gx in range(gs):
					for gy in range(gs):
						var d = abs(actor["pos"][0] - gx) + abs(actor["pos"][1] - gy)
						if d == 1:
							var occ = false
							for u in state["allies"]:
								if u["hp"] > 0 and int(u["pos"][0]) == gx and int(u["pos"][1]) == gy: occ = true; break
							for u in state["enemies"]:
								if u["hp"] > 0 and int(u["pos"][0]) == gx and int(u["pos"][1]) == gy: occ = true; break
							if not occ:
								var c = cell_to_screen(gx, gy)
								var pts = PackedVector2Array([c + Vector2(0, -th/2), c + Vector2(tw/2, 0), c + Vector2(0, th/2), c + Vector2(-tw/2, 0)])
								draw_colored_polygon(pts, Color(0, 1, 0, 0.2))

		# Units Depth Sorted
		var all_units = []
		for a in state["allies"]: all_units.append({"u": a, "side": "a"})
		for e in state["enemies"]: all_units.append({"u": e, "side": "e"})
		all_units.sort_custom(func(a, b): return (int(a["u"]["pos"][0]) + int(a["u"]["pos"][1])) < (int(b["u"]["pos"][0]) + int(b["u"]["pos"][1])))
		
		for item in all_units:
			var u = item["u"]
			var side = item["side"]
			var uid = u["id"]
			var key = side + str(uid)
			var c = unit_visual_pos.get(key, cell_to_screen(int(u["pos"][0]), int(u["pos"][1])))
			
			# Shadow
			var rx = tw * 0.22
			var ry = th * 0.18
			var s_pts = PackedVector2Array()
			for i in range(16):
				var t = TAU * i / 16.0
				s_pts.append(c + Vector2(cos(t) * rx, sin(t) * ry))
			draw_colored_polygon(s_pts, Color(0, 0, 0, 0.22))
			
			# Sprite
			var tex = tex_monster
			if side == "a":
				tex = tex_mage if u.get("range", 1) > 1 else tex_knight
			
			var w = tw * 1.1
			var h = tex.get_height() * (w / tex.get_width())
			var rect = Rect2(c.x - w / 2.0, c.y - h, w, h)
			var mod = Color.WHITE
			if u["hp"] <= 0: mod = Color(0.5, 0.5, 0.5, 0.6)
			
			for fx in effects:
				if fx["type"] == "flash" and fx["id"] == key: mod = Color(1, 0.5, 0.5)
				
			draw_texture_rect(tex, rect, false, mod)
			
			# HP Bar
			var max_hp = max_hps.get(key, 10)
			var hp_per = float(u["hp"]) / max_hp
			var bar_w = w * 0.6
			var bar_h = 4.0
			var bar_pos = Vector2(c.x - bar_w / 2.0, rect.position.y - 8.0)
			draw_rect(Rect2(bar_pos, Vector2(bar_w, bar_h)), Color(0, 0, 0, 0.5), true)
			var bar_col = Color.GREEN if side == "a" else Color.RED
			draw_rect(Rect2(bar_pos, Vector2(bar_w * max(0, hp_per), bar_h)), bar_col, true)
			if u["hp"] <= 0:
				draw_string(font, bar_pos + Vector2(bar_w/2 - 4, 10), "X", HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color.WHITE)
			
			# Selection Border
			if side == "a" and selected_unit_id == uid:
				var top = c + Vector2(0, -th/2); var right = c + Vector2(tw/2, 0); var bottom = c + Vector2(0, th/2); var left = c + Vector2(-tw/2, 0)
				draw_polyline(PackedVector2Array([top, right, bottom, left, top]), Color.YELLOW, 2.0)
			elif side == "e" and selected_unit_id != null:
				var actor = null
				for a in state["allies"]: if a["id"] == selected_unit_id: actor = a; break
				if actor:
					var d = abs(actor["pos"][0] - int(u["pos"][0])) + abs(actor["pos"][1] - int(u["pos"][1]))
					if d >= 1 and d <= actor.get("range", 1):
						var top = c + Vector2(0, -th/2); var right = c + Vector2(tw/2, 0); var bottom = c + Vector2(0, th/2); var left = c + Vector2(-tw/2, 0)
						draw_polyline(PackedVector2Array([top, right, bottom, left, top]), Color.RED, 2.0)

		# Arrows
		for fx in effects:
			if fx["type"] == "arrow":
				var a = cell_to_screen(int(fx["from_cell"][0]), int(fx["from_cell"][1])) + Vector2(0, -th * 0.4)
				var b = cell_to_screen(int(fx["to_cell"][0]), int(fx["to_cell"][1])) + Vector2(0, -th * 0.4)
				var alpha = clamp(fx["life"] / fx["max_life"], 0.0, 1.0)
				if not fx["ranged"]:
					draw_line(a, b, Color(1, 1, 0.3, alpha), 3.0)
				else:
					var pts = PackedVector2Array()
					for i in range(17):
						var t = i / 16.0
						pts.append(a.lerp(b, t) + Vector2(0, -th * 1.2 * (4.0 * t * (1.0 - t))))
					draw_polyline(pts, Color(0.6, 0.9, 1, alpha), 3.0)
				var dir = (b - a).normalized()
				var p1 = b - dir * 0.2 * Vector2(dir.y, -dir.x)
				var p2 = b - dir * 0.2 * Vector2(-dir.y, dir.x)
				draw_line(b, p1, Color(1, 1, 0.3, alpha), 2.0)
				draw_line(b, p2, Color(1, 1, 0.3, alpha), 2.0)
				
		# Floating Text
		for fx in effects:
			if fx["type"] == "text":
				var alpha = clamp(fx["life"] / fx["max_life"], 0.0, 1.0)
				var offset = Vector2(0, - (1.0 - alpha) * 60.0)
				var p = fx["pos"] + offset
				draw_string(font, p + Vector2(-1, -1), fx["text"], HORIZONTAL_ALIGNMENT_LEFT, -1, 22, Color(0,0,0,alpha))
				draw_string(font, p, fx["text"], HORIZONTAL_ALIGNMENT_LEFT, -1, 22, Color(fx["color"].r, fx["color"].g, fx["color"].b, alpha))

		# HUD
		draw_rect(Rect2(0, 0, 640, 36), Color(0, 0, 0, 0.5), true)
		var title = levels[current_mission_idx]["name"] + "  |  Turn: " + str(state["turn"])
		draw_string(font, Vector2(20, 10), title, HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Color.WHITE)
		
	elif screen == "RESULT":
		draw_rect(Rect2(0, 0, 640, 640), Color(0, 0, 0, 0.6), true)
		var story = levels[current_mission_idx]["story"]
		var text = story["victory"] if state["status"] == "VICTORY" else story["defeat"]
		var lines = text.split("\n")
		for i in range(lines.size()):
			draw_string(font, Vector2(220, 200 + i * 30), lines[i], HORIZONTAL_ALIGNMENT_LEFT, -1, 20, Color.WHITE)
		
		var btn_rect = Rect2(270, 400, 100, 50)
		draw_rect(btn_rect, Color(0.3, 0.3, 0.3, 1), true)
		var btn_text = "Next" if state["status"] == "VICTORY" else "Retry"
		draw_string(font, btn_rect.position + Vector2(20, 20), btn_text, HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Color.WHITE)
		
		var menu_rect = Rect2(270, 460, 100, 50)
		draw_rect(menu_rect, Color(0.3, 0.3, 0.3, 1), true)
		draw_string(font, menu_rect.position + Vector2(20, 20), "Menu", HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Color.WHITE)
		
		# RESULT input handles are part of _unhandled_input logic now.
