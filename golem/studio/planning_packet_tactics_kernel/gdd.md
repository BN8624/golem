- **Player Actions**
    - **MOVE [Direction]**: 
        - *Input*: Up, Down, Left, Right.
        - *State Change*: Updates `hero_pos` by 1 unit in the specified direction.
        - *Failure Case*: Moving outside the grid boundaries (if defined) or attempting to move while the game is already in a terminal state.
        - *Log*: "Hero moved to [x, y]".
    - **ATTACK [Direction]**: 
        - *Input*: Up, Down, Left, Right.
        - *State Change*: If an enemy exists at the target position, `enemy.hp -= hero.atk` AND `hero.hp -= enemy.atk`.
        - *Failure Case*: No enemy exists at the adjacent target position.
        - *Log*: "Hero attacked enemy [id]. Hero HP: [hp], Enemy HP: [hp]".

- **Entities**
    - **Hero**: Single unit with `hp`, `atk`, and `pos` [x, y].
    - **Enemies**: Multiple units, each with a unique `id`, `hp`, `atk`, and `pos` [x, y].
    - **Grid**: A coordinate system where units occupy unique [x, y] integers.

- **Win/Lose Conditions**
    - **Check Timing**: Evaluated strictly *after* each action is processed and `turn` is incremented.
    - **DEFEAT**: Triggered if `hero.hp <= 0`. This takes priority over victory.
    - **VICTORY**: Triggered if all enemies that existed at the start of the scenario have `hp <= 0`, provided at least one enemy existed initially.
    - **FINISHED**: Triggered if the action sequence completes and neither DEFEAT nor VICTORY occurred. (Also applies if 0 enemies were present initially).

- **NON-GOALS**
    - Randomness/Critical hits/Miss chances.
    - Real-time input or interactive CLI.
    - Graphical rendering or animations.
    - Complex AI or pathfinding.
    - Item systems or skill cooldowns.
