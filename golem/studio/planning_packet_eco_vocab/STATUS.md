# STATUS

- 아이디어: A deterministic tick-based predator-prey ecosystem on a 1D strip of cells. Each tick, in fixed order: every creature first loses 1 energy to hunger; then each creature moves one cell toward its target (a predator steps toward the nearest prey, a prey steps away from the nearest predator, ties broken toward the lower cell index); then eating resolves (a predator sharing a cell with a prey eats one prey, removing that prey and gaining energy); then any creature whose energy is at or above the reproduction threshold spends energy to split into a new creature on its own cell; finally any creature with energy at or below zero starves and is removed. The world runs in discrete ticks until only one species remains or a tick cap is reached.
- 리뷰어가 올린 BLOCKING 원본: 13
- 흡수: decisions 13 / assumed 2 / deferred 1
- 미해소 BLOCKING: 0
- interface_contract 파일 수: 2
- acceptance_tests 수: 3

CONTRACT_STATUS: FROZEN
