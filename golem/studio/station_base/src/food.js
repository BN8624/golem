// 정거장 식량 서브시스템 — 농장 생산에서 인구 소비를 빼되 배급제면 소비를 절반(바닥)으로 줄이고 부족 경보를 낸다
//
// 모델:
//   prod = powered ? farmIfPowered * farm : 0     (농장 레벨에 비례)
//   cons = usePerPop * population, 배급제면 floor(cons/2)
//   food' = clamp(food + prod - cons, 0, cap)
//
// 불변식:
//   - food는 항상 [0, caps.food] 정수 범위.
//   - 배급제(rationing)는 RATION 액션으로만 토글된다. 소비를 절반으로 줄이는 대신 morale.step에서
//     사기 페널티를 받는다(자원 보존 ↔ 사기의 트레이드오프).
//   - food<=0 이면 생존 판정이 깨진다.
//
// 경보:
//   - FOOD_LOW: food <= lowAlert. 배급제 전환 또는 농장 증설 신호.
const D = require('./constants').constants;
const { clamp, floorDiv } = require('./util');

exports.step = (state, c) => {
  const F = (c && c.food) || D.food;
  const cap = ((c && c.caps) || D.caps).food;
  const powered = state.power > 0;
  const prod = powered ? F.farmIfPowered * state.farm : 0;
  let cons = F.usePerPop * state.population;
  if (state.rationing) cons = floorDiv(cons, 2);
  state.food = clamp(state.food + prod - cons, 0, cap);
  if (state.food <= F.lowAlert) state.alerts.push('FOOD_LOW');
  return state;
};
