# 08_questions — 질문 처리 (§6 분류)

## 해소된 결정(decisions) 13
- Hero damage absorption refers specifically to damage received by the hero during the 'attack' action.
- An Anomaly trigger occurs if and only if hero.mana transitions from > 0 to <= 0 during a single 'attack' action.
- If hero.mana is already <= 0 at the start of an 'attack' action, no Anomaly can trigger regardless of further damage.
- Damage spillover is active: if damage received by the hero exceeds current mana, the remainder is subtracted from hero.hp.
- The Anomaly discharge deals 'anomaly_dmg' to all enemies at Manhattan distance == 1 from the hero.
- If the hero is on a 'Conductive' tile during a rupture, 'anomaly_dmg' is multiplied by 2 for all affected enemies.
- Ranged attacks deal damage equal to 'hero.atk' and do not affect mana or trigger anomalies, serving as a tactical utility.
- A failed action (due to walls, boundaries, or invalid targets) still increments the turn counter.
- The sequence of resolution for 'attack' is: 1. Simultaneous damage calculation -> 2. Mana/HP subtraction -> 3. Rupture check -> 4. Anomaly application -> 5. Victory/Defeat check.
- The target of the 'attack' action is included in the Anomaly damage if they are still alive and adjacent.
- The grid is semi-infinite: valid coordinates are x >= 0 and y >= 0; there is no upper boundary.
- Invalid target IDs in 'attack' or 'ranged_attack' result in action failure.
- Move action failures occur if x < 0 OR y < 0 OR target is Wall OR target is occupied by a living enemy.

## ASSUMED(가정 고정) 3
- Grid is semi-infinite (x>=0, y>=0) with no upper boundary.
- All coordinates and attributes are integers.
- The output log format remains as previously specified but includes markers for 'Shield Rupture' and 'Anomaly Discharge'.

## DEFERRED(후속 미룸) 2
- Mana regeneration mechanics.
- Multiple Anomaly triggers per game session (currently limited to the first rupture).
