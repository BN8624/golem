# system_design

## main.js
- 책임: CLI argument parsing, orchestration of scenario loading, and formatting the final result as a single JSON line.
- 입력: process.argv
- 출력: stdout (JSON string)
- 금지: state mutation, combat logic, rule evaluation

## src/scenarios.js
- 책임: Storage and retrieval of hardcoded combat scenarios and action sequences.
- 입력: scenario_id (string/integer)
- 출력: scenario_data (object)
- 금지: state mutation, CLI access

## src/game_logic.js
- 책임: Domain logic: state mutations (HP, positions, turns), combat damage calculations, and evaluation of game termination status.
- 입력: current_state (object), action/params (object)
- 출력: next_state (object) OR status (string)
- 금지: CLI access, console output

## src/engine.js
- 책임: Orchestration of the turn-based loop: executing actions via logic and checking status post-action.
- 입력: initial_state (object), action_sequence (array)
- 출력: { state: object, status: string }
- 금지: CLI argument parsing, direct state mutation

