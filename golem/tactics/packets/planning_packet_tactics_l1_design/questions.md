# 08_questions — 질문 처리 (§6 분류)

## 해소된 결정(decisions) 10
- The Anomaly burst triggers ONLY on the state transition from mana > 0 to mana <= 0. If mana is already 0 at the start of an attack, no Anomaly occurs.
- The 'dir' input for Move is a relative offset [dx, dy], where [0, 1] moves the hero one unit in the Y direction.
- Enemies with hp <= 0 are immediately removed from the grid and the enemies list at the end of the turn's resolution phase.
- The Anomaly burst is a one-time event per game, as there is no mechanism to restore mana.
- Damage resolution order: 1. Calculate mutual damage; 2. Apply damage to target enemy; 3. Apply damage to hero mana/hp; 4. Check for mana rupture transition; 5. If ruptured, apply Anomaly damage to all adjacent enemies; 6. Remove all dead enemies; 7. Evaluate Win/Lose conditions.
- The Requirements section (REQ-001 to REQ-007) is the definitive source of truth; the GDD is conceptual.
- If a Move action fails (out of bounds or occupied), the simulator logs the error and skips to the next action in the queue.
- The only way the hero takes damage is via the 'mutual damage' exchange during a Hero Attack action. Enemies have no independent turns or movement.
- A move of [0, 0] is treated as a valid no-op (no movement, success log).
- Invalid move inputs (non-integers, length != 2) are treated as failed moves and skipped.

## ASSUMED(가정 고정) 3
- The simulation is strictly single-threaded and sequential.
- Grid coordinates are always integers.
- The scenario file provides a valid JSON state matching the state_shape.

## DEFERRED(후속 미룸) 3
- Mana regeneration mechanics.
- Multiple different enemy types with varying behaviors.
- Complex grid obstacles (walls/terrain).
