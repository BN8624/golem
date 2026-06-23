# 아이소메트릭 2.5D 전술 보드 및 자동 전투 시스템
extends Node2D

var rules
var levels = []
var screen = "MENU"
var state = {}
var selected_unit_id = null
var pending_idx = 0
var current_mission_idx = 0
var font
var textures = {}

var auto_mode = true
var auto_ally_idx = 0
var auto_accum = 0.0

var effects = []
var max_hp_snapshot = {}
var unit_visual_pos = {}

var origin = Vector2(320, 0)
var TILE_W = 64.0
var TILE_H = 32.0

var tones = [
	Color(0.7, 0.7, 0.7), # 기본
	Color(0.5, 0.6, 0.7), # 청회색
	Color(0.4, 0.3, 0.5), # 보라어둠
	Color(0.8, 0.7, 0.4)  # 황금
]

func _ready():
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	rules = load("res://scripts/rules.gd").new()
	font = load("res://assets/fonts/NanumGothic-Regular.ttf")
	
	var data_file = load("res://data/squad_levels.json")
	var json_text = FileAccess.get_file_as_string("res://data/squad_levels.json")
	levels = JSON.parse_string(json_text)
	
	textures["knight"] = load("res://assets/tinydungeon/Tiles/tile_0096.png")
	textures["mage"] = load("res://assets/tinydungeon/Tiles/tile_0084.png")
	textures["monster"] = load("res://assets/tinydungeon/Tiles/tile_0108.png")

func load_mission(idx):
	current_mission_idx = idx
	var initial = levels[idx].initialState
	state = JSON.parse_string(JSON.stringify(initial))
	state.turn = 0
	state.status = "PLAYING"
	selected_unit_id = null
	screen = "PLAYING"
	
	# Visual Setup
	max_hp_snapshot = {}
	unit_visual_pos = {}
	for u in state.allies:
		max_hp_snapshot["a" + str(u.id)] = u.hp
		unit_visual_pos["a" + str(u.id)] = cell_to_screen(u.pos[0], u.pos[1])
	for u in state.enemies:
		max_hp_snapshot["e" + str(u.id)] = u.hp
		unit_visual_pos["e" + str(u.id)] = cell_to_screen(u.pos[0], u.pos[1])
	
	# Projection Setup
	var gs = state.gridSize
	TILE_W = 600.0 / gs
	TILE_H = TILE_W / 2.0
	origin.x = 320.0
	var board_height = (gs - 1) * TILE_H
	origin.y = (640.0 + 40.0) / 2.0 - board_height / 2.0
	
	auto_ally_idx = 0
	auto_accum = 0.0
	queue_redraw()

func cell_to_screen(gx: int, gy: int) -> Vector2:
	return origin + Vector2((gx - gy) * TILE_W / 2.0, (gx + gy) * TILE_H / 2.0)

func screen_to_cell(px: float, py: float) -> Vector2:
	var rx = (px - origin.x) / (TILE_W / 2.0)
	var ry = (py - origin.y) / (TILE_H / 2.0)
	var gx = int(round((rx + ry) / 2.0))
	var gy = int(round((ry - rx) / 2.0))
	return Vector2(gx, gy)

func _unhandled_input(event):
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		var m_pos = event.position
		if screen == "MENU":
			for i in range(levels.size()):
				var r = Rect2(220, 150 + i * 80, 200, 60)
				if r.has_point(m_pos):
					pending_idx = i
					screen = "BRIEFING"
					queue_redraw()
					return
		elif screen == "BRIEFING":
			load_mission(pending_idx)
		elif screen == "PLAYING":
			var cell = screen_to_cell(m_pos.x, m_pos.y)
			var gx = int(cell.x)
			var gy = int(cell.y)
			handle_play_click(gx, gy)
		elif screen == "RESULT":
			# Handle result buttons
			var btn_next = Rect2(220, 400, 200, 50)
			var btn_menu = Rect2(220, 470, 200, 50)
			if btn_next.has_point(m_pos):
				if current_mission_idx < levels.size() - 1:
					pending_idx = current_mission_idx + 1
					screen = "BRIEFING"
				else:
					screen = "MENU"
				queue_redraw()
			elif btn_menu.has_point(m_pos):
				screen = "MENU"
				queue_redraw()

	if event is InputEventKey and event.pressed:
		if event.keycode == KEY_R and screen == "PLAYING":
			load_mission(current_mission_idx)
		elif event.keycode == KEY_N:
			screen = "MENU"
		queue_redraw()

func handle_play_click(gx, gy):
	if gx < 0 or gx >= state.gridSize or gy < 0 or gy >= state.gridSize:
		return

	var clicked_ally = null
	for a in state.allies:
		if a.hp > 0 and int(a.pos[0]) == gx and int(a.pos[1]) == gy:
			clicked_ally = a
			break
	
	if clicked_ally:
		selected_unit_id = clicked_ally.id
		queue_redraw()
		return

	if selected_unit_id == null:
		return

	var actor = null
	for a in state.allies:
		if a.id == selected_unit_id and a.hp > 0:
			actor = a
			break
	if not actor: return

	var clicked_enemy = null
	for e in state.enemies:
		if e.hp > 0 and int(e.pos[0]) == gx and int(e.pos[1]) == gy:
			clicked_enemy = e
			break

	if clicked_enemy:
		var dist = abs(int(actor.pos[0]) - gx) + abs(int(actor.pos[1]) - gy)
		var range_val = actor.get("range", 1)
		if dist >= 1 and dist <= range_val:
			execute_action({"unit": actor.id, "type": "attack"})
	else:
		# Move check
		var dist = abs(int(actor.pos[0]) - gx) + abs(int(actor.pos[1]) - gy)
		if dist == 1:
			var dx = gx - int(actor.pos[0])
			var dy = gy - int(actor.pos[1])
			execute_action({"unit": actor.id, "type": "move", "dir": [dx, dy]})

func execute_action(action):
	var hp_before = {}
	for u in state.allies: hp_before["a" + str(u.id)] = u.hp
	for u in state.enemies: hp_before["e" + str(u.id)] = u.hp
	
	var status = rules.update_state(state, action)
	state.status = status
	
	# FX Generation
	if action.type == "attack":
		var actor = null
		for a in state.allies: 
			if a.id == action.unit: actor = a; break
		
		# Find damaged enemies for arrows and text
		for e in state.enemies:
			var eid = "e" + str(e.id)
			var diff = hp_before.get(eid, e.hp) - e.hp
			if diff > 0:
				spawn_damage_text(int(e.pos[0]), int(e.pos[1]), -int(round(diff)), Color(1, 0.3, 0.3))
				spawn_arrow(actor, e)

	for u in state.allies:
		var aid = "a" + str(u.id)
		var diff = hp_before.get(aid, u.hp) - u.hp
		if diff > 0: spawn_damage_text(int(u.pos[0]), int(u.pos[1]), -int(round(diff)), Color(1, 0.3, 0.3))
		if diff < 0: spawn_damage_text(int(u.pos[0]), int(u.pos[1]), int(round(-diff)), Color(0.3, 1, 0.3))

	if state.status != "PLAYING":
		screen = "RESULT"
	
	queue_redraw()

func spawn_damage_text(gx, gy, val, col):
	effects.append({
		"type": "text", "pos": cell_to_screen(gx, gy), 
		"text": str(val), "color": col, "life": 0.8, "max_life": 0.8
	})

func spawn_arrow(attacker, target):
	var range_val = attacker.get("range", 1)
	effects.append({
		"type": "arrow", "from_cell": [attacker.pos[0], attacker.pos[1]], 
		"to_cell": [target.pos[0], target.pos[1]], 
		"ranged": range_val > 1, "life": 0.4, "max_life": 0.4
	})

func auto_step():
	if screen != "PLAYING": return
	
	var living_allies = []
	for a in state.allies:
		if a.hp > 0: living_allies.append(a)
	living_allies.sort_custom(func(a, b): return a.id < b.id)
	
	if living_allies.size() == 0: return
	
	var actor = living_allies[auto_ally_idx % living_allies.size()]
	auto_ally_idx += 1
	
	# Greedy Policy
	var range_val = actor.get("range", 1)
	var target_enemy = null
	var min_dist = 999
	
	for e in state.enemies:
		if e.hp > 0:
			var d = abs(int(actor.pos[0]) - int(e.pos[0])) + abs(int(actor.pos[1]) - int(e.pos[1]))
			if d < min_dist:
				min_dist = d
				target_enemy = e
			elif d == min_dist and target_enemy and e.id < target_enemy.id:
				target_enemy = e
				
	if not target_enemy: return
	
	if min_dist >= 1 and min_dist <= range_val:
		execute_action({"unit": actor.id, "type": "attack"})
	else:
		# Move towards enemy
		var tx = int(target_enemy.pos[0])
		var ty = int(target_enemy.pos[1])
		var ax = int(actor.pos[0])
		var ay = int(actor.pos[1])
		
		var best_move = null
		var possible = [[1, 0], [-1, 0], [0, 1], [0, -1]]
		for m in possible:
			var nx = ax + m[0]
			var ny = ay + m[1]
			if nx >= 0 and nx < state.gridSize and ny >= 0 and ny < state.gridSize:
				var occ = false
				for u in state.allies: 
					if u.hp > 0 and int(u.pos[0]) == nx and int(u.pos[1]) == ny: occ = true; break
				if not occ:
					for u in state.enemies: 
						if u.hp > 0 and int(u.pos[0]) == nx and int(u.pos[1]) == ny: occ = true; break
				if not occ:
					var d = abs(nx - tx) + abs(ny - ty)
					if d < min_dist:
						best_move = m
						break
		if best_move:
			execute_action({"unit": actor.id, "type": "move", "dir": best_move})

func _process(delta):
	if screen == "PLAYING":
		if auto_mode:
			auto_accum += delta
			if auto_accum >= 0.6:
				auto_accum = 0.0
				auto_step()
		
		# Update Visuals (Tweens)
		for u in state.allies:
			var id = "a" + str(u.id)
			var target = cell_to_screen(int(u.pos[0]), int(u.pos[1]))
			unit_visual_pos[id] = unit_visual_pos.get(id, target).lerp(target, 0.25)
		for u in state.enemies:
			var id = "e" + str(u.id)
			var target = cell_to_screen(int(u.pos[0]), int(u.pos[1]))
			unit_visual_pos[id] = unit_visual_pos.get(id, target).lerp(target, 0.25)
		
		# Update FX
		var i = 0
		while i < effects.size():
			effects[i].life -= delta
			if effects[i].life <= 0:
				effects.remove_at(i)
			else:
				i += 1
		queue_redraw()

func _draw():
	if screen == "MENU":
		draw_string(font, Vector2(220, 100), "SQUAD TACTICS", HORIZONTAL_ALIGNMENT_LEFT, -1, 32, Color.WHITE)
		for i in range(levels.size()):
			var r = Rect2(220, 150 + i * 80, 200, 60)
			draw_rect(r, Color(0.2, 0.2, 0.2, 0.8), true)
			draw_string(font, r.position + Vector2(10, 25), levels[i].name, HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Color.WHITE)
			draw_string(font, r.position + Vector2(10, 45), levels[i].desc, HORIZONTAL_ALIGNMENT_LEFT, -1, 14, Color.LIGHT_GRAY)
	
	elif screen == "BRIEFING":
		draw_rect(Rect2(120, 120, 400, 300), Color(0, 0, 0, 0.7), true)
		var story = levels[pending_idx].story.briefing
		var lines = story.split("\n")
		for i in range(lines.size()):
			draw_string(font, Vector2(140, 160 + i * 24), lines[i], HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color.WHITE)
		draw_string(font, Vector2(240, 380), "탭하여 시작", HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color.YELLOW)
		
	elif screen == "PLAYING":
		# HUD
		draw_rect(Rect2(0, 0, 640, 40), Color(0, 0, 0, 0.5), true)
		draw_string(font, Vector2(20, 25), levels[current_mission_idx].name + "  Turn: " + str(state.turn), HORIZONTAL_ALIGNMENT_LEFT, -1, 20, Color.WHITE)
		
		var tone = tones[current_mission_idx % tones.size()]
		
		# 1. Floor
		for gx in range(state.gridSize):
			for gy in range(state.gridSize):
				var c = cell_to_screen(gx, gy)
				var pts = PackedVector2Array()
				pts.append(c + Vector2(0, -TILE_H/2))
				pts.append(c + Vector2(TILE_W/2, 0))
				pts.append(c + Vector2(0, TILE_H/2))
				pts.append(c + Vector2(-TILE_W/2, 0))
				
				var var_tone = tone
				var v_off = (gx * 7 + gy * 13) % 5
				var_tone = var_tone.lightened(0.02 * (v_off - 2))
				draw_colored_polygon(pts, var_tone)
				
				var line_pts = PackedVector2Array([pts[0], pts[1], pts[2], pts[3], pts[0]])
				draw_polyline(line_pts, Color(0, 0, 0, 0.15), 1.0)

		# 2. Range Highlights
		if selected_unit_id != null:
			var actor = null
			for a in state.allies:
				if a.id == selected_unit_id and a.hp > 0: actor = a; break
			if actor:
				var rng = actor.get("range", 1)
				for gx in range(state.gridSize):
					for gy in range(state.gridSize):
						var dist = abs(int(actor.pos[0]) - gx) + abs(int(actor.pos[1]) - gy)
						var c = cell_to_screen(gx, gy)
						var pts = PackedVector2Array()
						pts.append(c + Vector2(0, -TILE_H/2))
						pts.append(c + Vector2(TILE_W/2, 0))
						pts.append(c + Vector2(0, TILE_H/2))
						pts.append(c + Vector2(-TILE_W/2, 0))
						
						if dist >= 1 and dist <= rng:
							draw_colored_polygon(pts, Color(1, 0.3, 0.3, 0.12))
						
						if dist == 1:
							var occ = false
							for u in state.allies: if u.hp > 0 and int(u.pos[0]) == gx and int(u.pos[1]) == gy: occ = true; break
							for u in state.enemies: if u.hp > 0 and int(u.pos[0]) == gx and int(u.pos[1]) == gy: occ = true; break
							if not occ:
								draw_colored_polygon(pts, Color(0.3, 1, 0.3, 0.2))
						
						if gx == int(actor.pos[0]) and gy == int(actor.pos[1]):
							var l_pts = PackedVector2Array([pts[0], pts[1], pts[2], pts[3], pts[0]])
							draw_polyline(l_pts, Color.YELLOW, 2.0)
						
						# Target enemy highlight
						for e in state.enemies:
							if e.hp > 0 and int(e.pos[0]) == gx and int(e.pos[1]) == gy:
								if dist >= 1 and dist <= rng:
									var l_pts = PackedVector2Array([pts[0], pts[1], pts[2], pts[3], pts[0]])
									draw_polyline(l_pts, Color.RED, 2.0)

		# 3. Units (Z-Sorted)
		var units_to_draw = []
		for a in state.allies: units_to_draw.append({"u": a, "side": "a"})
		for e in state.enemies: units_to_draw.append({"u": e, "side": "e"})
		units_to_draw.sort_custom(func(a, b): 
			return (int(a.u.pos[0]) + int(a.u.pos[1])) < (int(b.u.pos[0]) + int(b.u.pos[1]))
		)

		for item in units_to_draw:
			var u = item.u
			var side = item.side
			var uid = side + str(u.id)
			var c = unit_visual_pos.get(uid, cell_to_screen(int(u.pos[0]), int(u.pos[1])))
			
			# Shadow
			var s_pts = PackedVector2Array()
			var rx = TILE_W * 0.22
			var ry = TILE_H * 0.18
			for i in range(16):
				var t = TAU * i / 16.0
				s_pts.append(c + Vector2(cos(t) * rx, sin(t) * ry))
			draw_colored_polygon(s_pts, Color(0, 0, 0, 0.22))
			
			# Sprite
			var tex = textures["monster"]
			if side == "a":
				tex = textures["mage"] if u.get("range", 1) > 1 else textures["knight"]
			
			var tw = TILE_W * 1.1
			var th = tex.get_height() * (tw / tex.get_width())
			var rect = Rect2(c.x - tw/2, c.y - th, tw, th)
			var mod = Color.WHITE
			if u.hp <= 0: mod = Color(0.4, 0.4, 0.4, 0.6)
			draw_texture_rect(tex, rect, false, mod)
			
			# HP Bar
			var max_h = max_hp_snapshot.get(uid, u.hp)
			var bar_w = tw * 0.6
			var bar_h = 4.0
			var bar_pos = Vector2(c.x - bar_w/2, rect.position.y - 8)
			draw_rect(Rect2(bar_pos, Vector2(bar_w, bar_h)), Color(0, 0, 0, 0.5), true)
			var fill_w = bar_w * (max(0, u.hp) / max(1, max_h))
			var fill_col = Color.GREEN if side == "a" else Color.RED
			draw_rect(Rect2(bar_pos, Vector2(fill_w, bar_h)), fill_col, true)
			if u.hp <= 0:
				draw_string(font, bar_pos + Vector2(bar_w/2 - 4, -4), "X", HORIZONTAL_ALIGNMENT_LEFT, -1, 10, Color.WHITE)

		# 4. Effects (Arrows then Text)
		for fx in effects:
			if fx.type == "arrow":
				var a_pos = cell_to_screen(int(fx.from_cell[0]), int(fx.from_cell[1])) + Vector2(0, -TILE_H * 0.4)
				var b_pos = cell_to_screen(int(fx.to_cell[0]), int(fx.to_cell[1])) + Vector2(0, -TILE_H * 0.4)
				var alpha = clamp(fx.life / fx.max_life, 0.0, 1.0)
				if not fx.ranged:
					draw_line(a_pos, b_pos, Color(1, 1, 0.3, alpha), 3.0)
				else:
					var p_pts = PackedVector2Array()
					for i in range(17):
						var t = i / 16.0
						p_pts.append(a_pos.lerp(b_pos, t) + Vector2(0, -TILE_H * 1.2 * (4.0 * t * (1.0 - t))))
					draw_polyline(p_pts, Color(0.6, 0.9, 1, alpha), 3.0)
			elif fx.type == "text":
				var alpha = clamp(fx.life / fx.max_life, 0.0, 1.0)
				var p = fx.pos + Vector2(0, - (fx.max_life - fx.life) * 80.0)
				draw_string(font, p + Vector2(-2, 0), fx.text, HORIZONTAL_ALIGNMENT_LEFT, -1, 22, Color(0,0,0, alpha))
				draw_string(font, p + Vector2(0, 0), fx.text, HORIZONTAL_ALIGNMENT_LEFT, -1, 22, Color(fx.color, alpha))

	elif screen == "RESULT":
		draw_rect(Rect2(0, 0, 640, 640), Color(0, 0, 0, 0.6), true)
		var is_vic = state.status == "VICTORY"
		var msg = levels[current_mission_idx].story.victory if is_vic else levels[current_mission_idx].story.defeat
		draw_string(font, Vector2(220, 200), msg, HORIZONTAL_ALIGNMENT_LEFT, -1, 20, Color.WHITE)
		
		var btn_txt = "다음 미션" if is_vic else "다시 하기"
		draw_rect(Rect2(220, 400, 200, 50), Color(0.3, 0.3, 0.3), true)
		draw_string(font, Vector2(260, 430), btn_txt, HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Color.WHITE)
		
		draw_rect(Rect2(220, 470, 200, 50), Color(0.3, 0.3, 0.3), true)
		draw_string(font, Vector2(260, 500), "메뉴로", HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Color.WHITE)
