# 빌드 게이트 실행 — static_gate + contract_validator(strict=False) + node 스모크로 시나리오 출력 수집(키0 경로)
"""build_graded에서 분리(보수적 분해 B). gate_and_run은 검증 스크립트·verify_tactics가 매번 호출하는 key0 핵심.
의존은 static_gate·contract_validator·stdlib뿐(build_graded 역참조 없음=순환 방지). build_graded는 이걸 re-export.
"""

import json
import subprocess

import contract_validator
import static_gate


def _norm_output(stdout):
    """key:value 출력을 정규화(dict) — 합의 비교용. 줄 순서 무관."""
    d = {}
    for line in stdout.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            d[k.strip()] = v.strip()
    if "logs" in d:  # 공백·따옴표 차이로 헛갈리지 않게 JSON 정규화(순서는 보존)
        try:
            d["logs"] = json.dumps(json.loads(d["logs"]))
        except Exception:  # noqa: BLE001
            pass
    return tuple(sorted(d.items()))


def gate_and_run(workspace, manifest, scenarios):
    """게이트 통과 시 채점가능 시나리오를 실행해 출력 dict 반환. (ok, reason, outputs) ."""
    sg = static_gate.check(str(workspace))
    if not sg["ok"]:
        return False, f"static_gate: {sg['reason']}", {}
    mpath = workspace.parent / "module_manifest.json"
    mpath.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    cv = contract_validator.validate(workspace, mpath, strict=False)  # 빌드=자유구현 수용
    if not cv["ok"]:
        return False, f"contract_validator: {cv['errors'][:2]}", {}
    outputs = {}
    for i, sc in enumerate(scenarios, 1):
        try:
            r = subprocess.run(["node", "main.js", "--scenario", str(i)], cwd=str(workspace),
                               capture_output=True, text=True, encoding="utf-8", errors="replace",
                               timeout=30, stdin=subprocess.DEVNULL)
        except subprocess.TimeoutExpired:
            return False, f"smoke SCN{i}: 타임아웃", {}
        if r.returncode != 0:
            return False, f"smoke SCN{i}: exit {r.returncode} out={r.stdout[:80]!r}", {}
        if i == 1 and ":" not in r.stdout:
            return False, f"smoke SCN1: 출력 형식 의심 out={r.stdout[:80]!r}", {}
        outputs[sc["id"]] = _norm_output(r.stdout)
    return True, "ok", outputs
