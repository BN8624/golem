# Golem Studio 자율 oracle self-suggest — 31B가 자기 불일치를 보고 "어느 계약줄이 모호한지+고친 rules"를 스스로 제안
"""frontier 캡스톤(G60~63 다음). G61·G63에선 모호성을 읽고 어느 rule을 박을지 정한 게 *사람*이다.
self-suggest는 그 read->propose 단계를 31B가 직접 하는지 测정한다. 되면 자율 oracle은 "탐지"를 넘어
"자가 처방"까지 닫는다.

방법(키 ★):
  1) 원본(모호) 계약 rules + 자기 예측 vs 골든 불일치(이전 auto_oracle 런)를 31B에 준다.
     답은 안 알려준다 — enum을 'FINISHED'로 박으라거나 번식 자격이 굶주림 전이라고 말하지 않는다.
  2) 31B가 {diagnosis, patched_rules}를 제안한다.
  3) patched_rules를 박은 변형 패킷을 쓰고 auto_oracle로 재측정 → G63(1.0)과 비교.

채점: ① 두 모호성(status enum·번식)을 진단에 다 짚었나 ② 처방을 박으면 수렴하나(=사람표 RULE과 동급 이상).

사용:
  python golem/studio/self_suggest.py --packet planning_packet_eco --specqa specqa_packet_eco \
      --prior build_runs/autooracle-20260618-102954/auto_oracle_result.json    # ★키
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent.parent))

from planning import _extract_json    # noqa: E402
import auto_oracle                    # noqa: E402

MODEL_31 = "gemma-4-31b-it"

_SUGGEST_PROMPT = """You are auditing the FROZEN RULES of a deterministic, turn-based game. An automated
ORACLE hand-executed these rules to compute each scenario's final output, but its results DISAGREE with the
trusted GOLDEN answers on some keys. By definition the GOLDEN is correct, so a disagreement means the RULES
are AMBIGUOUS or UNDER-SPECIFIED (or contradict the golden) — not that the golden is wrong.

FROZEN RULES:
{rules}

DISAGREEMENTS (each: the scenario input, the trusted GOLDEN output, and the oracle's ACTUAL outputs across
retries). Study where the oracle landed differently from the golden and infer what the rules failed to pin:
{evidence}

Your job: identify which rule(s) are ambiguous/under-specified/contradictory, then REWRITE the rules so that
a deterministic executor following them LITERALLY would reproduce the GOLDEN for every scenario. Make the
MINIMAL changes needed. Do not touch rules that are not implicated. Keep the same overall structure.

Output ONE JSON object EXACTLY, no prose:
{{
  "diagnosis": [{{"rule": "<short quote of the ambiguous rule>", "issue": "<why it is ambiguous>", "fix": "<what you pin>"}}],
  "patched_rules": ["<the full, final, ordered list of rule strings>"]
}}"""


def _build_evidence(prior, scenarios_by_id):
    """이전 auto_oracle 런에서 불일치 시나리오만 추려 증거 블록을 만든다(골든 + 서로 다른 예측들)."""
    blocks = []
    for p in prior["per_scenario"]:
        bad = {k: v for k, v in p["key_accuracy"].items() if v < 1.0}
        if not bad:
            continue
        sc = scenarios_by_id.get(p["id"], {})
        inp = sc.get("input") or {k: v for k, v in sc.items()
                                   if k not in ("id", "expected", "oracle_risk", "covers_reqs")}
        # 서로 다른 예측만(중복 제거, 순서 보존)
        seen, uniq = set(), []
        for pr in p["preds"]:
            s = json.dumps(pr, sort_keys=True, ensure_ascii=False)
            if s not in seen:
                seen.add(s)
                uniq.append(pr)
        blocks.append(
            f"- {p['id']} (disagreed on keys {list(bad)}):\n"
            f"    input:  {json.dumps(inp, ensure_ascii=False)}\n"
            f"    GOLDEN: {json.dumps(p['golden'], ensure_ascii=False)}\n"
            f"    oracle outputs: " + " | ".join(json.dumps(u, ensure_ascii=False) for u in uniq))
    return "\n".join(blocks)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--packet", default="planning_packet_eco")
    ap.add_argument("--specqa", default="specqa_packet_eco")
    ap.add_argument("--prior", required=True, help="원본 계약 auto_oracle 결과 json(불일치 증거원)")
    ap.add_argument("--n", type=int, default=3, help="처방 재측정 시드 수")
    args = ap.parse_args(argv)

    try:
        from config import force_utf8_stdout
        force_utf8_stdout()
    except Exception:  # noqa: BLE001
        pass

    contract = json.loads((HERE / args.packet / "contract.json").read_text(encoding="utf-8"))
    rules = contract["data_contract"]["rules"]
    scenarios = json.loads((HERE / args.specqa / "acceptance_tests_draft.json").read_text(encoding="utf-8"))
    by_id = {s["id"]: s for s in scenarios}
    prior = json.loads((HERE / args.prior).read_text(encoding="utf-8")) if not Path(args.prior).is_absolute() \
        else json.loads(Path(args.prior).read_text(encoding="utf-8"))

    evidence = _build_evidence(prior, by_id)
    prompt = _SUGGEST_PROMPT.format(rules="\n".join(f"- {r}" for r in rules), evidence=evidence)

    from config import get_api_keys
    from llm import KeyPool, LLMClient
    pool = KeyPool(get_api_keys(), models=[MODEL_31])

    print(f"[SELF-SUGGEST] {args.packet} | 불일치 시나리오 증거로 31B에 자가 처방 요청 | 모델 {MODEL_31}\n")
    with pool.checkout() as key:
        out = _extract_json(LLMClient(api_key=key).generate("generator", prompt))

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    base = HERE / "build_runs" / f"selfsuggest-{stamp}"
    base.mkdir(parents=True, exist_ok=True)

    if not out or "patched_rules" not in out:
        print("[SELF-SUGGEST] 31B가 유효한 처방 JSON을 안 냄. 원응답 저장.")
        (base / "raw.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        return 1

    print("== 31B 진단 ==")
    for d in out.get("diagnosis", []):
        print(f"  - rule: {d.get('rule','')[:80]}")
        print(f"    issue: {d.get('issue','')}")
        print(f"    fix  : {d.get('fix','')}")
    print(f"\n== 제안한 patched_rules ({len(out['patched_rules'])}줄) ==")
    for r in out["patched_rules"]:
        print(f"  - {r}")

    # 처방을 박은 변형 패킷 생성(골든=specqa 무변경 = 1변수)
    import shutil
    sug_packet = f"planning_packet_eco_selfsug"
    dst = HERE / sug_packet
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(HERE / args.packet, dst)
    patched = json.loads((dst / "contract.json").read_text(encoding="utf-8"))
    patched["data_contract"]["rules"] = out["patched_rules"]
    (dst / "contract.json").write_text(json.dumps(patched, ensure_ascii=False, indent=2), encoding="utf-8")
    (base / "suggestion.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[SELF-SUGGEST] 처방 패킷 → studio/{sug_packet} | 진단/처방 → {base/'suggestion.json'}")

    # 처방 재측정: auto_oracle로 수렴 확인(G63 1.0과 비교)
    print(f"\n[SELF-SUGGEST] 처방 재측정 (auto_oracle --n {args.n}) ...\n")
    auto_oracle.main(["--n", str(args.n), "--packet", sug_packet, "--specqa", args.specqa])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
