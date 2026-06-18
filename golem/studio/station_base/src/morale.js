// 정거장 사기 서브시스템 — 모든 생존 자원이 쾌적선을 넘으면 오르고 아니면 내리며 배급제는 추가로 깎는다
//
// 모델:
//   comfortable = food>comfort && oxygen>comfort && water>comfort
//   morale += comfortable ? +up : -down
//   배급제면 morale -= rationPenalty
//   morale' = clamp(morale, 0, cap)
//
// 불변식:
//   - morale은 항상 [0, caps.morale] 정수 범위.
//   - 다른 서브시스템(thermal 극단온도, crew 과로)도 morale을 깎을 수 있다. 이 step은 자원 쾌적도
//     기여분만 담당하고, 환경/승무원 페널티는 각자의 step에서 추가된다(가산 모델).
//   - morale은 현재 승패 판정에 직접 쓰이지 않지만 운영 건전성 지표이며 derive 지속가능성에 반영된다.
//
// 경보:
//   - MORALE_LOW: morale <= lowAlert. 사기 저하(이탈·생산성 하락의 전조).
const D = require('./constants').constants;
const { clamp } = require('./util');

exports.step = (state, c) => {
  const M = (c && c.morale) || D.morale;
  const cap = ((c && c.caps) || D.caps).morale;
  const comfortable =
    state.food > M.comfort && state.oxygen > M.comfort && state.water > M.comfort;
  state.morale += comfortable ? M.up : -M.down;
  if (state.rationing) state.morale -= M.rationPenalty;
  state.morale = clamp(state.morale, 0, cap);
  if (state.morale <= M.lowAlert) state.alerts.push('MORALE_LOW');
  return state;
};
