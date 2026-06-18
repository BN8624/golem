// 정거장 과학 — 누적 연구점수가 실험 마일스톤을 넘을 때마다 한 번씩 기록하고 정전 시 실험실 정지를 경보한다
//
// 모델:
//   research가 EXPERIMENT_MILESTONES[i].at 이상이 되면 코드를 로그하고 experiments 카운터 +1(순서대로, 1회씩).
//
// 불변식:
//   - research는 읽기 전용 — 이 모듈은 연구점수를 절대 바꾸지 않는다(승패 게이트 보존).
//   - experiments는 단조 증가 내부 카운터. 마일스톤은 연구점수가 단조 증가하므로 중복 로그가 없다.
//
// 경보/로그:
//   - 'EXPERIMENT <코드>': 마일스톤 최초 도달.
//   - LAB_IDLE: 정전(power<=0)으로 실험 중단.
const D = require('./constants').constants;
const { EXPERIMENT_MILESTONES } = require('./tables');

exports.step = (state, c) => {
  const SC = (c && c.science) || D.science;
  const EM = EXPERIMENT_MILESTONES;

  while (state.experiments < EM.length && state.research >= EM[state.experiments].at) {
    state.log.push('EXPERIMENT ' + EM[state.experiments].code);
    state.experiments += 1;
  }

  if (SC.idleIfDark && state.power <= 0) {
    state.alerts.push('LAB_IDLE');
  }
  return state;
};
