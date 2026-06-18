# system_design

## main.js
- 책임: Entry point to initialize the environment and execute scenario test suites.
- 입력: none
- 출력: console logs
- 금지: game rule implementation, state transition logic, direct state mutation

## src/constants.js
- 책임: Define immutable game configuration including fuel rates, stage costs, and stage nomenclature.
- 입력: none
- 출력: config object
- 금지: state mutation, logic processing

## src/logic.js
- 책임: Pure functions to provide the initial game state and calculate new state objects for WAIT (RULE-01) and ADVANCE (RULE-02).
- 입력: state, action
- 출력: new state object
- 금지: win condition checking, scenario looping, side effects

## src/engine.js
- 책임: Orchestrate action sequences, enforce win-check timing (RULE-03), and handle execution termination (RULE-04).
- 입력: action sequence
- 출력: final state
- 금지: direct fuel/stage arithmetic

