// 최종 소코반 상태를 출력 계약 줄로 평탄화 렌더링한다(상자는 정렬해 결정적으로)
function onTargetCount(s) {
  let n = 0;
  for (const b of s.boxes) {
    if (s.targets[b[0] + ',' + b[1]]) n += 1;
  }
  return n;
}

exports.render = (s) =>
  [
    'moves: ' + s.moves,
    'player: ' + s.player.join(','),
    'boxes: ' + JSON.stringify(s.boxes.map((b) => b.join(',')).sort()),
    'on_target: ' + onTargetCount(s),
    'isWon: ' + s.isWon,
    'isGameOver: ' + s.isGameOver,
    'logs: ' + JSON.stringify(s.logs),
  ].join('\n');
