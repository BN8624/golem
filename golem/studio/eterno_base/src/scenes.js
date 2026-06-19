// 장면 그래프 데이터(B겹) — 각 장면의 묘사·선택지·전이·조각을 담는 순수 콘텐츠 모듈. 카드는 장면을 추가한다
exports.SCENES = {
  start: {
    text: '에테르노의 성문 앞. 위조 통행증을 쥔 손이 떨린다. 붉은 망토의 감시병들이 길목을 막고 있다.',
    choices: {
      press_on: { label: '무작정 성문으로 나아간다', to: 'end_fled' },
      turn_back: { label: '돌아선다', to: 'end_fled' },
    },
  },
  end_dawn: {
    text: '다섯 조각이 하나로 융합되고, 거짓된 권능이 무너진다. 제국에 새로운 여명이 밝는다.',
    ending: 'NEW_DAWN',
  },
  end_caught: {
    text: '감시병의 손이 어깨를 움켜쥔다. 통행증이 바닥에 떨어진다. 도망자의 길은 여기서 끝난다.',
    ending: 'CAUGHT',
  },
  end_ritual: {
    text: '개기일식이 차오른다. 피의 제사가 완성되고, 제국의 모든 생명이 연료가 된다.',
    ending: 'RITUAL_COMPLETE',
  },
  end_fled: {
    text: '아직 길이 열리지 않았다. 남매는 그림자 속으로 물러난다.',
    ending: 'FLED',
  },
};
