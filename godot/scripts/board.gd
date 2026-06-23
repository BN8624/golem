# 미션 선택, 서사, 아이소메트릭 플레이 및 자동 전투를 제어하는 보드 스크립트
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
var pending_idx = 0
var current_mission_idx = 0

var auto_mode = true
var auto_ally_idx = 0
var auto_accum = 0.0

var TILE_W = 0.0
var TILE_H = 0.0
var origin = Vector2.ZERO

var max_hps = {} # "a1", "e1" 등 진영+id 키
var effects = [] # {type, pos, val, life, color}
var twins = {} # "a1": {start_pos, current_pos, t}
var flashes = {} # "a1": life

var tones = [
	Color(0.7, 0.7, 0.7), # 기본
	Color(0.5, 0.6, 0.7), # 청회색
	Color(0.4, 0.3, 0.5), # 보라어둠
	Color(0.8, 0.7, 0.4)  # 황금
]

func _ready():
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	rules = load("res://scripts/rules.gd").new()
	
	var file = FileAccess.open("res://data/squad_levels.json", FileAccess.READ)
	if file:
		levels = JSON.parse_string(file.get_as_text())
	
	font = load("res://assets/fonts/NanumGothic-Regular.ttf")
	tex_knight = load("res://assets/tinydungeon/Tiles/tile_0096.png")
	tex_mage = load("res://assets/tinydungeon/Tiles/tile_0084.png")
	tex_monster = load("res://assets/tinydungeon/Tiles/tile_0108.png")

func load_mission(idx):
	current_mission_idx = idx
	var initial = levels[idx]["initialState"]
	state = JSON.parse_string(JSON.stringify(initial))
	state["turn"] = 0
	state["status"] = "PLAYING"
	
	selected_unit_id = null
	screen = "PLAYING"
	
	# 표시용 스냅샷 및 리셋
	max_hps.clear()
	twins.clear()
	flashes.clear()
	effects.clear()
	auto_ally_idx = 0
	auto_accum = 0.0
	
	# max_hp 저장
	for u in state["allies"]:
		max_hps["a" + str(u["id"])] = u["hp"]
	for u in state["enemies"]:
		max_hps["e" + str(u["id"])] = u["hp"]
	
	# 보드 크기 계산
	var gs = state["gridSize"]
	TILE_W = 600.0 / gs
	TILE_H = TILE_W / 2.0
	origin.x = 320
	origin.y = (640 + 40) / 2.0 - (gs - 1) * TILE_H / 2.0
	
	queue_redraw()

func cell_to_screen(gx: int, gy: int) -> Vector2:
	var dx = (gx - gy) * TILE_W / 2.0
	var dy = (gx + gy) * TILE_H / 2.0
	return origin + Vector2(dx, dy)

func screen_to_cell(px: float, py: float) -> Vector2:
	var rx = (px - origin.x) / (TILE_W / 2.0)
	var ry = (py - origin.y) / (TILE_H / 2.0)
	var gx = round((rx + ry) / 2.0)
	var gy = round((ry - rx) / 2.0)
	return Vector2(gx, gy)

func _unhandled_input(event):
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		var mp = event.position
		if screen == "MENU":
			for i in range(levels.size()):
				var rect = Rect2(120, 150 + i * 70, 400, 50)
				if rect.has_point(mp):
					pending_idx = i
					screen = "BRIEFING"
					queue_redraw()
					return
		elif screen == "BRIEFING":
			load_mission(pending_idx)
		elif screen == "PLAYING":
			var cell = screen_to_cell(mp.x, mp.y)
			var gx = int(cell.x)
			var gy = int(cell.y)
			handle_play_click(gx, gy)
		elif screen == "RESULT":
			if mp.y > 400:
				if state["status"] == "VICTORY":
					var next_idx = current_mission_idx + 1
					if next_idx < levels.size():
						pending_idx = next_idx
						screen = "BRIEFING"
					else:
						screen = "MENU"
				else:
					load_mission(current_mission_idx)
			elif mp.y > 450: # 메뉴로
				screen = "MENU"
			queue_redraw()

func handle_play_click(gx: int, gy: int):
	if not state.has("gridSize"): return
	var gs = state["gridSize"]
	if gx < 0 or gx >= gs or gy < 0 or gy >= gs: return

	var ally_here = null
	for a in state["allies"]:
		if a["hp"] > 0 and a["pos"][0] == gx and a["pos"][1] == gy:
			ally_here = a
			break
	
	var enemy_here = null
	for e in state["enemies"]:
		if e["hp"] > 0 and e["pos"][0] == gx and e["pos"][1] == gy:
			enemy_here = e
			break

	if ally_here:
		selected_unit_id = ally_here["id"]
	elif selected_unit_id != null:
		var actor = null
		for a in state["allies"]:
			if a["id"] == selected_unit_id and a["hp"] > 0:
				actor = a
				break
		if not actor: return
		
		var dist = abs(actor["pos"][0] - gx) + abs(actor["pos"][1] - gy)
		var range_val = actor.get("range", 1)
		
		if enemy_here and dist >= 1 and dist <= range_val:
			execute_action({"unit": actor["id"], "type": "attack"})
		elif not enemy_here and dist == 1:
			var dx = gx - actor["pos"][0]
			var dy = gy - actor["pos"][1]
			execute_action({"unit": actor["id"], "type": "move", "dir": [dx, dy]})
	
	queue_redraw()

func execute_action(action):
	var snap = {}
	for a in state["allies"]: snap["a"+str(a["id"])] = a["hp"]
	for e in state["enemies"]: snap["e"+str(e["id"])] = e["hp"]
	
	var old_pos = {}
	for a in state["allies"]: old_pos["a"+str(a["id"])] = Vector2(a["pos"][0], a["pos"][1])
	for e in state["enemies"]: old_pos["e"+str(e["id"])] = Vector2(e["pos"][0], e["pos"][1])

	state["status"] = rules.update_state(state, action)
	
	# FX 생성
	for a in state["allies"]:
		var kid = "a"+str(a["id"])
		if a["hp"] < snap.get(kid, 999):
			spawn_damage_fx(kid, a["hp"] - snap[kid])
			flashes[kid] = 0.2
		if Vector2(a["pos"][0], a["pos"][1]) != old_pos.get(kid, Vector2(-1,-1)):
			twins[kid] = {"start": old_pos[kid], "curr": Vector2(a["pos"][0], a["pos"][1]), "t": 0.0}

	for e in state["enemies"]:
		var kid = "e"+str(e["id"])
		if e["hp"] < snap.get(kid, 999):
			spawn_damage_fx(kid, e["hp"] - snap[kid])
			flashes[kid] = 0.2
		if Vector2(e["pos"][0], e["pos"][1]) != old_pos.get(kid, Vector2(-1,-1)):
			twins[kid] = {"start": old_pos[kid], "curr": Vector2(e["pos"][0], e["pos"][1]), "t": 0.0}

	if state["status"] != "PLAYING":
		screen = "RESULT"
	queue_redraw()

func spawn_damage_fx(kid, diff):
	var u = null
	if kid.begins_with("a"):
		for a in state["allies"]: if "a"+str(a["id"]) == kid: u = a; break
	else:
		for e in state["enemies"]: if "e"+str(e["id"]) == kid: u = e; break
	if not u: return
	
	var color = Color.RED if diff < 0 else Color.GREEN
	effects.append({
		"type": "damage",
		"kid": kid,
		"val": str(int(round(abs(diff)))),
		"sign": "-" if diff < 0 else "+",
		"life": 0.8,
		"color": color,
		"pos_offset": Vector2(0, 0)
	})

func auto_step():
	if screen != "PLAYING": return
	
	var living_allies = []
	for a in state["allies"]:
		if a["hp"] > 0: living_allies.append(a)
	living_allies.sort_custom(func(a, b): return a["id"] < b["id"])
	
	if living_allies.size() == 0: return
	
	var u = living_allies[auto_ally_idx % living_allies.size()]
	auto_ally_idx += 1
	
	var range_val = u.get("range", 1)
	var target = null
	var min_dist = 999
	for e in state["enemies"]:
		if e["hp"] > 0:
			var d = abs(u["pos"][0] - e["pos"][0]) + abs(u["pos"][1] - e["pos"][1])
			if d < min_dist:
				min_dist = d
				target = e
			elif d == min_dist:
				if target == null or e["id"] < target["id"]:
					target = e
	
	if not target: return
	
	if min_dist >= 1 and min_dist <= range_val:
		execute_action({"unit": u["id"], "type": "attack"})
	else:
		var possible_moves = [[1, 0], [-1, 0], [0, 1], [0, -1]]
		var best_move = null
		var best_dist = min_dist
		
		for m in possible_moves:
			var nx = u["pos"][0] + m[0]
			var ny = u["pos"][1] + m[1]
			if nx >= 0 and nx < state["gridSize"] and ny >= 0 and ny < state["gridSize"]:
				var occupied = false
				for a in state["allies"]: if a["hp"] > 0 and a["pos"][0] == nx and a["pos"][1] == ny: occupied = true; break
				if not occupied:
					for e in state["enemies"]: if e["hp"] > 0 and e["pos"][0] == nx and e["pos"][1] == ny: occupied = true; break
				
				if not occupied:
					var d = abs(nx - target["pos"][0]) + abs(ny - target["pos"][1])
					if d < best_dist:
						best_dist = d
						best_move = m
		
		if best_move:
			execute_action({"unit": u["id"], "type": "move", "dir": best_move})

func _process(delta):
	if auto_mode and screen == "PLAYING":
		auto_accum += delta
		if auto_accum >= 0.6:
			auto_accum = 0
			auto_step()
	
	# FX Update
	for i in range(effects.size() - 1, -1, -1):
		effects[i]["life"] -= delta
		effects[i]["pos_offset"].y -= delta * 50.0
		if effects[i]["life"] <= 0: effects.remove_at(i)
	
	for kid in flashes.keys():
		flashes[kid] -= delta
		if flashes[kid] <= 0: flashes.erase(kid)
		
	for kid in twins.keys():
		twins[kid]["t"] += delta * 6.0
		if twins[kid]["t"] >= 1.0: twins.erase(kid)
	
	if screen == "PLAYING": queue_redraw()

func _draw():
	if screen == "MENU":
		draw_string(font, Vector2(220, 80), "SQUAD TACTICS", HORIZONTAL_ALIGNMENT_CENTER, -1, 32, Color.WHITE)
		for i in range(levels.size()):
			var rect = Rect2(120, 150 + i * 70, 400, 50)
			draw_rect(rect, Color(0.2, 0.2, 0.2, 0.8), true)
			draw_string(font, rect.position + Vector2(10, 30), levels[i]["name"], HORIZONTAL_ALIGNMENT_LEFT, -1, 20, Color.WHITE)
			draw_string(font, rect.position + Vector2(10, 45), levels[i]["desc"], HORIZONTAL_ALIGNMENT_LEFT, -1, 14, Color.LIGHT_GRAY)
	
	elif screen == "BRIEFING":
		draw_rect(Rect2(100, 100, 440, 400), Color(0, 0, 0, 0.7), true)
		var text = levels[pending_idx]["story"]["briefing"]
		var lines = text.split("\n")
		for i in range(lines.size()):
			draw_string(font, Vector2(120, 150 + i * 30), lines[i], HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Color.WHITE)
		draw_string(font, Vector2(320, 450), "Tap to Start", HORIZONTAL_ALIGNMENT_CENTER, -1, 20, Color.YELLOW)
		
	elif screen == "PLAYING":
		# HUD
		draw_rect(Rect2(0, 0, 640, 40), Color(0, 0, 0, 0.5), true)
		var mission_name = levels[current_mission_idx]["name"]
		draw_string(font, Vector2(20, 25), mission_name + " · Turn " + str(state["turn"]), HORIZONTAL_ALIGNMENT_LEFT, -1, 20, Color.WHITE)
		
		var gs = state["gridSize"]
		var tone = tones[current_mission_idx % tones.size()]
		
		# Floor
		for gx in range(gs):
			for gy in range(gs):
				var c = cell_to_screen(gx, gy)
				var th = TILE_H / 2.0
				var tw = TILE_W / 2.0
				var pts = PackedVector2Array([
					c + Vector2(0, -th),
					c + Vector2(tw, 0),
					c + Vector2(0, th),
					c + Vector2(-tw, 0)
				])
				var var_tone = tone + Color((gx*7+gy*13)%5 * 0.02 - 0.04, 0, 0, 0)
				draw_colored_polygon(pts, var_tone)
				var line_pts = PackedVector2Array([pts[0], pts[1], pts[2], pts[3], pts[0]])
				draw_polyline(line_pts, Color(0, 0, 0, 0.15), 1.0)
		
		# Depth Sorted Units
		var render_list = []
		for a in state["allies"]: render_list.append({"kind": "a", "u": a})
		for e in state["enemies"]: render_list.append({"kind": "e", "u": e})
		render_list.sort_custom(func(a, b): 
			var pa = a["u"]["pos"]
			var pb = b["u"]["pos"]
			return (pa[0] + pa[1]) < (pb[0] + pb[1])
		)
		
		for item in render_list:
			var u = item["u"]
			var kind = item["kind"]
			var kid = kind + str(u["id"])
			var gx = u["pos"][0]
			var gy = u["pos"][1]
			var c = cell_to_screen(gx, gy)
			
			# Tweening
			if twins.has(kid):
				var t_info = twins[kid]
				var start_p = Vector2(t_info["start"].x, t_info["start"].y)
				var end_p = Vector2(t_info["curr"].x, t_info["curr"].y)
				# We need to convert these grid coords to screen coords for interpolation
				var sc_start = cell_to_screen(int(start_p.x), int(start_p.y))
				var sc_end = cell_to_screen(int(end_p.x), int(end_p.y))
				c = sc_start.lerp(sc_end, t_info["t"])
			
			# Shadow
			var rx = TILE_W * 0.22
			var ry = TILE_H * 0.18
			var spts = PackedVector2Array()
			for i in range(16):
				var t = TAU * i / 16.0
				spts.append(c + Vector2(cos(t) * rx, sin(t) * ry))
			draw_colored_polygon(spts, Color(0, 0, 0, 0.22))
			
			# Sprite
			var tex = tex_monster
			if kind == "a":
				tex = tex_mage if u.get("range", 1) > 1 else tex_knight
			
			var w = TILE_W * 1.1
			var h = tex.get_height() * (w / tex.get_width())
			var rect = Rect2(c.x - w/2.0, c.y - h, w, h)
			
			var mod = Color.WHITE
			if u["hp"] <= 0: mod = Color(0.3, 0.3, 0.3, 0.6)
			if flashes.has(kid): mod = Color(1, 0.3, 0.3)
			draw_texture_rect(tex, rect, false, mod)
			
			# HP Bar
			var hp_bg = Rect2(c.x - 15, c.y - h - 8, 30, 4)
			draw_rect(hp_bg, Color(0,0,0,0.5), true)
			var hp_ratio = float(u["hp"]) / max_hps.get(kid, 10.0)
			var hp_col = Color.GREEN if kind == "a" else Color.RED
			draw_rect(Rect2(hp_bg.position.x, hp_bg.position.y, hp_bg.size.x * clamp(hp_ratio, 0, 1), 4), hp_col, true)
			if u["hp"] <= 0:
				draw_string(font, c + Vector2(-5, -h - 10), "X", HORIZONTAL_ALIGNMENT_CENTER, -1, 12, Color.WHITE)

			# Highlights
			if selected_unit_id == u["id"] and kind == "a":
				var hpts = PackedVector2Array([
					c + Vector2(0, -TILE_H/2), c + Vector2(TILE_W/2, 0),
					c + Vector2(0, TILE_H/2), c + Vector2(-TILE_W/2, 0), c + Vector2(0, -TILE_H/2)
				])
				draw_polyline(hpts, Color.YELLOW, 2.0)

		# Action Highlights
		if selected_unit_id != null:
			var actor = null
			for a in state["allies"]:
				if a["id"] == selected_unit_id and a["hp"] > 0: actor = a; break
			if actor:
				var range_val = actor.get("range", 1)
				for gx in range(gs):
					for gy in range(gs):
						var dist = abs(actor["pos"][0] - gx) + abs(actor["pos"][1] - gy)
						var c = cell_to_screen(gx, gy)
						var pts = PackedVector2Array([
							c + Vector2(0, -TILE_H/2), c + Vector2(TILE_W/2, 0),
							c + Vector2(0, TILE_H/2), c + Vector2(-TILE_W/2, 0)
						])
						var occupied = false
						for a in state["allies"]: if a["hp"] > 0 and a["pos"][0] == gx and a["pos"][1] == gy: occupied = true; break
						for e in state["enemies"]: if e["hp"] > 0 and e["pos"][0] == gx and e["pos"][1] == gy: occupied = true; break
						
						if not occupied and dist == 1:
							draw_colored_polygon(pts, Color(0, 1, 0, 0.3))
						elif dist >= 1 and dist <= range_val:
							var enemy_here = false
							for e in state["enemies"]: if e["hp"] > 0 and e["pos"][0] == gx and e["pos"][1] == gy: enemy_here = true; break
							if enemy_here:
								var lpts = PackedVector2Array([pts[0], pts[1], pts[2], pts[3], pts[0]])
								draw_polyline(lpts, Color.RED, 2.0)

		# Damage FX
		for fx in effects:
			var u = null
			if fx["kid"].begins_with("a"):
				for a in state["allies"]: if "a"+str(a["id"]) == fx["kid"]: u = a; break
			else:
				for e in state["enemies"]: if "e"+str(e["id"]) == fx["kid"]: u = e; break
			if not u: continue
			var pos = cell_to_screen(u["pos"][0], u["pos"][1]) + Vector2(0, -TILE_W) + fx["pos_offset"]
			var txt = fx["sign"] + fx["val"]
			# Outline
			for ox in [-1, 1]:
				for oy in [-1, 1]:
					draw_string(font, pos + Vector2(ox, oy), txt, HORIZONTAL_ALIGNMENT_CENTER, -1, 22, Color.BLACK)
			draw_string(font, pos, txt, HORIZONTAL_ALIGNMENT_CENTER, -1, 22, fx["color"])

	elif screen == "RESULT":
		draw_rect(Rect2(0, 0, 640, 640), Color(0, 0, 0, 0.6), true)
		var res_text = "VICTORY!" if state["status"] == "VICTORY" else "DEFEAT..."
		var story_text = levels[current_mission_idx]["story"][state["status"].to_lower()]
		draw_string(font, Vector2(320, 200), res_text, HORIZONTAL_ALIGNMENT_CENTER, -1, 40, Color.YELLOW)
		
		var lines = story_text.split("\n")
		for i in range(lines.size()):
			draw_string(font, Vector2(320, 250 + i * 30), lines[i], HORIZONTAL_ALIGNMENT_CENTER, -1, 18, Color.WHITE)
		
		var btn_y = 400
		if state["status"] == "VICTORY":
			draw_rect(Rect2(220, btn_y, 200, 50), Color(0.3, 0.3, 0.3), true)
			draw_string(font, Vector2(320, btn_y + 30), "Next Mission", HORIZONTAL_ALIGNMENT_CENTER, -1, 20, Color.WHITE)
		else:
			draw_rect(Rect2(220, btn_y, 200, 50), Color(0.3, 0.3, 0.3), true)
			draw_string(font, Vector2(320, btn_y + 30), "Retry", HORIZONTAL_ALIGNMENT_CENTER, -1, 20, Color.WHITE)
		
		draw_rect(Rect2(220, 460, 200, 50), Color(0.3, 0.3, 0.3), true)
		draw_string(font, Vector2(320, 490), "Main Menu", HORIZONTAL_ALIGNMENT_CENTER, -1, 20, Color.WHITE)
