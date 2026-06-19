# 08_questions — 질문 처리 (§6 분류)

## 해소된 결정(decisions) 10
- Direction mapping: UP [0, -1], DOWN [0, 1], LEFT [-1, 0], RIGHT [1, 0].
- Grid boundaries: The grid is infinite; no boundaries are enforced, removing MOVE failure cases related to bounds.
- Collision: The hero can occupy the same coordinate as an enemy (no collision).
- Enemy Existence: An enemy 'exists' if they are present in the scenario list, but they are only 'targetable' for ATTACK and capable of dealing damage if hp > 0.
- Combat Logic: A mutual damage exchange occurs only if the target enemy's hp > 0. If the target is already dead (hp <= 0), the ATTACK action is a failure.
- Termination: The action loop terminates immediately upon reaching a terminal state (VICTORY or DEFEAT). Remaining actions in the sequence are not processed and the turn counter does not increment further.
- Failure Resolution: On a failed action (e.g., ATTACKing an empty cell or a dead enemy), no state changes occur to positions or HP, but the turn counter increments by 1 per REQ-002.
- Invalid Input: If an invalid --scenario N is provided, the program must exit with process.exit(1) and no output.
- Scenario Definition: A 'scenario' comprises the initial state (hero attributes, enemy attributes) and the ordered list of actions to execute.
- Log Handling: Internal logs are maintained during execution but are strictly excluded from the final JSON output as per REQ-008.

## ASSUMED(가정 고정) 2
- The grid is infinite in all directions (no boundary checks needed).
- The output JSON must strictly match the keys requested in REQ-008, ignoring internal log state.

## DEFERRED(후속 미룸) 1
- Loading scenarios from external JSON files instead of hardcoded JS objects.
