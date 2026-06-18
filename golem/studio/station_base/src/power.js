// 정거장 전력 서브시스템 — 태양광 발전에서 인구 소비를 빼 전력을 갱신하고 정전 경보를 올린다
//
// 모델:
//   gen = genPerSolar * solar      (태양광 패널 레벨에 선형 비례하는 발전)
//   use = usePerPop  * population   (생활·생명유지 부하)
//   power' = clamp(power + gen - use, 0, cap)
//
// 불변식:
//   - power는 항상 [0, caps.power] 정수 범위 안에 머문다(clamp 보장).
//   - 이 step은 다른 서브시스템보다 먼저 실행된다(systems ORDER 0번). 산소·물·식량·연구가
//     모두 "전력이 있는가(power>0)"를 읽으므로, 갱신된 전력이 같은 틱의 하류 판단에 쓰인다.
//   - solar/population은 이 step에서 바뀌지 않는다(읽기 전용). solar는 BUILD로만 오른다.
//
// 경보:
//   - POWER_OUT: 전력이 0으로 떨어진 순간(완전 정전). 같은 틱의 산소 감소·식량 생산 중단으로 이어진다.
const D = require('./constants').constants;
const { clamp } = require('./util');

exports.step = (state, c) => {
  const P = (c && c.power) || D.power;
  const cap = ((c && c.caps) || D.caps).power;
  const gen = P.genPerSolar * state.solar;
  const use = P.usePerPop * state.population;
  const net = gen - use;
  state.power = clamp(state.power + net, 0, cap);
  if (state.power === 0) {
    state.alerts.push('POWER_OUT');
  } else if (net < 0 && state.power <= use) {
    // 발전이 소비를 못 따라가고 비축도 한 턴치 이하면 적자 경보.
    state.alerts.push('POWER_DEFICIT');
  }
  return state;
};
