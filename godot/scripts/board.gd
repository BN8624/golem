# 미션 선택, 부대 편성, 아이소메트릭 전투 및 자동 전투 시스템 구현
extends Node2D

var rules
var levels = []
var roster = []
var font

var screen = "MENU"
var state = {}
var selected_unit_id = null
var pending_idx = 0
var auto_mode = true
var auto_ally_idx = 0
var auto_accum = 0.0

var picked_ids = []
var max_hps = {}
var effects = []
var unit_twins = {}

var tex_knight
var tex_mage
var tex_monster

var TILE_W = 64.0
var TILE_H = 32.0
var origin = Vector2(320, 320)

func _ready():
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	rules = load("res://scripts/rules.gd").new()
	font = load("res://assets/fonts/NanumGothic-Regular.ttf")
	
	var lv_json = FileAccess.open("res://data/squad_levels.json", FileAccess.READ).get_as_text()
	levels = JSON.parse_string(lv_json)
	
	var rs_json = FileAccess.open("res://data/roster.json", FileAccess.READ).get_as_text()
	roster = JSON.parse_string(rs_json)["units"]
	
	tex_knight = load("res://assets/tinydungeon/Tiles/tile_0096.png")
	tex_mage = load("res://assets/tinydungeon/Tiles/tile_0084.png")
	tex_monster = load("res://assets/tinydungeon/Tiles/tile_0108.png")

func cell_to_screen(gx: int, gy: int) -> Vector2:
	if screen != "PLAYING": return Vector2.ZERO
	var gw = 600.0 / state.gridSize
	var gh = gw / 2.0
	var ox = 320
	var oy = 340 - (state.gridSize - 1) * gh / 2.0
	return Vector2(ox, oy) + Vector2((gx - gy) * gw / 2.0, (gx + gy) * gh / 2.0)

func screen_to_cell(px: float, py: float) -> Vector2:
	if screen != "PLAYING": return Vector2.ZERO
	var gw = 600.0 / state.gridSize
	var gh = gw / 2.0
	var ox = 320
	var oy = 340 - (state.gridSize - 1) * gh / 2.0
	var rx = (px - ox) / (gw / 2.0)
	var ry = (py - oy) / (gh / 2.0)
	return Vector2(round((rx + ry) / 2.0), round((ry - rx) / 2.0))

func load_mission(idx: int) -> void:
	pending_idx = idx
	var init = JSON.parse_string(JSON.stringify(levels[idx].initialState))
	_enter_battle(init)

func start_battle_with(ids: Array) -> void:
	var squad_size = levels[pending_idx].initialState.allies.size()
	var picked_allies = []
	for i in range(ids.size()):
		var u_raw = null
		for r in roster:
			if r.id == ids[i]:
				u_raw = r
				break
		var u = JSON.parse_string(JSON.stringify(u_raw))
		u.id = i + 1
		u.pos = [0, i]
		picked_allies.append(u)
	
	var init = JSON.parse_string(JSON.stringify(levels[pending_idx].initialState))
	init.allies = picked_allies
	_enter_battle(init)

func _enter_battle(init_state: Dictionary) -> void:
	state = init_state
	state.turn = 0
	state.status = "PLAYING"
	selected_unit_id = null
	auto_ally_idx = 0
	auto_accum = 0.0
	screen = "PLAYING"
	max_hps.clear()
	for u in state.allies: max_hps["a" + str(u.id)] = u.hp
	for u in state.enemies: max_hps["e" + str(u.id)] = u.hp
	queue_redraw()

func _process(delta):
	if screen == "PLAYING":
		if auto_mode:
			auto_accum += delta
			if auto_accum >= 0.6:
				auto_accum = 0
				auto_step()
		
		var changed = false
		for i in range(effects.size() - 1, -1, -1):
			effects[i].life -= delta
			if effects[i].life <= 0:
				effects.remove_at(i)
				changed = true
		
		for key in unit_twins.keys():
			var tw = unit_twins[key]
			tw.t += delta * 6.0
			if tw.t >= 1.0:
				unit_twins.erase(key)
				changed = true
		
		if changed: queue_redraw()

func _unhandled_input(event):
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		var mp = event.position
		if screen == "MENU":
			for i in range(levels.size()):
				if mp.y > 150 + i * 70 and mp.y < 210 + i * 70:
					pending_idx = i
					screen = "BRIEFING"
					queue_redraw()
		elif screen == "BRIEFING":
			screen = "SQUAD_SELECT"
			picked_ids.clear()
			queue_redraw()
		elif screen == "SQUAD_SELECT":
			var squad_size = levels[pending_idx].initialState.allies.size()
			for i in range(roster.size()):
				if mp.x > 100 and mp.x < 540 and mp.y > 100 + i * 60 and mp.y < 150 + i * 60:
					if picked_ids.has(roster[i].id):
						picked_ids.erase(roster[i].id)
					elif picked_ids.size() < squad_size:
						picked_ids.append(roster[i].id)
					queue_redraw()
			if mp.x > 220 and mp.x < 420 and mp.y > 540 and mp.y < 590:
				if picked_ids.size() == squad_size:
					start_battle_with(picked_ids)
		elif screen == "PLAYING":
			var cell = screen_to_cell(mp.x, mp.y)
			var gx = int(cell.x)
			var gy = int(cell.y)
			
			var clicked_ally = null
			for u in state.allies:
				if u.hp > 0 and int(u.pos[0]) == gx and int(u.pos[1]) == gy:
					clicked_ally = u
					break
			
			if clicked_ally:
				selected_unit_id = clicked_ally.id
			elif selected_unit_id != null:
				var actor = null
				for u in state.allies:
					if u.id == selected_unit_id:
						actor = u
						break
				
				var clicked_enemy = null
				for e in state.enemies:
					if e.hp > 0 and int(e.pos[0]) == gx and int(e.pos[1]) == gy:
						clicked_enemy = e
						break
				
				if clicked_enemy:
					var dist = abs(actor.pos[0] - gx) + abs(actor.pos[1] - gy)
					var rng = actor.get("range", 1)
					if dist >= 1 and dist <= rng:
						execute_action({"unit": actor.id, "type": "attack"})
				else:
					var dist = abs(actor.pos[0] - gx) + abs(actor.pos[1] - gy)
					if dist == 1:
						var dx = gx - actor.pos[0]
						var dy = gy - actor.pos[1]
						execute_action({"unit": actor.id, "type": "move", "dir": [dx, dy]})
			queue_redraw()
		elif screen == "RESULT":
			if state.status == "VICTORY":
				if mp.x > 220 and mp.x < 420 and mp.y > 500 and mp.y < 550:
					if pending_idx < levels.size() - 1:
						pending_idx += 1
						screen = "BRIEFING"
					else:
						screen = "MENU"
			else:
				if mp.x > 150 and mp.x < 300 and mp.y > 500 and mp.y < 550:
					load_mission(pending_idx)
				elif mp.x > 340 and mp.x < 490 and mp.y > 500 and mp.y < 550:
					screen = "MENU"
			queue_redraw()

func execute_action(action: Dictionary) -> void:
	var snapshot = {}
	for u in state.allies: snapshot["a" + str(u.id)] = u.hp
	for u in state.enemies: snapshot["e" + str(u.id)] = u.hp
	
	var old_pos = {}
	for u in state.allies: old_pos["a" + str(u.id)] = Vector2(u.pos[0], u.pos[1])
	for u in state.enemies: old_pos["e" + str(u.id)] = Vector2(u.pos[0], u.pos[1])
	
	state.status = rules.update_state(state, action)
	
	for u in state.allies:
		var key = "a" + str(u.id)
		if u.hp != snapshot.get(key, u.hp):
			spawn_damage_text(u.pos, u.hp - snapshot.get(key, u.hp))
			if u.hp < snapshot.get(key, u.hp): spawn_flash(key)
		var np = Vector2(u.pos[0], u.pos[1])
		if np != old_pos.get(key, np):
			unit_twins[key] = {"from": old_pos[key], "to": np, "t": 0.0}
			
	for e in state.enemies:
		var key = "e" + str(e.id)
		if e.hp != snapshot.get(key, e.hp):
			spawn_damage_text(e.pos, e.hp - snapshot.get(key, e.hp))
			if e.hp < snapshot.get(key, e.hp): spawn_flash(key)
		var np = Vector2(e.pos[0], e.pos[1])
		if np != old_pos.get(key, np):
			unit_twins[key] = {"from": old_pos[key], "to": np, "t": 0.0}

	if action.type == "attack":
		var actor = null
		for u in state.allies:
			if u.id == action.unit: actor = u; break
		var range_val = actor.get("range", 1)
		for e in state.enemies:
			var key = "e" + str(e.id)
			if snapshot.get(key, e.hp) > e.hp:
				effects.append({"type": "arrow", "from_cell": actor.pos, "to_cell": e.pos, "ranged": range_val > 1, "life": 0.4, "max_life": 0.4})
	
	if state.status != "PLAYING":
		screen = "RESULT"
	queue_redraw()

func auto_step() -> void:
	if screen != "PLAYING": return
	var living = []
	for u in state.allies:
		if u.hp > 0: living.append(u)
	if living.size() == 0: return
	living.sort_custom(func(a, b): return a.id < b.id)
	
	var u = living[auto_ally_idx % living.size()]
	auto_ally_idx += 1
	
	var targets = []
	for e in state.enemies:
		if e.hp > 0:
			var d = abs(u.pos[0] - e.pos[0]) + abs(u.pos[1] - e.pos[1])
			if d >= 1 and d <= u.get("range", 1): targets.append(e)
	
	if targets.size() > 0:
		targets.sort_custom(func(a, b): return a.id < b.id)
		execute_action({"unit": u.id, "type": "attack"})
	else:
		var closest_e = null
		var min_d = 999
		for e in state.enemies:
			if e.hp > 0:
				var d = abs(u.pos[0] - e.pos[0]) + abs(u.pos[1] - e.pos[1])
				if d < min_d: min_d = d; closest_e = e
		
		if closest_e:
			var dx = 0
			var dy = 0
			if closest_e.pos[0] != u.pos[0]:
				dx = 1 if closest_e.pos[0] > u.pos[0] else -1
			elif closest_e.pos[1] != u.pos[1]:
				dy = 1 if closest_e.pos[1] > u.pos[1] else -1
			
			var nx = u.pos[0] + dx
			var ny = u.pos[1] + dy
			if nx >= 0 and nx < state.gridSize and ny >= 0 and ny < state.gridSize:
				var occupied = false
				for a in state.allies:
					if a.hp > 0 and int(a.pos[0]) == nx and int(a.pos[1]) == ny: occupied = true; break
				for e in state.enemies:
					if e.hp > 0 and int(e.pos[0]) == nx and int(e.pos[1]) == ny: occupied = true; break
				if not occupied:
					execute_action({"unit": u.id, "type": "move", "dir": [dx, dy]})

func spawn_damage_text(pos: Array, diff: float) -> void:
	effects.append({"type": "text", "pos": Vector2(pos[0], pos[1]), "text": str(int(round(diff))), "color": Color.RED if diff < 0 else Color.GREEN, "life": 0.8, "max_life": 0.8})

func spawn_flash(key: String) -> void:
	effects.append({"type": "flash", "key": key, "life": 0.2, "max_life": 0.2})

func _draw():
	if screen == "MENU":
		draw_string(font, Vector2(220, 80), "SQUAD TACTICS", HORIZONTAL_ALIGNMENT_CENTER, -1, 32, Color.WHITE)
		for i in range(levels.size()):
			var rect = Rect2(150, 150 + i * 70, 340, 60)
			draw_rect(rect, Color(0.2, 0.2, 0.2, 0.8), true)
			draw_string(font, rect.position + Vector2(10, 25), levels[i].name, HORIZONTAL_ALIGNMENT_LEFT, -1, 20, Color.WHITE)
			draw_string(font, rect.position + Vector2(10, 45), levels[i].desc, HORIZONTAL_ALIGNMENT_LEFT, -1, 14, Color.LIGHT_GRAY)
	
	elif screen == "BRIEFING":
		var rect = Rect2(100, 100, 440, 400)
		draw_rect(rect, Color(0, 0, 0, 0.7), true)
		var lines = levels[pending_idx].story.briefing.split("\n")
		for i in range(lines.size()):
			draw_string(font, rect.position + Vector2(20, 40 + i * 30), lines[i], HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Color.WHITE)
		draw_string(font, Vector2(320, 460), "탭하여 시작", HORIZONTAL_ALIGNMENT_CENTER, -1, 20, Color.YELLOW)
	
	elif screen == "SQUAD_SELECT":
		draw_string(font, Vector2(320, 60), "출전 부대 편성", HORIZONTAL_ALIGNMENT_CENTER, -1, 24, Color.WHITE)
		var squad_size = levels[pending_idx].initialState.allies.size()
		for i in range(roster.size()):
			var u = roster[i]
			var rect = Rect2(100, 100 + i * 60, 440, 50)
			var is_picked = picked_ids.has(u.id)
			draw_rect(rect, Color(0.3, 0.3, 0.3, 1.0) if not is_picked else Color(0.4, 0.6, 0.4, 1.0), true)
			if is_picked: draw_rect(rect, Color.YELLOW, false, 2.0)
			draw_string(font, rect.position + Vector2(10, 30), u.name + " [" + u.role + "] HP:" + str(u.hp) + " ATK:" + str(u.atk), HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color.WHITE)
		
		var btn_rect = Rect2(220, 540, 200, 50)
		var active = picked_ids.size() == squad_size
		draw_rect(btn_rect, Color(0.5, 0.5, 0.5, 1.0) if not active else Color(0.2, 0.8, 0.2, 1.0), true)
		draw_string(font, btn_rect.position + Vector2(100, 30), "출전", HORIZONTAL_ALIGNMENT_CENTER, -1, 20, Color.WHITE)
	
	elif screen == "PLAYING":
		var tones = [Color(0.4, 0.4, 0.4), Color(0.3, 0.4, 0.5), Color(0.3, 0.2, 0.4), Color(0.5, 0.4, 0.2)]
		var tone = tones[pending_idx % tones.size()]
		
		draw_rect(Rect2(0, 0, 640, 36), Color(0, 0, 0, 0.5), true)
		draw_string(font, Vector2(20, 25), levels[pending_idx].name + " · Turn " + str(state.turn), HORIZONTAL_ALIGNMENT_LEFT, -1, 20, Color.WHITE)
		
		for gx in range(state.gridSize):
			for gy in range(state.gridSize):
				var c = cell_to_screen(gx, gy)
				var th = TILE_W/2.0
				var tw = TILE_W
				var pts = PackedVector2Array([c + Vector2(0, -th/2), c + Vector2(tw/2, 0), c + Vector2(0, th/2), c + Vector2(-tw/2, 0)])
				var v_tone = tone
				v_tone.v += (gx * 7 + gy * 13) % 5 * 0.02 - 0.04
				draw_colored_polygon(pts, v_tone)
				var line_pts = PackedVector2Array([pts[0], pts[1], pts[2], pts[3], pts[0]])
				draw_polyline(line_pts, Color(0, 0, 0, 0.15), 1.0)
		
		if selected_unit_id != null:
			var actor = null
			for u in state.allies:
				if u.id == selected_unit_id: actor = u; break
			if actor:
				var rng = actor.get("range", 1)
				for gx in range(state.gridSize):
					for gy in range(state.gridSize):
						var dist = abs(actor.pos[0] - gx) + abs(actor.pos[1] - gy)
						if dist >= 1 and dist <= rng:
							var c = cell_to_screen(gx, gy)
							var pts = PackedVector2Array([c + Vector2(0, -TILE_H/2), c + Vector2(TILE_W/2, 0), c + Vector2(0, TILE_H/2), c + Vector2(-TILE_W/2, 0)])
							draw_colored_polygon(pts, Color(1, 0.3, 0.3, 0.12))
						
						if dist == 1:
							var occupied = false
							for u in state.allies:
								if u.hp > 0 and int(u.pos[0]) == gx and int(u.pos[1]) == gy: occupied = true; break
							for e in state.enemies:
								if e.hp > 0 and int(e.pos[0]) == gx and int(e.pos[1]) == gy: occupied = true; break
							if not occupied:
								var c = cell_to_screen(gx, gy)
								var pts = PackedVector2Array([c + Vector2(0, -TILE_H/2), c + Vector2(TILE_W/2, 0), c + Vector2(0, TILE_H/2), c + Vector2(-TILE_W/2, 0)])
								draw_colored_polygon(pts, Color(0, 1, 0, 0.2))
								
							var is_enemy = false
							for e in state.enemies:
								if e.hp > 0 and int(e.pos[0]) == gx and int(e.pos[1]) == gy: is_enemy = true; break
							if is_enemy and dist <= rng:
								var c = cell_to_screen(gx, gy)
								var pts = PackedVector2Array([c + Vector2(0, -TILE_H/2), c + Vector2(TILE_W/2, 0), c + Vector2(0, TILE_H/2), c + Vector2(-TILE_W/2, 0), c + Vector2(0, -TILE_H/2)])
								draw_polyline(pts, Color.RED, 2.0)

		var all_units = []
		for u in state.allies: all_units.append({"u": u, "side": "a"})
		for e in state.enemies: all_units.append({"u": e, "side": "e"})
		all_units.sort_custom(func(a, b): return (int(a.u.pos[0]) + int(a.u.pos[1])) < (int(b.u.pos[0]) + int(b.u.pos[1])))
		
		for item in all_units:
			var u = item.u
			var side = item.side
			var key = side + str(u.id)
			var pos_vec = Vector2(u.pos[0], u.pos[1])
			if unit_twins.has(key):
				var tw = unit_twins[key]
				pos_vec = tw.from.lerp(tw.to, tw.t)
			
			var c = cell_to_screen(int(pos_vec.x), int(pos_vec.y)) # approx, strictly the target cell
			# Actual projection of the lerped pos:
			var cur_c = origin + Vector2((pos_vec.x - pos_vec.y) * (600.0/state.gridSize) / 2.0, (pos_vec.x + pos_vec.y) * (300.0/state.gridSize) / 2.0)
			# Adjustment for origin.y:
			cur_c.y = 340 - (state.gridSize - 1) * (300.0/state.gridSize) / 2.0 + (pos_vec.x + pos_vec.y) * (300.0/state.gridSize) / 2.0
			cur_c.x = 320 + (pos_vec.x - pos_vec.y) * (600.0/state.gridSize) / 2.0
			
			var shadow_pts = PackedVector2Array()
			for i in range(16):
				var t = TAU * i / 16.0
				shadow_pts.append(cur_c + Vector2(cos(t) * (600.0/state.gridSize)*0.22, sin(t) * (300.0/state.gridSize)*0.18))
			draw_colored_polygon(shadow_pts, Color(0, 0, 0, 0.22))
			
			var tex = tex_monster if side == "e" else (tex_mage if u.get("range", 1) > 1 else tex_knight)
			var w = (600.0/state.gridSize) * 1.1
			var h = tex.get_height() * (w / tex.get_width())
			var rect = Rect2(cur_c.x - w/2, cur_c.y - h, w, h)
			var mod = Color.WHITE
			if u.hp <= 0: mod = Color(0.5, 0.5, 0.5, 0.5)
			for fx in effects:
				if fx.type == "flash" and fx.key == key: mod = Color(1, 0.4, 0.4, 1.0)
			draw_texture_rect(tex, rect, false, mod)
			
			if u.hp > 0:
				var max_h = max_hps.get(key, u.hp)
				var bw = 30.0
				var bh = 4.0
				draw_rect(Rect2(cur_c.x - bw/2, cur_c.y - h - 6, bw, bh), Color.BLACK, true)
				var fill = max(0, min(1.0, float(u.hp) / max_h))
				draw_rect(Rect2(cur_c.x - bw/2, cur_c.y - h - 6, bw * fill, bh), Color.GREEN if side == "a" else Color.RED, true)
			else:
				draw_string(font, cur_c + Vector2(-5, -h/2), "X", HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color.RED)
			
			if side == "a" and u.id == selected_unit_id:
				var pts = PackedVector2Array([cur_c + Vector2(0, -TILE_H/2), cur_c + Vector2(TILE_W/2, 0), cur_c + Vector2(0, TILE_H/2), cur_c + Vector2(-TILE_W/2, 0), cur_c + Vector2(0, -TILE_H/2)])
				draw_polyline(pts, Color.YELLOW, 2.0)

		for fx in effects:
			if fx.type == "arrow":
				var a = cell_to_screen(int(fx.from_cell[0]), int(fx.from_cell[1])) + Vector2(0, -TILE_H * 0.4)
				var b = cell_to_screen(int(fx.to_cell[0]), int(fx.to_cell[1])) + Vector2(0, -TILE_H * 0.4)
				var alpha = clamp(fx.life / fx.max_life, 0.0, 1.0)
				if not fx.ranged:
					draw_line(a, b, Color(1, 1, 0.3, alpha), 3.0)
				else:
					var pts = PackedVector2Array()
					for i in range(17):
						var t = i / 16.0
						pts.append(a.lerp(b, t) + Vector2(0, -TILE_H * 1.2 * (4.0 * t * (1.0 - t))))
					draw_polyline(pts, Color(0.6, 0.9, 1, alpha), 3.0)
			elif fx.type == "text":
				var c = cell_to_screen(int(fx.pos.x), int(fx.pos.y))
				var py = c.y - (1.0 - fx.life/fx.max_life) * 60.0
				var txt = fx.text
				draw_string(font, c + Vector2(-5, py), txt, HORIZONTAL_ALIGNMENT_LEFT, -1, 22, Color.BLACK)
				draw_string(font, c + Vector2(-4, py-1), txt, HORIZONTAL_ALIGNMENT_LEFT, -1, 22, fx.color)
	
	elif screen == "RESULT":
		var rect = Rect2(120, 200, 400, 200)
		draw_rect(rect, Color(0, 0, 0, 0.8), true)
		var msg = levels[pending_idx].story.victory if state.status == "VICTORY" else levels[pending_idx].story.defeat
		var lines = msg.split("\n")
		for i in range(lines.size()):
			draw_string(font, rect.position + Vector2(20, 50 + i * 30), lines[i], HORIZONTAL_ALIGNMENT_LEFT, -1, 20, Color.WHITE)
		
		if state.status == "VICTORY":
			var btn = Rect2(220, 500, 200, 50)
			draw_rect(btn, Color(0.2, 0.6, 0.2, 1.0), true)
			draw_string(font, btn.position + Vector2(100, 30), "다음 미션", HORIZONTAL_ALIGNMENT_CENTER, -1, 20, Color.WHITE)
		else:
			var btn1 = Rect2(150, 500, 150, 50)
			draw_rect(btn1, Color(0.6, 0.2, 0.2, 1.0), true)
			draw_string(font, btn1.position + Vector2(75, 30), "다시", HORIZONTAL_ALIGNMENT_CENTER, -1, 20, Color.WHITE)
			var btn2 = Rect2(340, 500, 150, 50)
			draw_rect(btn2, Color(0.4, 0.4, 0.4, 1.0), true)
			draw_string(font, btn2.position + Vector2(75, 30), "메뉴로", HORIZONTAL_ALIGNMENT_CENTER, -1, 20, Color.WHITE)
