- **Player Actions**
    - **Move**: `input: {unitId, dir}`. Change `pos` by 1 cell in given direction. *Failure*: Target cell is out of bounds or occupied by any living unit. *Log*: Action recorded, turn increments regardless of success.
    - **Attack**: `input: {unitId}`. Target the living enemy with the lowest `id` among those at Manhattan distance 1. *Failure*: No adjacent living enemies. *Log*: Target HP reduced by ally `atk`, turn increments.

- **Entities**
    - **Allies/Enemies**: Defined by `{id, hp, atk, pos: [x, y]}`. 
    - **Enemy AI Logic** (Executed in ascending `id` order after every ally action):
        1. **Targeting**: Select living ally with smallest Manhattan distance. Tie-break: smallest `id`.
        2. **Action**:
            - If distance == 1: Attack target (reduce ally `hp` by enemy `atk`).
            - If distance > 1: Move to a cell that reduces Manhattan distance to target.
                - *Constraint*: Must be within `gridSize` and not occupied by any living unit.
                - *Tie-break*: X-axis move > Y-axis move $\rightarrow$ resulting smaller $x$ $\rightarrow$ resulting smaller $y$.
                - *Failure*: If no distance-reducing move is possible, the enemy stays put.

- **Win/Lose Conditions**
    - **VICTORY**: All enemies' `hp <= 0`.
    - **DEFEAT**: All allies' `hp <= 0`.
    - **FINISHED**: Action sequence exhausted and neither side is fully eliminated.

- **NON-GOALS**
    - Randomness (`Math.random`), graphics/UI, real-time input, map obstacles, complex pathfinding (A*), or persistence.
