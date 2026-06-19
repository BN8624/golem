// 에테르노 IF 초기 상태 — 시작 장면·빈 조각/비트/로그·보름 카운트다운(ECLIPSE_TURNS에서 시작)으로 결정적 시작 상태를 만든다
const { ECLIPSE_TURNS } = require('./constants');

exports.createInitialState = () => ({
  turn: 0,
  scene: 'start',
  fragments: [],
  beats: [],
  eclipse: ECLIPSE_TURNS,
  ending: null,
  isGameOver: false,
  logs: [],
});
