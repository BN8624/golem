# traceability_report (traceability.json에서 생성)

| REQ | text | modules | tests | status |
|---|---|---|---|---|
| RULE-01 | WAIT action -> turn += 1, fuel += consta | src/logic.js | SCN-001 | covered |
| RULE-02 | ADVANCE action -> cost check, stage incr | src/logic.js | SCN-002 | covered |
| RULE-03 | Evaluate win check at scenario start AND | src/engine.js | SCN-003 | covered |
| RULE-04 | Once gameStatus == 'WON', stop immediate | src/engine.js | SCN-004 | covered |
| RULE-05 | Initialization of state (turn=0, fuel=0, | src/logic.js | SCN-005, SCN-006 | covered |
