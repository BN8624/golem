// 탐정 IF 진행 루프 — 선택을 순서대로 적용해 장면 전이·단서 수집·비트 발동·결말 판정을 결정적으로 수행한다. 카드는 이 모듈을 편집한다
const C = require('./constants');
const { SCENES } = require('./scenes');
const { createInitialState } = require('./state');
const { fireBeats } = require('./beats');

function applyBeats(state) {
  const newly = fireBeats(state.clues, state.beats);
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

    if (option.clue && !state.clues.includes(option.clue)) {
      state.clues.push(option.clue);
      state.logs.push('단서:' + option.clue);
      applyBeats(state); // 단서를 얻을 때마다 비트 조건을 재평가한다
    }

    if (option.verdict) { // 지목: 단서 완비 여부로 결말이 갈린다
      state.scene = C.ALL_CLUES.every((c) => state.clues.includes(c)) ? 'end_solved' : 'end_wrong';
    } else {
      state.scene = option.to;
    }
  }

  const finalScene = SCENES[state.scene];
  if (finalScene && finalScene.ending != null) {
    state.ending = finalScene.ending;
    state.isGameOver = true;
  }
  return state;
};
