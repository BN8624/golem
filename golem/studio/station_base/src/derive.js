// 정거장 지속가능성 지표 — 자원별 가중합을 정규화한 요약 점수를 계산한다(틱 마지막, 경보 없음)
const { floorDiv, sum } = require('./util');
const { SUSTAIN_WEIGHTS } = require('./tables');

exports.step = (state, c) => {
  const W = SUSTAIN_WEIGHTS;
  const weighted =
    state.oxygen * W.oxygen +
    state.water * W.water +
    state.food * W.food +
    state.power * W.power +
    state.hull * W.hull +
    state.morale * W.morale;
  const totalWeight = sum([W.oxygen, W.water, W.food, W.power, W.hull, W.morale]);
  state.sustain = floorDiv(weighted, totalWeight);
  return state;
};
