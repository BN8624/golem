# 전술 카드 l5(루트 맵) 확장 참조를 키0으로 검증 — 게이트·22세계 골든 일치·결정성 확인
"""★키 빌드 전 안전망. tactics_kernel_base + 확장 참조 game_logic(l4+route) + 계약 세계 주입을
워크스페이스로 만들어 build_graded.gate_and_run(static_gate+contract_validator+node 22시나리오)
→ specqa 골든(expected) 대조 + 2회 실행 동일(결정성). engine.js는 불변이라 game_logic만 교체.
"""

import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = "tactics_kernel_base"
PACKET = "planning_packet_tactics_l5"
SPECQA = "specqa_packet_tactics_l5"


def main():
    sys.path.insert(0, str(HERE.parent))
    sys.path.insert(0, str(HERE))
    try:
        from config import force_utf8_stdout
        force_utf8_stdout()
    except Exception:  # noqa: BLE001
        pass

    import build_graded as bg
    from gen_tactics_l5_golden import REF_GAME_LOGIC

    base = HERE / BASE
    manifest = json.loads((base / "module_manifest.json").read_text(encoding="utf-8"))
    contract = json.loads((HERE / PACKET / "contract.json").read_text(encoding="utf-8"))
    scenario_data = contract["data_contract"]["scenario_data"]
    output_keys = contract["data_contract"]["output_contract"]["fields"]
    scenarios = json.loads((HERE / SPECQA / "acceptance_tests_draft.json").read_text(encoding="utf-8"))

    ws = HERE / "build_runs" / "_validate_tactics_l5" / "workspace"
    if ws.parent.exists():
        shutil.rmtree(ws.parent)
    shutil.copytree(base, ws)
    (ws / "module_manifest.json").unlink(missing_ok=True)
    (ws / "src" / "game_logic.js").write_text(REF_GAME_LOGIC, encoding="utf-8")
    (ws / "src" / "scenarios.js").write_text(bg._gen_scenarios_module(scenario_data), encoding="utf-8")

    ok1, reason1, out1 = bg.gate_and_run(ws, manifest, scenarios)
    if not ok1:
        print(f"  GATE FAIL: {reason1}")
        print("RESULT: FAIL")
        return 1

    mismatches = []
    for s in scenarios:
        got = dict(out1.get(s["id"], ()))
        exp = s.get("expected") or {}
        for k in output_keys:
            if k in exp and bg._canon(got.get(k)) != bg._canon(exp[k]):
                mismatches.append(f"{s['id']}.{k}")
    if mismatches:
        print(f"  GOLDEN MISMATCH: {mismatches[:8]}")
        print("RESULT: FAIL")
        return 1

    ok2, _, out2 = bg.gate_and_run(ws, manifest, scenarios)
    if not ok2 or out1 != out2:
        print("  DETERMINISM FAIL: 두 번째 실행이 첫 실행과 다름")
        print("RESULT: FAIL")
        return 1

    print(f"  PASS — gate ok, {len(scenarios)}세계 골든 일치, 결정적(2회 동일)")
    print("RESULT: ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
