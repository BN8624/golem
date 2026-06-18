# 정거장 대형카드 l(EVACUATE) 골든 생성기 — 참조 engine을 node로 역산해 specqa expected를 채운다(키0)
"""레버4 스케일 프로브의 골든은 손계산하지 않고 참조 구현을 실제 실행해 역산한다(모델 독립).

흐름:
  1) station_base를 임시 ref 디렉토리로 복사하고 engine.js만 EVACUATE 버전으로 교체.
  2) 시나리오 입력(actions/constants)을 scenarios.json으로 쓰고 `node main.js --scenario N` 실행.
  3) 출력 줄(key: value)을 타입과 함께 파싱해 expected dict로 만든다.
  4) specqa_packet_station_l/acceptance_tests_draft.json + oracle_risk_review.json 작성.
  5) 회귀 시나리오(EVACUATE 미사용)는 base 엔진 출력과 ref 엔진 출력이 바이트동일인지 검증(회귀 무결).
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE / "station_base"
SPECQA = HERE / "specqa_packet_station_l"

# 참조 engine = base 액션 루프 + EVACUATE 즉시중단 분기. 이 카드가 빌더에게 시키려는 정답 편집이다.
REF_ENGINE = """// 정거장 시나리오 실행 루프 — 액션을 순서대로 적용하고 매 단계 종료(WON/LOST)를 판정한다
const actions = require('./actions');
const { createInitialState, checkEnd } = require('./state');

exports.runScenario = (scenario) => {
  const input = scenario && scenario.input ? scenario.input : {};
  const c = input.constants || {};
  const acts = input.actions || [];

  let state = createInitialState(c);
  state = checkEnd(state, c); // 액션 적용 전 1회 종료 판정

  for (const a of acts) {
    if (state.gameStatus !== 'PLAYING') break; // 종료 상태면 즉시 중단
    if (a && a.action === 'EVACUATE') {
      // [신규 RULE-07] 즉시 대피·중단. 그 외 상태는 직전 그대로 유지(틱·로그·경보 없음).
      state = { ...state, alerts: [...state.alerts], log: [...state.log] };
      state.gameStatus = 'EVACUATED';
      break;
    }
    state = actions.apply(state, a, c);
    state = checkEnd(state, c);
  }

  return state;
};
"""

W = {"action": "WAIT"}


def scn(sid, reqs, actions, constants=None):
    inp = {"actions": actions}
    if constants is not None:
        inp["constants"] = constants
    return {"id": sid, "covers_reqs": reqs, "input": inp}


COLLAPSE = {
    "start": {
        "power": 0, "oxygen": 4, "water": 4, "food": 4, "population": 1,
        "morale": 50, "research": 0, "credits": 0, "solar": 0, "farm": 0, "recycler": 0,
    }
}

SCENARIOS = [
    scn("SCN-001", ["RULE-02", "RULE-05"], [W, W, W]),
    scn("SCN-002", ["RULE-01"], []),
    scn("SCN-003", ["RULE-02", "RULE-05"], [W] * 10),
    scn("SCN-004", ["RULE-05"], [W, W, W], COLLAPSE),
    scn("SCN-005", ["RULE-03", "RULE-04"],
        [{"action": "BUILD", "target": "solar"}, W, {"action": "RATION"}, W]),
    scn("SCN-006", ["RULE-02", "RULE-03"],
        [W, {"action": "BUILD", "target": "farm"}, W, {"action": "BUILD", "target": "recycler"}, W, W]),
    scn("SCN-007", ["RULE-07", "RULE-02"], [W, W, W, W, {"action": "EVACUATE"}, W]),
    scn("SCN-008", ["RULE-07"], [{"action": "EVACUATE"}]),
    scn("SCN-009", ["RULE-06", "RULE-05"], [W] * 12),
    scn("SCN-010", ["RULE-07", "RULE-03"],
        [{"action": "BUILD", "target": "solar"}, W, W, {"action": "EVACUATE"}, W, W]),
]

# EVACUATE를 쓰지 않는 회귀 시나리오 id(base==ref 바이트동일이어야 함).
REGRESSION = {"SCN-001", "SCN-002", "SCN-003", "SCN-004", "SCN-005", "SCN-006", "SCN-009"}

OUTPUT_KEYS = ["turn", "power", "oxygen", "water", "food", "population",
               "morale", "research", "credits", "gameStatus", "alerts", "logs"]


def run(workdir, idx):
    r = subprocess.run(["node", "main.js", "--scenario", str(idx)], cwd=str(workdir),
                       capture_output=True, text=True, encoding="utf-8", timeout=30,
                       stdin=subprocess.DEVNULL)
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
        if k in ("alerts", "logs"):
            exp[k] = json.loads(v)
        elif k == "gameStatus":
            exp[k] = v
        else:
            exp[k] = int(v)
    return exp


def main():
    sys.path.insert(0, str(HERE.parent))
    try:
        from config import force_utf8_stdout
        force_utf8_stdout()
    except Exception:  # noqa: BLE001
        pass

    ref = HERE / "_station_ref_tmp"
    if ref.exists():
        shutil.rmtree(ref)
    shutil.copytree(BASE, ref)
    (ref / "src" / "engine.js").write_text(REF_ENGINE, encoding="utf-8")

    # 빌드 하네스와 동일 포맷: 각 원소는 채점키를 뺀 시나리오 = {"input": {...}} (input 래퍼 유지).
    inputs = [{"input": s["input"]} for s in SCENARIOS]
    (ref / "scenarios.json").write_text(json.dumps(inputs, ensure_ascii=False), encoding="utf-8")
    (BASE / "scenarios.json").write_text(json.dumps(inputs, ensure_ascii=False), encoding="utf-8")

    out = []
    regression_ok = True
    for i, s in enumerate(SCENARIOS, 1):
        ref_out = run(ref, i)
        expected = parse_expected(ref_out)
        rec = {"id": s["id"], "input": s["input"], "covers_reqs": s["covers_reqs"],
               "expected": expected, "oracle_risk": {"risk": False, "reason": ""}}
        out.append(rec)
        if s["id"] in REGRESSION:
            base_out = run(BASE, i)
            same = base_out == ref_out
            regression_ok = regression_ok and same
            print(f"  {s['id']} 회귀 base==ref: {same}  status={expected['gameStatus']}")
        else:
            print(f"  {s['id']} EVACUATE  status={expected['gameStatus']}")

    SPECQA.mkdir(parents=True, exist_ok=True)
    (SPECQA / "acceptance_tests_draft.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    (SPECQA / "oracle_risk_review.json").write_text(json.dumps(
        {"risky_scenarios": [],
         "notes": [{"risk": False,
                    "reason": "전 시나리오 oracle_risk.risk=false. 레버4 스케일 프로브 — 골든은 station_base+참조 engine 실Node 역산(모델 독립)."}]},
        ensure_ascii=False, indent=2), encoding="utf-8")

    # 정리: 임시 ref 삭제, base의 임시 scenarios.json 삭제(빌드 하네스가 워크스페이스에 자체 생성).
    (BASE / "scenarios.json").unlink(missing_ok=True)
    shutil.rmtree(ref)

    print(f"\n회귀 무결: {regression_ok}  시나리오 {len(out)}개 → {SPECQA}")
    return 0 if regression_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
