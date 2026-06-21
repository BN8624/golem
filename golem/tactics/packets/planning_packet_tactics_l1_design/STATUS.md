# STATUS

- 아이디어: Extend a deterministic tactical-grid combat kernel (one hero vs enemies on a small integer grid; each scenario via --scenario N gives an initial state {hero:{hp,atk,pos}, enemies:[{id,hp,atk,pos}]} and an ordered action list of move {dir:[dx,dy]} or attack {target:id}; attack on an orthogonally-adjacent enemy deals simultaneous mutual damage; kill all enemies = VICTORY, hero hp<=0 = DEFEAT, both dead = DEFEAT, 0 initial enemies or actions exhausted = FINISHED; fully deterministic, no RNG; CLI prints status/turn/hero_hp/hero_pos/enemies). NEW CARD '변칙검술 (anomaly swordsmanship)': give the hero a MANA SHIELD that absorbs incoming attack damage before it reaches HP, plus an ANOMALY effect that triggers when the shield breaks. Design the exact deterministic mana-shield absorption and ANOMALY-trigger rules as an additive layer that leaves all existing kernel behavior unchanged when no mana/anomaly is involved.
- 리뷰어 BLOCKING 원본 11 → distinct 11(중복 제거)
- 흡수: decisions 10 / assumed 3 / deferred 3
- 미해소 BLOCKING(흡수 부족분): 0
- interface_contract 파일 수: 2
- acceptance_tests 수: 4

CONTRACT_STATUS: FROZEN
