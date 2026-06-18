// 정거장 액션 처리 — WAIT는 한 턴 진행(틱), BUILD/RATION은 턴을 넘기지 않는 즉시 설정 변경
const D = require('./constants').constants;
const { clone } = require('./state');
const systems = require('./systems');

const BUILDABLE = ['solar', 'farm', 'recycler'];

exports.apply = (state, action, c) => {
  state = clone(state);
  const type = action && action.action;

  if (type === 'WAIT') {
    state.turn += 1;
    return systems.tick(state, c);
  }

  if (type === 'BUILD') {
    const B = (c && c.build) || D.build;
    const t = action.target;
    const cost = B[t];
    if (cost !== undefined && BUILDABLE.indexOf(t) !== -1 && state.credits >= cost) {
      state.credits -= cost;
      state[t] += 1;
      state.log.push('BUILT ' + t);
    } else {
      state.log.push('BUILD_FAILED ' + (t || '?'));
    }
    return state;
  }

  if (type === 'RATION') {
    state.rationing = !state.rationing;
    state.log.push('RATION ' + (state.rationing ? 'ON' : 'OFF'));
    return state;
  }

  // 알 수 없는 액션은 상태를 바꾸지 않는다.
  return state;
};
