# 08_questions — 질문 처리 (§6 분류)

## 해소된 결정(decisions) 12
- Damage calculation order: Final Damage = max(0, (Base - HardenedPenalty) * GlassMultiplier).
- Mana absorption: Melee damage is subtracted from hero.mana first; any remaining damage (overflow) is subtracted directly from hero.hp.
- Resonant penalty: The 1 self-damage dealt to the hero when a Resonant enemy is hit by Anomaly is subtracted directly from hero.hp, bypassing mana.
- Targeting dead enemies: If an action targets an enemy ID that is already dead, the action is considered a 'Failure' (skipped), but the turn still increments and Corrosion ticks still occur.
- Mana recovery: Mana is a non-renewable resource for the entire route; there is no recovery mechanism.
- Route system: The multi-battle route system is confirmed as a core feature. State (hp, atk, mana) persists across battles.
- CLI Output: Expanded to include 'mana', 'current_battle_idx', and 'Corrosion duration' to ensure all state transitions are observable.
- Rupture target: The target of the melee attack is included in the Rupture AoE if they are orthogonally adjacent to the hero.
- Corrosion Tick Timing: Occurs at the end of every action attempt, after the action's primary effects are resolved, but before victory/transition checks.
- Damage Floor: All damage calculations are floored at 0 to prevent negative damage (healing).
- Multiplier stacking: Conductive (x2) and Glass (x2) are multiplicative (Total x4) for Anomaly damage.
- Battle Transition: Victory check occurs after the Corrosion tick of the turn that kills the final enemy.

## ASSUMED(가정 고정) 2
- The action_list is processed sequentially in a single execution flow.
- Mana is clamped at 0 (cannot be negative).

## DEFERRED(후속 미룸) 1
- Implementation of mana-recovery items or environmental shrines.
