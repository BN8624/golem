# 탐정 IF 카드 파이프라인을 키0으로 검증 — 올바른 참조 패치가 하네스 게이트를 통과하고 골든과 일치하는지 확인
"""키 쓰기 전 안전망. 각 카드 레벨에 대해:
  1) detective_base를 워크스페이스로 복사, touched 모듈을 그 카드의 참조 버전으로 교체(=모델이 내야 할 정답).
  2) build_graded.gate_and_run으로 static_gate + contract_validator + node 스모크를 실제로 돌린다.
  3) 각 시나리오 출력이 specqa의 expected 골든과 출력표면 키 전부 일치하는지 _canon으로 대조.
하나라도 실패하면 비0 종료(CI 편입용).
"""

import importlib
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# (레벨, 골든생성기 모듈, {복원할 상대경로: 생성기 내 누적 참조 소스 속성명}, specqa 디렉토리명, 계약 디렉토리명)
# touched 매핑은 "정답 전체 게임을 복원하는 데 필요한 모듈" = base와 다른 모듈 전부(누적). 빌드의 inject-modules와 별개.
CARDS = [
    ("l1", "gen_detective_l1_golden",
     {"src/scenes.js": "REF_SCENES", "src/beats.js": "REF_BEATS"},
     "specqa_packet_detective_l1", "planning_packet_detective_l1"),
    ("l2", "gen_detective_l2_golden",
     {"src/scenes.js": "REF_SCENES", "src/beats.js": "REF_BEATS"},
     "specqa_packet_detective_l2", "planning_packet_detective_l2"),
    ("l3", "gen_detective_l3_golden",
     {"src/scenes.js": "REF_SCENES", "src/beats.js": "REF_BEATS"},
     "specqa_packet_detective_l3", "planning_packet_detective_l3"),
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

    base = HERE / "detective_base"
    manifest = json.loads((base / "module_manifest.json").read_text(encoding="utf-8"))

    allok = True
    for level, gen_name, touched, specqa_name, packet_name in CARDS:
        gen = importlib.import_module(gen_name)
        output_keys = [k for k, v in
                       json.loads((HERE / packet_name / "contract.json")
                                  .read_text(encoding="utf-8"))["data_contract"]["state_shape"].items()
                       if not isinstance(v, dict)]
        scenarios = json.loads((HERE / specqa_name / "acceptance_tests_draft.json").read_text(encoding="utf-8"))
        scen_inputs = [{"input": s["input"]} for s in scenarios]

        ws = HERE / "build_runs" / f"_validate_detective_{level}" / "workspace"
        if ws.parent.exists():
            shutil.rmtree(ws.parent)
        shutil.copytree(base, ws)
        for rel, attr in touched.items():
            (ws / rel).write_text(getattr(gen, attr), encoding="utf-8")
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
        else:
            print(f"  [{level}] PASS — gate ok, {len(scenarios)}시나리오 골든 일치")

    print("RESULT:", "ALL PASS" if allok else "FAIL")
    return 0 if allok else 1


if __name__ == "__main__":
    raise SystemExit(main())
