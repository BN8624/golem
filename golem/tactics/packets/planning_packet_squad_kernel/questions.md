# 08_questions — 질문 처리 (§6 분류)

## 해소된 결정(decisions) 9
- Coordinate System: [x, y] where [0, 0] is the top-left corner. x increases right, y increases down.
- Direction Mapping: 'up': [0, -1], 'down': [0, 1], 'left': [-1, 0], 'right': [1, 0].
- Win/Loss Timing: Condition checks occur immediately after any HP change. If the last enemy dies, the game transitions to VICTORY and terminates immediately, even if other enemies were queued to act in the AI phase. If the last ally dies, the game transitions to DEFEAT and terminates immediately.
- Dead Unit Actions: If an action in the sequence is assigned to a unit that is already dead (hp <= 0), the action fails, the turn counter increments by 1, and the game proceeds to the enemy AI phase.
- Invalid Inputs: Any direction string not in the Direction Mapping is treated as a failed MOVE action; the turn counter increments and the game proceeds.
- Enemy Movement Logic: An enemy evaluates moves that reduce Manhattan distance to the target. Priority: 1. Any move along the X-axis (x-1 or x+1). 2. Any move along the Y-axis (y-1 or y+1). Because only one move per axis can reduce Manhattan distance on a square grid, the 'smaller resulting coordinate' rule serves as a final deterministic fallback.
- Output Sorting: Living allies and enemies in the final state must be sorted by their 'id' in ascending order.
- Output Frequency: The CLI will output the final state object after the game terminates (VICTORY, DEFEAT, or FINISHED).
- Math.random Constraint: Verified via static analysis of the source code to ensure no calls to Math.random(), Date.now() for seeds, or other non-deterministic APIs.

## ASSUMED(가정 고정) 2
- The CLI will receive scenarios as JSON files or internal lookup tables indexed by N.
- The memory footprint is small enough that state can be passed by value or reference without performance bottlenecks.

## DEFERRED(후속 미룸) 2
- Support for complex maps with obstacles
- Support for varied unit types with different movement ranges
