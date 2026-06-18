# l4(ABORT) 골든을 rocket_base + 참조 engine을 실제 Node로 돌려 역산한다(키0, 1회용)
import json
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE / "rocket_base"
TMP = HERE / "build_runs" / "_l4_golden_derive"

CONST = {"fuelRate": 1, "stageCost": [2, 3, 4, 5], "stageNames": ["대기권", "궤도", "달", "화성"]}


def A(*acts):
    return {"input": {"constants": CONST, "actions": [{"action": a} for a in acts]}}


# 6 회귀(원본 로켓과 동일 입력) + 2 ABORT
scen_inputs = [
    A("WAIT", "WAIT", "ADVANCE"),                                                  # SCN-001
    A("ADVANCE"),                                                                  # SCN-002
    A("WAIT", "WAIT", "WAIT", "WAIT", "WAIT", "ADVANCE", "ADVANCE"),               # SCN-003
    A(*(["WAIT"] * 14 + ["ADVANCE"] * 4)),                                         # SCN-004
    A(*(["WAIT"] * 14 + ["ADVANCE"] * 4 + ["WAIT"] * 3 + ["ADVANCE"])),            # SCN-005
    A(),                                                                           # SCN-006
    A("WAIT", "WAIT", "WAIT", "ADVANCE", "ABORT", "WAIT"),                         # SCN-007 ABORT 후 중단
    A("ABORT"),                                                                    # SCN-008 즉시 ABORT
]
covers = [["RULE-01", "RULE-02"], ["RULE-02"], ["RULE-01", "RULE-02"], ["RULE-02"],
          ["RULE-02"], ["RULE-05"], ["RULE-07", "RULE-02"], ["RULE-07"]]

# 참조 engine.js — ABORT를 더한 정답 편집(골든 역산 전용, 빌더 답이 아님)
REF_ENGINE = """const { createInitialState, applyWait, applyAdvance } = require('./logic');

function checkWin(state) {
  if (state.stage >= 4) {
    return { ...state, gameStatus: 'WON' };
  }
  return state;
}

exports.runScenario = (scenario) => {
  const config = scenario.input.constants;
  const actions = scenario.input.actions;

  let state = createInitialState();
  state = checkWin(state);

  for (const actionObj of actions) {
    if (state.gameStatus === 'WON') break;
    if (state.gameStatus === 'ABORTED') break;

    const action = actionObj.action;
    if (action === 'WAIT') {
      state = applyWait(state, config);
    } else if (action === 'ADVANCE') {
      state = applyAdvance(state, config);
    } else if (action === 'ABORT') {
      state = { ...state, gameStatus: 'ABORTED' };
      break;
    }

    state = checkWin(state);
  }

  return state;
};
"""

if TMP.exists():
    shutil.rmtree(TMP)
(TMP / "src").mkdir(parents=True)
shutil.copy(BASE / "src" / "logic.js", TMP / "src" / "logic.js")
shutil.copy(BASE / "src" / "constants.js", TMP / "src" / "constants.js")
shutil.copy(BASE / "main.js", TMP / "main.js")
(TMP / "src" / "engine.js").write_text(REF_ENGINE, encoding="utf-8")
(TMP / "scenarios.json").write_text(json.dumps(scen_inputs, ensure_ascii=False), encoding="utf-8")

OUT_KEYS = ["turn", "fuel", "stage", "gameStatus", "events"]
scenarios = []
for i, si in enumerate(scen_inputs, 1):
    r = subprocess.run(["node", "main.js", "--scenario", str(i)], cwd=str(TMP),
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
    d = {}
    for line in r.stdout.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            d[k.strip()] = v.strip()
    exp = {}
    for k in OUT_KEYS:
        v = d.get(k)
        if k == "events":
            exp[k] = json.loads(v)
        elif k in ("turn", "fuel", "stage"):
            exp[k] = int(v)
        else:
            exp[k] = v
    sid = f"SCN-{i:03d}"
    print(sid, exp)
    scenarios.append({"id": sid, "input": si["input"], "covers_reqs": covers[i - 1],
                      "expected": exp, "oracle_risk": {"risk": False, "reason": ""}})

sdir = HERE / "specqa_packet_rocket_l4"
(sdir / "acceptance_tests_draft.json").write_text(
    json.dumps(scenarios, ensure_ascii=False, indent=2), encoding="utf-8")
(sdir / "oracle_risk_review.json").write_text(json.dumps({
    "risky_scenarios": [],
    "notes": [{"risk": False, "reason": "전 시나리오 oracle_risk.risk=false. 레버4 프로브 — 골든은 "
               "rocket_base+참조 engine 실Node 역산."}]
}, ensure_ascii=False, indent=2), encoding="utf-8")
print("WROTE", sdir)
