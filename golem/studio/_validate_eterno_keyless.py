# 에테르노 IF 카드 파이프라인을 키0으로 검증 — 올바른 참조 패치가 하네스 게이트를 통과하고 골든과 일치하는지 확인
"""키 쓰기 전 안전망. 각 카드 레벨에 대해:
  1) eterno_base를 워크스페이스로 복사, touched 모듈을 그 카드의 참조 버전(specqa의 ref/)으로 교체(=모델이 내야 할 정답).
  2) build_graded.gate_and_run으로 static_gate + contract_validator + node 스모크를 실제로 돌린다.
  3) 각 시나리오 출력이 specqa의 expected 골든과 출력표면 키 전부 일치하는지 _canon으로 대조.
  4) base경로 회귀 시나리오(SCN-001~005)는 eterno_base/golden과도 바이트 동일한지 확인.
하나라도 실패하면 비0 종료(CI 편입용).
"""

import importlib
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# (레벨, specqa 디렉토리, 계약 디렉토리, {복원할 상대경로: specqa/ref 내 소스 파일}, base경로 회귀 시나리오 id)
CARDS = [
    ("l1", "specqa_packet_eterno_l1", "planning_packet_eterno_l1",
     {"src/scenes.js": "scenes.js"},
     ["SCN-001", "SCN-002", "SCN-003", "SCN-004", "SCN-005"]),
]


def main():
    sys.path.insert(0, str(HERE.parent))  # config
    sys.path.insert(0, str(HERE))         # studio 모듈
    try:
        from config import force_utf8_stdout
        force_utf8_stdout()
    except Exception:  # noqa: BLE001
        pass

    import build_graded as bg

    base = HERE / "eterno_base"
    manifest = json.loads((base / "module_manifest.json").read_text(encoding="utf-8"))
    base_golden = base / "golden"

    allok = True
    for level, specqa_name, packet_name, touched, regression_ids in CARDS:
        output_keys = [k for k, v in
                       json.loads((HERE / packet_name / "contract.json")
                                  .read_text(encoding="utf-8"))["data_contract"]["state_shape"].items()
                       if not isinstance(v, dict)]
        specqa = HERE / specqa_name
        scenarios = json.loads((specqa / "acceptance_tests_draft.json").read_text(encoding="utf-8"))
        scen_inputs = [{"input": s["input"]} for s in scenarios]

        ws = HERE / "build_runs" / f"_validate_eterno_{level}" / "workspace"
        if ws.parent.exists():
            shutil.rmtree(ws.parent)
        shutil.copytree(base, ws)
        for rel, srcfile in touched.items():
            (ws / rel).write_text((specqa / "ref" / srcfile).read_text(encoding="utf-8"), encoding="utf-8")
        (ws / "module_manifest.json").unlink(missing_ok=True)  # gate가 parent에 씀
        (ws / "scenarios.json").write_text(json.dumps(scen_inputs, ensure_ascii=False), encoding="utf-8")

        ok, reason, outputs = bg.gate_and_run(ws, manifest, scenarios)
        if not ok:
            print(f"  [{level}] GATE FAIL: {reason}")
            allok = False
            continue

        mismatches = []
        for s in scenarios:
            sid = s["id"]
            got = dict(outputs.get(sid, ()))
            exp = s["expected"]
            for k in output_keys:
                if k in exp and bg._canon(got.get(k)) != bg._canon(exp[k]):
                    mismatches.append(f"{sid}.{k}")
        if mismatches:
            print(f"  [{level}] GOLDEN MISMATCH: {mismatches[:6]}")
            allok = False
            continue

        # base경로 회귀: card golden(SCN-00N) == base golden(SCN-N) 바이트 동일
        reg_bad = []
        for i, sid in enumerate(regression_ids, 1):
            bg_path = base_golden / f"SCN-{i}.txt"
            cg_path = specqa / "golden" / f"{sid}.txt"
            if not bg_path.exists() or bg_path.read_text(encoding="utf-8") != cg_path.read_text(encoding="utf-8"):
                reg_bad.append(f"{sid}!=SCN-{i}")
        if reg_bad:
            print(f"  [{level}] REGRESSION DRIFT: {reg_bad}")
            allok = False
        else:
            print(f"  [{level}] PASS — gate ok, {len(scenarios)}시나리오 골든 일치, 회귀 {len(regression_ids)}건 base와 바이트동일")

    print("RESULT:", "ALL PASS" if allok else "FAIL")
    return 0 if allok else 1


if __name__ == "__main__":
    raise SystemExit(main())
