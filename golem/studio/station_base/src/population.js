// 정거장 인구 서브시스템 — 생존 자원이 모두 양수면 주기마다 늘고, 하나라도 고갈이면 사상자가 난다
//
// 모델:
//   alive = oxygen>0 && water>0 && food>0
//   !alive            -> population -= 1, 'CASUALTY'
//   alive & 성장주기   -> population += 1 (cap 미만일 때), 'BIRTH'
//
// 불변식:
//   - population은 항상 [0, caps.population] 정수 범위.
//   - population<=0 이 되면 state.checkEnd가 gameStatus='LOST'로 종료시킨다(패배 판정의 입력).
//   - 산소·물·식량 step 뒤에 실행되므로(systems ORDER 4번) 같은 틱의 갱신된 자원으로 생존을 본다.
//   - 성장은 turn % growEvery === 0 일 때만. turn은 WAIT에서 증가하므로 성장은 일정 간격으로만 발생.
//
// 경보:
//   - CASUALTY : 이번 틱 사상자 발생(자원 고갈).
//   - BIRTH    : 이번 틱 인원 증가.
//   - POP_LOW  : population <= lowAlert. 임계 인원(추가 손실 시 패배 위험).
const D = require('./constants').constants;
const { clamp } = require('./util');

exports.step = (state, c) => {
  const PP = (c && c.population) || D.population;
  const cap = ((c && c.caps) || D.caps).population;
  const alive = state.oxygen > 0 && state.water > 0 && state.food > 0;
  if (!alive) {
    state.population = clamp(state.population - 1, 0, cap);
    state.alerts.push('CASUALTY');
  } else if (state.turn % PP.growEvery === 0 && state.population < cap) {
    state.population = clamp(state.population + 1, 0, cap);
    state.alerts.push('BIRTH');
  }
  if (state.population <= PP.lowAlert) state.alerts.push('POP_LOW');
  return state;
};
