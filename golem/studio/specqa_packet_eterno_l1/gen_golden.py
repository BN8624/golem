# Card1 골든 역산기(키0) — eterno_base에 ref/ 누적본(scenes.js만)을 적용해 시나리오를 실제 node로 돌려 기대값을 역산한다
"""detective gen_*_golden 규율과 동형. REF node가 정답 오라클이므로 손으로 기대값을 적지 않는다.
Card1은 scenes.js만 touched(검문 잠입 곁가지 add-only) — beats/engine은 base 그대로.
출력: acceptance_tests_draft.json(시나리오+expected) + golden/SCN-*.txt(원시 렌더).
"""
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "eterno_base"
REF = HERE / "ref"

# 누적 시나리오 — base 줄거리 회귀(SCN-001~005) + Card1 잠입 곁가지(SCN-006~008)
SCENARIOS = [
    {"id": "SCN-001", "covers_reqs": ["RULE-03", "RULE-04", "RULE-05"],
     "input": {"choices": ["enter", "altar_1", "altar_2", "altar_3", "altar_4", "altar_5", "march"]}},  # 5조각→NEW_DAWN
    {"id": "SCN-002", "covers_reqs": ["RULE-05"],
     "input": {"choices": ["enter", "altar_1", "march"]}},                       # 조각부족→RITUAL_COMPLETE
    {"id": "SCN-003", "covers_reqs": ["RULE-06"],
     "input": {"choices": ["turn_back"]}},                                        # 포기→FLED
    {"id": "SCN-004", "covers_reqs": ["RULE-07"],
     "input": {"choices": ["enter"] + ["altar_1"] * 9}},                          # 시간 소진→RITUAL_COMPLETE(타이머)
    {"id": "SCN-005", "covers_reqs": ["RULE-02"],
     "input": {"choices": ["enter", "nonsense", "altar_1"]}},                     # 무효선택 무시 + 비종료
    {"id": "SCN-006", "covers_reqs": ["RULE-08", "RULE-04"],
     "input": {"choices": ["infiltrate", "attune", "altar_1", "altar_2", "altar_3", "altar_4", "altar_5", "march"]}},  # 잠입→완주
    {"id": "SCN-007", "covers_reqs": ["RULE-08", "RULE-06"],
     "input": {"choices": ["infiltrate", "bluff"]}},                              # 들킴→CAUGHT
    {"id": "SCN-008", "covers_reqs": ["RULE-08"],
     "input": {"choices": ["infiltrate", "attune", "altar_1"]}},                  # 잠입 성공 후 조각1(비종료)
]


def parse_render(out):
    d = {}
    for ln in out.splitlines():
        k, _, v = ln.partition(": ")
        d[k.strip()] = v
    return {
        "turn": int(d["turn"]),
        "scene": d["scene"],
        "fragments": json.loads(d["fragments"]),
        "beats": json.loads(d["beats"]),
        "eclipse": int(d["eclipse"]),
        "ending": None if d["ending"] == "null" else d["ending"],
        "isGameOver": d["isGameOver"] == "true",
        "logs": json.loads(d["logs"]),
    }


def main():
    work = Path(tempfile.mkdtemp(prefix="eterno_l1_ref_"))
    shutil.copytree(BASE, work, dirs_exist_ok=True)
    shutil.copy(REF / "scenes.js", work / "src" / "scenes.js")  # Card1 touched = scenes.js만
    (work / "scenarios.json").write_text(
        json.dumps([{"input": s["input"]} for s in SCENARIOS], ensure_ascii=False), encoding="utf-8")

    golden_dir = HERE / "golden"
    golden_dir.mkdir(exist_ok=True)
    tests = []
    for i, s in enumerate(SCENARIOS, 1):
        r = subprocess.run(["node", "main.js", "--scenario", str(i)], cwd=str(work),
                           capture_output=True, text=True, encoding="utf-8", timeout=30)
        out = r.stdout.replace("\r\n", "\n").rstrip("\n")
        (golden_dir / f"{s['id']}.txt").write_text(out + "\n", encoding="utf-8", newline="\n")
        tests.append({"id": s["id"], "input": s["input"], "covers_reqs": s["covers_reqs"],
                      "expected": parse_render(out), "oracle_risk": {"risk": False, "reason": ""}})

    (HERE / "acceptance_tests_draft.json").write_text(
        json.dumps(tests, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    shutil.rmtree(work, ignore_errors=True)
    print(f"생성 완료 — 시나리오 {len(tests)}개")
    for t in tests:
        e = t["expected"]
        print(f"  {t['id']}: scene={e['scene']} ending={e['ending']} frags={e['fragments']} "
              f"beats={e['beats']} eclipse={e['eclipse']}")


if __name__ == "__main__":
    main()
