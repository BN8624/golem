# 08_questions — 질문 처리 (§6 분류)

## 해소된 결정(decisions) 11
- Anomaly trigger: 'single attack' refers to any event where the hero receives incoming damage. Since ranged_attack causes no damage to the hero, it cannot trigger an anomaly.
- Invalid targets: Attempting to attack a non-existent or dead (hp <= 0) enemy is treated as a failure. Log: 'Attack failed: target invalid'.
- Action list handling: The action list is input to the engine; the 'turn' in state tracks the current action index. The simulation terminates immediately upon 'VICTORY' or 'DEFEAT'.
- Failure penalty: A failed action (invalid range, invalid target, etc.) still increments the turn counter and consumes the action from the list.
- Status transitions: The 'status' field transitions to 'VICTORY', 'DEFEAT', or 'FINISHED' (if list exhausted).
- Execution order for 'attack': 1. Calculate damage for both parties. 2. Apply damage to target enemy. 3. Apply damage to hero via Mana Shield. 4. Trigger Anomaly if Mana Shield breaks. 5. Check Victory/Defeat conditions.
- Anomaly logic: The initial target of a melee attack takes damage before the Anomaly checks for 'living enemies'. If the target dies from the melee hit, it is not affected by the Anomaly.
- Defeat priority: If the hero reaches 0 HP and the last enemy reaches 0 HP in the same action, the status is 'DEFEAT'.
- Damage value: Damage dealt is exactly equal to the attacker's 'atk' stat.
- Log requirements: Successes are logged as per GDD; failures are logged as: 'Move failed: [reason]', 'Attack failed: target not adjacent', 'Ranged attack failed: target out of range', or 'Attack failed: target invalid'.
- Mana clamping: Mana is clamped at a minimum of 0.

## ASSUMED(가정 고정) 2
- Initial action list is provided as a JSON array of command objects.
- The CLI argument --scenario N maps to an index in the SCENARIOS object.

## DEFERRED(후속 미룸) 2
- Implementation of advanced targeting (e.g., 'attack nearest').
- Hero stats progression or leveling system.
