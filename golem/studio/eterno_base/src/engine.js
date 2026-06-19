// 에테르노 IF 진행 루프 — 선택을 순서대로 적용해 장면 전이·조각 수집·비트 발동·일식 카운트다운·결말 판정을 결정적으로 수행한다. 카드는 scenes/beats를 편집한다
const C = require('./constants');
const { SCENES } = require('./scenes');
const { createInitialState } = require('./state');
const { fireBeats } = require('./beats');

function applyBeats(state) {
  const newly = fireBeats(state.fragments, state.beats);
  for (const b of newly) {
    state.beats.push(b);
    state.logs.push('BEAT:' + b);
  }
}

exports.runScenario = (scenario) => {
  const input = (scenario && scenario.input) || {};
  const choices = input.choices || [];
  const state = createInitialState();

  for (let i = 0; i < choices.length && i < C.MAX_STEPS; i++) {
    const scene = SCENES[state.scene];
    if (!scene || scene.ending != null) break; // 결말 장면이면 종료

    const choiceId = choices[i];
    const option = scene.choices && scene.choices[choiceId];
    if (!option) { state.logs.push('무시:' + choiceId); continue; } // 무효 선택은 상태 변화 없이 무시

    state.turn += 1;
    state.logs.push('선택:' + choiceId);

    if (option.fragment && !state.fragments.includes(option.fragment)) {
      state.fragments.push(option.fragment);
      state.logs.push('조각:' + option.fragment);
      applyBeats(state); // 조각을 얻을 때마다 비트 조건을 재평가한다
    }

    if (option.startTimer && state.eclipse === null) {
      state.eclipse = C.ECLIPSE_TURNS; // 개기일식까지의 보름 카운트다운 점화
    }

    if (option.verdict) { // 찬탈자 대면: 다섯 조각 완비 여부로 결말이 갈린다
      state.scene = C.ALL_FRAGMENTS.every((f) => state.fragments.includes(f)) ? 'end_dawn' : 'end_ritual';
    } else {
      state.scene = option.to;
    }

    // 일식이 점화됐고 아직 결말이 아니면 매 턴 보름이 줄고, 0이면 피의 제사가 완성된다
    const next = SCENES[state.scene];
    if (state.eclipse !== null && next && next.ending == null) {
      state.eclipse -= 1;
      if (state.eclipse <= 0) state.scene = 'end_ritual';
    }
  }

  const finalScene = SCENES[state.scene];
  if (finalScene && finalScene.ending != null) {
    state.ending = finalScene.ending;
    state.isGameOver = true;
  }
  return state;
};
