# 미션 선택, 서사 진행 및 전술 전투 시스템을 제어하는 보드 스크립트
extends Node2D

var rules
var levels = []
var font
var screen = "MENU"
var state = {}
var selected_unit_id = null
var pending_idx = 0
var current_mission_idx = 0

# 에셋 캐시
var tex_floor = []
var tex_knight
var tex_mage
var tex_monster

# 이펙트 상태
var floating_texts = [] # {pos: Vector2, text: String, color: Color, life: float}
var flash_timers = {} # {"a1": 0.2, "e1": 0.1}

func _ready():
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	rules = load("res://scripts/rules.gd").new()
	font = load("res://assets/fonts/NanumGothic-Regular.ttf")
	
	var file = FileAccess.open("res://data/squad_levels.json", FileAccess.READ)
	levels = JSON.parse_string(file.get_as_text())
	
	# 텍스처 로드
	tex_floor = [
		load("res://assets/tinydungeon/Tiles/tile_0048.png"),
		load("res://assets/tinydungeon/Tiles/tile_0049.png"),
		load("res://assets/tinydungeon/Tiles/tile_0050.png"),
		load("res://assets/tinydungeon/Tiles/tile_0051.png")
	]
	tex_knight = load("res://assets/tinydungeon/Tiles/tile_0096.png")
	tex_mage = load("res://assets/tinydungeon/Tiles/tile_0084.png")
	tex_monster = load("res://assets/tinydungeon/Tiles/tile_0108.png")
	
	set_process(true)
	queue_redraw()

func _process(delta):
	# 플로팅 텍스트 업데이트
	for i in range(floating_texts.size() - 1, -1, -1):
		var ft = floating_texts[i]
		ft.life -= delta
		ft.pos.y -= delta * 30.0
		if ft.life <= 0:
			floating_texts.remove_at(i)
	
	# 플래시 타이머 업데이트
	for key in flash_timers.keys():
		flash_timers[key] -= delta
		if flash_timers[key] <= 0:
			flash_timers.erase(key)
	
	if floating_texts.size() > 0 or flash_timers.size() > 0:
		queue_redraw()

func load_mission(idx):
	current_mission_idx = idx
	var initialState = levels[idx].initialState
	state = JSON.parse_string(JSON.stringify(initialState))
	state.turn = 0
	state.status = "PLAYING"
	selected_unit_id = null
	screen = "PLAYING"
	queue_redraw()

func _unhandled_input(event):
	if not (event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT):
		return

	if screen == "MENU":
		for i in range(levels.size()):
			var rect = Rect2(120, 150 + i * 80, 400, 60)
			if rect.has_point(event.position):
				pending_idx = i
				screen = "BRIEFING"
				queue_redraw()
				return

	elif screen == "BRIEFING":
		load_mission(pending_idx)
		return

	elif screen == "PLAYING":
		var cell_size = 640.0 / state.gridSize
		var gx = int(event.position.x / cell_size)
		var gy = int(event.position.y / cell_size)
		
		if gx < 0 or gx >= state.gridSize or gy < 0 or gy >= state.gridSize:
			return

		# 아군 선택 확인
		var clicked_ally = null
		for a in state.allies:
			if a.hp > 0 and a.pos[0] == gx and a.pos[1] == gy:
				clicked_ally = a
				break
		
		if clicked_ally:
			selected_unit_id = clicked_ally.id
			queue_redraw()
			return

		# 액션 처리
		if selected_unit_id != null:
			var ally = null
			for a in state.allies:
				if a.id == selected_unit_id:
					ally = a
					break
			
			if ally and ally.hp > 0:
				var target_enemy = null
				for e in state.enemies:
					if e.hp > 0 and e.pos[0] == gx and e.pos[1] == gy:
						target_enemy = e
						break
				
				if target_enemy:
					# 공격 시도
					var dist = abs(ally.pos[0] - gx) + abs(ally.pos[1] - gy)
					var range_val = ally.get("range", 1)
					if dist >= 1 and dist <= range_val:
						execute_action({"unit": selected_unit_id, "type": "attack"})
						return
				else:
					# 이동 시도
					var dist = abs(ally.pos[0] - gx) + abs(ally.pos[1] - gy)
					if dist == 1:
						var dx = gx - ally.pos[0]
						var dy = gy - ally.pos[1]
						execute_action({"unit": selected_unit_id, "type": "move", "dir": [dx, dy]})
						return

	elif screen == "RESULT":
		# 버튼 판정
		if state.status == "VICTORY":
			var next_rect = Rect2(220, 400, 200, 50)
			if next_rect.has_point(event.position):
				var next_idx = current_mission_idx + 1
				if next_idx < levels.size():
					pending_idx = next_idx
					screen = "BRIEFING"
				else:
					screen = "MENU"
				queue_redraw()
		else:
			var retry_rect = Rect2(150, 400, 150, 50)
			var menu_rect = Rect2(340, 400, 150, 50)
			if retry_rect.has_point(event.position):
				load_mission(current_mission_idx)
			elif menu_rect.has_point(event.position):
				screen = "MENU"
			queue_redraw()

func execute_action(action):
	var hp_before = {}
	for a in state.allies: hp_before["a" + str(a.id)] = a.hp
	for e in state.enemies: hp_before["e" + str(e.id)] = e.hp
	
	var result_status = rules.update_state(state, action)
	state.status = result_status
	
	# 데미지/회복 이펙트 생성
	for a in state.allies:
		var diff = a.hp - hp_before.get("a" + str(a.id), a.hp)
		if diff != 0:
			spawn_float_text(a.pos, str(diff), Color.GREEN if diff > 0 else Color.RED)
			if diff < 0: flash_timers["a" + str(a.id)] = 0.2
	for e in state.enemies:
		var diff = e.hp - hp_before.get("e" + str(e.id), e.hp)
		if diff != 0:
			spawn_float_text(e.pos, str(diff), Color.GREEN if diff > 0 else Color.RED)
			if diff < 0: flash_timers["e" + str(e.id)] = 0.2
	
	if result_status != "PLAYING":
		screen = "RESULT"
	
	selected_unit_id = null
	queue_redraw()

func spawn_float_text(pos, text, color):
	var cell_size = 640.0 / state.gridSize
	floating_texts.append({
		"pos": Vector2(pos[0] * cell_size + cell_size/2, pos[1] * cell_size + cell_size/2),
		"text": text,
		"color": color,
		"life": 0.8
	})

func _draw():
	if screen == "MENU":
		draw_string(font, Vector2(240, 80), "SQUAD TACTICS", HORIZONTAL_ALIGNMENT_CENTER, -1, 32, Color.WHITE)
		for i in range(levels.size()):
			var rect = Rect2(120, 150 + i * 80, 400, 60)
			draw_rect(rect, Color(0.2, 0.2, 0.2, 0.8))
			draw_string(font, Vector2(rect.position.x + 10, rect.position.y + 25), levels[i].name, HORIZONTAL_ALIGNMENT_LEFT, -1, 20, Color.YELLOW)
			draw_string(font, Vector2(rect.position.x + 10, rect.position.y + 45), levels[i].desc, HORIZONTAL_ALIGNMENT_LEFT, -1, 14, Color.LIGHT_GRAY)

	elif screen == "BRIEFING":
		draw_rect(Rect2(50, 50, 540, 540), Color(0, 0, 0, 0.7))
		var story = levels[pending_idx].story.briefing
		var lines = story.split("\n")
		for i in range(lines.size()):
			draw_string(font, Vector2(80, 150 + i * 30), lines[i], HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Color.WHITE)
		draw_string(font, Vector2(320, 500), "탭하여 시작", HORIZONTAL_ALIGNMENT_CENTER, -1, 20, Color.GRAY)

	elif screen == "PLAYING":
		var grid = state.gridSize
		var cell = 640.0 / grid
		var tones = [Color.WHITE, Color(0.7, 0.8, 0.9), Color(0.6, 0.4, 0.8), Color(1, 0.9, 0.5)]
		var tone = tones[current_mission_idx % tones.size()]
		
		for gx in range(grid):
			for gy in range(grid):
				var rect = Rect2(gx * cell, gy * cell, cell, cell)
				var tex_idx = 0
				if (gx * 7 + gy * 13) % 10 == 0:
					tex_idx = (gx * 3 + gy * 5) % 3 + 1
				draw_texture_rect(tex_floor[tex_idx], rect, false, tone)
		
		# 유닛 그리기
		for a in state.allies:
			draw_unit(a, "ally", cell)
		for e in state.enemies:
			draw_unit(e, "enemy", cell)
		
		# 하이라이트
		if selected_unit_id != null:
			var ally = null
			for a in state.allies:
				if a.id == selected_unit_id: ally = a; break
			if ally:
				var range_val = ally.get("range", 1)
				for gx in range(grid):
					for gy in range(grid):
						var dist = abs(ally.pos[0] - gx) + abs(ally.pos[1] - gy)
						var rect = Rect2(gx * cell, gy * cell, cell, cell)
						if dist == 1:
							var occ = false
							for u in state.allies + state.enemies:
								if u.hp > 0 and u.pos[0] == gx and u.pos[1] == gy: occ = true; break
							if not occ:
								draw_rect(rect, Color(0, 1, 0, 0.3))
						elif dist >= 1 and dist <= range_val:
							for e in state.enemies:
								if e.hp > 0 and e.pos[0] == gx and e.pos[1] == gy:
									draw_rect(rect, Color(1, 0, 0, 0.5), false, 2.0)
		
		draw_string(font, Vector2(10, 30), levels[current_mission_idx].name + "  Turn: " + str(state.turn), HORIZONTAL_ALIGNMENT_LEFT, -1, 20, Color.WHITE)

	elif screen == "RESULT":
		draw_rect(Rect2(0, 0, 640, 640), Color(0, 0, 0, 0.6))
		var story = levels[current_mission_idx].story
		var msg = story.victory if state.status == "VICTORY" else story.defeat
		var lines = msg.split("\n")
		for i in range(lines.size()):
			draw_string(font, Vector2(320, 200 + i * 30), lines[i], HORIZONTAL_ALIGNMENT_CENTER, -1, 20, Color.WHITE)
		
		if state.status == "VICTORY":
			var btn_rect = Rect2(220, 400, 200, 50)
			draw_rect(btn_rect, Color(0.3, 0.3, 0.3))
			draw_string(font, Vector2(320, 430), "다음 미션", HORIZONTAL_ALIGNMENT_CENTER, -1, 20, Color.WHITE)
		else:
			var r_rect = Rect2(150, 400, 150, 50)
			var m_rect = Rect2(340, 400, 150, 50)
			draw_rect(r_rect, Color(0.3, 0.3, 0.3))
			draw_string(font, Vector2(225, 430), "다시", HORIZONTAL_ALIGNMENT_CENTER, -1, 20, Color.WHITE)
			draw_rect(m_rect, Color(0.3, 0.3, 0.3))
			draw_string(font, Vector2(415, 430), "메뉴로", HORIZONTAL_ALIGNMENT_CENTER, -1, 20, Color.WHITE)

	for ft in floating_texts:
		draw_string(font, ft.pos, ft.text, HORIZONTAL_ALIGNMENT_CENTER, -1, 18, ft.color)

func draw_unit(u, side, cell):
	var gx = u.pos[0]
	var gy = u.pos[1]
	var rect = Rect2(gx * cell + cell * 0.1, gy * cell + cell * 0.1, cell * 0.8, cell * 0.8)
	var tex
	if side == "ally":
		tex = tex_mage if u.get("range", 1) > 1 else tex_knight
	else:
		tex = tex_monster
	
	var mod = Color.WHITE
	var key = ( "a" if side == "ally" else "e" ) + str(u.id)
	if flash_timers.has(key):
		mod = Color(1, 0.3, 0.3)
	if u.hp <= 0:
		mod = Color(0.5, 0.5, 0.5, 0.5)
	
	draw_texture_rect(tex, rect, false, mod)
	
	var hp_text = "HP %d" % u.hp
	var color = Color.WHITE
	if u.hp <= 0:
		hp_text = "✕"
		color = Color(0.5, 0.5, 0.5)
	
	draw_string(font, Vector2(rect.position.x, rect.position.y - 5), hp_text, HORIZONTAL_ALIGNMENT_LEFT, -1, 14, color)
	
	if side == "ally" and selected_unit_id == u.id:
		draw_rect(Rect2(gx * cell, gy * cell, cell, cell), Color(1, 1, 0, 0.4), false, 3.0)
