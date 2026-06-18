// 정거장 물 서브시스템 — 전력이 있으면 재활용기 레벨만큼 정수하고 인구 소비를 빼며 부족 경보를 낸다
//
// 모델:
//   prod   = powered ? recycleIfPowered * recycler : 0   (재활용기 레벨에 비례)
//   water' = clamp(water + prod - usePerPop*population, 0, cap)
//
// 불변식:
//   - water는 항상 [0, caps.water] 정수 범위.
//   - power.step 이후 실행(systems ORDER 2번). 정전이면 정수가 0이 되어 소비만 남는다.
//   - water<=0 이면 population.step 생존 판정이 깨진다(산소·식량과 동일한 고갈 경로).
//
// 경보:
//   - WATER_LOW: water <= lowAlert. 재활용 여유가 줄어 보급/증설 검토가 필요한 상태.
const D = require('./constants').constants;
const { clamp } = require('./util');

exports.step = (state, c) => {
  const W = (c && c.water) || D.water;
  const cap = ((c && c.caps) || D.caps).water;
  const powered = state.power > 0;
  const prod = powered ? W.recycleIfPowered * state.recycler : 0;
  state.water = clamp(state.water + prod - W.usePerPop * state.population, 0, cap);
  if (state.water <= W.lowAlert) state.alerts.push('WATER_LOW');
  return state;
};
