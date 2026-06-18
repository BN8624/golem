// 정거장 최종 상태를 출력 계약 줄로 렌더링한다(main에서 사용, 줄 순서 고정)
exports.render = (s) =>
  [
    'turn: ' + s.turn,
    'power: ' + s.power,
    'oxygen: ' + s.oxygen,
    'water: ' + s.water,
    'food: ' + s.food,
    'population: ' + s.population,
    'morale: ' + s.morale,
    'research: ' + s.research,
    'credits: ' + s.credits,
    'gameStatus: ' + s.gameStatus,
    'alerts: ' + JSON.stringify(s.alerts),
    'logs: ' + JSON.stringify(s.log),
  ].join('\n');
