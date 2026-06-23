# 미션 선택, 서사, 아이소메트릭 전투를 처리하는 보드 씬 스크립트
extends Node2D

var rules
var levels = []
var current_mission_idx = -1
var pending_idx = -1
var screen = "MENU"

# 검증 계약 멤버
var state = {}
var selected_unit_id = null

# 표시용 데이터
var font
var textures = {}
var max_hp = {} # "a1", "e1" keys
var visual_pos = {} # tweening
var effects = [] # {type: "text", pos: Vector2, text: String, color: Color, life: float}
var flashes = {} # "a1": timer
var tones = [Color(0.6, 0.6, 0.6), Color(0.5, 0.6, 0.7), Color(0.5, 0.4, 0.6), Color(0.7, 0.6, 0.4)]

var TILE_W = 0.0
var TILE_H = 0.0
var origin = Vector2.ZERO

func _ready():
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	rules = load("res://scripts/rules.gd").new()
	font = load("res://assets/fonts/NanumGothic-Regular.ttf")
	
	var file = FileAccess.open("res://data/squad_levels.json", FileAccess.READ)
	if file:
		levels = JSON.parse_string(file.get_as_text())
	
	_load_textures()
	queue_redraw()

func _load_textures():
	var paths = {
		"knight": "res://assets/tinydungeon/Tiles/tile_0096.png",
		"mage": "res://assets/tinydungeon/Tiles/tile_0084.png",
		"monster": "res://assets/tinydungeon/Tiles/tile_0108.png"
	}
	for k in paths:
		textures[k] = load(paths[k])

func load_mission(idx):
	current_mission_idx = idx
	var initial = levels[idx]["initialState"]
	state = JSON.parse_string(JSON.stringify(initial))
	state.turn = 0
	state.status = "PLAYING"
	
	selected_unit_id = null
	screen = "PLAYING"
	
	# 픽셀 설정
	TILE_W = 600.0 / state.gridSize
	TILE_H = TILE_W / 2.0
	origin.x = 320
	origin.y = (640 + 36) / 2.0 - (state.gridSize - 1) * TILE_H / 2.0
	
	# Max HP 스냅샷
	max_hp.clear()
	for u in state.allies: max_hp["a" + str(u.id)] = u.hp
	for u in state.enemies: max_hp["e" + str(u.id)] = u.hp
	
	# Initial Visual Pos
	visual_pos.clear()
	for u in state.allies: visual_pos["a" + str(u.id)] = cell_to_screen(u.pos[0], u.pos[1])
	for u in state.enemies: visual_pos["e" + str(u.id)] = cell_to_screen(u.pos[0], u.pos[1])
	
	queue_redraw()

func cell_to_screen(gx: int, gy: int) -> Vector2:
	return origin + Vector2((gx - gy) * TILE_W / 2.0, (gx + gy) * TILE_H / 2.0)

func screen_to_cell(px: float, py: float) -> Vector2:
	var rx = (px - origin.x) / (TILE_W / 2.0)
	var ry = (py - origin.y) / (TILE_H / 2.0)
	return Vector2(round((rx + ry) / 2.0), round((ry - rx) / 2.0))

func _process(delta):
	if screen != "PLAYING": return
	
	# Tweening
	var changed = false
	for u in state.allies:
		var key = "a" + str(u.id)
		var target = cell_to_screen(u.pos[0], u.pos[1])
		visual_pos[key] = visual_pos[key].lerp(target, 15.0 * delta)
		if visual_pos[key].distance_to(target) > 0.1: changed = true
	for u in state.enemies:
		var key = "e" + str(u.id)
		var target = cell_to_screen(u.pos[0], u.pos[1])
		visual_pos[key] = visual_pos[key].lerp(target, 15.0 * delta)
		if visual_pos[key].distance_to(target) > 0.1: changed = true
	
	# Effects
	for i in range(effects.size() - 1, -1, -1):
		effects[i].pos.y -= 60.0 * delta
		effects[i].life -= delta
		if effects[i].life <= 0:
			effects.remove_at(i)
		else:
			changed = true
			
	# Flash
	for k in flashes.keys():
		flashes[k] -= delta
		if flashes[k] <= 0:
			flashes.erase(k)
			changed = true
			
	if changed: queue_redraw()

func _unhandled_input(event):
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		var mp = event.position
		if screen == "MENU":
			for i in range(levels.size()):
				var rect = Rect2(120, 150 + i * 80, 400, 60)
				if rect.has_point(mp):
					pending_idx = i
					screen = "BRIEFING"
					queue_redraw()
					return
		elif screen == "BRIEFING":
			load_mission(pending_idx)
			return
		elif screen == "PLAYING":
			var cell = screen_to_cell(mp.x, mp.y)
			var gx = int(cell.x)
			var gy = int(cell.y)
			
			if gx < 0 or gx >= state.gridSize or gy < 0 or gy >= state.gridSize: return
			
			# Select Ally
			var clicked_ally = null
			for a in state.allies:
				if a.hp > 0 and a.pos[0] == gx and a.pos[1] == gy:
					clicked_ally = a
					break
			
			if clicked_ally:
				selected_unit_id = clicked_ally.id
				queue_redraw()
				return
			
			if selected_unit_id != null:
				# Attack or Move
				var ally = null
				for a in state.allies:
					if a.id == selected_unit_id: ally = a; break
				
				var clicked_enemy = null
				for e in state.enemies:
					if e.hp > 0 and e.pos[0] == gx and e.pos[1] == gy:
						clicked_enemy = e
						break
				
				if clicked_enemy:
					var dist = abs(ally.pos[0] - gx) + abs(ally.pos[1] - gy)
					var r = ally.get("range", 1)
					if dist >= 1 and dist <= r:
						perform_action({"unit": selected_unit_id, "type": "attack"})
						return
				else:
					# Move
					var dist = abs(ally.pos[0] - gx) + abs(ally.pos[1] - gy)
					if dist == 1:
						var dir = [gx - ally.pos[0], gy - ally.pos[1]]
						perform_action({"unit": selected_unit_id, "type": "move", "dir": dir})
						return
		elif screen == "RESULT":
			var btn_next = Rect2(220, 450, 200, 50)
			var btn_retry = Rect2(120, 510, 180, 50)
			var btn_menu = Rect2(320, 510, 180, 50)
			if btn_next.has_point(mp):
				var next = (current_mission_idx + 1) % levels.size()
				if next == 0: screen = "MENU"
				else: pending_idx = next; screen = "BRIEFING"
				queue_redraw()
			elif btn_retry.has_point(mp):
				load_mission(current_mission_idx)
			elif btn_menu.has_point(mp):
				screen = "MENU"
				queue_redraw()

	if event is InputEventKey and event.pressed:
		if event.keycode == KEY_R and screen == "PLAYING": load_mission(current_mission_idx)
		if event.keycode == KEY_N: screen = "MENU"; queue_redraw()

func perform_action(action):
	var hp_before = {}
	for u in state.allies: hp_before["a" + str(u.id)] = u.hp
	for u in state.enemies: hp_before["e" + str(u.id)] = u.hp
	
	var res = rules.update_state(state, action)
	state.status = res
	
	# HP change effects
	for u in state.allies:
		var key = "a" + str(u.id)
		var diff = u.hp - hp_before[key]
		if diff != 0:
			spawn_float_text(u.pos, str(int(round(diff))), diff > 0)
			if diff < 0: flashes[key] = 0.2
	for u in state.enemies:
		var key = "e" + str(u.id)
		var diff = u.hp - hp_before[key]
		if diff != 0:
			spawn_float_text(u.pos, str(int(round(diff))), diff > 0)
			if diff < 0: flashes[key] = 0.2
			
	if state.status != "PLAYING":
		screen = "RESULT"
	
	selected_unit_id = null
	queue_redraw()

func spawn_float_text(pos, text, is_heal):
	effects.append({
		"type": "text",
		"pos": cell_to_screen(pos[0], pos[1]) + Vector2(0, -20),
		"text": ( "+" if is_heal else "" ) + text,
		"color": Color.GREEN if is_heal else Color.RED,
		"life": 1.0
	})

func _draw():
	if screen == "MENU":
		draw_rect(Rect2(0,0,640,640), Color(0.1, 0.1, 0.15))
		draw_string(font, Vector2(320, 80), "SQUAD MISSION", HORIZONTAL_ALIGNMENT_CENTER, -1, 32, Color.WHITE)
		for i in range(levels.size()):
			var rect = Rect2(120, 150 + i * 80, 400, 60)
			draw_rect(rect, Color(0.2, 0.2, 0.3))
			draw_string(font, rect.position + Vector2(10, 25), levels[i].name, HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Color.WHITE)
			draw_string(font, rect.position + Vector2(10, 45), levels[i].desc, HORIZONTAL_ALIGNMENT_LEFT, -1, 14, Color(0.8, 0.8, 0.8))
	
	elif screen == "BRIEFING":
		draw_rect(Rect2(0,0,640,640), Color(0,0,0,0.8))
		var rect = Rect2(100, 150, 440, 300)
		draw_rect(rect, Color(0.1, 0.1, 0.2, 0.9))
		var story = levels[pending_idx].story.briefing
		var lines = story.split("\n")
		for i in range(lines.size()):
			draw_string(font, rect.position + Vector2(20, 40 + i * 24), lines[i], HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color.WHITE)
		draw_string(font, Vector2(320, 500), "Tap to Start", HORIZONTAL_ALIGNMENT_CENTER, -1, 18, Color.YELLOW)
		
	elif screen == "PLAYING":
		# HUD
		draw_rect(Rect2(0,0,640,36), Color(0,0,0,0.5))
		draw_string(font, Vector2(20, 24), levels[current_mission_idx].name + " · Turn " + str(state.turn), HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color.WHITE)
		
		# Floor
		var tone = tones[current_mission_idx % tones.size()]
		for gx in range(state.gridSize):
			for gy in range(state.gridSize):
				var c = cell_to_screen(gx, gy)
				var pts = PackedVector2Array([
					c + Vector2(0, -TILE_H/2),
					c + Vector2(TILE_W/2, 0),
					c + Vector2(0, TILE_H/2),
					c + Vector2(-TILE_W/2, 0)
				])
				var var_tone = tone + Color((gx*7+gy*13)%5 * 0.01, (gx*7+gy*13)%5 * 0.01, (gx*7+gy*13)%5 * 0.01, 0)
				draw_colored_polygon(pts, var_tone)
				var line_pts = PackedVector2Array(pts)
				line_pts.append(pts[0])
				draw_polyline(line_pts, Color(0,0,0,0.15), 1.0)
		
		# Highlights
		if selected_unit_id != null:
			var ally = null
			for a in state.allies: if a.id == selected_unit_id: ally = a; break
			
			# Selection
			var sc = cell_to_screen(ally.pos[0], ally.pos[1])
			var spts = PackedVector2Array([sc+Vector2(0,-TILE_H/2), sc+Vector2(TILE_W/2,0), sc+Vector2(0,TILE_H/2), sc+Vector2(-TILE_W/2,0)])
			var slpts = PackedVector2Array(spts); slpts.append(spts[0])
			draw_polyline(slpts, Color.YELLOW, 2.0)
			
			# Valid Moves & Attacks
			for gx in range(state.gridSize):
				for gy in range(state.gridSize):
					var dist = abs(ally.pos[0] - gx) + abs(ally.pos[1] - gy)
					var c = cell_to_screen(gx, gy)
					var hpts = PackedVector2Array([c+Vector2(0,-TILE_H/2), c+Vector2(TILE_W/2,0), c+Vector2(0,TILE_H/2), c+Vector2(-TILE_W/2,0)])
					
					var is_enemy = false
					for e in state.enemies: if e.hp > 0 and e.pos[0] == gx and e.pos[1] == gy: is_enemy = true; break
					
					if is_enemy and dist >= 1 and dist <= ally.get("range", 1):
						var hlpts = PackedVector2Array(hpts); hlpts.append(hpts[0])
						draw_polyline(hlpts, Color.RED, 2.0)
					elif not is_enemy:
						var occ = false
						for a_o in state.allies: if a_o.hp > 0 and a_o.pos[0] == gx and a_o.pos[1] == gy: occ = true; break
						if not occ and dist == 1:
							draw_colored_polygon(hpts, Color(0, 1, 0, 0.3))

		# Depth Sorted Units
		var render_list = []
		for u in state.allies: render_list.append({"type":"u", "z":u.pos[0]+u.pos[1], "unit":u, "side":"a"})
		for u in state.enemies: render_list.append({"type":"u", "z":u.pos[0]+u.pos[1], "unit":u, "side":"e"})
		render_list.sort_custom(func(a, b): return a.z < b.z)
		
		for item in render_list:
			var u = item.unit
			var side = item.side
			var key = side + str(u.id)
			var c = visual_pos[key]
			
			# Shadow
			var rx = TILE_W * 0.22
			var ry = TILE_H * 0.18
			var shpts = PackedVector2Array()
			for i in range(16):
				var t = TAU * i / 16.0
				shpts.append(c + Vector2(cos(t)*rx, sin(t)*ry))
			draw_colored_polygon(shpts, Color(0,0,0,0.22))
			
			# Sprite
			var tex = textures["monster"] if side == "e" else (textures["mage"] if u.get("range", 1) > 1 else textures["knight"])
			var tw = TILE_W * 1.1
			var th = tex.get_height() * (tw / tex.get_width())
			var rect = Rect2(c.x - tw/2, c.y - th, tw, th)
			var color = Color.WHITE
			if u.hp <= 0: color = Color(0.3, 0.3, 0.3, 0.6)
			elif flashes.has(key): color = Color(1, 0.2, 0.2)
			draw_texture_rect(tex, rect, false, color)
			
			# HP Bar
			var hp_max = max_hp.get(key, 10)
			var bar_w = tw * 0.6
			var bar_h = 4.0
			var bar_pos = Vector2(c.x - bar_w/2, c.y - th - 6)
			draw_rect(Rect2(bar_pos, Vector2(bar_w, bar_h)), Color(0,0,0,0.5))
			var ratio = clamp(u.hp / hp_max, 0.0, 1.0)
			var bar_color = Color.GREEN if side == "a" else Color.RED
			draw_rect(Rect2(bar_pos, Vector2(bar_w * ratio, bar_h)), bar_color)
			if u.hp <= 0:
				draw_string(font, bar_pos + Vector2(bar_w/2 - 4, -2), "X", HORIZONTAL_ALIGNMENT_CENTER, -1, 12, Color.WHITE)
		
		# Floating Effects
		for ef in effects:
			var p = ef.pos
			draw_string(font, p + Vector2(-1, 0), ef.text, HORIZONTAL_ALIGNMENT_LEFT, -1, 20, Color.BLACK)
			draw_string(font, p + Vector2(1, 0), ef.text, HORIZONTAL_ALIGNMENT_LEFT, -1, 20, Color.BLACK)
			draw_string(font, p + Vector2(0, -1), ef.text, HORIZONTAL_ALIGNMENT_LEFT, -1, 20, Color.BLACK)
			draw_string(font, p + Vector2(0, 1), ef.text, HORIZONTAL_ALIGNMENT_LEFT, -1, 20, Color.BLACK)
			draw_string(font, p, ef.text, HORIZONTAL_ALIGNMENT_LEFT, -1, 20, ef.color)

	elif screen == "RESULT":
		draw_rect(Rect2(0,0,640,640), Color(0,0,0,0.6))
		var is_win = state.status == "VICTORY"
		var story = levels[current_mission_idx].story.victory if is_win else levels[current_mission_idx].story.defeat
		draw_string(font, Vector2(320, 200), "MISSION " + ("SUCCESS" if is_win else "FAILED"), HORIZONTAL_ALIGNMENT_CENTER, -1, 32, Color.WHITE)
		
		var lines = story.split("\n")
		for i in range(lines.size()):
			draw_string(font, Vector2(320, 260 + i * 24), lines[i], HORIZONTAL_ALIGNMENT_CENTER, -1, 16, Color.WHITE)
		
		if is_win:
			var btn = Rect2(220, 450, 200, 50)
			draw_rect(btn, Color(0.2, 0.5, 0.2))
			draw_string(font, Vector2(320, 480), "Next Mission", HORIZONTAL_ALIGNMENT_CENTER, -1, 18, Color.WHITE)
		else:
			var btn_r = Rect2(120, 510, 180, 50)
			var btn_m = Rect2(320, 510, 180, 50)
			draw_rect(btn_r, Color(0.5, 0.2, 0.2))
			draw_string(font, Vector2(210, 535), "Retry", HORIZONTAL_ALIGNMENT_CENTER, -1, 18, Color.WHITE)
			draw_rect(btn_m, Color(0.3, 0.3, 0.3))
			draw_string(font, Vector2(410, 535), "Menu", HORIZONTAL_ALIGNMENT_CENTER, -1, 18, Color.WHITE)
