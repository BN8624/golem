# STATUS

- 아이디어: Extend a deterministic tactical-grid combat kernel (one hero vs enemies on a small integer grid; each scenario via --scenario N gives an initial state {hero:{hp,atk,pos,mana,anomaly_dmg}, enemies:[{id,hp,atk,pos}]} and an ordered action list of move {dir:[dx,dy]} or attack {target:id}; an attack on an orthogonally-adjacent enemy deals simultaneous mutual damage; a Mana Shield absorbs incoming attack damage before HP (overflow only reduces hp, mana clamps at 0) and an ANOMALY discharge deals hero.anomaly_dmg to all orthogonally-adjacent living enemies when the shield ruptures, i.e. mana crosses from >0 to <=0 within one attack; kill all enemies = VICTORY, hero hp<=0 = DEFEAT, both dead = DEFEAT, 0 initial enemies or actions exhausted = FINISHED; fully deterministic, no RNG; CLI prints status/turn/hero_hp/hero_pos/enemies). NEW CARD 'ranged attack (사거리)': let the hero attack enemies that are NOT orthogonally adjacent but within a defined range. Design the exact deterministic rules yourself: how range/distance is measured, what the range value is, whether and how the targeted enemy counterattacks against a ranged (non-adjacent) attack, any line-of-sight or blocking, and how this interacts with the existing adjacent melee, mana shield, and anomaly. It MUST be a purely additive layer that leaves all existing kernel behavior unchanged when only adjacent melee attacks are used.
- 리뷰어 BLOCKING 원본 8 → distinct 8(중복 제거)
- 흡수: decisions 11 / assumed 2 / deferred 2
- 미해소 BLOCKING(흡수 부족분): 0
- interface_contract 파일 수: 3
- acceptance_tests 수: 4

CONTRACT_STATUS: FROZEN
