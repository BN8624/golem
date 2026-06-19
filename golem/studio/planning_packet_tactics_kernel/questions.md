# 08_questions — 질문 처리 (§6 분류)

## 해소된 결정(decisions) 11
- ATTACK command must include a target Enemy ID (e.g., 'ATTACK E1').
- Target selection for ATTACK is explicit via ID; if the specified ID is not adjacent, the action fails.
- A Turn Cycle consists of: 1. Player Action, 2. Enemy Actions (processed in ascending order of Enemy ID), 3. Turn Increment.
- Enemy Action Priority: If adjacent to Hero, the enemy MUST ATTACK. If not adjacent, the enemy MUST MOVE toward the Hero.
- Deterministic Enemy Movement: Enemies prioritize reducing X-distance first, then Y-distance. If the target tile is occupied by another enemy, the enemy stays put for that turn.
- Collision: Only one entity may occupy a tile. The Hero cannot MOVE into a tile occupied by an enemy.
- Invalid Input: Commands that are not 'MOVE [N/S/E/W]' or 'ATTACK [ID]' result in a log 'Invalid command' and the player's turn is consumed.
- Invalid Direction: MOVE commands with directions other than N, S, E, W result in 'Invalid direction' and the turn is consumed.
- Win/Lose Priority: If both conditions are met in the same cycle (impossible by current sequence, but defined for safety), 'LOSE' takes priority.
- Damage Calculation: Damage is exactly equal to the attacker's attackPower; no modifiers or randomness.
- Enemy Attack Trigger: Enemies attack during their phase if the Hero is in an adjacent orthogonal tile.

## ASSUMED(가정 고정) 3
- Enemies do not attack the Hero during the Player's action phase, only during their own turn phase.
- The 'Scenario N' argument in the CLI maps to a set of hardcoded initial states for testing.
- The coordinate system is (x, y) where x is horizontal (E/W) and y is vertical (N/S).

## DEFERRED(후속 미룸) 2
- Support for multiple enemy types with different movement patterns.
- Implementation of a persistent save/load state system.
