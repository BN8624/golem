// 정거장 산소 서브시스템 — 전력이 있으면 산소를 생산하고 정전이면 감소시키며 저산소 경보를 낸다
//
// 모델:
//   powered = power > 0
//   delta   = powered ? +genIfPowered : -decayIfDark
//   oxygen' = clamp(oxygen + delta - usePerPop*population, 0, cap)
//
// 불변식:
//   - oxygen은 항상 [0, caps.oxygen] 정수 범위.
//   - power.step 이후에 실행되므로 같은 틱의 갱신된 전력 상태를 읽는다(systems ORDER 1번).
//   - oxygen<=0 이면 population.step에서 생존 판정이 깨져 사상자가 난다(자원 고갈 → 인구 감소 경로).
//
// 경보 단계:
//   - O2_LOW       : oxygen <= lowAlert. 생명유지 여유가 한 자릿수 틱으로 줄어든 상태.
//   - O2_CRITICAL  : oxygen <= lowAlert/2. 즉시 조치 필요(다음 틱 고갈 위험).
const D = require('./constants').constants;
const { clamp } = require('./util');

exports.step = (state, c) => {
  const O = (c && c.oxygen) || D.oxygen;
  const cap = ((c && c.caps) || D.caps).oxygen;
  const powered = state.power > 0;
  const delta = powered ? O.genIfPowered : -O.decayIfDark;
  state.oxygen = clamp(state.oxygen + delta - O.usePerPop * state.population, 0, cap);
  if (state.oxygen <= Math.floor(O.lowAlert / 2)) {
    state.alerts.push('O2_CRITICAL');
  } else if (state.oxygen <= O.lowAlert) {
    state.alerts.push('O2_LOW');
  }
  return state;
};
