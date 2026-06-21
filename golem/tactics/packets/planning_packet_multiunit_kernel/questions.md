# 08_questions — 질문 처리 (§6 분류)

## 해소된 결정(decisions) 9
- Enemy AI triggers after every individual hero command, regardless of whether the command succeeded or failed.
- Enemies execute their AI actions in ascending order of their ID.
- Enemy movement tie-break: 1. Filter moves that minimize Manhattan distance to hero. 2. Prefer X-axis moves over Y-axis moves. 3. Prefer the move resulting in the smallest X coordinate, then smallest Y coordinate.
- If all moves that minimize Manhattan distance are blocked by the grid boundary, the hero, or another enemy, the enemy remains stationary for that turn.
- A failed hero command (e.g., MOVE into a wall) still consumes the turn and triggers the Enemy AI phase.
- The internal state object will track 'gridSize' and 'log', but the output of the engine's step function will return a pruned object containing exactly: status, turn, hero_hp, hero_pos, and enemies.
- Damage calculation is strictly: target_hp = target_hp - attacker_atk.
- The 'FINISHED' state is triggered when the provided command sequence is exhausted and neither 'VICTORY' nor 'DEFEAT' conditions are met.
- The state object will be expanded to include 'hero_atk' to ensure deterministic damage calculations.

## ASSUMED(가정 고정) 2
- Scenario data (initial state and command sequence) is provided to main.js as a JS object.
- The output for each step is printed to stdout in JSON format.

## DEFERRED(후속 미룸) 0
