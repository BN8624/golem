- **Player Actions**
    - `move {dir:[dx,dy]}`: 
        - State Change: Updates `hero.pos` by `dx, dy`. 
        - Failure: If target tile is 'Wall' or out of bounds, position remains unchanged.
        - Log: `turn++`, status update.
    - `attack {target:id}`: 
        - Condition: Target must be at Manhattan distance 1.
        - State Change: 
            1. Target takes `hero.atk` damage (modified by `unit_type`). 
            2. Hero receives `enemy.atk` damage.
            3. This damage is first absorbed by `hero.mana`. If `hero.mana` drops from >0 to $\le$ 0, the shield RUPTURES.
            4. **Rupture**: All living enemies orthogonally adjacent to hero take `hero.anomaly_dmg`. Damage is doubled if hero's current tile is 'Conductive'.
        - Failure: If target is not at distance 1, action is skipped.
        - Log: `turn++`, status update.
    - `ranged_attack {target:id}`: 
        - Condition: Target must be at Manhattan distance 2 or 3.
        - State Change: 
            1. Target takes `hero.atk` damage (modified by `unit_type`).
            2. Target is inflicted with **Corrosion** status (Duration: 3, Damage: 1).
        - Failure: If target is not at distance 2..3, action is skipped.
        - Log: `turn++`, status update.

- **Entities & Rules**
    - **Hero**: The only active agent. Carries `hp`, `atk`, `mana`, `anomaly_dmg`.
    - **Enemies**: Passive targets.
        - `Hardened`: Melee attacks deal -1 damage.
        - `Glass`: All incoming damage (including status/anomaly) is x2.
        - `Resonant`: Hero takes 1 self-damage whenever this enemy is hit by an Anomaly.
    - **Tiles**: 
        - `Wall`: Impassable for hero.
        - `Conductive`: Doubles Anomaly damage.
    - **Status Effect (Corrosion)**:
        - **Application**: Inflicted by `ranged_attack`. If already present, duration is reset to 3.
        - **Tick**: At the end of every hero action attempt (including failed moves/attacks), every enemy with Corrosion takes 1 damage (modified by `unit_type` Glass).
        - **Decay**: Duration decreases by 1 after the damage tick. Effect expires at 0.

- **Win/Lose Conditions**
    - **Victory**: All enemies in the final battle of the route are dead and hero is alive.
    - **Defeat**: `hero.hp <= 0`.
    - **Finished**: Hero is alive, but the action list is exhausted before all enemies in the route are dead.
    - **Battle Transition**: When all enemies in current battle are dead, load next battle: reset `hero.pos` to [0,0], keep `hp/atk/mana`, increment route index.

- **NON-GOALS**
    - No enemy movement, AI, or turns.
    - No random number generation (RNG).
    - No graphics or real-time input.
    - No additive status stacking (only refresh).
