// 정거장 거주성 — 생명유지 지수·사기·온도 쾌적도에서 거주성 지수를 산출해 양호 시 사기를 올리고 열악 시 경보한다
//
// 모델:
//   hab = floor((lifeIndex + morale) / 2); 목표온도 근접(|temp-target|<=comfortTemp)이면 hab += 5
//   hab' = clamp(hab, 0, 100)
//   hab >= goodAlert면 morale += moraleBonus (작게·bounded, 게이트 무관)
//
// 불변식:
//   - lifeIndex·temperature는 읽기 전용. habitability는 [0,100] 정수 내부 지표.
//   - morale만 조건부로 올리되 clamp 유지. 승패 판정(인구·연구)에는 영향 없음.
//
// 경보:
//   - HABITAT_POOR: 거주성이 경보선 이하.
const D = require('./constants').constants;
const { clamp, floorDiv } = require('./util');

exports.step = (state, c) => {
  const HB = (c && c.habitat) || D.habitat;
  const TH = (c && c.thermal) || D.thermal;
  const caps = (c && c.caps) || D.caps;

  const dt = state.temperature >= TH.target
    ? state.temperature - TH.target
    : TH.target - state.temperature;
  let hab = floorDiv(state.lifeIndex + state.morale, 2);
  if (dt <= HB.comfortTemp) hab += 5;
  state.habitability = clamp(hab, 0, 100);

  if (state.habitability >= HB.goodAlert) {
    state.morale = clamp(state.morale + HB.moraleBonus, 0, caps.morale);
  } else if (state.habitability <= HB.poorAlert) {
    state.alerts.push('HABITAT_POOR');
  }
  return state;
};
