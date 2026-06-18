# 정거장 누적카드 l3(서사 비트 A겹) 골든 생성기 — REF_V3(EVACUATE+PING+BEAT) node 역산, 누적회귀(키0)
"""레버3 누적빌드 3장째: 카드1(EVACUATE)+카드2(PING) 위에 카드3(RULE-10 서사 비트)을 얹는다.

흐름:
  1) B2(=station_base+REF_ENGINE_V2, 카드2까지 적용) 베이스 생성 — 카드3 ★키 빌드의 --base.
  2) 누적 시나리오 = 카드2까지 13개(gen_station_l2에서 import) + 비트 신규 2개.
  3) golden = ref_v3(EVACUATE+PING+BEAT) node 역산. 카드2까지 시나리오는 ref_v2와 비교해 비트가
     붙은 곳/안 붙은 곳을 보고(turn 2·3 안 닿으면 바이트동일 = 누적회귀 무결).
"""

import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE / "station_base"
SPECQA = HERE / "specqa_packet_station_l3"

import gen_station_l_golden as g1
import gen_station_l2_golden as g2

# 참조 engine v3 = 카드1 EVACUATE + 카드2 PING + 카드3 BEAT(turn 2→BEAT-1, turn 3→BEAT-2).
REF_ENGINE_V3 = """// 정거장 시나리오 실행 루프 — 액션을 순서대로 적용하고 매 단계 종료(WON/LOST)를 판정한다
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
      // [카드1 RULE-07] 즉시 대피·중단.
      state = { ...state, alerts: [...state.alerts], log: [...state.log] };
      state.gameStatus = 'EVACUATED';
      break;
    }
    if (a && a.action === 'PING') {
      // [카드2 RULE-09] log에 'PING' 덧붙이고 계속.
      state = { ...state, log: [...state.log, 'PING'] };
      state = checkEnd(state, c);
      continue;
    }
    const before = state.turn;
    state = actions.apply(state, a, c);
    state = checkEnd(state, c);
    // [카드3 RULE-10] WAIT 틱 후 PLAYING이면 turn 마일스톤 서사 비트(각 1회).
    if (state.gameStatus === 'PLAYING' && state.turn !== before) {
      if (state.turn === 2) state = { ...state, log: [...state.log, 'BEAT-1'] };
      if (state.turn === 3) state = { ...state, log: [...state.log, 'BEAT-2'] };
    }
  }

  return state;
};
"""

W = g1.W
P = {"action": "PING"}

NEW = [
    g1.scn("SCN-014", ["RULE-10", "RULE-02"], [W, W]),                 # turn 2 → BEAT-1
    g1.scn("SCN-015", ["RULE-10", "RULE-09"], [P, W, W, W]),           # PING + turn 3 → BEAT-1,2
]
SCENARIOS = g2.SCENARIOS + NEW       # 카드2까지 13 + 비트 2 = 15
PREV = set(s["id"] for s in g2.SCENARIOS)   # 카드2까지 = 누적회귀 대상


def main():
    sys.path.insert(0, str(HERE.parent))
    try:
        from config import force_utf8_stdout
        force_utf8_stdout()
    except Exception:  # noqa: BLE001
        pass

    # B2 = 카드2까지 적용된 베이스(생성물·gitignore, 생성기로 키0 재현). 카드3 ★키 빌드의 --base.
    b2 = HERE / "station_base_v2"
    if b2.exists():
        shutil.rmtree(b2)
    shutil.copytree(BASE, b2)
    (b2 / "src" / "engine.js").write_text(g2.REF_ENGINE_V2, encoding="utf-8")

    ref2 = HERE / "_station_ref2b_tmp"
    ref3 = HERE / "_station_ref3_tmp"
    for ref, eng in [(ref2, g2.REF_ENGINE_V2), (ref3, REF_ENGINE_V3)]:
        if ref.exists():
            shutil.rmtree(ref)
        shutil.copytree(BASE, ref)
        (ref / "src" / "engine.js").write_text(eng, encoding="utf-8")

    inputs = [{"input": s["input"]} for s in SCENARIOS]
    for ref in (ref2, ref3):
        (ref / "scenarios.json").write_text(json.dumps(inputs, ensure_ascii=False), encoding="utf-8")

    out = []
    unchanged_ok = True
    for i, s in enumerate(SCENARIOS, 1):
        v3_out = g1.run(ref3, i)
        expected = g1.parse_expected(v3_out)
        out.append({"id": s["id"], "input": s["input"], "covers_reqs": s["covers_reqs"],
                    "expected": expected, "oracle_risk": {"risk": False, "reason": ""}})
        if s["id"] in PREV:
            v2_out = g1.run(ref2, i)
            beat = "BEAT" in v3_out
            same = v2_out == v3_out
            if not beat:  # 비트 안 닿는 기존 시나리오는 바이트동일이어야(누적회귀 무결)
                unchanged_ok = unchanged_ok and same
            print(f"  {s['id']} {'비트추가' if beat else ('v2==v3:'+str(same))}  status={expected['gameStatus']}")
        else:
            print(f"  {s['id']} BEAT신규  status={expected['gameStatus']}  logs={expected['logs']}")

    SPECQA.mkdir(parents=True, exist_ok=True)
    (SPECQA / "acceptance_tests_draft.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    (SPECQA / "oracle_risk_review.json").write_text(json.dumps(
        {"risky_scenarios": [],
         "notes": [{"risk": False,
                    "reason": "전 시나리오 oracle_risk.risk=false. 레버3 누적카드3(서사 비트 A겹) — 골든은 station_base+참조 engine v3(EVACUATE+PING+BEAT) 실Node 역산(모델 독립)."}]},
        ensure_ascii=False, indent=2), encoding="utf-8")

    for ref in (ref2, ref3):
        shutil.rmtree(ref)
    print(f"\n비트 미발동 시나리오 바이트동일(누적회귀): {unchanged_ok}  시나리오 {len(out)}개 → {SPECQA}")
    return 0 if unchanged_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
