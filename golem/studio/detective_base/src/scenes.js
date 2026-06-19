// 장면 그래프 데이터(B겹) — 각 장면의 묘사·선택지·전이·단서를 담는 순수 콘텐츠 모듈
exports.SCENES = {
  start: {
    text: '비가 창을 두드린다. 문이 열리고, 검은 코트의 여자가 들어선다. "동업자가 죽었어요. 경찰은 자살이라지만, 아니에요."',
    choices: {
      take_case: { label: '사건을 맡는다', to: 'crime_scene' },
      refuse: { label: '거절한다', to: 'end_refused' },
    },
  },
  crime_scene: {
    text: '피해자의 사무실. 공기에서 식은 담배 냄새가 난다. 책상, 깨진 창, 열린 금고가 눈에 들어온다.',
    choices: {
      inspect_body: { label: '시신을 살핀다', to: 'crime_scene', clue: 'WOUND' },
      inspect_desk: { label: '책상을 뒤진다', to: 'crime_scene', clue: 'LETTER' },
      inspect_window: { label: '깨진 창을 본다', to: 'confront', clue: 'PRINT' },
    },
  },
  confront: {
    text: '돌아온 사무소. 의뢰인이 기다린다. 진실을 말할 시간이다.',
    choices: {
      accuse: { label: '범인을 지목한다', verdict: true },
      walk: { label: '입을 다문다', to: 'end_wrong' },
    },
  },
  end_refused: {
    text: '문이 닫힌다. 빗소리만 남는다. 어떤 이야기는 시작되지 않는다.',
    ending: 'WALKED_AWAY',
  },
  end_solved: {
    text: '모든 조각이 맞물린다. 상처의 각도, 찢긴 편지, 진흙 발자국 — 자살이 아니었다. 너는 이름을 말한다.',
    ending: 'TRUTH',
  },
  end_wrong: {
    text: '확신이 서지 않는다. 너는 추측을 내뱉고, 그것은 빗나간다. 진짜 살인자는 빗속으로 사라진다.',
    ending: 'COLD_CASE',
  },
};
