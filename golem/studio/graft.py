# 카드 그래프트 자동화 — 이전 패킷 + 카드 델타(새 REQ·새 세계·참조 game_logic)로 lN 패킷을 조립·키0 검증
"""손그래프트(카드당 contract 캐리포워드 + gen + specqa + validator 4파일)를 하네스로 흡수한다.
규율: 새 REQ는 자기완결, 이전 REQ는 verbatim 캐리(back-edit 금지). 골든은 참조엔진(모델 독립) 실Node 역산.

graft(level, prev_level, new_req, new_state, new_worlds, ref_src, prev_ref_src):
  1) 이전 contract.rules verbatim + [new_req], 이전 scenario_data + new_worlds, state_shape 병합 → lN contract 조립.
  2) 참조(ref_src)와 이전참조(prev_ref_src)를 base에 얹어 전 세계 실Node 실행.
  3) 회귀(이전 세계) prev_ref==ref 바이트동일, 신규 세계 differ → 가산성 자동 보증.
  4) gate(static_gate+contract_validator+node) + 골든(ref 출력) + 결정성(2회) → specqa 작성.
다음 단계(★키): 골렘이 base-델타 모드로 new_req/new_worlds/ref 델타를 직접 뱉으면 이 조립이 끝까지 무인.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE / "tactics_kernel_base"
OUTPUT_KEYS = ["status", "turn", "hero_hp", "hero_pos", "enemies"]


def _run(workdir, idx):
    r = subprocess.run(["node", "main.js", "--scenario", str(idx)], cwd=str(workdir),
                       capture_output=True, text=True, encoding="utf-8", timeout=30, stdin=subprocess.DEVNULL)
    if r.returncode != 0:
        raise RuntimeError(f"node 실패 scn{idx}: {r.stderr[:200]}")
    return r.stdout


def _parse(stdout):
    exp = {}
    for line in stdout.splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        k, v = k.strip(), v.strip()
        if k == "turn":
            exp[k] = int(v)
        elif k in ("hero_pos", "enemies"):
            exp[k] = json.loads(v)
        elif k == "hero_hp":
            exp[k] = int(v)
        else:
            exp[k] = v
    return exp


def _build_ref(name, game_logic_src, scenarios_js):
    ref = HERE / name
    if ref.exists():
        shutil.rmtree(ref)
    shutil.copytree(BASE, ref)
    (ref / "module_manifest.json").unlink(missing_ok=True)
    (ref / "src" / "game_logic.js").write_text(game_logic_src, encoding="utf-8")
    (ref / "src" / "scenarios.js").write_text(scenarios_js, encoding="utf-8")
    return ref


def assemble_contract(prev_contract, new_req, new_state, new_worlds):
    """이전 계약에 카드 델타를 가산 — 이전 REQ verbatim, 새 REQ append, 세계 append, state 병합."""
    dc = json.loads(json.dumps(prev_contract))  # deep copy
    d = dc["data_contract"]
    d["rules"] = list(d["rules"]) + [new_req]
    d["scenario_data"] = list(d["scenario_data"]) + new_worlds
    for k, v in (new_state or {}).items():
        d["state_shape"][k] = v
    return dc


def graft(level, prev_level, new_req, new_state, new_worlds, ref_src, prev_ref_src,
          packet_dir=None, write=True):
    """카드 델타로 lN 패킷 조립 + 키0 검증. 반환=(contract, specqa, ok)."""
    sys.path.insert(0, str(HERE.parent))
    sys.path.insert(0, str(HERE))
    try:
        from config import force_utf8_stdout
        force_utf8_stdout()
    except Exception:  # noqa: BLE001
        pass
    import build_graded as bg

    prev_pkt = HERE / f"planning_packet_tactics_{prev_level}"
    prev_contract = json.loads((prev_pkt / "contract.json").read_text(encoding="utf-8"))
    prev_n = len(prev_contract["data_contract"]["scenario_data"])

    contract = assemble_contract(prev_contract, new_req, new_state, new_worlds)
    scenario_data = contract["data_contract"]["scenario_data"]
    manifest = json.loads((BASE / "module_manifest.json").read_text(encoding="utf-8"))
    scenarios_js = bg._gen_scenarios_module(scenario_data)

    refN = _build_ref(f"_graft_ref_{level}_tmp", ref_src, scenarios_js)
    refP = _build_ref(f"_graft_refprev_{level}_tmp", prev_ref_src, scenarios_js)

    specqa = []
    regression_ok = True
    new_fired = 0
    for i, s in enumerate(scenario_data, 1):
        oN = _run(refN, i)
        oP = _run(refP, i)
        specqa.append({"id": s["id"], "input": {"args": ["--scenario", str(i)]},
                       "covers_reqs": s.get("covers_reqs", []),
                       "expected": _parse(oN), "oracle_risk": {"risk": False, "reason": ""}})
        if i <= prev_n:
            regression_ok = regression_ok and (oN == oP)
        elif oN != oP:
            new_fired += 1
    shutil.rmtree(refN)
    shutil.rmtree(refP)

    new_total = len(scenario_data) - prev_n
    # gate + 골든 + 결정성(조립 참조가 게이트 클린·결정적인지)
    ws = HERE / "build_runs" / f"_graft_{level}" / "workspace"
    if ws.parent.exists():
        shutil.rmtree(ws.parent)
    shutil.copytree(BASE, ws)
    (ws / "module_manifest.json").unlink(missing_ok=True)
    (ws / "src" / "game_logic.js").write_text(ref_src, encoding="utf-8")
    (ws / "src" / "scenarios.js").write_text(scenarios_js, encoding="utf-8")
    g1, reason, out1 = bg.gate_and_run(ws, {"schema_version": "0.1", "module_format": "commonjs", **manifest}, specqa)
    golden_ok = g1 and all(
        bg._canon(dict(out1.get(s["id"], ())).get(k)) == bg._canon(s["expected"][k])
        for s in specqa for k in OUTPUT_KEYS if k in s["expected"])
    g2, _, out2 = bg.gate_and_run(ws, {"schema_version": "0.1", "module_format": "commonjs", **manifest}, specqa)
    det_ok = g2 and out1 == out2

    ok = regression_ok and new_fired == new_total and g1 and golden_ok and det_ok
    print(f"  [{level}] 조립 {len(scenario_data)}세계(회귀 {prev_n}+신규 {new_total}) | "
          f"회귀무결={regression_ok} 신규발동={new_fired}/{new_total} gate={g1} golden={golden_ok} det={det_ok} → {'OK' if ok else 'FAIL'}")
    if not g1:
        print(f"    GATE: {reason}")

    if write and ok:
        pkt = packet_dir or (HERE / f"planning_packet_tactics_{level}")
        spq = HERE / f"specqa_packet_tactics_{level}"
        pkt.mkdir(parents=True, exist_ok=True)
        spq.mkdir(parents=True, exist_ok=True)
        (pkt / "contract.json").write_text(json.dumps(contract, ensure_ascii=False, indent=2), encoding="utf-8")
        (spq / "acceptance_tests_draft.json").write_text(json.dumps(specqa, ensure_ascii=False, indent=2), encoding="utf-8")
        (spq / "oracle_risk_review.json").write_text(json.dumps(
            {"risky_scenarios": [], "notes": [{"risk": False, "reason": f"graft.py 자동 그래프트 {level} — 골든은 참조엔진 실Node 역산(모델 독립)."}]},
            ensure_ascii=False, indent=2), encoding="utf-8")
    return contract, specqa, ok


def _demo_l7():
    """l7을 l6 + 델타(REQ-020·config·SCN-026~028·l7 참조)로 재조립 → 커밋된 l7 specqa와 동치 검증."""
    from gen_tactics_l7_golden import REF_GAME_LOGIC as L7
    from gen_tactics_l6_golden import REF_GAME_LOGIC as L6

    l7 = json.loads((HERE / "planning_packet_tactics_l7" / "contract.json").read_text(encoding="utf-8"))["data_contract"]
    new_req = next(r for r in l7["rules"] if r.startswith("REQ-020"))
    new_worlds = [w for w in l7["scenario_data"] if w["id"] in ("SCN-026", "SCN-027", "SCN-028")]
    new_state = {"config": l7["state_shape"]["config"]}

    contract, specqa, ok = graft("l7", "l6", new_req, new_state, new_worlds, L7, L6, write=False)

    committed = json.loads((HERE / "specqa_packet_tactics_l7" / "acceptance_tests_draft.json").read_text(encoding="utf-8"))
    gen_exp = {s["id"]: s["expected"] for s in specqa}
    com_exp = {s["id"]: s["expected"] for s in committed}
    specqa_match = gen_exp == com_exp
    # 조립 계약: 이전 REQ verbatim + 새 REQ, 세계 = l6 + 3
    rules_carry = contract["data_contract"]["rules"][:19] == json.loads(
        (HERE / "planning_packet_tactics_l6" / "contract.json").read_text(encoding="utf-8"))["data_contract"]["rules"]
    print(f"  [demo] specqa 골든 == 커밋된 l7: {specqa_match} | 이전 REQ verbatim 캐리: {rules_carry} | 검증 ok: {ok}")
    return 0 if (ok and specqa_match and rules_carry) else 1


if __name__ == "__main__":
    raise SystemExit(_demo_l7())
