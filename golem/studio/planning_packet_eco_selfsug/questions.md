# 08_questions — 질문 처리 (§6 분류)

## 해소된 결정(decisions) 13
- Tie-break logic: 'Move toward the lower index' means the resulting position must be the smaller integer of the available options (e.g., if moving left or right both satisfy the primary goal, move left).
- Prey movement when occupying the same cell as a predator: The prey must move toward index 0.
- Movement targets: If no entities of the target species exist in the state, the entity remains stationary during the movement phase.
- Predation priority (Predators): If multiple predators occupy the same cell as one or more prey, predators are processed in ascending order of ID. Each predator can eat a maximum of one prey per tick.
- Predation priority (Prey): If a predator is on a cell with multiple prey, it consumes the prey with the lowest ID.
- Reproduction offspring energy: New entities spawn with energy equal to config.reproductionCost.
- Newborn behavior: Entities spawned during the reproduction phase are added to the state but are ineligible for any actions (hunger, movement, predation, reproduction, death) until the following tick.
- ID Assignment: The state object includes a 'nextId' integer which increments by 1 every time a new entity is spawned.
- Processing Order: All phases (Hunger, Movement, Predation, Reproduction, Death) process entities sequentially sorted by ID in ascending order.
- Movement Calculation: Movement is calculated based on a snapshot of all entity positions taken at the start of the movement phase to ensure the sequence of movement does not affect the targets of others within the same phase.
- Termination check: The simulation checks the termination condition (species < 2 or tick == tickCap) at the very beginning of each tick. If met, the simulation stops before the hunger phase.
- Boundary handling: If a movement rule dictates a move to index < 0 or index >= worldSize, the entity remains at the boundary cell (0 or worldSize-1).
- Summary Log Format: 'Tick [N]: Predators: [X], Prey: [Y]'

## ASSUMED(가정 고정) 2
- The simulation is executed in a single-threaded Node.js environment.
- Input scenarios are provided as predefined state objects.

## DEFERRED(후속 미룸) 1
- Implementation of a scenario JSON loader (will use hardcoded map in main.js for now).
