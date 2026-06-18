# 정거장 누적카드 l2(PING) 골든 생성기 — REF_V2(EVACUATE+PING)를 node로 역산, 누적회귀 검증(키0)
"""레버3 누적빌드: 카드1(EVACUATE) 위에 카드2(PING)를 얹는다. 골든은 손계산 않고 참조 구현 실행으로 역산.

흐름:
  1) station_base를 ref_v1(EVACUATE만)·ref_v2(EVACUATE+PING) 두 임시 디렉토리로 복사, engine.js 교체.
  2) 누적 시나리오 = 카드1 10개(gen_station_l_golden에서 import) + PING 신규 3개.
  3) 각 시나리오 golden = ref_v2 node 출력. 카드1 시나리오는 ref_v1==ref_v2 바이트동일 검증(누적회귀 무결).
  4) specqa_packet_station_l2/acceptance_tests_draft.json + oracle_risk_review.json 작성.
"""

import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE / "station_base"
SPECQA = HERE / "specqa_packet_station_l2"

import gen_station_l_golden as g1  # 카드1 시나리오·참조 engine·실행 헬퍼 재사용

# 참조 engine v2 = 카드1 EVACUATE 분기 + 카드2 PING 분기. 이 카드가 빌더에게 시키려는 정답 편집이다.
REF_ENGINE_V2 = """// 정거장 시나리오 실행 루프 — 액션을 순서대로 적용하고 매 단계 종료(WON/LOST)를 판정한다
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
      // [카드1 RULE-07] 즉시 대피·중단. 그 외 상태는 직전 그대로 유지(틱·로그·경보 없음).
      state = { ...state, alerts: [...state.alerts], log: [...state.log] };
      state.gameStatus = 'EVACUATED';
      break;
    }
    if (a && a.action === 'PING') {
      // [카드2 RULE-09] log에 'PING' 한 줄 덧붙이고 계속. turn·자원·틱·경보·gameStatus 불변.
      state = { ...state, log: [...state.log, 'PING'] };
      state = checkEnd(state, c);
      continue;
    }
    state = actions.apply(state, a, c);
    state = checkEnd(state, c);
  }

  return state;
};
"""

W = g1.W
P = {"action": "PING"}

# 누적 시나리오 = 카드1 10개 + PING 신규 3개(PING 단독·틱 사이·EVACUATE와 합성).
NEW = [
    g1.scn("SCN-011", ["RULE-09"], [P]),
    g1.scn("SCN-012", ["RULE-09", "RULE-02"], [W, P, W]),
    g1.scn("SCN-013", ["RULE-09", "RULE-07"], [P, {"action": "EVACUATE"}, W]),
]
SCENARIOS = g1.SCENARIOS + NEW
REGRESSION = set(s["id"] for s in g1.SCENARIOS)  # 카드1 전부 = 누적회귀(ref_v1==ref_v2 바이트동일)


def main():
    sys.path.insert(0, str(HERE.parent))
    try:
        from config import force_utf8_stdout
        force_utf8_stdout()
    except Exception:  # noqa: BLE001
        pass

    # B1 = 카드1(EVACUATE) 적용 후 베이스 = station_base + REF_ENGINE. 카드2 ★키 빌드의 --base다.
    # 생성물(gitignore)이지만 이 생성기로 키0 재현된다(★키 카드1 출력과 행동 동일 = golden_diff 0).
    b1 = HERE / "station_base_v1"
    if b1.exists():
        shutil.rmtree(b1)
    shutil.copytree(BASE, b1)
    (b1 / "src" / "engine.js").write_text(g1.REF_ENGINE, encoding="utf-8")

    ref1 = HERE / "_station_ref1_tmp"
    ref2 = HERE / "_station_ref2_tmp"
    for ref, eng in [(ref1, g1.REF_ENGINE), (ref2, REF_ENGINE_V2)]:
        if ref.exists():
            shutil.rmtree(ref)
        shutil.copytree(BASE, ref)
        (ref / "src" / "engine.js").write_text(eng, encoding="utf-8")

    inputs = [{"input": s["input"]} for s in SCENARIOS]
    for ref in (ref1, ref2):
        (ref / "scenarios.json").write_text(json.dumps(inputs, ensure_ascii=False), encoding="utf-8")

    out = []
    regression_ok = True
    for i, s in enumerate(SCENARIOS, 1):
        v2_out = g1.run(ref2, i)
        expected = g1.parse_expected(v2_out)
        out.append({"id": s["id"], "input": s["input"], "covers_reqs": s["covers_reqs"],
                    "expected": expected, "oracle_risk": {"risk": False, "reason": ""}})
        if s["id"] in REGRESSION:  # 누적회귀: PING 안 쓰면 카드1(ref_v1) 출력과 바이트동일이어야
            v1_out = g1.run(ref1, i)
            same = v1_out == v2_out
            regression_ok = regression_ok and same
            print(f"  {s['id']} 누적회귀 v1==v2: {same}  status={expected['gameStatus']}")
        else:
            print(f"  {s['id']} PING  status={expected['gameStatus']}  logs={expected['logs']}")

    SPECQA.mkdir(parents=True, exist_ok=True)
    (SPECQA / "acceptance_tests_draft.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    (SPECQA / "oracle_risk_review.json").write_text(json.dumps(
        {"risky_scenarios": [],
         "notes": [{"risk": False,
                    "reason": "전 시나리오 oracle_risk.risk=false. 레버3 누적카드 — 골든은 station_base+참조 engine v2(EVACUATE+PING) 실Node 역산(모델 독립)."}]},
        ensure_ascii=False, indent=2), encoding="utf-8")

    for ref in (ref1, ref2):
        shutil.rmtree(ref)
    print(f"\n누적회귀 무결: {regression_ok}  시나리오 {len(out)}개(카드1 {len(REGRESSION)}+PING {len(NEW)}) → {SPECQA}")
    return 0 if regression_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
