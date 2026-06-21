# STATUS

- 아이디어: Extend a deterministic tactical-grid combat kernel (one hero vs enemies on a 2D integer grid with minimum coordinate 0; each scenario via --scenario N gives an initial state object {hero:{hp,atk,pos,mana,anomaly_dmg}, enemies:[{id,hp,atk,pos}]} plus any new fields this card needs, and an ordered action list. Action types: move {dir:[dx,dy]} blocked if the destination is off-grid (negative) or occupied by a living enemy; attack {target:id} is melee requiring orthogonal adjacency (Manhattan dist==1) with simultaneous mutual damage; ranged_attack {target:id} requires Manhattan distance 2..3 and deals one-way damage (hero takes nothing). A Mana Shield absorbs incoming melee damage before HP, and an ANOMALY discharges hero.anomaly_dmg to orthogonally-adjacent living enemies when the shield ruptures (mana crosses >0 to <=0 within one melee attack); ranged attacks deal the hero no damage so they never rupture. Kill all enemies = VICTORY, hero hp<=0 = DEFEAT, both dead = DEFEAT, 0 initial enemies or actions exhausted = FINISHED; fully deterministic, no RNG; the CLI prints status/turn/hero_hp/hero_pos/enemies and this output format is FIXED and must not change). NEW CARD 'terrain (지형)': introduce terrain tiles on the grid that affect play. Design the exact deterministic rules yourself: what terrain type(s) exist, how the terrain map is represented as STATIC data inside each scenario's initial state object, how terrain affects movement and/or combat, and how it interacts with melee, ranged, mana shield, and anomaly. It MUST be a purely additive layer: when a scenario defines no terrain, all existing behavior is byte-for-byte unchanged, and the printed output stays exactly status/turn/hero_hp/hero_pos/enemies.
- 리뷰어 BLOCKING 원본 10 → distinct 10(중복 제거)
- 흡수: decisions 13 / assumed 3 / deferred 2
- 미해소 BLOCKING(흡수 부족분): 0
- interface_contract 파일 수: 2
- acceptance_tests 수: 3

CONTRACT_STATUS: FROZEN
