// 정거장 종합보고 — 틱 마지막에 지속가능성 점수를 읽어 정기 스냅샷을 로그하고 저하 시 종합 경보를 낸다
//
// 불변식:
//   - sustain은 읽기 전용(derive step이 직전에 갱신했으므로 systems ORDER에서 derive 뒤에 둔다).
//   - 승패 판정과 무관(경보/로그 전용). 스냅샷은 결정적 스케줄(난수 0).
//
// 경보/로그:
//   - 'STATUS <지속가능성>': 상태 스냅샷 스케줄 턴의 현재 지속가능성 점수.
//   - SYSTEM_DEGRADED: 지속가능성이 저하 임계 이하.
const D = require('./constants').constants;
const { STATUS_SCHEDULE } = require('./tables');

exports.step = (state, c) => {
  const RP = (c && c.report) || D.report;

  if (STATUS_SCHEDULE.indexOf(state.turn) !== -1) {
    state.log.push('STATUS ' + state.sustain);
  }

  if (state.sustain <= RP.degradedSustain) {
    state.alerts.push('SYSTEM_DEGRADED');
  }
  return state;
};
