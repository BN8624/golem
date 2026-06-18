// 최종 전투 상태를 출력 계약 줄로 평탄화 렌더링한다(중첩 player/enemy를 player_*·enemy_* 스칼라로)
exports.render = (s) =>
  [
    'tick: ' + s.tick,
    'player_hp: ' + s.player.hp,
    'player_energy: ' + s.player.energy,
    'player_gauge: ' + s.player.gauge,
    'player_pos: ' + s.player.pos,
    'enemy_hp: ' + s.enemy.hp,
    'enemy_energy: ' + s.enemy.energy,
    'enemy_gauge: ' + s.enemy.gauge,
    'enemy_pos: ' + s.enemy.pos,
    'isGameOver: ' + s.isGameOver,
    'winner: ' + (s.winner === null ? 'null' : s.winner),
    'logs: ' + JSON.stringify(s.gameLog),
  ].join('\n');
