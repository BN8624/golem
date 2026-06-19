# 전술 커널 base를 키0으로 검증 — 동결된 base가 게이트 통과·6세계 골든 일치·결정적인지 확인
"""키 쓰기 전 안전망. tactics_kernel_base를 워크스페이스로 복사 → build_graded.gate_and_run
(static_gate+contract_validator+node 6시나리오) → specqa 골든(expected) 대조 + 2회 실행 동일(결정성).
카드 누적 base가 회귀 없이 1.0을 유지하는지의 회귀잠금.
"""

import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

BASE = "tactics_kernel_base"
PACKET = "planning_packet_tactics_kernel"
SPECQA = "specqa_packet_tactics_kernel"


def main():
    sys.path.insert(0, str(HERE.parent))
    sys.path.insert(0, str(HERE))
    try:
        from config import force_utf8_stdout
        force_utf8_stdout()
    except Exception:  # noqa: BLE001
        pass

    import build_graded as bg

    base = HERE / BASE
    manifest = json.loads((base / "module_manifest.json").read_text(encoding="utf-8"))
    contract = json.loads((HERE / PACKET / "contract.json").read_text(encoding="utf-8"))
    oc = contract.get("data_contract", {}).get("output_contract") or {}
    output_keys = oc.get("fields") or [
        k for k, v in contract["data_contract"]["state_shape"].items() if not isinstance(v, dict)]
    scenarios = json.loads((HERE / SPECQA / "acceptance_tests_draft.json").read_text(encoding="utf-8"))

    ws = HERE / "build_runs" / "_validate_tactics" / "workspace"
    if ws.parent.exists():
        shutil.rmtree(ws.parent)
    shutil.copytree(base, ws)
    (ws / "module_manifest.json").unlink(missing_ok=True)

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
