# 08_questions — 질문 처리 (§6 분류)

## 해소된 결정(decisions) 13
- Actions are 'consumed' and the turn counter increments regardless of whether the action succeeded or failed.
- Victory takes priority over Finished: If the final action in the list kills the final enemy of the final battle, the result is VICTORY.
- Ranged Attack Line-of-Sight (LOS): An attack is blocked if any tile on the L-shaped path (horizontal then vertical) between hero and target is a 'Wall'.
- Actions targeting an enemy_id not present in the current battle are treated as failures (no damage, turn still increments).
- Enemy turn trigger: After every player action, all surviving enemies in the current battle attack the hero in ascending order of their ID.
- Battle Transition timing: Occurs immediately after the killing blow of the final enemy in a battle. The hero position resets to [0,0] before the next player action is processed.
- Collision at [0,0]: If [0,0] is a Wall upon battle transition, the Wall is removed. If it is an Enemy, the Enemy is pushed to the nearest available tile (searching x+1, then y+1).
- Damage Order of Operations: Damage = (BaseDamage - HardenedModifier) * GlassMultiplier. Minimum damage is 0.
- Turn counter persists across battle transitions and does not reset.
- Enemy IDs are unique only within their own battle context, not across the entire route.
- Anomaly Rupture: Triggered when an enemy's 'anomaly' counter reaches a threshold of 3. This causes 'anomaly_dmg' to the enemy and triggers 'Resonant' trait if applicable.
- CLI 'status' refers to the current game state: 'ACTIVE', 'VICTORY', 'DEFEAT', or 'FINISHED'.
- The 'enemies' segment of the CLI output is serialized as a comma-separated list of 'id:hp@x,y' (e.g., '1:3@1,1,2:2@2,2').

## ASSUMED(가정 고정) 3
- The 'combat kernel' anomaly threshold is exactly 3 hits to trigger a rupture.
- The scenario provided via CLI will always have valid integers for coordinates and stats.
- The L-shaped path for LOS is defined as moving along the X axis first, then the Y axis.

## DEFERRED(후속 미룸) 2
- Dynamic enemy movement or AI behaviors.
- Adding mana to the CLI output for easier debugging.
