# 탐정 카드 l2(금고 일기 MOTIVE + MOTIVE_REVEALED 비트) 골든 생성기 — 카드1 위에 누적, 회귀 무결 검증(키0)
"""쇼케이스 카드2(누적). 카드1(집사 ALIBI) 위에 '금고 속 일기' 경로(단서 MOTIVE)와 MOTIVE_REVEALED 비트를 더한다.
골든은 detective_base + 누적 참조 모듈(카드1+카드2) 실행으로 역산. 회귀는 카드1 결과(prev)와 바이트동일.

흐름:
  1) prev_ref = base + 카드1 참조(scenes/beats). cur_ref = base + 카드1+카드2 참조.
  2) 시나리오 입력을 node 실행 → expected = cur_ref 출력.
  3) 회귀(금고 경로 미사용 = 카드1까지의 11종 중 1~8)는 prev==cur 바이트동일. 신규(금고 경로)는 prev와 달라야.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE / "detective_base"
SPECQA = HERE / "specqa_packet_detective_l2"

import gen_detective_l1_golden as L1  # noqa: E402  (prev 참조 + 헬퍼 재사용)

# cur 참조 scenes = 카드1(집사) + crime_scene에 search_safe 선택, safe 장면(단서 MOTIVE).
REF_SCENES = """// 장면 그래프 데이터(B겹) — 각 장면의 묘사·선택지·전이·단서를 담는 순수 콘텐츠 모듈
exports.SCENES = {
  start: {
    text: '비가 창을 두드린다. 문이 열리고, 검은 코트의 여자가 들어선다. "동업자가 죽었어요. 경찰은 자살이라지만, 아니에요."',
    choices: {
      take_case: { label: '사건을 맡는다', to: 'crime_scene' },
      refuse: { label: '거절한다', to: 'end_refused' },
    },
  },
  crime_scene: {
    text: '피해자의 사무실. 공기에서 식은 담배 냄새가 난다. 책상, 깨진 창, 열린 금고가 눈에 들어온다. 문가에 집사가 서 있다.',
    choices: {
      inspect_body: { label: '시신을 살핀다', to: 'crime_scene', clue: 'WOUND' },
      inspect_desk: { label: '책상을 뒤진다', to: 'crime_scene', clue: 'LETTER' },
      inspect_window: { label: '깨진 창을 본다', to: 'confront', clue: 'PRINT' },
      question_butler: { label: '집사를 심문한다', to: 'butler_room' },
      search_safe: { label: '금고를 뒤진다', to: 'safe' },
    },
  },
  butler_room: {
    text: '집사는 굳은 얼굴로 말한다. "그 시각 저는 서재에 있었습니다." 그의 손끝이 미세하게 떨린다.',
    choices: {
      confront_alibi: { label: '알리바이를 캐묻는다', to: 'crime_scene', clue: 'ALIBI' },
      leave_butler: { label: '돌아선다', to: 'crime_scene' },
    },
  },
  safe: {
    text: '열린 금고 안쪽, 가죽 표지의 일기가 있다. 마지막 장에 피해자의 글씨로 누군가를 향한 분노가 적혀 있다.',
    choices: {
      read_diary: { label: '일기를 읽는다', to: 'crime_scene', clue: 'MOTIVE' },
      close_safe: { label: '금고를 닫는다', to: 'crime_scene' },
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
"""

# cur 참조 beats = 카드1(DEDUCTION, FALSE_ALIBI) + MOTIVE_REVEALED(MOTIVE && WOUND: 동기와 상처가 계획범죄를 가리킴).
REF_BEATS = """// 서사 비트 발동 로직(A겹) — 단서 집합이 조건을 만족할 때 결정적으로 발동할 비트를 반환한다
const { ALL_CLUES } = require('./constants');

// 이미 발동한 비트를 제외하고, 현재 단서로 새로 발동하는 비트 목록을 반환한다
exports.fireBeats = (clues, firedBeats) => {
  const out = [];
  const has = (c) => clues.includes(c);
  // DEDUCTION: 세 단서(상처·편지·발자국)가 모두 모이면 진실의 윤곽이 드러난다
  if (ALL_CLUES.every(has) && !firedBeats.includes('DEDUCTION')) {
    out.push('DEDUCTION');
  }
  // FALSE_ALIBI: 알리바이 진술과 찢긴 편지가 함께 손에 들어오면 거짓 알리바이가 드러난다
  if (has('ALIBI') && has('LETTER') && !firedBeats.includes('FALSE_ALIBI')) {
    out.push('FALSE_ALIBI');
  }
  // MOTIVE_REVEALED: 일기 속 동기와 시신의 상처가 함께 모이면 계획된 범행임이 드러난다
  if (has('MOTIVE') && has('WOUND') && !firedBeats.includes('MOTIVE_REVEALED')) {
    out.push('MOTIVE_REVEALED');
  }
  return out;
};
"""

TC, IB, ID, IW, AC, WK, QB, CA = (
    "take_case", "inspect_body", "inspect_desk", "inspect_window",
    "accuse", "walk", "question_butler", "confront_alibi")
SS, RD = "search_safe", "read_diary"

# 카드1까지의 8종(회귀) + 카드2 신규 3종.
SCENARIOS = L1.SCENARIOS + [
    L1.scn("SCN-009", ["RULE-08"], [TC, SS, RD, IB, IW, AC]),       # MOTIVE+WOUND → MOTIVE_REVEALED, LETTER 부족 → COLD_CASE
    L1.scn("SCN-010", ["RULE-04", "RULE-08"], [TC, SS, RD, IB, ID, IW, AC]),  # 전 핵심+동기 → DEDUCTION+MOTIVE_REVEALED → TRUTH
    L1.scn("SCN-011", ["RULE-08"], [TC, SS, RD, IW, AC]),           # MOTIVE만(상처 없음) → MOTIVE_REVEALED 미발동 → COLD_CASE
]
# 회귀(금고 경로 미사용) = 카드1까지의 8종. 신규(금고) = 009/010/011.
NEW = {"SCN-009", "SCN-010", "SCN-011"}


def build_ref(name, scenes_src, beats_src):
    ref = HERE / name
    if ref.exists():
        shutil.rmtree(ref)
    shutil.copytree(BASE, ref)
    (ref / "src" / "scenes.js").write_text(scenes_src, encoding="utf-8")
    (ref / "src" / "beats.js").write_text(beats_src, encoding="utf-8")
    return ref


def main():
    sys.path.insert(0, str(HERE.parent))
    try:
        from config import force_utf8_stdout
        force_utf8_stdout()
    except Exception:  # noqa: BLE001
        pass

    prev = build_ref("_detective_ref_l1_prev_tmp", L1.REF_SCENES, L1.REF_BEATS)
    cur = build_ref("_detective_ref_l2_tmp", REF_SCENES, REF_BEATS)

    inputs = [{"input": s["input"]} for s in SCENARIOS]
    for d in (prev, cur):
        (d / "scenarios.json").write_text(json.dumps(inputs, ensure_ascii=False), encoding="utf-8")

    out = []
    regression_ok = True
    new_fired = 0
    for i, s in enumerate(SCENARIOS, 1):
        prev_out = L1.run(prev, i)
        cur_out = L1.run(cur, i)
        expected = L1.parse_expected(cur_out)
        out.append({"id": s["id"], "input": s["input"], "covers_reqs": s["covers_reqs"],
                    "expected": expected, "oracle_risk": {"risk": False, "reason": ""}})
        same = prev_out == cur_out
        if s["id"] in NEW:
            if not same:
                new_fired += 1
        else:
            regression_ok = regression_ok and same
        tag = ("신규발동" if not same else "신규미발동(?)") if s["id"] in NEW else ("회귀 prev==cur:" + str(same))
        print(f"  {s['id']} {tag}  beats={expected['beats']} ending={expected['ending']}")

    SPECQA.mkdir(parents=True, exist_ok=True)
    (SPECQA / "acceptance_tests_draft.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    (SPECQA / "oracle_risk_review.json").write_text(json.dumps(
        {"risky_scenarios": [],
         "notes": [{"risk": False,
                    "reason": "전 시나리오 oracle_risk.risk=false. 탐정 IF 카드2(누적) — 골든은 base+카드1+카드2 참조 실Node 역산(모델 독립)."}]},
        ensure_ascii=False, indent=2), encoding="utf-8")

    shutil.rmtree(prev)
    shutil.rmtree(cur)
    print(f"\n회귀 무결(prev==cur): {regression_ok}  신규 발동 {new_fired}/{len(NEW)}  시나리오 {len(out)}개 → {SPECQA}")
    return 0 if (regression_ok and new_fired == len(NEW)) else 1


if __name__ == "__main__":
    raise SystemExit(main())
