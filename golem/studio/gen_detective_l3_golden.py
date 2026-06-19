# 탐정 카드 l3(전 단서 5개 → CASE_CLOSED 비트) 골든 생성기 — 카드2 위에 누적, beats.js만 패치, 회귀 무결(키0)
"""쇼케이스 카드3(누적). 카드2(금고 MOTIVE) 위에 CASE_CLOSED 비트만 더한다(beats.js만 touched, scenes 불변).
다섯 단서(WOUND·LETTER·PRINT·ALIBI·MOTIVE)가 전부 모이면 전모가 드러난다.
골든은 base+카드1+카드2+카드3 참조 실Node 역산. 회귀는 카드2 결과(prev)와 바이트동일.
"""

import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE / "detective_base"
SPECQA = HERE / "specqa_packet_detective_l3"

import gen_detective_l1_golden as L1  # noqa: E402  (헬퍼 재사용)
import gen_detective_l2_golden as L2  # noqa: E402  (prev 참조 + 시나리오 누적)

# cur scenes = 카드2와 동일(카드3은 scenes 미변경).
REF_SCENES = L2.REF_SCENES

# cur beats = 카드2(DEDUCTION, FALSE_ALIBI, MOTIVE_REVEALED) + CASE_CLOSED(다섯 단서 전부).
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
  // CASE_CLOSED: 다섯 단서가 전부 모이면 사건의 전모가 닫힌다
  if (ALL_CLUES.every(has) && has('ALIBI') && has('MOTIVE') && !firedBeats.includes('CASE_CLOSED')) {
    out.push('CASE_CLOSED');
  }
  return out;
};
"""

TC, IB, ID, IW, AC, QB, CA, SS, RD = (
    "take_case", "inspect_body", "inspect_desk", "inspect_window",
    "accuse", "question_butler", "confront_alibi", "search_safe", "read_diary")

# 카드2까지의 11종(회귀) + 카드3 신규 1종(다섯 단서 전부 → CASE_CLOSED).
SCENARIOS = L2.SCENARIOS + [
    L1.scn("SCN-012", ["RULE-09"], [TC, SS, RD, IB, QB, CA, ID, IW, AC]),  # 5단서 전부 → CASE_CLOSED(+DEDUCTION 등) → TRUTH
]
NEW = {"SCN-012"}


def main():
    sys.path.insert(0, str(HERE.parent))
    try:
        from config import force_utf8_stdout
        force_utf8_stdout()
    except Exception:  # noqa: BLE001
        pass

    prev = L2.build_ref("_detective_ref_l2_prev_tmp", L2.REF_SCENES, L2.REF_BEATS)
    cur = L2.build_ref("_detective_ref_l3_tmp", REF_SCENES, REF_BEATS)

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
                    "reason": "전 시나리오 oracle_risk.risk=false. 탐정 IF 카드3(누적, beats만) — 골든은 base+카드1~3 참조 실Node 역산(모델 독립)."}]},
        ensure_ascii=False, indent=2), encoding="utf-8")

    shutil.rmtree(prev)
    shutil.rmtree(cur)
    print(f"\n회귀 무결(prev==cur): {regression_ok}  신규 발동 {new_fired}/{len(NEW)}  시나리오 {len(out)}개 → {SPECQA}")
    return 0 if (regression_ok and new_fired == len(NEW)) else 1


if __name__ == "__main__":
    raise SystemExit(main())
