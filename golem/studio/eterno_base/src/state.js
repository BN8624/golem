// 에테르노 IF 초기 상태 — 시작 장면·빈 조각/비트/로그·미점화 일식 타이머로 결정적 시작 상태를 만든다
exports.createInitialState = () => ({
  turn: 0,
  scene: 'start',
  fragments: [],
  beats: [],
  eclipse: null,
  ending: null,
  isGameOver: false,
  logs: [],
});
