- **Player Actions**:
    - `MOVE [direction]`: Changes `hero_pos`. Fails if the target cell is outside the grid or occupied by an enemy. Log: "Hero moved to [x,y]".
    - `ATTACK`: Reduces HP of an enemy at Manhattan distance 1. If multiple enemies are adjacent, the one with the smallest `id` is targeted. Fails if no enemy is adjacent. Log: "Hero attacked enemy [id]".
- **Entities**:
    - **Hero**: Has `hp`, `atk`, and `pos {x, y}`.
    - **Enemy**: Has `id`, `hp`, `atk`, and `pos {x, y}`.
- **Enemy AI Rules (executed after every hero action)**:
    1. If Manhattan distance to hero is 1: Attack hero (`hero_hp -= enemy_atk`).
    2. Else: Move 1 cell closer to hero. 
        - Valid moves: Up, Down, Left, Right.
        - Selection: Choose the move that minimizes Manhattan distance.
        - Tie-break: Priority is X-axis then Y-axis, favoring the smaller coordinate value.
        - Collision: Cannot move out of bounds or into a cell occupied by the hero or another enemy.
- **Win/Lose Conditions**:
    - **VICTORY**: All enemies' `hp <= 0`.
    - **DEFEAT**: `hero_hp <= 0`.
    - **FINISHED**: Action sequence exhausted while hero and at least one enemy survive.
- **NON-GOALS**: Real-time input, random number generation, graphics/UI, pathfinding (A*), file I/O.
