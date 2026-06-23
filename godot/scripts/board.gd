# 미션 선택부터 전투 플레이까지 처리하는 메인 보드 스크립트
extends Node2D

var rules
var levels = []
var font
var tex_floor = null
var tex_floor_vars = []
var tex_knight = null
var tex_mage = null
var tex_monster = null

var screen = "MENU"
var state = {}
var selected_unit_id = null
var pending_idx = 0
var current_mission_idx = 0

# 표시 전용 데이터
var max_hps = {}
var visual_pos = {}
var flashes = {}
var floating_texts = []

func _ready():
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	rules = load("res://scripts/rules.gd").new()
	font = load("res://assets/fonts/NanumGothic-Regular.ttf")
	
	var file = FileAccess.open("res://data/squad_levels.json", FileAccess.READ)
	if file:
		levels = JSON.parse_string(file.get_as_text())
	
	tex_floor = load("res://assets/tinydungeon/Tiles/tile_0048.png")
	tex_floor_vars = [
		load("res://assets/tinydungeon/Tiles/tile_0049.png"),
		load("res://assets/tinydungeon/Tiles/tile_0050.png"),
		load("res://assets/tinydungeon/Tiles/tile_0051.png")
	]
	tex_knight = load("res://assets/tinydungeon/Tiles/tile_0096.png")
	tex_mage = load("res://assets/tinydungeon/Tiles/tile_0084.png")
	tex_monster = load("res://assets/tinydungeon/Tiles/tile_0108.png")
	
	set_process(true)

func load_mission(idx):
	current_mission_idx = idx
	var init = levels[idx]["initialState"]
	state = JSON.parse_string(JSON.stringify(init))
	state["turn"] = 0
	state["status"] = "PLAYING"
	
	selected_unit_id = null
	screen = "PLAYING"
	
	# 표시 데이터 초기화
	max_hps = {}
	visual_pos = {}
	flashes = {}
	floating_texts = []
	
	for u in state["allies"]:
		var key = "a" + str(u["id"])
		max_hps[key] = u["hp"]
		visual_pos[key] = Vector2(u["pos"][0], u["pos"][1])
	for u in state["enemies"]:
		var key = "e" + str(u["id"])
		max_hps[key] = u["hp"]
		visual_pos[key] = Vector2(u["pos"][0], u["pos"][1])
	
	queue_redraw()

func _unhandled_input(event):
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		var pos = event.position
		if screen == "MENU":
			for i in range(levels.size()):
				var btn_rect = Rect2(120, 100 + i * 80, 400, 60)
				if btn_rect.has_point(pos):
					pending_idx = i
					screen = "BRIEFING"
					queue_redraw()
					return
		
		elif screen == "BRIEFING":
			load_mission(pending_idx)
			return
		
		elif screen == "PLAYING":
			var gridSize = state.get("gridSize", 8)
			var cell_size = 640.0 / gridSize
			var gx = int(pos.x / cell_size)
			var gy = int(pos.y / cell_size)
			
			if gx < 0 or gx >= gridSize or gy < 0 or gy >= gridSize: return
			
			# 아군 선택 체크
			var clicked_ally = null
			for a in state["allies"]:
				if a["hp"] > 0 and a["pos"][0] == gx and a["pos"][1] == gy:
					clicked_ally = a
					break
			
			if clicked_ally:
				selected_unit_id = clicked_ally["id"]
				queue_redraw()
				return
			
			# 선택된 아군이 있을 때 행동
			if selected_unit_id != null:
				var ally = null
				for a in state["allies"]:
					if a["id"] == selected_unit_id: ally = a; break
				if not ally or ally["hp"] <= 0: return
				
				# 대상 확인 (적군)
				var target_enemy = null
				for e in state["enemies"]:
					if e["hp"] > 0 and e["pos"][0] == gx and e["pos"][1] == gy:
						target_enemy = e
						break
				
				if target_enemy:
					var dist = abs(ally["pos"][0] - gx) + abs(ally["pos"][1] - gy)
					var rng = ally.get("range", 1)
					if dist >= 1 and dist <= rng:
						execute_action({"unit": selected_unit_id, "type": "attack"})
						return
				else:
					# 빈 칸 이동
					var dist = abs(ally["pos"][0] - gx) + abs(ally["pos"][1] - gy)
					if dist == 1:
						var dx = gx - ally["pos"][0]
						var dy = gy - ally["pos"][1]
						execute_action({"unit": selected_unit_id, "type": "move", "dir": [dx, dy]})
						return
		
		elif screen == "RESULT":
			var res_rect = Rect2(220, 400, 200, 50) # 기본 버튼 영역
			if res_rect.has_point(pos):
				if state["status"] == "VICTORY":
					if current_mission_idx < levels.size() - 1:
						pending_idx = current_mission_idx + 1
						screen = "BRIEFING"
					else:
						screen = "MENU"
				else:
					load_mission(current_mission_idx)
				queue_redraw()

	elif event is InputEventKey and event.pressed:
		if event.keycode == KEY_R and screen == "PLAYING":
			load_mission(current_mission_idx)
		elif event.keycode == KEY_N:
			screen = "MENU"
		queue_redraw()

func execute_action(action):
	# HP 스냅샷
	var hp_before = {}
	for a in state["allies"]: hp_before["a"+str(a["id"])] = a["hp"]
	for e in state["enemies"]: hp_before["e"+str(e["id"])] = e["hp"]
	
	var result = rules.update_state(state, action)
	state["status"] = result
	
	# 변화 감지 및 이펙트 생성
	for a in state["allies"]:
		var key = "a"+str(a["id"])
		var diff = a["hp"] - hp_before.get(key, a["hp"])
		if diff != 0:
			create_floating_text(key, diff)
			flashes[key] = 0.2
	for e in state["enemies"]:
		var key = "e"+str(e["id"])
		var diff = e["hp"] - hp_before.get(key, e["hp"])
		if diff != 0:
			create_floating_text(key, diff)
			flashes[key] = 0.2
			
	if state["status"] == "VICTORY" or state["status"] == "DEFEAT":
		screen = "RESULT"
	
	selected_unit_id = null
	queue_redraw()

func create_floating_text(unit_key, diff):
	var pos = visual_pos.get(unit_key, Vector2.ZERO)
	floating_texts.append({
		"key": unit_key,
		"text": ("+" if diff > 0 else "") + str(diff),
		"color": Color.GREEN if diff > 0 else Color.RED,
		"life": 0.8,
		"offset": 0.0
	})

func _process(delta):
	if screen != "PLAYING": return
	
	# 위치 보간
	for u in state["allies"]:
		var key = "a"+str(u["id"])
		visual_pos[key] = visual_pos[key].lerp(Vector2(u["pos"][0], u["pos"][1]), 20 * delta)
	for u in state["enemies"]:
		var key = "e"+str(u["id"])
		visual_pos[key] = visual_pos[key].lerp(Vector2(u["pos"][0], u["pos"][1]), 20 * delta)
	
	# 플래시 타이머
	var flash_keys = flashes.keys()
	for k in flash_keys:
		flashes[k] -= delta
		if flashes[k] <= 0: flashes.erase(k)
	
	# 플로팅 텍스트
	var i = floating_texts.size() - 1
	while i >= 0:
		var t = floating_texts[i]
		t["life"] -= delta
		t["offset"] += delta * 60.0
		if t["life"] <= 0: floating_texts.remove_at(i)
		i -= 1
	
	queue_redraw()

func _draw():
	if screen == "MENU":
		draw_string(font, Vector2(220, 50), "SQUAD MISSION", HORIZONTAL_ALIGNMENT_CENTER, 640, 32, Color.WHITE)
		for i in range(levels.size()):
			var rect = Rect2(120, 100 + i * 80, 400, 60)
			draw_rect(rect, Color(0.2, 0.2, 0.2, 0.8), true)
			draw_rect(rect, Color.WHITE, false, 2.0)
			draw_string(font, rect.position + Vector2(10, 25), levels[i]["name"], HORIZONTAL_ALIGNMENT_LEFT, -1, 20, Color.YELLOW)
			draw_string(font, rect.position + Vector2(10, 45), levels[i]["desc"], HORIZONTAL_ALIGNMENT_LEFT, -1, 14, Color.LIGHT_GRAY)
	
	elif screen == "BRIEFING":
		draw_rect(Rect2(100, 100, 440, 300), Color(0, 0, 0, 0.7), true)
		draw_rect(Rect2(100, 100, 440, 300), Color.WHITE, false, 2.0)
		var story = levels[pending_idx]["story"]["briefing"]
		var lines = story.split("\n")
		for i in range(lines.size()):
			draw_string(font, Vector2(120, 140 + i * 30), lines[i], HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Color.WHITE)
		draw_string(font, Vector2(320, 360), "Tap to Start", HORIZONTAL_ALIGNMENT_CENTER, 640, 20, Color.YELLOW)
	
	elif screen == "PLAYING":
		var gridSize = state.get("gridSize", 8)
		var cell_size = 640.0 / gridSize
		
		# HUD
		draw_rect(Rect2(0, 0, 640, 40), Color(0, 0, 0, 0.5), true)
		var title = levels[current_mission_idx]["name"] + "  |  Turn: " + str(state["turn"])
		draw_string(font, Vector2(20, 25), title, HORIZONTAL_ALIGNMENT_LEFT, -1, 20, Color.WHITE)
		
		# Map Tones
		var tones = [Color.WHITE, Color(0.7, 0.8, 0.9), Color(0.6, 0.5, 0.7), Color(0.9, 0.8, 0.5)]
		var tone = tones[current_mission_idx % tones.size()]
		
		for x in range(gridSize):
			for y in range(gridSize):
				var rect = Rect2(x * cell_size, y * cell_size, cell_size, cell_size)
				# 바닥 타일 변주
				var hash_val = (x * 7 + y * 13) % 10
				var tex = tex_floor
				if hash_val == 0: tex = tex_floor_vars[0]
				elif hash_val == 1: tex = tex_floor_vars[1]
				elif hash_val == 2: tex = tex_floor_vars[2]
				
				var cell_tone = tone
				cell_tone.v += (hash_val - 5) * 0.01
				draw_texture_rect(tex, rect, false, cell_tone)
				draw_rect(rect, Color(0, 0, 0, 0.15), false, 1.0)
		
		# 하이라이트
		if selected_unit_id != null:
			var ally = null
			for a in state["allies"]:
				if a["id"] == selected_unit_id: ally = a; break
			if ally:
				var rng = ally.get("range", 1)
				for x in range(gridSize):
					for y in range(gridSize):
						var dist = abs(ally["pos"][0] - x) + abs(ally["pos"][1] - y)
						var rect = Rect2(x * cell_size, y * cell_size, cell_size, cell_size)
						if dist == 1:
							var occ = false
							for u in state["allies"]: if u["hp"] > 0 and u["pos"][0] == x and u["pos"][1] == y: occ = true
							for u in state["enemies"]: if u["hp"] > 0 and u["pos"][0] == x and u["pos"][1] == y: occ = true
							if not occ: draw_rect(rect, Color(0, 1, 0, 0.3), true)
						if dist >= 1 and dist <= rng:
							var enemy_here = false
							for e in state["enemies"]: if e["hp"] > 0 and e["pos"][0] == x and e["pos"][1] == y: enemy_here = true
							if enemy_here: draw_rect(rect, Color(1, 0, 0, 0.4), false, 3.0)

		# 유닛 렌더링
		var render_units = []
		for a in state["allies"]: render_units.append({"key":"a"+str(a["id"]), "u":a, "side":"A"})
		for e in state["enemies"]: render_units.append({"key":"e"+str(e["id"]), "u":e, "side":"E"})
		
		for item in render_units:
			var u = item["u"]
			var key = item["key"]
			var vpos = visual_pos.get(key, Vector2(u["pos"][0], u["pos"][1]))
			var rect = Rect2(vpos.x * cell_size + (cell_size * 0.1), vpos.y * cell_size + (cell_size * 0.1), cell_size * 0.8, cell_size * 0.8)
			
			var tex = tex_monster
			if item["side"] == "A":
				tex = tex_mage if u.get("range", 1) > 1 else tex_knight
			
			var mod = Color.WHITE
			if u["hp"] <= 0: mod = Color(0.3, 0.3, 0.3, 0.5)
			elif flashes.has(key): mod = Color(1, 0.3, 0.3)
			
			draw_texture_rect(tex, rect, false, mod)
			if u["hp"] <= 0:
				draw_string(font, rect.position + Vector2(cell_size*0.3, cell_size*0.5), "X", HORIZONTAL_ALIGNMENT_LEFT, -1, 24, Color.RED)
			else:
				# HP Bar
				var bar_bg = Rect2(rect.position.x, rect.end.y - 6, rect.size.x, 4)
				draw_rect(bar_bg, Color.BLACK, true)
				var hp_ratio = float(u["hp"]) / max_hps.get(key, 1.0)
				var bar_fg = Rect2(bar_bg.position.x, bar_bg.position.y, bar_bg.size.x * hp_ratio, 4)
				draw_rect(bar_fg, Color.GREEN if item["side"] == "A" else Color.RED, true)
			
			if item["side"] == "A" and u["id"] == selected_unit_id:
				draw_rect(rect.grow(4), Color.YELLOW, false, 2.0)

		# 플로팅 텍스트
		for t in floating_texts:
			var vpos = visual_pos.get(t["key"], Vector2.ZERO)
			var text_pos = Vector2(vpos.x * cell_size + cell_size*0.3, vpos.y * cell_size + cell_size*0.2) - Vector2(0, t["offset"])
			# 외곽선
			for dx in [-1, 1]:
				for dy in [-1, 1]:
					draw_string(font, text_pos + Vector2(dx, dy), t["text"], HORIZONTAL_ALIGNMENT_LEFT, -1, 22, Color.BLACK)
			draw_string(font, text_pos, t["text"], HORIZONTAL_ALIGNMENT_LEFT, -1, 22, t["color"])

	elif screen == "RESULT":
		draw_rect(Rect2(0, 0, 640, 640), Color(0, 0, 0, 0.6), true)
		var res_text = "VICTORY!" if state["status"] == "VICTORY" else "DEFEAT..."
		var res_col = Color.YELLOW if state["status"] == "VICTORY" else Color.ORANGE
		draw_string(font, Vector2(320, 200), res_text, HORIZONTAL_ALIGNMENT_CENTER, 640, 48, res_col)
		
		var story_text = ""
		if state["status"] == "VICTORY": story_text = levels[current_mission_idx]["story"]["victory"]
		else: story_text = levels[current_mission_idx]["story"]["defeat"]
		
		var lines = story_text.split("\n")
		for i in range(lines.size()):
			draw_string(font, Vector2(320, 260 + i * 30), lines[i], HORIZONTAL_ALIGNMENT_CENTER, 640, 18, Color.WHITE)
		
		var btn_text = "Next Mission" if state["status"] == "VICTORY" else "Retry"
		var btn_rect = Rect2(220, 400, 200, 50)
		draw_rect(btn_rect, Color(0.2, 0.2, 0.2), true)
		draw_rect(btn_rect, Color.WHITE, false, 2.0)
		draw_string(font, Vector2(320, 430), btn_text, HORIZONTAL_ALIGNMENT_CENTER, 640, 20, Color.WHITE)
		
		if state["status"] == "DEFEAT":
			var menu_rect = Rect2(220, 460, 200, 50)
			draw_rect(menu_rect, Color(0.2, 0.2, 0.2), true)
			draw_rect(menu_rect, Color.WHITE, false, 2.0)
			draw_string(font, Vector2(320, 490), "Back to Menu", HORIZONTAL_ALIGNMENT_CENTER, 640, 20, Color.WHITE)
