# Golem Atelier — 캐논 일관성 채점기: 31B가 동결 바이블 대비 챕터 초고의 캐논 위반을 잡아내나 측정
"""핵심 질문(소설 스튜디오의 코어 frontier): 싼 모델(31B)이 동결 바이블(FROZEN CANON)만 보고
한 챕터 초고가 *어느 캐논을 위반*하는지 정확히 짚어낼 수 있나. 짚어내면 '굴러가나'를
'캐논이 맞나(잴 수 있나)'로 바꾼 것 — 골렘 auto_oracle의 소설판이다.

미학(문장·페이싱·목소리)은 여기서 채점하지 않는다 — exact-match 골든이 없다. 이 채점기는
캐논 층(연속성·세계규칙·인물사실·타임라인)만 본다. 경계는 이 채점기를 돌려보고 데이터로 정한다.

방법(키 ★): 골든을 *심은* 픽스처(깨끗한 초고 + 모순 심은 초고)로
  입력 = canon 규칙 목록 + 챕터 초고 전문
  출력 = 31B가 찾은 위반 [{rule_id, evidence(인용)}]
채점 = 찾은 rule_id 집합 vs 골든(심은) 집합. exact = 누락도 오탐도 0.
N시드 재실행 → 정확률 + 규칙별 검출률(recall) + 오탐(false alarm) + 시드 안정성.

사용:
  python canon_check.py --replay fixtures/replay_demo.json     # 키 안 씀(배선·채점 검증)
  python canon_check.py --n 3                                  # ★키 (사용자 go 뒤에만)
  python canon_check.py --n 3 --fixtures fixtures
"""

import argparse
import json
import re
import statistics
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "lib"))   # vendored 인프라(config·llm·key_usage·jsonutil) — golem 폴더 비의존

from jsonutil import extract_json        # noqa: E402

# 캐논 일관성 판단은 '머리' 일이다 → critic 역할(=gemma 31B). 실제 모델 ID는 get_model이 준다
# (역할→모델 매핑은 lib/config.py·.env가 정본; 여기 문자열을 박지 않아 print가 실제와 안 어긋난다).
ROLE = "critic"

_CANON_PROMPT = """You are the CONTINUITY EDITOR for a novel. You are given the FROZEN CANON
(established facts that must NEVER be contradicted) and a CHAPTER DRAFT. Find every place in the
draft that HARD-CONTRADICTS a listed canon fact. Judge ONLY contradictions of the listed facts —
never style, pacing, beauty, or quality. If a fact is not contradicted, do not report it.

A sentence that AGREES WITH or merely RESTATES a canon fact is NOT a violation — report a fact ONLY
when the draft asserts something that CANNOT BE TRUE if that canon fact holds. Mentioning a fact is
not contradicting it. When in doubt, do NOT report — an empty list is the correct answer for a draft
that contradicts nothing.

EXAMPLES (how to judge direction):
- CANON "[C1] Mira lost her right hand." / DRAFT "Mira reached out with her left hand, the only one
  she had." -> NO violation (the draft AGREES with C1).
- CANON "[C1] Mira lost her right hand." / DRAFT "Mira clapped both her hands together." -> VIOLATION
  of C1 (she cannot have two hands).
- CANON "[C2] Sara is Tom's biological sister." / DRAFT "Sara, his sister by the same mother, wept."
  -> NO violation (the draft AGREES with C2).
- CANON "[C2] Sara is Tom's biological sister." / DRAFT "Sara, an orphan he had taken in with no
  blood between them." -> VIOLATION of C2 (they are not biological siblings).

FROZEN CANON:
{canon}

CHAPTER DRAFT:
{draft}

Output ONE JSON object EXACTLY, no prose, no explanation:
{{ "violations": [ {{ "rule_id": "<id from canon>", "evidence": "<short quote from the draft>" }} ] }}"""


_VERIFY_PROMPT = """You are a STRICT FACT-CHECKER auditing flagged canon violations for FALSE ALARMS.
For each candidate, decide if the draft quote REALLY contradicts its canon fact.

A real contradiction means the draft asserts something that CANNOT BE TRUE if the canon fact holds.
A quote that AGREES WITH, RESTATES, or merely MENTIONS the fact is NOT a contradiction (confirmed=false).

FROZEN CANON:
{canon}

CHAPTER DRAFT:
{draft}

CANDIDATE VIOLATIONS (JSON): {candidates}

Output ONE JSON object EXACTLY, no prose:
{{ "verdicts": [ {{ "rule_id": "<id>", "confirmed": true }} ] }}"""


def _ask_check(pool, canon, draft_text):
    """31B에 한 초고의 캐논 위반을 찾게 시킨다. 반환 = 파싱된 {violations:[...]} 또는 None."""
    from llm import LLMClient
    canon_str = "\n".join(f'- [{r["id"]}] {r["text"]}' for r in canon)
    prompt = _CANON_PROMPT.format(canon=canon_str, draft=draft_text)
    with pool.checkout() as key:
        return extract_json(LLMClient(api_key=key).generate(ROLE, prompt))


def _verify(pool, canon, draft_text, pred):
    """2패스: 1패스가 낸 위반 후보를 '정말 모순인가' 재확인해 confirmed=true만 남긴다(precision↑).
    후보 0이면 콜 없이 그대로. 검증 콜 실패 시 1패스 보존(누락보다 보수적)."""
    cands = [{"rule_id": _norm_id(v["rule_id"]), "evidence": v.get("evidence", "")}
             for v in pred.get("violations", []) if v.get("rule_id")]
    if not cands:
        return pred
    from llm import LLMClient
    canon_str = "\n".join(f'- [{r["id"]}] {r["text"]}' for r in canon)
    prompt = _VERIFY_PROMPT.format(canon=canon_str, draft=draft_text,
                                   candidates=json.dumps(cands, ensure_ascii=False))
    with pool.checkout() as key:
        res = extract_json(LLMClient(api_key=key).generate(ROLE, prompt))
    if not res:
        return pred
    confirmed = {_norm_id(v["rule_id"]) for v in res.get("verdicts", [])
                 if v.get("confirmed") and v.get("rule_id")}
    return {"violations": [v for v in pred.get("violations", [])
                           if _norm_id(v.get("rule_id", "")) in confirmed]}


def _norm_id(rid):
    """모델이 '[C2]'·'C2 '처럼 형식을 흔들어도 같은 규칙으로 정규화한다(대괄호·공백 제거)."""
    m = re.search(r"[A-Za-z]+\d+", str(rid))
    return m.group(0).upper() if m else str(rid).strip()


def _found_ids(pred):
    """예측에서 위반 rule_id 집합만 뽑는다(정규화; 증거 인용은 채점에 안 씀, 보고용)."""
    if not pred:
        return set()
    return {_norm_id(v["rule_id"]) for v in pred.get("violations", []) if v.get("rule_id")}


def _score(pred, golden_ids):
    """찾은 위반 집합 vs 골든(심은) 집합. exact = 누락·오탐 0."""
    found = _found_ids(pred)
    golden = set(golden_ids)
    return {
        "found": sorted(found),
        "tp": sorted(found & golden),
        "fp": sorted(found - golden),   # 오탐(없는 위반을 지어냄)
        "fn": sorted(golden - found),   # 누락(심은 위반을 놓침)
        "exact": (found == golden),
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=3, help="시드(재실행) 수 — 안정성/분산용")
    ap.add_argument("--fixtures", default="fixtures")
    ap.add_argument("--replay", default=None, help="키 없이 채점 배선 검증 (canned 응답 JSON)")
    ap.add_argument("--verify", action="store_true",
                    help="2패스 검증 — 1패스 위반 후보를 재확인 콜로 걸러 오탐 억제(★키 더 씀)")
    args = ap.parse_args(argv)

    try:
        from config import force_utf8_stdout
        force_utf8_stdout()
    except Exception:  # noqa: BLE001
        pass

    fx = (HERE / args.fixtures)
    canon = json.loads((fx / "bible.json").read_text(encoding="utf-8"))["canon"]
    cases = json.loads((fx / "cases.json").read_text(encoding="utf-8"))
    for c in cases:
        c["draft_text"] = (fx / c["draft"]).read_text(encoding="utf-8")

    replay = None
    pool = None
    model_id = None
    if args.replay:
        replay = json.loads((HERE / args.replay).read_text(encoding="utf-8"))
        print(f"[CANON-CHECK · REPLAY] 키 안 씀 | 케이스 {len(cases)} × {args.n}시드\n")
    else:
        from config import get_api_keys, get_model, load_env
        from llm import KeyPool
        env_path = HERE / ".env"
        if not env_path.exists():
            raise SystemExit(f"[CANON-CHECK] atelier 전용 키가 없다 — {env_path} 에 "
                             "GOOGLE_API_KEY_1..N 을 넣어라 (golem 키와 섞이지 않게).")
        load_env(env_path)
        keys = get_api_keys()
        model_id = get_model(ROLE)
        pool = KeyPool(keys, models=[model_id])
        print(f"[CANON-CHECK] atelier 전용 키 {len(keys)}개 ({env_path}) | "
              f"케이스 {len(cases)} × {args.n}시드 | 모델 {model_id}\n")

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    base = HERE / "runs" / f"canon-{stamp}"
    base.mkdir(parents=True, exist_ok=True)

    per_case = []
    for c in cases:
        golden = c["golden"]
        seed_exact, seed_found, fp_counts, fn_total = [], [], [], Counter()
        fp_total, fp_ev = Counter(), {}   # 오탐 진단: 어떤 규칙을 무슨 근거로 헛잡나
        for i in range(args.n):
            if replay is not None:
                seq = replay.get(c["id"], [])
                pred = seq[i % len(seq)] if seq else None
            else:
                pred = _ask_check(pool, canon, c["draft_text"])
                if args.verify and pred:
                    pred = _verify(pool, canon, c["draft_text"], pred)
            sc = _score(pred, golden)
            seed_exact.append(sc["exact"])
            seed_found.append(tuple(sc["found"]))
            fp_counts.append(len(sc["fp"]))
            for rid in sc["fn"]:
                fn_total[rid] += 1
            for rid in sc["fp"]:
                fp_total[rid] += 1
            for v in (pred or {}).get("violations", []):
                rid = _norm_id(v.get("rule_id", ""))
                if rid in sc["fp"]:
                    fp_ev.setdefault(rid, []).append(str(v.get("evidence", "")))
        exact_rate = sum(seed_exact) / args.n
        votes = Counter(seed_found)
        stability = votes.most_common(1)[0][1] / args.n if votes else 0.0
        recall_by_rule = {rid: round((args.n - fn_total[rid]) / args.n, 3) for rid in golden}
        per_case.append({
            "id": c["id"], "golden": golden, "exact_rate": round(exact_rate, 3),
            "stability": round(stability, 3), "mean_false_alarm": round(statistics.mean(fp_counts), 3),
            "recall_by_rule": recall_by_rule,
            "false_alarm_by_rule": dict(fp_total),
            "false_alarm_evidence": {rid: list(dict.fromkeys(e))[:3] for rid, e in fp_ev.items()},
        })
        print(f"  {c['id']:10s} exact {exact_rate:.2f} 안정 {stability:.2f} "
              f"오탐 {statistics.mean(fp_counts):.2f}  검출 {recall_by_rule or '(깨끗한 초고)'}")

    exact_all = [p["exact_rate"] for p in per_case]
    recalls = [(p["id"], rid, r) for p in per_case for rid, r in p["recall_by_rule"].items()]
    by_rule = {}
    for _, rid, r in recalls:
        by_rule.setdefault(rid, []).append(r)
    recall_by_name = {rid: round(statistics.mean(v), 3) for rid, v in by_rule.items()}
    summary = {
        "fixtures": args.fixtures, "n_seeds": args.n, "cases": len(per_case),
        "model": model_id,
        "exact_rate_mean": round(statistics.mean(exact_all), 3) if exact_all else None,
        "fully_exact_cases": sum(1 for p in per_case if p["exact_rate"] == 1.0),
        "recall_by_rule": recall_by_name,
        "mean_stability": round(statistics.mean([p["stability"] for p in per_case]), 3) if per_case else None,
        "mean_false_alarm": round(statistics.mean([p["mean_false_alarm"] for p in per_case]), 3) if per_case else None,
        "worst_rules": sorted(recalls, key=lambda t: t[2])[:8],
        "per_case": per_case,
    }
    (base / "canon_check_result.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n" + "=" * 60)
    print(f"[CANON-CHECK 결과] exact 정확률 {summary['exact_rate_mean']} "
          f"(완전정확 케이스 {summary['fully_exact_cases']}/{len(per_case)}), "
          f"평균 안정성 {summary['mean_stability']}, 평균 오탐 {summary['mean_false_alarm']}")
    print(f"  규칙별 검출률(recall): {recall_by_name}")
    print(f"[CANON-CHECK] → {base / 'canon_check_result.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
