// 탐정 IF 초기 상태 생성 — 시작 장면과 빈 단서/비트/로그로 결정적 시작 상태를 만든다
exports.createInitialState = () => ({
  turn: 0,
  scene: 'start',
  clues: [],
  beats: [],
  logs: [],
  ending: null,
  isGameOver: false,
});
