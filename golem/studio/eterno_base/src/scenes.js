// 장면 그래프 데이터(B겹) — 허브(은신처)에서 다섯 조각을 모아 찬탈자와 대면하는 완결 줄거리. 카드는 허브에 곁가지를 ADD한다
exports.SCENES = {
  start: {
    text: '에테르노의 성문 앞. 위조 통행증을 쥔 손이 떨린다. 붉은 망토의 감시병들이 길목을 막고 있다.',
    choices: {
      enter: { label: '성문을 지나 옛 배수로로 들어선다', to: 'hub' },
      turn_back: { label: '돌아선다', to: 'end_fled' },
    },
  },
  hub: {
    text: '남매의 은신처. 낡은 지도가 다섯 영혼의 조각이 잠든 곳을 가리킨다. 개기일식이 다가온다.',
    choices: {
      altar_1: { label: '지하 제단의 조각을 회수한다', to: 'hub', fragment: 'F1' },
      altar_2: { label: '고대 유적의 조각을 회수한다', to: 'hub', fragment: 'F2' },
      altar_3: { label: '북부 무기고의 조각을 회수한다', to: 'hub', fragment: 'F3' },
      altar_4: { label: '얼어붙은 고봉의 조각을 회수한다', to: 'hub', fragment: 'F4' },
      altar_5: { label: '만년설 성소의 조각을 회수한다', to: 'hub', fragment: 'F5' },
      march: { label: '에테르노로 진군해 찬탈자와 대면한다', verdict: true },
      flee: { label: '모든 걸 포기하고 달아난다', to: 'end_fled' },
    },
  },
  end_dawn: {
    text: '다섯 조각이 하나로 융합되고, 거짓된 권능이 무너진다. 제국에 새로운 여명이 밝는다.',
    ending: 'NEW_DAWN',
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
