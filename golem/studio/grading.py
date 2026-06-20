# 빌드 채점 — 출력 정규화(_canon)·다수합의(consensus)·합의 vs 골든 diff·실패 분류(build_graded에서 분리)
"""보수적 분해 B. 순수 함수(stdlib·Counter만, build_graded 역참조 없음=순환 방지). build_graded가 re-export.
정답 앵커는 모델 합의가 아니라 모델 독립 골든(_golden_diff) — 합의는 '계약 빡빡함' 측정용."""

import json
from collections import Counter

MIN_VOTERS = 2  # 합의는 최소 2표부터 의미 — 1표는 자기자신과 자명히 1.0(G55 표본수 오염 가드)


def _canon(val):
    """빌드 stdout 문자열이든 oracle 파이썬 값이든 같은 캐노니컬 JSON 문자열로 만든다.
    표현차(파이썬 repr vs JS JSON: None/'None'·True/'true', dict 키순서·공백, 리스트 출력)를
    제거해 거짓 불일치를 막는다. 파싱 불가한 순수 문자열(예: 'RUNNING')은 그대로 둔다."""
    if isinstance(val, str):
        try:
            val = json.loads(val)
        except (ValueError, TypeError):
            return val
    return json.dumps(val, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def classify_attempt_failure(reason):
    """게이트 실패 사유를 기존 라벨 어휘로 사전분류(키0, G48). 카드 탓 전에 INFRA/HARNESS 먼저 분리.
    INFRA=api·network·쿼터 / HARNESS=우리 도구 크래시 / CARD=생성 코드·계약 난이도."""
    from observability import INFRA_MARKERS
    t = str(reason).lower()
    if t.startswith("infra:") or any(m in t for m in INFRA_MARKERS):
        return "INFRA"
    if t.startswith("harness:"):
        return "HARNESS"
    return "CARD"


def consensus(passed_outputs, gradeable_ids):
    """시나리오별 다수합의 + 일치율. passed_outputs: {build: {scen_id: norm_output}}.
    overall은 표 ≥ MIN_VOTERS 시나리오만 평균(자명한 1표 합의 제외) — 표 부족이면 None(G55)."""
    report = {}
    for sid in gradeable_ids:
        votes = [outs.get(sid) for outs in passed_outputs.values() if outs.get(sid) is not None]
        if not votes:
            report[sid] = {"agree": 0, "total": 0, "rate": 0.0}
            continue
        top, n = Counter(votes).most_common(1)[0]
        report[sid] = {"agree": n, "total": len(votes), "rate": round(n / len(votes), 3)}
    rates = [r["rate"] for r in report.values() if r["total"] >= MIN_VOTERS]
    overall = round(sum(rates) / len(rates), 3) if rates else None
    return overall, report


def _golden_diff(passed_outputs, scenarios, gradeable, contract):
    """합의(다수) vs golden(expected) 자동 대조 — 출력표면 키만. 수작업 diff 제거(키0).
    각 항목에 reconcile.resolve가 쓰는 `input`(채점메타 제외 시나리오)도 담는다."""
    ss = contract.get("data_contract", {}).get("state_shape", {})
    oc = contract.get("data_contract", {}).get("output_contract")
    if oc and oc.get("fields"):
        output_keys = set(oc["fields"])
    else:
        output_keys = {k for k, v in ss.items() if not isinstance(v, dict)}
    grading = {"id", "expected", "oracle_risk", "covers_reqs"}
    by_id = {s["id"]: s for s in scenarios}
    diffs = []
    for sid in gradeable:
        votes = [outs[sid] for outs in passed_outputs.values() if outs.get(sid) is not None]
        if not votes:
            continue
        top = Counter(votes).most_common(1)[0]
        cons = dict(top[0])
        sc = by_id.get(sid, {})
        exp = sc.get("expected") or {}
        d = {k: {"consensus": _canon(cons.get(k)), "oracle": _canon(exp[k])}
             for k in (set(exp) & output_keys) if _canon(cons.get(k)) != _canon(exp[k])}
        if d:
            diffs.append({"id": sid, "input": {k: v for k, v in sc.items() if k not in grading},
                          "differing": d, "agreement": {"agree": top[1], "total": len(votes)}})
    return diffs
