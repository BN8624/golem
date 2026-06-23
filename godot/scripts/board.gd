# 미션 선택, 서사 진행 및 아이소메트릭 전투를 제어하는 보드 스크립트
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
var max_hp_snapshot = {}
var effects = [] # {type: "text", pos: Vector2, value: str, color: Color, life: float}
var flashes = {} # {"a1": {color: Color, life: float}}
var tweens = {} # {"a1": {from: Vector2, to: Vector2, life: float}}

var TILE_W = 64.0
var TILE_H = 32.0
var origin = Vector2(320, 120)
var tones = [Color(0.7, 0.7, 0.7), Color(0.5, 0.6, 0.7), Color(0.5, 0.4, 0.6), Color(0.7, 0.6, 0.4)]

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
	
	# Max HP snapshot for HP bars
	max_hp_snapshot = {}
	for u in state["allies"]:
		max_hp_snapshot["a" + str(u["id"])] = u["hp"]
	for u in state["enemies"]:
		max_hp_snapshot["e" + str(u["id"])] = u["hp"]
	
	# Initialize tweens to current pos
	tweens.clear()
	for u in state["allies"]:
		var p = cell_to_screen(u["pos"][0], u["pos"][1])
		tweens["a" + str(u["id"])] = {"from": p, "to": p, "life": 0.0}
	for u in state["enemies"]:
		var p = cell_to_screen(u["pos"][0], u["pos"][1])
		tweens["e" + str(u["id"])] = {"from": p, "to": p, "life": 0.0}
	
	# Dynamic scale based on gridSize
	TILE_W = 600.0 / state["gridSize"]
	TILE_H = TILE_W / 2.0
	origin = Vector2(320, 120)
	
	queue_redraw()

func cell_to_screen(gx: int, gy: int) -> Vector2:
	return origin + Vector2((gx - gy) * TILE_W / 2.0, (gx + gy) * TILE_H / 2.0)

func screen_to_cell(px: float, py: float) -> Vector2:
	var rx = (px - origin.x) / (TILE_W / 2.0)
	var ry = (py - origin.y) / (TILE_H / 2.0)
	return Vector2(round((rx + ry) / 2.0), round((ry - rx) / 2.0))

func _unhandled_input(event):
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		var m_pos = event.position
		if screen == "MENU":
			for i in range(levels.size()):
				var rect = Rect2(220, 100 + i * 70, 200, 50)
				if rect.has_point(m_pos):
					pending_idx = i
					screen = "BRIEFING"
					queue_redraw()
					return
		elif screen == "BRIEFING":
			load_mission(pending_idx)
			queue_redraw()
		elif screen == "PLAYING":
			var cell = screen_to_cell(m_pos.x, m_pos.y)
			var gx = int(cell.x)
			var gy = int(cell.y)
			_handle_play_click(gx, gy)
		elif screen == "RESULT":
			if state["status"] == "VICTORY":
				if pending_idx < levels.size() - 1:
					pending_idx += 1
					screen = "BRIEFING"
				else:
					screen = "MENU"
			else:
				load_mission(current_mission_idx)
			queue_redraw()
	
	if event is InputEventKey and event.pressed:
		if event.keycode == KEY_R and screen == "PLAYING":
			load_mission(current_mission_idx)
		elif event.keycode == KEY_N:
			screen = "MENU"
		queue_redraw()

func _handle_play_click(gx, gy):
	if gx < 0 or gx >= state["gridSize"] or gy < 0 or gy >= state["gridSize"]:
		return
	
	# Check if ally is clicked
	var clicked_ally = null
	for a in state["allies"]:
		if a["hp"] > 0 and a["pos"][0] == gx and a["pos"][1] == gy:
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
		if not ally: return

		var clicked_enemy = null
		for e in state["enemies"]:
			if e["hp"] > 0 and e["pos"][0] == gx and e["pos"][1] == gy:
				clicked_enemy = e
				break
		
		var dist = abs(ally["pos"][0] - gx) + abs(ally["pos"][1] - gy)
		var range_val = ally.get("range", 1)
		
		if clicked_enemy and dist >= 1 and dist <= range_val:
			_perform_action({"unit": selected_unit_id, "type": "attack"})
		elif not clicked_enemy and dist == 1:
			# Check if any other unit occupies this
			var occupied = false
			for u in state["allies"] + state["enemies"]:
				if u["hp"] > 0 and u["pos"][0] == gx and u["pos"][1] == gy:
					occupied = true
					break
			if not occupied:
				var dir = [gx - ally["pos"][0], gy - ally["pos"][1]]
				_perform_action({"unit": selected_unit_id, "type": "move", "dir": dir})
		else:
			selected_unit_id = null
			queue_redraw()

func _perform_action(action):
	var old_hp = {}
	for u in state["allies"]: old_hp["a" + str(u["id"])] = u["hp"]
	for u in state["enemies"]: old_hp["e" + str(u["id"])] = u["hp"]
	
	var old_pos = {}
	for u in state["allies"]: old_pos["a" + str(u["id"])] = Vector2(u["pos"][0], u["pos"][1])
	for u in state["enemies"]: old_pos["e" + str(u["id"])] = Vector2(u["pos"][0], u["pos"][1])

	var res_status = rules.update_state(state, action)
	state["status"] = res_status
	
	# Create effects & tweens
	for u in state["allies"]:
		var uid = "a" + str(u["id"])
		var diff = u["hp"] - old_hp.get(uid, u["hp"])
		if diff != 0:
			_add_float_text(u["pos"], str(diff), diff > 0)
			flashes[uid] = {"color": Color(1, 0.2, 0.2), "life": 0.2}
		var new_p = cell_to_screen(u["pos"][0], u["pos"][1])
		if new_p != old_pos[uid]:
			tweens[uid] = {"from": cell_to_screen(old_pos[uid].x, old_pos[uid].y), "to": new_p, "life": 0.15}
			
	for u in state["enemies"]:
		var uid = "e" + str(u["id"])
		var diff = u["hp"] - old_hp.get(uid, u["hp"])
		if diff != 0:
			_add_float_text(u["pos"], str(diff), diff > 0)
			flashes[uid] = {"color": Color(1, 0.2, 0.2), "life": 0.2}
		var new_p = cell_to_screen(u["pos"][0], u["pos"][1])
		if new_p != old_pos[uid]:
			tweens[uid] = {"from": cell_to_screen(old_pos[uid].x, old_pos[uid].y), "to": new_p, "life": 0.15}

	if res_status != "PLAYING":
		screen = "RESULT"
	
	selected_unit_id = null
	queue_redraw()

func _add_float_text(pos_grid, text, is_heal):
	var p = cell_to_screen(pos_grid[0], pos_grid[1])
	effects.append({"type": "text", "pos": p, "text": text, "color": Color.GREEN if is_heal else Color.RED, "life": 0.6})

func _process(delta):
	var changed = false
	for e in effects:
		e.life -= delta
		e.pos.y -= 40 * delta
		changed = true
	effects = effects.filter(func(e): return e.life > 0)
	
	for uid in flashes:
		flashes[uid].life -= delta
		changed = true
	var flash_keys = flashes.keys()
	for k in flash_keys:
		if flashes[k].life <= 0: flashes.erase(k)
	
	for uid in tweens:
		tweens[uid].life -= delta
		changed = true
	var tween_keys = tweens.keys()
	for k in tween_keys:
		if tweens[k].life <= 0: tweens.erase(k)
		
	if changed:
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
	draw_string(font, Vector2(320, 50), "SQUAD MISSION", HORIZONTAL_ALIGNMENT_CENTER, -1, 24, Color.WHITE)
	for i in range(levels.size()):
		var rect = Rect2(220, 100 + i * 70, 200, 50)
		draw_rect(rect, Color(0.2, 0.2, 0.2, 0.8), true)
		draw_rect(rect, Color.WHITE, false, 1.0)
		draw_string(font, rect.position + Vector2(10, 20), levels[i]["name"], HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color.YELLOW)
		draw_string(font, rect.position + Vector2(10, 38), levels[i]["desc"], HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color.LIGHT_GRAY)

func _draw_briefing():
	var bg = Rect2(120, 80, 400, 300)
	draw_rect(bg, Color(0, 0, 0, 0.7), true)
	draw_rect(bg, Color.WHITE, false, 2.0)
	
	var story = levels[pending_idx]["story"].briefing
	var lines = story.split("\n")
	for i in range(lines.size()):
		draw_string(font, bg.position + Vector2(20, 40 + i * 25), lines[i], HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color.WHITE)
	
	draw_string(font, Vector2(320, 350), "탭하여 시작", HORIZONTAL_ALIGNMENT_CENTER, -1, 16, Color.YELLOW)

func _draw_playing():
	# HUD
	draw_rect(Rect2(0, 0, 640, 36), Color(0, 0, 0, 0.5), true)
	var title = levels[current_mission_idx]["name"] + " · Turn " + str(state["turn"])
	draw_string(font, Vector2(20, 22), title, HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color.WHITE)
	
	var tone = tones[current_mission_idx % tones.size()]
	var size = state["gridSize"]
	
	# Floor - Sorted for depth
	var cells = []
	for gx in range(size):
		for gy in range(size):
			cells.append(Vector2(gx, gy))
	cells.sort_custom(func(a, b): return (a.x + a.y) < (b.x + b.y))
	
	for c in cells:
		var gx = int(c.x)
		var gy = int(c.y)
		var cp = cell_to_screen(gx, gy)
		var pts = [
			cp + Vector2(0, -TILE_H/2),
			cp + Vector2(TILE_W/2, 0),
			cp + Vector2(0, TILE_H/2),
			cp + Vector2(-TILE_W/2, 0)
		]
		var var_tone = tone * (1.0 + (float((gx * 7 + gy * 13) % 5) - 2.0) * 0.04)
		draw_colored_polygon(pts, var_tone)
		draw_polyline(pts + [pts[0]], Color(0, 0, 0, 0.15), 1.0)
		
		# Highlights
		if selected_unit_id != null:
			var ally = null
			for a in state["allies"]:
				if a["id"] == selected_unit_id: ally = a; break
			if ally:
				var dist = abs(ally["pos"][0] - gx) + abs(ally["pos"][1] - gy)
				if gx == ally["pos"][0] and gy == ally["pos"][1]:
					draw_polyline(pts + [pts[0]], Color.YELLOW, 2.0)
				elif dist == 1:
					var occupied = false
					for u in state["allies"] + state["enemies"]:
						if u["hp"] > 0 and u["pos"][0] == gx and u["pos"][1] == gy: occupied = true; break
					if not occupied:
						draw_colored_polygon(pts, Color(0, 1, 0, 0.3))
				elif dist >= 1 and dist <= ally.get("range", 1):
					var enemy = null
					for e in state["enemies"]:
						if e["hp"] > 0 and e["pos"][0] == gx and e["pos"][1] == gy: enemy = e; break
					if enemy:
						draw_polyline(pts + [pts[0]], Color.RED, 2.0)

	# Units - Sorted for depth
	var units = []
	for a in state["allies"]: units.append({"u": a, "type": "a"})
	for e in state["enemies"]: units.append({"u": e, "type": "e"})
	units.sort_custom(func(a, b): return (a.u["pos"][0] + a.u["pos"][1]) < (b.u["pos"][0] + b.u["pos"][1]))
	
	for item in units:
		var u = item["u"]
		var uid = item["type"] + str(u["id"])
		var gx = int(u["pos"][0])
		var gy = int(u["pos"][1])
		var cp = cell_to_screen(gx, gy)
		
		# Tween position
		var draw_pos = cp
		if tweens.has(uid):
			var t = tweens[uid]
			var weight = 1.0 - (t.life / 0.15)
			draw_pos = t.from.lerp(t.to, weight)
		
		# Shadow
		draw_circle(draw_pos, TILE_W * 0.3, Color(0, 0, 0, 0.3))
		
		# Sprite
		var tex = textures["monster"]
		if item["type"] == "a":
			tex = textures["mage"] if u.get("range", 1) > 1 else textures["knight"]
		
		var sprite_rect = Rect2(draw_pos.x - textures["knight"].get_width()/2, draw_pos.y - textures["knight"].get_height(), textures["knight"].get_width(), textures["knight"].get_height())
		var modulate = Color.WHITE
		if u["hp"] <= 0:
			modulate = Color(0.4, 0.4, 0.4, 0.6)
		if flashes.has(uid):
			modulate = flashes[uid].color
			
		draw_texture_rect(tex, sprite_rect, false, modulate)
		if u["hp"] <= 0:
			draw_string(font, sprite_rect.position + Vector2(5, 15), "X", HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color.RED)
			
		# HP Bar
		var max_h = max_hp_snapshot.get(uid, u["hp"])
		var bar_w = TILE_W * 0.6
		var bar_h = 4.0
		var bar_pos = Vector2(draw_pos.x - bar_w/2, sprite_rect.position.y - 6)
		draw_rect(Rect2(bar_pos, Vector2(bar_w, bar_h)), Color(0, 0, 0, 0.5), true)
		if u["hp"] > 0:
			var fill_w = bar_w * (float(u["hp"]) / max_h)
			var fill_color = Color.GREEN if item["type"] == "a" else Color.RED
			draw_rect(Rect2(bar_pos, Vector2(fill_w, bar_h)), fill_color, true)

	# Effects
	for e in effects:
		if e.type == "text":
			var txt = e.text
			var p = e.pos
			draw_string(font, p + Vector2(-2, -2), txt, HORIZONTAL_ALIGNMENT_LEFT, -1, 22, Color.BLACK)
			draw_string(font, p + Vector2(2, 2), txt, HORIZONTAL_ALIGNMENT_LEFT, -1, 22, Color.BLACK)
			draw_string(font, p, txt, HORIZONTAL_ALIGNMENT_LEFT, -1, 22, e.color)

func _draw_result():
	var bg = Rect2(120, 100, 400, 200)
	draw_rect(bg, Color(0, 0, 0, 0.8), true)
	draw_rect(bg, Color.WHITE, false, 2.0)
	
	var story = levels[current_mission_idx]["story"]
	var text = story.victory if state["status"] == "VICTORY" else story.defeat
	var lines = text.split("\n")
	for i in range(lines.size()):
		draw_string(font, bg.position + Vector2(20, 50 + i * 25), lines[i], HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color.WHITE)
	
	var btn_txt = "다음 미션" if state["status"] == "VICTORY" else "다시 시도"
	var btn_rect = Rect2(220, 220, 200, 40)
	draw_rect(btn_rect, Color(0.3, 0.3, 0.3), true)
	draw_rect(btn_rect, Color.WHITE, false, 1.0)
	draw_string(font, btn_rect.position + Vector2(100, 25), btn_txt, HORIZONTAL_ALIGNMENT_CENTER, -1, 16, Color.YELLOW)
	
	var menu_rect = Rect2(220, 270, 200, 40)
	draw_rect(menu_rect, Color(0.2, 0.2, 0.2), true)
	draw_rect(menu_rect, Color.WHITE, false, 1.0)
	draw_string(font, menu_rect.position + Vector2(100, 25), "메뉴로", HORIZONTAL_ALIGNMENT_CENTER, -1, 16, Color.LIGHT_GRAY)
