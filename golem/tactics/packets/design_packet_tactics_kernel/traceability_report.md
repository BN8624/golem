# traceability_report (traceability.json에서 생성)

| REQ | text | modules | tests | status |
|---|---|---|---|---|
| REQ-01 | CLI argument --scenario N selects the ha | main.js, src/scenarios.js | SCN-001 | covered |
| REQ-02 | turn = turn + 1 after every action attem | src/game_logic.js, src/engine.js | SCN-002 | covered |
| REQ-03 | Combat is simultaneous mutual damage. | src/game_logic.js | SCN-003 | covered |
| REQ-04 | HP can be negative. | src/game_logic.js | SCN-003 | covered |
| REQ-05 | Win/Lose checks occur strictly post-acti | src/engine.js, src/game_logic.js | SCN-004 | covered |
| REQ-06 | If both hero.hp <= 0 and all enemies.hp  | src/game_logic.js | SCN-004 | covered |
| REQ-07 | Initial enemy count 0 results in FINISHE | src/game_logic.js | SCN-001 | covered |
| REQ-08 | Output is a single JSON line with: statu | main.js | SCN-001 | covered |
