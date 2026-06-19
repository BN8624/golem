// 최종 IF 상태를 출력 계약 줄로 평탄화 렌더링한다(단서/비트는 정렬해 결정적으로)
exports.render = (s) =>
  [
    'turn: ' + s.turn,
    'scene: ' + s.scene,
    'clues: ' + JSON.stringify([...s.clues].sort()),
    'beats: ' + JSON.stringify([...s.beats].sort()),
    'ending: ' + (s.ending === null ? 'null' : s.ending),
    'isGameOver: ' + s.isGameOver,
    'logs: ' + JSON.stringify(s.logs),
  ].join('\n');
