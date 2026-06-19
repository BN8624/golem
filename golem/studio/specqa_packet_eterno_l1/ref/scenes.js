// [Card1 REF] 장면 그래프(B겹) 누적본 — base에 검문 잠입(checkpoint)+조각1 제단(altar_1) 스레드를 ADD한 정답 참조
exports.SCENES = {
  start: {
    text: '에테르노의 성문 앞. 위조 통행증을 쥔 손이 떨린다. 붉은 망토의 감시병들이 길목을 막고 있다.',
    choices: {
      infiltrate: { label: '호흡을 가다듬어 검문소로 잠입한다', to: 'checkpoint' },
      press_on: { label: '무작정 성문으로 나아간다', to: 'end_fled' },
      turn_back: { label: '돌아선다', to: 'end_fled' },
    },
  },
  checkpoint: {
    text: '검문소. 감시병이 위조 통행증을 훑는다. 빈 왼쪽 소매에 의심이 스친다.',
    choices: {
      attune: { label: '심박과 마력을 동조시켜 존재감을 지운다', to: 'altar_1' },
      bluff: { label: '의심을 무시하고 그대로 들이댄다', to: 'end_caught' },
    },
  },
  altar_1: {
    text: '왕궁의 옛 배수로 끝, 지하 제단. 석대 위 결정체가 희미하게 빛난다.',
    choices: {
      bleed: { label: '손바닥의 피를 결정체에 떨어뜨린다', to: 'altar_1_done', fragment: 'F1' },
      leave: { label: '건드리지 않고 물러난다', to: 'end_fled' },
    },
  },
  altar_1_done: {
    text: '조각이 깨어나 빛의 이정표를 정신에 새긴다. 두 사람은 살아남은 방계 혈통임을 자각한다. 다음 조각이 부른다.',
    ending: 'AWAKENED',
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
