# Golem Studio 자율 oracle 프로브 — 31B가 계약만 보고 expected(골든)를 스스로 만들 수 있나 측정
"""핵심 질문(코어 다음 frontier): 싼 모델(31B)이 빌드를 *안 보고* 동결 rules + 시나리오 입력만으로
각 시나리오의 expected를 손계산해 낼 수 있나. 낼 수 있으면 손-oracle을 자율 생성으로 대체 가능,
못 내면 그게 리뷰 #5가 경고한 'oracle 후보 오염' 위험의 실거리다.

방법(키 ★): 수렴 카드(방치형, 골든 1.0=신뢰 정답)의 시나리오마다
  입력 = rules + scenario.input + 채워야 할 출력키(=골든 expected 키)
  출력 = 31B가 손실행한 expected {key: value}
채점 = 골든 expected와 키별 정확일치(_canon, build_graded와 동일 캐노니컬). 시나리오 통과 = 전 키 일치.
N시드 재실행 → 자율 oracle 정확률 + 키별 정확률 + 시드 안정성(분산) + 어긋난 곳(난이도가 어디로 가나).

빌드합의 leg는 v1서 뺀다 — 수렴 카드는 골든==빌드합의라 골든 한 기준이면 충분(중복 제거).

사용:
  python golem/studio/auto_oracle.py --n 3                 # ★키 (방치형 기본)
  python golem/studio/auto_oracle.py --n 3 --packet planning_packet_eco --specqa specqa_packet_eco
"""

import argparse
import json
import statistics
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent.parent))

from build_graded import _canon            # noqa: E402
from planning import _extract_json         # noqa: E402

MODEL_31 = "gemma-4-31b-it"

_ORACLE_PROMPT = """You are the ORACLE for a deterministic, turn-based game. Hand-execute the FROZEN
RULES on the scenario input, step by step, and compute the EXACT final output. Be fully deterministic:
no randomness, follow the rules literally, integer math as written.

FROZEN RULES:
{rules}

SCENARIO INPUT (constants and the ordered list of player actions, applied in order):
{input}

Report ONLY these output keys, with their FINAL values after ALL actions are applied:
{keys}

Output ONE JSON object EXACTLY, no prose, no explanation:
{template}"""


def _scenario_input(sc):
    """시나리오의 게임 입력(constants+actions)만. 골든/채점 메타키는 모델에 안 준다."""
    if "input" in sc:
        return sc["input"]
    return {k: v for k, v in sc.items()
            if k not in ("id", "expected", "oracle_risk", "covers_reqs")}


def _ask_oracle(pool, rules, sc):
    """31B에 한 시나리오의 expected를 손계산시켜 받는다(골든 키만 채우게 지시)."""
    from llm import LLMClient
    keys = list((sc.get("expected") or {}).keys())
    template = "{ " + ", ".join(f'"{k}": <value>' for k in keys) + " }"
    prompt = _ORACLE_PROMPT.format(
        rules="\n".join(f"- {r}" for r in rules),
        input=json.dumps(_scenario_input(sc), ensure_ascii=False),
        keys=", ".join(keys),
        template=template)
    with pool.checkout() as key:
        return _extract_json(LLMClient(api_key=key).generate("generator", prompt))


def _score(pred, golden):
    """예측 expected vs 골든 expected 키별 정확일치(_canon). (per_key dict, all_match bool)."""
    per_key = {}
    for k, gv in golden.items():
        pv = (pred or {}).get(k, "__MISSING__")
        per_key[k] = (pred is not None and k in pred and _canon(pv) == _canon(gv))
    return per_key, all(per_key.values())


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=3, help="시드(재실행) 수 — 안정성/분산용")
    ap.add_argument("--packet", default="planning_packet")
    ap.add_argument("--specqa", default="specqa_packet")
    args = ap.parse_args(argv)

    try:
        from config import force_utf8_stdout
        force_utf8_stdout()
    except Exception:  # noqa: BLE001
        pass

    contract = json.loads((HERE / args.packet / "contract.json").read_text(encoding="utf-8"))
    rules = contract["data_contract"]["rules"]
    scenarios = json.loads((HERE / args.specqa / "acceptance_tests_draft.json").read_text(encoding="utf-8"))
    scenarios = [s for s in scenarios if (s.get("expected") or {})]

    from config import get_api_keys
    from llm import KeyPool
    pool = KeyPool(get_api_keys(), models=[MODEL_31])

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    base = HERE / "build_runs" / f"autooracle-{stamp}"
    base.mkdir(parents=True, exist_ok=True)
    print(f"[AUTO-ORACLE] {args.packet} | 시나리오 {len(scenarios)} × {args.n}시드 | 모델 {MODEL_31}\n")

    per_scn = []
    for sc in scenarios:
        golden = sc["expected"]
        seed_match, seed_preds, key_hits = [], [], Counter()
        for i in range(args.n):
            pred = _ask_oracle(pool, rules, sc)
            per_key, ok = _score(pred, golden)
            seed_match.append(ok)
            seed_preds.append(pred)
            for k, hit in per_key.items():
                if hit:
                    key_hits[k] += 1
        pass_rate = sum(seed_match) / args.n
        # 시드 간 일관성: 같은 예측을 얼마나 반복하나(자율 oracle 결정성)
        votes = Counter(json.dumps(p, sort_keys=True) for p in seed_preds if p is not None)
        stability = (votes.most_common(1)[0][1] / args.n) if votes else 0.0
        per_scn.append({"id": sc["id"], "golden": golden, "pass_rate": round(pass_rate, 3),
                        "stability": round(stability, 3),
                        "key_accuracy": {k: round(key_hits[k] / args.n, 3) for k in golden},
                        "preds": seed_preds})
        print(f"  {sc['id']:8s} 통과 {pass_rate:.2f} 안정 {stability:.2f}  "
              f"키별 {[f'{k}:{key_hits[k]}/{args.n}' for k in golden]}")

    scn_pass = [p["pass_rate"] for p in per_scn]
    all_keys = [(p["id"], k, acc) for p in per_scn for k, acc in p["key_accuracy"].items()]
    # 키 이름별 정확률 — 시나리오단위(완전정확)는 한 모호키가 전 시나리오를 끌어내려 오해를 부른다(eco status).
    by_name = {}
    for _, k, acc in all_keys:
        by_name.setdefault(k, []).append(acc)
    key_acc_by_name = {k: round(statistics.mean(v), 3) for k, v in by_name.items()}
    summary = {
        "packet": args.packet, "n_seeds": args.n, "scenarios": len(per_scn), "model": MODEL_31,
        "oracle_accuracy_mean": round(statistics.mean(scn_pass), 3) if scn_pass else None,
        "fully_correct_scenarios": sum(1 for p in per_scn if p["pass_rate"] == 1.0),
        "key_accuracy_by_name": key_acc_by_name,
        "mean_stability": round(statistics.mean([p["stability"] for p in per_scn]), 3) if per_scn else None,
        "worst_keys": sorted(all_keys, key=lambda t: t[2])[:8],
        "per_scenario": per_scn}
    (base / "auto_oracle_result.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n" + "=" * 60)
    print(f"[AUTO-ORACLE 결과] 자율 oracle 정확률 {summary['oracle_accuracy_mean']} "
          f"(완전정확 시나리오 {summary['fully_correct_scenarios']}/{len(per_scn)}), "
          f"평균 안정성 {summary['mean_stability']}")
    print(f"  키 이름별 정확률(진짜 신호): {key_acc_by_name}")
    print("  최약 키(틀린 곳):")
    for sid, k, acc in summary["worst_keys"]:
        if acc < 1.0:
            print(f"    {sid} {k}: {acc}")
    print(f"[AUTO-ORACLE] → {base / 'auto_oracle_result.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
