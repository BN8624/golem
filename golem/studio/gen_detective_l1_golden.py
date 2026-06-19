# 탐정 카드 l1(집사 ALIBI + FALSE_ALIBI 비트) 골든 생성기 — 참조 scenes/beats를 node로 역산, 회귀 무결 검증(키0)
"""쇼케이스 카드1. detective_base에 '집사 심문' 경로(단서 ALIBI)와 FALSE_ALIBI 비트를 더한다.
골든은 손계산 않고 detective_base + 참조 모듈(scenes/beats) 실행으로 역산(모델 독립).

흐름:
  1) detective_base를 ref로 복사, src/scenes.js·src/beats.js만 카드1 버전으로 교체.
  2) 시나리오 입력(choices)을 scenarios.json으로 쓰고 node 실행 → expected.
  3) 회귀(원래 5종)는 base==ref 바이트동일. 신규(집사 경로)는 base와 달라야(죽은코드 아님).
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE / "detective_base"
SPECQA = HERE / "specqa_packet_detective_l1"

# 참조 scenes = base + crime_scene에 question_butler 선택, butler_room 장면(단서 ALIBI).
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
    },
  },
  butler_room: {
    text: '집사는 굳은 얼굴로 말한다. "그 시각 저는 서재에 있었습니다." 그의 손끝이 미세하게 떨린다.',
    choices: {
      confront_alibi: { label: '알리바이를 캐묻는다', to: 'crime_scene', clue: 'ALIBI' },
      leave_butler: { label: '돌아선다', to: 'crime_scene' },
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

# 참조 beats = base(DEDUCTION) + FALSE_ALIBI(ALIBI && LETTER: 편지가 알리바이를 거짓으로 드러냄).
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
  return out;
};
"""

TC, IB, ID, IW, AC, WK, QB, CA = (
    "take_case", "inspect_body", "inspect_desk", "inspect_window",
    "accuse", "walk", "question_butler", "confront_alibi")


def scn(sid, reqs, choices):
    return {"id": sid, "covers_reqs": reqs, "input": {"choices": choices}}


SCENARIOS = [
    scn("SCN-001", ["RULE-04", "RULE-05"], [TC, IB, ID, IW, AC]),
    scn("SCN-002", ["RULE-06"], ["refuse"]),
    scn("SCN-003", ["RULE-05"], [TC, IW, AC]),
    scn("SCN-004", ["RULE-05"], [TC, IB, IW, AC]),
    scn("SCN-005", ["RULE-04", "RULE-05"], [TC, ID, IB, IW, WK]),
    scn("SCN-006", ["RULE-07"], [TC, QB, CA, ID, IW, AC]),      # ALIBI+LETTER → FALSE_ALIBI, WOUND 부족 → COLD_CASE
    scn("SCN-007", ["RULE-04", "RULE-07"], [TC, IB, ID, QB, CA, IW, AC]),  # 전 단서 → DEDUCTION+FALSE_ALIBI → TRUTH
    scn("SCN-008", ["RULE-07"], [TC, QB, CA, IW, AC]),          # ALIBI만(편지 없음) → FALSE_ALIBI 미발동 → COLD_CASE
]
# 회귀(카드1 경로 미사용) = 원래 5종. 신규(집사 경로) = 6/7/8 (base와 달라야).
REGRESSION = {"SCN-001", "SCN-002", "SCN-003", "SCN-004", "SCN-005"}

OUTPUT_KEYS = ["turn", "scene", "clues", "beats", "ending", "isGameOver", "logs"]


def run(workdir, idx):
    r = subprocess.run(["node", "main.js", "--scenario", str(idx)], cwd=str(workdir),
                       capture_output=True, text=True, encoding="utf-8", timeout=30, stdin=subprocess.DEVNULL)
    if r.returncode != 0:
        raise RuntimeError(f"node 실패 scn{idx}: {r.stderr[:200]}")
    return r.stdout


def parse_expected(stdout):
    exp = {}
    for line in stdout.splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        k, v = k.strip(), v.strip()
        if k in ("clues", "beats", "logs"):
            exp[k] = json.loads(v)
        elif k == "isGameOver":
            exp[k] = (v == "true")
        elif k == "turn":
            exp[k] = int(v)
        elif k == "ending":
            exp[k] = None if v == "null" else v
        else:
            exp[k] = v
    return exp


def main():
    sys.path.insert(0, str(HERE.parent))
    try:
        from config import force_utf8_stdout
        force_utf8_stdout()
    except Exception:  # noqa: BLE001
        pass

    ref = HERE / "_detective_ref_l1_tmp"
    if ref.exists():
        shutil.rmtree(ref)
    shutil.copytree(BASE, ref)
    (ref / "src" / "scenes.js").write_text(REF_SCENES, encoding="utf-8")
    (ref / "src" / "beats.js").write_text(REF_BEATS, encoding="utf-8")

    inputs = [{"input": s["input"]} for s in SCENARIOS]
    (ref / "scenarios.json").write_text(json.dumps(inputs, ensure_ascii=False), encoding="utf-8")
    (BASE / "scenarios.json").write_text(json.dumps(inputs, ensure_ascii=False), encoding="utf-8")

    out = []
    regression_ok = True
    new_fired = 0
    for i, s in enumerate(SCENARIOS, 1):
        ref_out = run(ref, i)
        base_out = run(BASE, i)
        expected = parse_expected(ref_out)
        out.append({"id": s["id"], "input": s["input"], "covers_reqs": s["covers_reqs"],
                    "expected": expected, "oracle_risk": {"risk": False, "reason": ""}})
        same = base_out == ref_out
        if not same:
            new_fired += 1
        if s["id"] in REGRESSION:
            regression_ok = regression_ok and same
        tag = ("회귀 base==ref:" + str(same)) if s["id"] in REGRESSION else ("신규발동" if not same else "신규미발동(?)")
        print(f"  {s['id']} {tag}  beats={expected['beats']} ending={expected['ending']}")

    SPECQA.mkdir(parents=True, exist_ok=True)
    (SPECQA / "acceptance_tests_draft.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    (SPECQA / "oracle_risk_review.json").write_text(json.dumps(
        {"risky_scenarios": [],
         "notes": [{"risk": False,
                    "reason": "전 시나리오 oracle_risk.risk=false. 탐정 IF 카드1 — 골든은 detective_base+참조 scenes/beats 실Node 역산(모델 독립)."}]},
        ensure_ascii=False, indent=2), encoding="utf-8")

    (BASE / "scenarios.json").unlink(missing_ok=True)
    shutil.rmtree(ref)
    print(f"\n회귀 무결: {regression_ok}  신규 발동 {new_fired}개  시나리오 {len(out)}개 → {SPECQA}")
    return 0 if (regression_ok and new_fired > 0) else 1


if __name__ == "__main__":
    raise SystemExit(main())
