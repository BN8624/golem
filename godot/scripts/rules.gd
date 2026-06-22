# 게임 규칙 엔진 - 스쿼드 룰 포팅
extends RefCounted

func update_state(state: Dictionary, action: Dictionary) -> String:
	apply_action(state, action)

	var status_after_ally = check_game_state(state)
	if status_after_ally == "VICTORY":
		state["turn"] += 1
		return "VICTORY"

	var living_enemies = []
	for e in state["enemies"]:
		if e["hp"] > 0:
			living_enemies.append(e)
	
	living_enemies.sort_custom(func(a, b): return a["id"] < b["id"])

	for enemy in living_enemies:
		execute_enemy_ai(state, enemy)
		var status_during_enemy = check_game_state(state)
		if status_during_enemy == "DEFEAT":
			state["turn"] += 1
			return "DEFEAT"

	state["turn"] += 1
	return "PLAYING"

func check_game_state(state: Dictionary) -> String:
	var enemies_alive = false
	for e in state["enemies"]:
		if e["hp"] > 0:
			enemies_alive = true
			break
	
	var allies_alive = false
	for a in state["allies"]:
		if a["hp"] > 0:
			allies_alive = true
			break

	if not enemies_alive:
		return "VICTORY"
	if not allies_alive:
		return "DEFEAT"
	return "PLAYING"

func apply_action(state: Dictionary, action: Dictionary) -> void:
	var ally = null
	for a in state["allies"]:
		if a["id"] == action["unit"]:
			ally = a
			break
	
	if not ally or ally["hp"] <= 0:
		return

	if action["type"] == "move":
		var dir = action.get("dir", [0, 0])
		var nx = ally["pos"][0] + dir[0]
		var ny = ally["pos"][1] + dir[1]

		if nx >= 0 and nx < state["gridSize"] and ny >= 0 and ny < state["gridSize"] and not is_occupied(state, nx, ny):
			ally["pos"] = [nx, ny]
	
	elif action["type"] == "attack":
		var range_val = ally.get("range", 1)
		var targets = []
		for e in state["enemies"]:
			var dist = manhattan(ally["pos"], e["pos"])
			if e["hp"] > 0 and dist <= range_val and dist >= 1:
				targets.append(e)
		
		if targets.size() > 0:
			targets.sort_custom(func(a, b): return a["id"] < b["id"])
			var target = targets[0]
			
			var damage = ally["atk"]
			if ally.has("flank_bonus"):
				var flanking_count = 0
				for a_other in state["allies"]:
					if a_other["id"] != ally["id"] and a_other["hp"] > 0 and manhattan(a_other["pos"], target["pos"]) == 1:
						flanking_count += 1
				damage += ally["flank_bonus"] * flanking_count
			
			if ally.get("asymmetric_strike", 0) > 0 and ally["pos"][0] < target["pos"][0]:
				damage += ally["asymmetric_strike"]
			
			var enemy_shield = 0
			for e_other in state["enemies"]:
				if e_other["id"] != target["id"] and e_other["hp"] > 0 and manhattan(e_other["pos"], target["pos"]) == 1:
					enemy_shield += e_other.get("aura_shield", 0)
			
			var final_damage = max(0, damage - enemy_shield)
			if target.get("phalanx_defense", 0) > 0:
				var has_neighbor = false
				for e_other in state["enemies"]:
					if e_other["id"] != target["id"] and e_other["hp"] > 0 and manhattan(e_other["pos"], target["pos"]) == 1:
						has_neighbor = true
						break
				if has_neighbor:
					final_damage = max(0, final_damage - target["phalanx_defense"])
			
			target["hp"] -= final_damage

			if target.get("reflect_dmg", 0) > 0:
				var ally_shield = 0
				for a_other in state["allies"]:
					if a_other["id"] != ally["id"] and a_other["hp"] > 0 and manhattan(a_other["pos"], ally["pos"]) == 1:
						ally_shield += a_other.get("aura_shield", 0)
				ally["hp"] -= max(0, target["reflect_dmg"] - ally_shield)

			if ally.get("knockback") == true and target.get("unmovable") != true:
				var dx = target["pos"][0] - ally["pos"][0]
				var dy = target["pos"][1] - ally["pos"][1]
				var nx = target["pos"][0] + dx
				var ny = target["pos"][1] + dy

				if nx >= 0 and nx < state["gridSize"] and ny >= 0 and ny < state["gridSize"] and not is_occupied(state, nx, ny):
					target["pos"] = [nx, ny]

func execute_enemy_ai(state: Dictionary, enemy: Dictionary) -> void:
	var living_allies = []
	for a in state["allies"]:
		if a["hp"] > 0:
			living_allies.append(a)
	
	if living_allies.size() == 0:
		return

	living_allies.sort_custom(func(a, b):
		var dist_a = manhattan(enemy["pos"], a["pos"])
		var dist_b = manhattan(enemy["pos"], b["pos"])
		if dist_a != dist_b:
			return dist_a < dist_b
		return a["id"] < b["id"]
	)
	
	var target = living_allies[0]
	var dist_to_target = manhattan(enemy["pos"], target["pos"])

	if dist_to_target == 1:
		var damage = enemy["atk"]
		if enemy.get("asymmetric_strike", 0) > 0 and enemy["pos"][0] < target["pos"][0]:
			damage += enemy["asymmetric_strike"]

		var ally_shield = 0
		for a_other in state["allies"]:
			if a_other["id"] != target["id"] and a_other["hp"] > 0 and manhattan(a_other["pos"], target["pos"]) == 1:
				ally_shield += a_other.get("aura_shield", 0)
		
		var final_damage = max(0, damage - ally_shield)
		if target.get("phalanx_defense", 0) > 0:
			var has_neighbor = false
			for a_other in state["allies"]:
				if a_other["id"] != target["id"] and a_other["hp"] > 0 and manhattan(a_other["pos"], target["pos"]) == 1:
					has_neighbor = true
					break
			if has_neighbor:
				final_damage = max(0, final_damage - target["phalanx_defense"])
		
		target["hp"] -= final_damage

		if target.get("reflect_dmg", 0) > 0:
			var enemy_shield = 0
			for e_other in state["enemies"]:
				if e_other["id"] != enemy["id"] and e_other["hp"] > 0 and manhattan(e_other["pos"], enemy["pos"]) == 1:
					enemy_shield += e_other.get("aura_shield", 0)
			enemy["hp"] -= max(0, target["reflect_dmg"] - enemy_shield)
	else:
		var possible_moves = [[1, 0], [-1, 0], [0, 1], [0, -1]]
		var candidates = []

		for move in possible_moves:
			var nx = enemy["pos"][0] + move[0]
			var ny = enemy["pos"][1] + move[1]

			if nx >= 0 and nx < state["gridSize"] and ny >= 0 and ny < state["gridSize"] and not is_occupied(state, nx, ny):
				if manhattan([nx, ny], target["pos"]) < dist_to_target:
					candidates.append([nx, ny])

		if candidates.size() > 0:
			var enemy_pos = enemy["pos"]
			candidates.sort_custom(func(a, b):
				var a_is_x = a[0] != enemy_pos[0]
				var b_is_x = b[0] != enemy_pos[0]
				if a_is_x != b_is_x:
					return a_is_x # a_is_x true means it's first
				if a[0] != b[0]:
					return a[0] < b[0]
				return a[1] < b[1]
			)
			enemy["pos"] = candidates[0]

func manhattan(p1: Array, p2: Array) -> int:
	return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

func is_occupied(state: Dictionary, x: int, y: int) -> bool:
	for u in state["allies"]:
		if u["hp"] > 0 and u["pos"][0] == x and u["pos"][1] == y:
			return true
	for u in state["enemies"]:
		if u["hp"] > 0 and u["pos"][0] == x and u["pos"][1] == y:
			return true
	return false
