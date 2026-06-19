# 08_questions — 질문 처리 (§6 분류)

## 해소된 결정(decisions) 10
- Introduced a new action `anomaly_attack {target: id}` to trigger anomaly damage, using the `hero.anomaly_dmg` stat.
- Defined 'Shield Rupture' as a state active whenever an enemy's current HP is less than 50% of their initial HP.
- Resolved `hero.mana/hp` damage: Damage is subtracted from `mana` first; any remaining damage overflows to `hp`.
- Resolved trait priority: Damage is calculated as (Base - Hardened Reduction) * Glass Multiplier.
- Action failure behavior: If an action fails (invalid target, blocked move, out of range), the turn still advances, the action is logged as 'FAILED', and no state change occurs.
- Targeting: Attacks on enemies with hp <= 0 or non-existent IDs are treated as failed actions.
- Grid boundaries: Grid is fixed at 10x10 (0-9 for both x and y).
- Output integration: Each turn produces a log line followed by the state string specified in REQ-005.
- Hero unit_type: Hero's 'unit_type' is for identification only and does not grant combat modifiers.
- Conductive Tile Logic: When the hero is on a Conductive tile and the target of an `anomaly_attack` is in a state of 'Shield Rupture', `hero.anomaly_dmg` is doubled.

## ASSUMED(가정 고정) 3
- Initial HP is captured at the start of the simulation to determine the 'Shield Rupture' threshold.
- The hero's anomaly_dmg is the base for all anomaly attacks.
- The CLI argument `--scenario N` will map to a hardcoded set of scenario objects in the code.

## DEFERRED(후속 미룸) 3
- Multiple traits per enemy (restricted to one unit_type for now).
- Complex terrain interaction (e.g., obstacles that don't block but slow).
- Dynamic action lists based on game state.
