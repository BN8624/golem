# 전술 본선 검증 정본 — 9카드 골든 회귀 + 안정 base strict 승격검사 + 하네스 CI를 한 명령으로 (키0)
"""수정 후 반드시 실행하는 본선 검증 단일 진입점. _validate_tactics_l*_keyless 9개를 한 루프로 통합.

  1) 카드 l1~l9: tactics_kernel_base + 검증 참조(gen_tactics_lN_golden.REF) + 계약 세계 주입 →
     build_graded.gate_and_run(static_gate+contract_validator strict=False+node) → specqa 골든 일치 + 결정성(2회).
  2) 승격 게이트: 안정 baseline(tactics_base_l8)을 contract_validator strict=True로(구조 부패 차단).
  3) 하네스 CI: run_keyless.py(compileall·replay·레버4·게이트#2·FROZEN#1).
전부 PASS여야 그린. 정본 명령: python golem/validators/verify_tactics.py
"""
import sys as _sys
from pathlib import Path as _Path
_PKG = _Path(__file__).resolve().parents[1]
for _p in (str(_PKG), str(_PKG / "core"), str(_PKG / "tools"), str(_PKG / "tactics"),
           str(_PKG / "validators"), str(_PKG.parent)):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)
from paths import (PKG, REPO_ROOT, CORE, TOOLS, TACTICS, VALIDATORS,  # noqa: E402,F401
                   BASES, PACKETS, PLAY, FIXTURES, SCHEMAS, BUILD_RUNS, SCRATCH)

import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = BASES / "tactics_kernel_base"
LEVELS = [f"l{i}" for i in range(1, 10)]   # l1~l9
STABLE = "l8"                               # 안정 baseline(strict 승격검사 대상). 실험=l9.
OUTPUT_KEYS = ["status", "turn", "hero_hp", "hero_pos", "enemies"]


def _card_regression(bg):
    """카드 l1~l9: 참조 + 계약 세계로 gate+골든+결정성. 실패 목록 반환(빈=통과)."""
    from importlib import import_module
    fails = []
    manifest = json.loads((BASE / "module_manifest.json").read_text(encoding="utf-8"))
    manifest_v = {"schema_version": "0.1", "module_format": "commonjs", **manifest}
    for lvl in LEVELS:
        pkt = PACKETS / f"planning_packet_tactics_{lvl}"
        spq = PACKETS / f"specqa_packet_tactics_{lvl}"
        if not (pkt / "contract.json").exists():
            fails.append(f"{lvl}: 패킷 없음")
            continue
        ref = import_module(f"gen_tactics_{lvl}_golden").REF_GAME_LOGIC
        contract = json.loads((pkt / "contract.json").read_text(encoding="utf-8"))
        scenarios = json.loads((spq / "acceptance_tests_draft.json").read_text(encoding="utf-8"))
        ws = BUILD_RUNS / "_verify_tactics" / lvl
        if ws.exists():
            shutil.rmtree(ws)
        shutil.copytree(BASE, ws)
        (ws / "module_manifest.json").unlink(missing_ok=True)
        (ws / "src" / "game_logic.js").write_text(ref, encoding="utf-8")
        (ws / "src" / "scenarios.js").write_text(
            bg._gen_scenarios_module(contract["data_contract"]["scenario_data"]), encoding="utf-8")
        ok1, reason, out1 = bg.gate_and_run(ws, manifest_v, scenarios)
        if not ok1:
            fails.append(f"{lvl}: gate {reason}")
            continue
        bad = [f"{s['id']}.{k}" for s in scenarios for k in OUTPUT_KEYS
               if k in (s.get("expected") or {})
               and bg._canon(dict(out1.get(s["id"], ())).get(k)) != bg._canon(s["expected"][k])]
        if bad:
            fails.append(f"{lvl}: 골든 {bad[:4]}")
            continue
        ok2, _, out2 = bg.gate_and_run(ws, manifest_v, scenarios)
        if not ok2 or out1 != out2:
            fails.append(f"{lvl}: 비결정")
        print(f"  [{lvl}] {len(scenarios)}세계 gate·골든·결정성 OK")
    shutil.rmtree(BUILD_RUNS / "_verify_tactics", ignore_errors=True)
    return fails


def main():
    sys.path.insert(0, str(HERE))
    sys.path.insert(0, str(HERE.parent))
    sys.path.insert(0, str(HERE.parent.parent))
    try:
        from config import force_utf8_stdout
        force_utf8_stdout()
    except Exception:  # noqa: BLE001
        pass
    import build_graded as bg
    import contract_validator

    print("== 1) 카드 l1~l9 골든 회귀 ==")
    card_fails = _card_regression(bg)

    print(f"== 2) 승격 게이트: tactics_base_{STABLE} strict=True ==")
    stable = BASES / f"tactics_base_{STABLE}"
    promo_fail = None
    if not stable.exists():
        promo_fail = f"{stable.name} 없음"
    else:
        cv = contract_validator.validate(stable, stable / "module_manifest.json", strict=True)
        if not cv.get("ok", not cv.get("errors")):
            promo_fail = f"strict 위반 {cv.get('errors', [])[:3]}"
    print(f"  {STABLE}: {'OK' if not promo_fail else promo_fail}")

    print("== 3) 하네스 CI: run_keyless.py ==")
    rk = subprocess.run([sys.executable, str(VALIDATORS / "run_keyless.py")],
                        cwd=str(HERE.parent.parent), capture_output=True, text=True, encoding="utf-8")
    rk_ok = "RESULT: ALL PASS" in rk.stdout
    print("  run_keyless:", "ALL PASS" if rk_ok else "FAIL\n" + rk.stdout[-500:])

    ok = not card_fails and not promo_fail and rk_ok
    print("\n=== verify_tactics:", "ALL PASS ===" if ok else f"FAIL === 카드{card_fails} 승격={promo_fail} ci={rk_ok}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
