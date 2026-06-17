# system_design

## main.js
- 책임: Application entry point: defines simulation configuration (hungerLoss, eatingGain, threshold, cost), initializes state, and invokes the engine.
- 입력: User-defined configuration
- 출력: Simulation trigger
- 금지: Simulation logic, state mutation, direct distance calculations

## src/engine.js
- 책임: Orchestration of the tick sequence; manages state transitions, creates position snapshots for movement, and monitors termination conditions.
- 입력: Initial state, configuration
- 출력: Final state or step-by-step state progression
- 금지: Direct state mutation, low-level entity logic

## src/metabolism.js
- 책임: Deterministic metabolism phases: Hunger (energy reduction) and Death (removal of entities with energy <= 0).
- 입력: Current state, configuration
- 출력: New state object (immutable copy)
- 금지: Movement, predation, reproduction logic, Direct state mutation

## src/behavior.js
- 책임: Deterministic interaction phases: Movement (using snapshots to move 1 cell toward/away from targets), Predation (lowest ID prey in shared cell), and Reproduction (energy threshold check). All entities sorted by ID before processing.
- 입력: Current state, configuration, position snapshot
- 출력: New state object (immutable copy)
- 금지: Hunger/Death logic, Direct state mutation

