# 08_questions — 질문 처리 (§6 분류)

## 해소된 결정(decisions) 15
- The Hero possesses the Mana Shield; it is depleted via 'Counter-Damage' received whenever the Hero performs a melee attack(enemy_id).
- Counter-Damage value is floor(enemy.atk * recMult).
- Rupture triggers if the Hero's mana transitions from > 0 to <= 0 during the Counter-Damage phase of a melee attack.
- Rupture damage is inclusive of the enemy that triggered the rupture.
- Corrosion is a debuff applied to enemies; REQ-007 is corrected: Corrosion damages enemies, not the hero.
- Corrosion tick damage is floor(current_dot_magnitude * atkMult).
- Corrosion timing: Every action (including failed ones) triggers: 1. Corrosion Ticks (all enemies) -> 2. Corrosion Decay (all enemies) -> 3. Action Resolution.
- Ranged attack applies a Corrosion magnitude equal to the hero's 'corrosion' stat.
- Conductive terrain doubles Rupture damage if the victim (enemy) is standing on a conductive tile.
- Hero object is moved to the root of the state to ensure persistence across scenarios.
- Win condition takes priority over Lose condition if both occur in the same action.
- After mana is <= 0, all subsequent Counter-Damage is applied directly to Hero HP.
- Adjacency is defined as Manhattan distance = 1.
- The 'No... mana' non-goal is clarified to 'No enemy mana'.
- Failed actions (e.g., moving into a wall) still trigger the turn's Corrosion ticks and decay.

## ASSUMED(가정 고정) 3
- Assuming 'atkMult' applies to Corrosion damage since it's a hero-originated offensive effect.
- Assuming the 'status' field in CLI output is one of: 'ACTIVE', 'VICTORY', 'DEFEAT'.
- Assuming 'adjacent' always refers to Manhattan distance 1.

## DEFERRED(후속 미룸) 2
- Implementation of a complex route branching system (currently linear).
- Additional enemy types beyond Hardened, Glass, and Resonant.
