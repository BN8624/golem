# 미션 선택, 서사, 아이소메트릭 전투 및 자동 전투를 구현하는 보드 스크립트
extends Node2D

var rules
var levels = []
var font
var tex_knight
var tex_mage
var tex_monster

var screen = "MENU"
var state = {}
var selected_unit_id = null
var current_mission_idx = 0
var pending_idx = 0
var initial_hps = {}
var effects = []
var twins = {}

var auto_mode = true
var auto_ally_idx = 0
var auto_accum = 0.0

var TILE_W = 0.0
var TILE_H = 0.0
var origin = Vector2.ZERO
var tones = [
	Color(0.4, 0.5, 0.3), # Greenish
	Color(0.3, 0.4, 0.5), # Blueish
	Color(0.3, 0.2, 0.4), # Purplish
	Color(0.5, 0.4, 0.2)  # Golden
]

func _ready():
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	rules = load("res://scripts/rules.gd").new()
	font = load("res://assets/fonts/NanumGothic-Regular.ttf")
	
	tex_knight = load("res://assets/tinydungeon/Tiles/tile_0096.png")
	tex_mage = load("res://assets/tinydungeon/Tiles/tile_0084.png")
	tex_monster = load("res://assets/tinydungeon/Tiles/tile_0108.png")
	
	var file = FileAccess.open("res://data/squad_levels.json", FileAccess.READ)
	if file:
		levels = JSON.parse_string(file.get_as_text())
	
	queue_redraw()

func load_mission(idx):
	current_mission_idx = idx
	var init = levels[idx]["initialState"]
	state = JSON.parse_string(JSON.stringify(init))
	state["turn"] = 0
	state["status"] = "PLAYING"
	
	initial_hps = {}
	for u in state["allies"]:
		initial_hps["a" + str(u["id"])] = u["hp"]
	for u in state["enemies"]:
		initial_hps["e" + str(u["id"])] = u["hp"]
	
	selected_unit_id = null
	auto_ally_idx = 0
	auto_accum = 0.0
	twins = {}
	screen = "PLAYING"
	
	# Calculate ISO layout
	var gs = state["gridSize"]
	TILE_W = 600.0 / gs
	TILE_H = TILE_W / 2.0
	origin.x = 320.0
	origin.y = (640.0 + 40.0) / 2.0 - (gs - 1) * TILE_H / 2.0
	
	queue_redraw()

func cell_to_screen(gx: int, gy: int) -> Vector2:
	if screen != "PLAYING": return Vector2.ZERO
	var dx = gx - gy
	var dy = gx + gy
	return origin + Vector2(dx * TILE_W / 2.0, dy * TILE_H / 2.0)

func screen_to_cell(pos: Vector2) -> Vector2:
	if screen != "PLAYING": return Vector2.ZERO
	var rx = (pos.x - origin.x) / (TILE_W / 2.0)
	var ry = (pos.y - origin.y) / (TILE_H / 2.0)
	var gx = int(round((rx + ry) / 2.0))
	var gy = int(round((ry - rx) / 2.0))
	return Vector2(gx, gy)

func _unhandled_input(event):
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		var m_pos = event.position
		if screen == "MENU":
			for i in range(levels.size()):
				var rect = Rect2(220, 150 + i * 80, 200, 60)
				if rect.has_point(m_pos):
					pending_idx = i
					screen = "BRIEFING"
					queue_redraw()
					return
		elif screen == "BRIEFING":
			load_mission(pending_idx)
			queue_redraw()
		elif screen == "PLAYING":
			var cell = screen_to_cell(m_pos)
			var gx = int(cell.x)
			var gy = int(cell.y)
			handle_play_click(gx, gy)
		elif screen == "RESULT":
			# Result buttons logic
			var res_btns = []
			if state["status"] == "VICTORY":
				res_btns.append({"rect": Rect2(220, 300, 200, 50), "type": "next"})
			else:
				res_btns.append({"rect": Rect2(220, 300, 200, 50), "type": "retry"})
			res_btns.append({"rect": Rect2(220, 370, 200, 50), "type": "menu"})
			
			for btn in res_btns:
				if btn["rect"].has_point(m_pos):
					if btn["type"] == "next":
						var next_idx = (current_mission_idx + 1) % levels.size()
						pending_idx = next_idx
						screen = "BRIEFING"
					elif btn["type"] == "retry":
						load_mission(current_mission_idx)
					elif btn["type"] == "menu":
						screen = "MENU"
					queue_redraw()
					return
	elif event is InputEventKey and event.pressed:
		if event.keycode == KEY_R and screen == "PLAYING":
			load_mission(current_mission_idx)
			queue_redraw()
		elif event.keycode == KEY_N:
			screen = "MENU"
			queue_redraw()

func handle_play_click(gx, gy):
	if not (gx >= 0 and gx < state["gridSize"] and gy >= 0 and gy < state["gridSize"]): return
	
	var clicked_ally = null
	for a in state["allies"]:
		if a["hp"] > 0 and int(a["pos"][0]) == gx and int(a["pos"][1]) == gy:
			clicked_ally = a
			break
	
	if clicked_ally:
		selected_unit_id = clicked_ally["id"]
		queue_redraw()
		return
		
	if selected_unit_id != null:
		var ally = null
		for a in state["allies"]:
			if a["id"] == selected_unit_id:
				ally = a
				break
		if not ally or ally["hp"] <= 0: return
		
		var clicked_enemy = null
		for e in state["enemies"]:
			if e["hp"] > 0 and int(e["pos"][0]) == gx and int(e["pos"][1]) == gy:
				clicked_enemy = e
				break
		
		if clicked_enemy:
			var dist = abs(int(ally["pos"][0]) - gx) + abs(int(ally["pos"][1]) - gy)
			var rng = ally.get("range", 1)
			if dist >= 1 and dist <= rng:
				execute_action({"unit": ally["id"], "type": "attack"})
		else:
			var dist = abs(int(ally["pos"][0]) - gx) + abs(int(ally["pos"][1]) - gy)
			if dist == 1:
				var dx = gx - int(ally["pos"][0])
				var dy = gy - int(ally["pos"][1])
				execute_action({"unit": ally["id"], "type": "move", "dir": [dx, dy]})

func execute_action(action):
	var pre_hp = {}
	for u in state["allies"]: pre_hp["a"+str(u["id"])] = u["hp"]
	for u in state["enemies"]: pre_hp["e"+str(u["id"])] = u["hp"]
	
	var ally = null
	for a in state["allies"]:
		if a["id"] == action["unit"]:
			ally = a
			break
	
	var pre_pos = {}
	if ally: pre_pos["a"+str(ally["id"])] = Vector2(ally["pos"][0], ally["pos"][1])
	for e in state["enemies"]:
		if e["hp"] > 0: pre_pos["e"+str(e["id"])] = Vector2(e["pos"][0], e["pos"][1])

	var res = rules.update_state(state, action)
	state["status"] = res
	
	# Process FX
	if action["type"] == "attack":
		var range_val = ally.get("range", 1)
		var is_ranged = range_val > 1
		var attacker_pos = Vector2(ally["pos"][0], ally["pos"][1])
		
		for e in state["enemies"]:
			var eid = "e" + str(e["id"])
			if pre_hp.has(eid) and pre_hp[eid] > e["hp"]:
				var diff = pre_hp[eid] - e["hp"]
				var e_pos = Vector2(e["pos"][0], e["pos"][1])
				effects.append({"type": "dmg", "pos": e_pos, "val": "-%d" % int(round(diff)), "color": Color(1, 0.3, 0.3), "life": 0.6, "max_life": 0.6})
				effects.append({"type": "flash", "uid": eid, "life": 0.2, "max_life": 0.2})
				effects.append({"type": "arrow", "from_cell": [attacker_pos.x, attacker_pos.y], "to_cell": [e_pos.x, e_pos.y], "ranged": is_ranged, "life": 0.4, "max_life": 0.4})

	for u in state["allies"]:
		var uid = "a" + str(u["id"])
		if pre_hp.has(uid) and pre_hp[uid] < u["hp"]:
			var diff = u["hp"] - pre_hp[uid]
			effects.append({"type": "dmg", "pos": Vector2(u["pos"][0], u["pos"][1]), "val": "+%d" % int(round(diff)), "color": Color(0.3, 1, 0.3), "life": 0.6, "max_life": 0.6})

	# Update twins for movement
	for u in state["allies"]:
		var uid = "a" + str(u["id"])
		if pre_pos.has(uid) and pre_pos[uid] != Vector2(u["pos"][0], u["pos"][1]):
			twins[uid] = {"from": pre_pos[uid], "to": Vector2(u["pos"][0], u["pos"][1]), "life": 0.15, "max_life": 0.15}
	for u in state["enemies"]:
		var uid = "e" + str(u["id"])
		if pre_pos.has(uid) and pre_pos[uid] != Vector2(u["pos"][0], u["pos"][1]):
			twins[uid] = {"from": pre_pos[uid], "to": Vector2(u["pos"][0], u["pos"][1]), "life": 0.15, "max_life": 0.15}

	if state["status"] != "PLAYING":
		screen = "RESULT"
	
	queue_redraw()

func auto_step():
	if screen != "PLAYING": return
	
	var alive_allies = []
	for a in state["allies"]:
		if a["hp"] > 0: alive_allies.append(a)
	alive_allies.sort_custom(func(a, b): return a["id"] < b["id"])
	
	if alive_allies.size() == 0: return
	
	var u = alive_allies[auto_ally_idx % alive_allies.size()]
	auto_ally_idx += 1
	
	var range_val = u.get("range", 1)
	var closest_enemy = null
	var min_dist = 999
	
	for e in state["enemies"]:
		if e["hp"] > 0:
			var d = abs(int(u["pos"][0]) - int(e["pos"][0])) + abs(int(u["pos"][1]) - int(e["pos"][1]))
			if d < min_dist:
				min_dist = d
				closest_enemy = e
			elif d == min_dist:
				if closest_enemy == null or e["id"] < closest_enemy["id"]:
					closest_enemy = e
	
	if not closest_enemy: return
	
	if min_dist >= 1 and min_dist <= range_val:
		execute_action({"unit": u["id"], "type": "attack"})
	else:
		var ex = int(closest_enemy["pos"][0])
		var ey = int(closest_enemy["pos"][1])
		var ux = int(u["pos"][0])
		var uy = int(u["pos"][1])
		
		var best_move = null
		var moves = [[1,0], [-1,0], [0,1], [0,-1]]
		for m in moves:
			var nx = ux + m[0]
			var ny = uy + m[1]
			if nx >= 0 and nx < state["gridSize"] and ny >= 0 and ny < state["gridSize"]:
				var occ = false
				for a in state["allies"]:
					if a["hp"] > 0 and int(a["pos"][0]) == nx and int(a["pos"][1]) == ny: occ = true; break
				if not occ:
					for e in state["enemies"]:
						if e["hp"] > 0 and int(e["pos"][0]) == nx and int(e["pos"][1]) == ny: occ = true; break
				if not occ:
					var nd = abs(nx - ex) + abs(ny - ey)
					if nd < min_dist:
						best_move = m
						break
		if best_move:
			execute_action({"unit": u["id"], "type": "move", "dir": best_move})

func _process(delta):
	if screen == "PLAYING" and auto_mode:
		auto_accum += delta
		if auto_accum >= 0.6:
			auto_accum = 0.0
			auto_step()
	
	var changed = false
	for i in range(effects.size() - 1, -1, -1):
		effects[i]["life"] -= delta
		if effects[i]["life"] <= 0:
			effects.remove_at(i)
			changed = true
	
	for uid in twins.keys():
		twins[uid]["life"] -= delta
		if twins[uid]["life"] <= 0:
			twins.erase(uid)
			changed = true
			
	if changed: queue_redraw()

func _draw():
	if screen == "MENU":
		draw_string(font, Vector2(220, 100), "SQUAD TACTICS", HORIZONTAL_ALIGNMENT_LEFT, -1, 32, Color.WHITE)
		for i in range(levels.size()):
			var rect = Rect2(220, 150 + i * 80, 200, 60)
			draw_rect(rect, Color(0.2, 0.2, 0.2, 0.8), true)
			draw_string(font, rect.position + Vector2(10, 20), levels[i]["name"], HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Color.WHITE)
			draw_string(font, rect.position + Vector2(10, 40), levels[i]["desc"], HORIZONTAL_ALIGNMENT_LEFT, -1, 14, Color(0.8, 0.8, 0.8))
		
	elif screen == "BRIEFING":
		var bg = Rect2(120, 120, 400, 300)
		draw_rect(bg, Color(0, 0, 0, 0.7), true)
		var text = levels[pending_idx]["story"]["briefing"]
		var lines = text.split("\n")
		for i in range(lines.size()):
			draw_string(font, bg.position + Vector2(20, 40 + i * 25), lines[i], HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color.WHITE)
		draw_string(font, Vector2(250, 380), "Tap to Start", HORIZONTAL_ALIGNMENT_CENTER, -1, 18, Color.YELLOW)
		
	elif screen == "PLAYING":
		# HUD
		draw_rect(Rect2(0, 0, 640, 40), Color(0, 0, 0, 0.5), true)
		draw_string(font, Vector2(20, 25), "%s  |  Turn: %d" % [levels[current_mission_idx]["name"], state["turn"]], HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Color.WHITE)
		
		var gs = state["gridSize"]
		var tone_base = tones[current_mission_idx % tones.size()]
		
		# Background tiles
		for gx in range(gs):
			for gy in range(gs):
				var c = cell_to_screen(gx, gy)
				var h_var = ((gx * 7 + gy * 13) % 5) * 0.01
				var color = tone_base + Color(h_var, h_var, h_var)
				var pts = PackedVector2Array([
					c + Vector2(0, -TILE_H / 2.0),
					c + Vector2(TILE_W / 2.0, 0),
					c + Vector2(0, TILE_H / 2.0),
					c + Vector2(-TILE_W / 2.0, 0)
				])
				draw_colored_polygon(pts, color)
				draw_polyline(PackedVector2Array([pts[0], pts[1], pts[2], pts[3], pts[0]]), Color(0, 0, 0, 0.15), 1.0)

		# Highlights
		if selected_unit_id != null:
			var ally = null
			for a in state["allies"]:
				if a["id"] == selected_unit_id: ally = a; break
			if ally and ally["hp"] > 0:
				var ux = int(ally["pos"][0])
				var uy = int(ally["pos"][1])
				var c_sel = cell_to_screen(ux, uy)
				var pts_sel = PackedVector2Array([
					c_sel + Vector2(0, -TILE_H / 2.0),
					c_sel + Vector2(TILE_W / 2.0, 0),
					c_sel + Vector2(0, TILE_H / 2.0),
					c_sel + Vector2(-TILE_W / 2.0, 0)
				])
				draw_polyline(PackedVector2Array([pts_sel[0], pts_sel[1], pts_sel[2], pts_sel[3], pts_sel[0]]), Color.YELLOW, 2.0)
				
				# Reachable moves / attacks
				for gx in range(gs):
					for gy in range(gs):
						var dist = abs(ux - gx) + abs(uy - gy)
						var c_h = cell_to_screen(gx, gy)
						var pts_h = PackedVector2Array([
							c_h + Vector2(0, -TILE_H / 2.0),
							c_h + Vector2(TILE_W / 2.0, 0),
							c_h + Vector2(0, TILE_H / 2.0),
							c_h + Vector2(-TILE_W / 2.0, 0)
						])
						if dist == 1:
							var occ = false
							for a in state["allies"]:
								if a["hp"] > 0 and int(a["pos"][0]) == gx and int(a["pos"][1]) == gy: occ = true; break
							for e in state["enemies"]:
								if e["hp"] > 0 and int(e["pos"][0]) == gx and int(e["pos"][1]) == gy: occ = true; break
							if not occ:
								draw_colored_polygon(pts_h, Color(0, 1, 0, 0.3))
						elif dist >= 1 and dist <= ally.get("range", 1):
							var enemy_here = false
							for e in state["enemies"]:
								if e["hp"] > 0 and int(e["pos"][0]) == gx and int(e["pos"][1]) == gy: enemy_here = true; break
							if enemy_here:
								draw_polyline(PackedVector2Array([pts_h[0], pts_h[1], pts_h[2], pts_h[3], pts_h[0]]), Color.RED, 2.0)

		# Units (Depth Sorted)
		var all_units = []
		for a in state["allies"]: all_units.append({"u": a, "side": "a"})
		for e in state["enemies"]: all_units.append({"u": e, "side": "e"})
		all_units.sort_custom(func(a, b): 
			return (int(a["u"]["pos"][0]) + int(a["u"]["pos"][1])) < (int(b["u"]["pos"][0]) + int(b["u"]["pos"][1]))
		)
		
		for item in all_units:
			var u = item["u"]
			var side = item["side"]
			var uid = side + str(u["id"])
			var gx = int(u["pos"][0])
			var gy = int(u["pos"][1])
			var c = cell_to_screen(gx, gy)
			
			# Twin interpolation
			if twins.has(uid):
				var t_info = twins[uid]
				var alpha = 1.0 - (t_info["life"] / t_info["max_life"])
				c = t_info["from"].lerp(c, alpha)
			
			# Shadow
			var rx = TILE_W * 0.22
			var ry = TILE_H * 0.18
			var s_pts = PackedVector2Array()
			for i in range(16):
				var t_ang = TAU * i / 16.0
				s_pts.append(c + Vector2(cos(t_ang) * rx, sin(t_ang) * ry))
			draw_colored_polygon(s_pts, Color(0, 0, 0, 0.22))
			
			# Sprite
			var tex = tex_monster if side == "e" else (tex_mage if u.get("range", 1) > 1 else tex_knight)
			var w = TILE_W * 1.1
			var h = tex.get_height() * (w / tex.get_width())
			var rect = Rect2(c.x - w / 2.0, c.y - h, w, h)
			
			var mod = Color.WHITE
			if u["hp"] <= 0: mod = Color(0.4, 0.4, 0.4, 0.6)
			for fx in effects:
				if fx["type"] == "flash" and fx["uid"] == uid:
					mod = Color(1, 0.3, 0.3)
			
			draw_texture_rect(tex, rect, false, mod)
			if u["hp"] <= 0:
				draw_line(rect.position + Vector2(5, 5), rect.position + Vector2(w-5, h-5), Color.RED, 2.0)
				draw_line(rect.position + Vector2(w-5, 5), rect.position + Vector2(5, h-5), Color.RED, 2.0)
			
			# HP Bar
			var max_hp = initial_hps.get(uid, 10)
			var hp_w = 30.0
			var hp_h = 4.0
			var hp_rect = Rect2(c.x - hp_w / 2.0, c.y - h - 6, hp_w, hp_h)
			draw_rect(hp_rect, Color(0, 0, 0, 0.5), true)
			if u["hp"] > 0:
				var ratio = clamp(u["hp"] / max_hp, 0.0, 1.0)
				var color = Color.GREEN if side == "a" else Color.RED
				draw_rect(Rect2(hp_rect.position.x, hp_rect.position.y, hp_w * ratio, hp_h), color, true)
			else:
				draw_string(font, hp_rect.position + Vector2(12, -2), "X", HORIZONTAL_ALIGNMENT_LEFT, -1, 10, Color.WHITE)

		# Effects (Arrows, Dmg)
		for fx in effects:
			var alpha = clamp(fx["life"] / fx["max_life"], 0.0, 1.0)
			if fx["type"] == "arrow":
				var a = cell_to_screen(int(fx["from_cell"][0]), int(fx["from_cell"][1])) + Vector2(0, -TILE_H * 0.4)
				var b = cell_to_screen(int(fx["to_cell"][0]), int(fx["to_cell"][1])) + Vector2(0, -TILE_H * 0.4)
				if fx["ranged"]:
					var pts_arr = PackedVector2Array()
					for i in range(17):
						var t_p = i / 16.0
						pts_arr.append(a.lerp(b, t_p) + Vector2(0, -TILE_H * 1.2 * (4.0 * t_p * (1.0 - t_p))))
					draw_polyline(pts_arr, Color(0.6, 0.9, 1, alpha), 3.0)
				else:
					draw_line(a, b, Color(1, 1, 0.3, alpha), 3.0)
			elif fx["type"] == "dmg":
				var pos = cell_to_screen(int(fx["pos"][0]), int(fx["pos"][1])) + Vector2(0, -TILE_H * 1.5)
				var offset = Vector2(0, (1.0 - alpha) * 60.0)
				var final_pos = pos + offset
				# Shadow
				draw_string(font, final_pos + Vector2(1, 1), fx["val"], HORIZONTAL_ALIGNMENT_CENTER, -1, 22, Color.BLACK)
				draw_string(font, final_pos, fx["val"], HORIZONTAL_ALIGNMENT_CENTER, -1, 22, fx["color"])

	elif screen == "RESULT":
		var bg = Rect2(0, 0, 640, 640)
		draw_rect(bg, Color(0, 0, 0, 0.6), true)
		var res_text = levels[current_mission_idx]["story"]["victory"] if state["status"] == "VICTORY" else levels[current_mission_idx]["story"]["defeat"]
		var lines = res_text.split("\n")
		for i in range(lines.size()):
			draw_string(font, Vector2(220, 200 + i * 25), lines[i], HORIZONTAL_ALIGNMENT_CENTER, -1, 18, Color.WHITE)
		
		if state["status"] == "VICTORY":
			draw_rect(Rect2(220, 300, 200, 50), Color(0.2, 0.5, 0.2), true)
			draw_string(font, Vector2(320, 330), "Next Mission", HORIZONTAL_ALIGNMENT_CENTER, -1, 18, Color.WHITE)
		else:
			draw_rect(Rect2(220, 300, 200, 50), Color(0.5, 0.2, 0.2), true)
			draw_string(font, Vector2(320, 330), "Retry", HORIZONTAL_ALIGNMENT_CENTER, -1, 18, Color.WHITE)
		
		draw_rect(Rect2(220, 370, 200, 50), Color(0.3, 0.3, 0.3), true)
		draw_string(font, Vector2(320, 400), "Menu", HORIZONTAL_ALIGNMENT_CENTER, -1, 18, Color.WHITE)
