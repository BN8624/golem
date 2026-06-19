# Card1 골든 역산기(키0) — eterno_base에 ref/ 누적본(scenes·beats)을 적용해 시나리오를 실제 node로 돌려 기대값을 역산한다
"""detective gen_*_golden 규율과 동형. REF node가 정답 오라클이므로 손으로 기대값을 적지 않는다.
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

# Card1 시나리오 — THIS CARD(RULE-08) 잠입/각성 커버 + base 회귀 + 무효선택/비종료
SCENARIOS = [
    {"id": "SCN-001", "covers_reqs": ["RULE-08", "RULE-03", "RULE-04"],
     "input": {"choices": ["infiltrate", "attune", "bleed"]}},      # 잠입 성공→조각1 각성(AWAKENED)
    {"id": "SCN-002", "covers_reqs": ["RULE-08", "RULE-06"],
     "input": {"choices": ["infiltrate", "bluff"]}},                # 들킴→CAUGHT
    {"id": "SCN-003", "covers_reqs": ["RULE-08", "RULE-06"],
     "input": {"choices": ["infiltrate", "attune", "leave"]}},      # 제단서 물러남→FLED
    {"id": "SCN-004", "covers_reqs": ["RULE-02", "RULE-06"],
     "input": {"choices": ["press_on"]}},                          # 회귀: base press_on 불변
    {"id": "SCN-005", "covers_reqs": ["RULE-02", "RULE-06"],
     "input": {"choices": ["turn_back"]}},                         # 회귀: base turn_back 불변
    {"id": "SCN-006", "covers_reqs": ["RULE-02"],
     "input": {"choices": ["infiltrate", "nonsense", "attune"]}},  # 무효선택 무시 + 비종료(ending null)
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
        "eclipse": None if d["eclipse"] == "null" else int(d["eclipse"]),
        "ending": None if d["ending"] == "null" else d["ending"],
        "isGameOver": d["isGameOver"] == "true",
        "logs": json.loads(d["logs"]),
    }


def main():
    work = Path(tempfile.mkdtemp(prefix="eterno_l1_ref_"))
    shutil.copytree(BASE, work, dirs_exist_ok=True)
    shutil.copy(REF / "scenes.js", work / "src" / "scenes.js")
    shutil.copy(REF / "beats.js", work / "src" / "beats.js")
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
        print(f"  {t['id']}: scene={t['expected']['scene']} ending={t['expected']['ending']} "
              f"fragments={t['expected']['fragments']} beats={t['expected']['beats']}")


if __name__ == "__main__":
    main()
