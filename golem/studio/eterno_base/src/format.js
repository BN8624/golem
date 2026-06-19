// 최종 IF 상태를 출력 계약 줄로 평탄화 렌더링한다(조각/비트는 정렬해 결정적으로, 일식은 null 또는 잔여 보름)
exports.render = (s) =>
  [
    'turn: ' + s.turn,
    'scene: ' + s.scene,
    'fragments: ' + JSON.stringify([...s.fragments].sort()),
    'beats: ' + JSON.stringify([...s.beats].sort()),
    'eclipse: ' + (s.eclipse === null ? 'null' : s.eclipse),
    'ending: ' + (s.ending === null ? 'null' : s.ending),
    'isGameOver: ' + s.isGameOver,
    'logs: ' + JSON.stringify(s.logs),
  ].join('\n');
