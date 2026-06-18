# Golem Atelier — 비트시트 setup→payoff 채점기: 31B가 동결 바이블의 약속 중 회수 안 된 설정을 잡나 측정
"""핵심 질문(design frontier): 싼 모델(31B)이 비트시트(챕터 아웃라인)를 보고 *도입됐으나
회수되지 않은 설정*(unresolved setup)을 정확히 짚어낼 수 있나. canon_check의 거울이다 —
canon_check은 "동결 사실을 *모순*하나"를, design_check은 "동결 약속을 *회수*하나"를 잰다.
모순 검출의 반대 방향(약속 미회수 검출)이라 같은 검출/검증 2패스 기계가 그대로 돈다.

미학(긴장·페이싱·목소리)은 여기서 채점하지 않는다 — exact-match 골든이 없다. 이 채점기는
구조 층(복선 setup→payoff traceability)만 본다. 경계는 canon_check과 같은 방식으로 데이터로 정한다.

방법(키 ★): 골든을 *심은* 픽스처(모든 설정을 회수한 비트시트 + 일부 설정을 일부러 떨군 비트시트)로
  입력 = 추적 설정 목록(promise/object/mystery/threat) + 비트시트 전문
  출력 = 31B가 찾은 미회수 설정 [{setup_id, evidence(인용)}]
채점 = 찾은 setup_id 집합 vs 골든(심은 미회수) 집합. exact = 누락도 오탐도 0.
N시드 재실행 → 정확률 + 설정별 검출률(recall) + 오탐(false alarm) + 시드 안정성.

사용:
  python design_check.py --replay fixtures_design/replay_demo.json   # 키 안 씀(배선·채점 검증)
  python design_check.py --n 3                                       # ★키 (사용자 go 뒤에만)
  python design_check.py --n 3 --verify --fixtures fixtures_design
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

# setup→payoff 추적 판단은 '머리' 일이다 → critic 역할(=gemma 31B). 실제 모델 ID는 get_model이 준다.
ROLE = "critic"

_SETUP_PROMPT = """You are the STORY EDITOR auditing a beat sheet (chapter outline) for UNRESOLVED SETUPS.
You are given the PREMISE, a list of TRACKED SETUPS (promises/objects/mysteries/threats the story
introduces and MUST pay off before it ends), and the BEAT SHEET (ordered beats). For each tracked
setup, decide whether some LATER beat PAYS IT OFF — the promise is fulfilled, the object is used or
resolved, the mystery is answered, the threat is confronted. Report ONLY setups that are NEVER paid
off anywhere in the beat sheet.

A setup that IS paid off (even implicitly, in a later beat) is NOT a problem — do not report it.
Merely RE-MENTIONING a setup is not paying it off; a payoff means the promise is resolved on the page.
When in doubt whether a beat counts as a payoff, assume it IS paid off and do NOT report — an empty
list is the correct answer for a beat sheet that resolves everything.

EXAMPLES (how to judge direction):
- SETUP "[S1] A sealed letter from the dead king." / a later beat "Kael breaks the seal and reads the
  king's confession aloud." -> PAID OFF (do not report S1).
- SETUP "[S1] A sealed letter from the dead king." / the letter is shown in beat 1 and never opened or
  mentioned again. -> UNRESOLVED (report S1).
- SETUP "[S2] Lia's silver pendant from her mother." / a later beat "The pendant clicks open, revealing
  the royal crest that proves their bloodline." -> PAID OFF (do not report S2).

PREMISE:
{premise}

TRACKED SETUPS:
{setups}

BEAT SHEET:
{draft}

Output ONE JSON object EXACTLY, no prose, no explanation:
{{ "unresolved": [ {{ "setup_id": "<id from setups>", "evidence": "<short quote of the beat that introduces it>" }} ] }}"""


_VERIFY_PROMPT = """You are a STRICT STORY EDITOR auditing flagged UNRESOLVED setups for FALSE ALARMS.
For each candidate, decide if the setup is REALLY never paid off anywhere in the beat sheet.

A setup is paid off if ANY beat (especially a later one) fulfills, resolves, uses, or answers it.
If you can point to such a beat, the setup is paid off (confirmed=false). Only confirm setups that
truly have NO payoff beat anywhere.

PREMISE:
{premise}

TRACKED SETUPS:
{setups}

BEAT SHEET:
{draft}

CANDIDATE UNRESOLVED SETUPS (JSON): {candidates}

Output ONE JSON object EXACTLY, no prose:
{{ "verdicts": [ {{ "setup_id": "<id>", "confirmed": true }} ] }}"""


def _ask_detect(pool, premise, setups, draft_text):
    """31B에 비트시트의 미회수 설정을 찾게 시킨다. 반환 = 파싱된 {unresolved:[...]} 또는 None."""
    from llm import LLMClient
    setups_str = "\n".join(f'- [{s["id"]}] {s["text"]}' for s in setups)
    prompt = _SETUP_PROMPT.format(premise=premise, setups=setups_str, draft=draft_text)
    with pool.checkout() as key:
        return extract_json(LLMClient(api_key=key).generate(ROLE, prompt))


def _verify(pool, premise, setups, draft_text, pred):
    """2패스: 1패스가 낸 미회수 후보를 '정말 회수 안 됐나' 재확인해 confirmed=true만 남긴다(precision↑).
    후보 0이면 콜 없이 그대로. 검증 콜 실패 시 1패스 보존(누락보다 보수적)."""
    cands = [{"setup_id": _norm_id(v["setup_id"]), "evidence": v.get("evidence", "")}
             for v in pred.get("unresolved", []) if v.get("setup_id")]
    if not cands:
        return pred
    from llm import LLMClient
    setups_str = "\n".join(f'- [{s["id"]}] {s["text"]}' for s in setups)
    prompt = _VERIFY_PROMPT.format(premise=premise, setups=setups_str, draft=draft_text,
                                   candidates=json.dumps(cands, ensure_ascii=False))
    with pool.checkout() as key:
        res = extract_json(LLMClient(api_key=key).generate(ROLE, prompt))
    if not res:
        return pred
    confirmed = {_norm_id(v["setup_id"]) for v in res.get("verdicts", [])
                 if v.get("confirmed") and v.get("setup_id")}
    return {"unresolved": [v for v in pred.get("unresolved", [])
                           if _norm_id(v.get("setup_id", "")) in confirmed]}


def _norm_id(rid):
    """모델이 '[S2]'·'S2 '처럼 형식을 흔들어도 같은 설정으로 정규화한다(대괄호·공백 제거)."""
    m = re.search(r"[A-Za-z]+\d+", str(rid))
    return m.group(0).upper() if m else str(rid).strip()


def _found_ids(pred):
    """예측에서 미회수 setup_id 집합만 뽑는다(정규화; 증거 인용은 채점에 안 씀, 보고용)."""
    if not pred:
        return set()
    return {_norm_id(v["setup_id"]) for v in pred.get("unresolved", []) if v.get("setup_id")}


def _score(pred, golden_ids):
    """찾은 미회수 집합 vs 골든(심은) 집합. exact = 누락·오탐 0."""
    found = _found_ids(pred)
    golden = set(golden_ids)
    return {
        "found": sorted(found),
        "tp": sorted(found & golden),
        "fp": sorted(found - golden),   # 오탐(회수된 설정을 미회수라 지어냄)
        "fn": sorted(golden - found),   # 누락(심은 미회수를 놓침)
        "exact": (found == golden),
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=3, help="시드(재실행) 수 — 안정성/분산용")
    ap.add_argument("--fixtures", default="fixtures_design")
    ap.add_argument("--replay", default=None, help="키 없이 채점 배선 검증 (canned 응답 JSON)")
    ap.add_argument("--verify", action="store_true",
                    help="2패스 검증 — 1패스 미회수 후보를 재확인 콜로 걸러 오탐 억제(★키 더 씀)")
    args = ap.parse_args(argv)

    try:
        from config import force_utf8_stdout
        force_utf8_stdout()
    except Exception:  # noqa: BLE001
        pass

    fx = (HERE / args.fixtures)
    outline = json.loads((fx / "outline.json").read_text(encoding="utf-8"))
    premise = outline.get("premise", "")
    setups = outline["setups"]
    cases = json.loads((fx / "cases.json").read_text(encoding="utf-8"))
    for c in cases:
        c["draft_text"] = (fx / c["draft"]).read_text(encoding="utf-8")

    replay = None
    pool = None
    model_id = None
    if args.replay:
        replay = json.loads((HERE / args.replay).read_text(encoding="utf-8"))
        print(f"[DESIGN-CHECK · REPLAY] 키 안 씀 | 케이스 {len(cases)} × {args.n}시드\n")
    else:
        from config import get_api_keys, get_model, load_env
        from llm import KeyPool
        env_path = HERE / ".env"
        if not env_path.exists():
            raise SystemExit(f"[DESIGN-CHECK] atelier 전용 키가 없다 — {env_path} 에 "
                             "GOOGLE_API_KEY_1..N 을 넣어라 (golem 키와 섞이지 않게).")
        load_env(env_path)
        keys = get_api_keys()
        model_id = get_model(ROLE)
        pool = KeyPool(keys, models=[model_id])
        print(f"[DESIGN-CHECK] atelier 전용 키 {len(keys)}개 ({env_path}) | "
              f"케이스 {len(cases)} × {args.n}시드 | 모델 {model_id}\n")

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    base = HERE / "runs" / f"design-{stamp}"
    base.mkdir(parents=True, exist_ok=True)

    per_case = []
    for c in cases:
        golden = c["golden"]
        seed_exact, seed_found, fp_counts, fn_total = [], [], [], Counter()
        fp_total, fp_ev = Counter(), {}   # 오탐 진단: 어떤 설정을 무슨 근거로 헛잡나
        for i in range(args.n):
            if replay is not None:
                seq = replay.get(c["id"], [])
                pred = seq[i % len(seq)] if seq else None
            else:
                pred = _ask_detect(pool, premise, setups, c["draft_text"])
                if args.verify and pred:
                    pred = _verify(pool, premise, setups, c["draft_text"], pred)
            sc = _score(pred, golden)
            seed_exact.append(sc["exact"])
            seed_found.append(tuple(sc["found"]))
            fp_counts.append(len(sc["fp"]))
            for rid in sc["fn"]:
                fn_total[rid] += 1
            for rid in sc["fp"]:
                fp_total[rid] += 1
            for v in (pred or {}).get("unresolved", []):
                rid = _norm_id(v.get("setup_id", ""))
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
        print(f"  {c['id']:18s} exact {exact_rate:.2f} 안정 {stability:.2f} "
              f"오탐 {statistics.mean(fp_counts):.2f}  검출 {recall_by_rule or '(전부 회수된 비트시트)'}")

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
    (base / "design_check_result.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n" + "=" * 60)
    print(f"[DESIGN-CHECK 결과] exact 정확률 {summary['exact_rate_mean']} "
          f"(완전정확 케이스 {summary['fully_exact_cases']}/{len(per_case)}), "
          f"평균 안정성 {summary['mean_stability']}, 평균 오탐 {summary['mean_false_alarm']}")
    print(f"  설정별 검출률(recall): {recall_by_name}")
    print(f"[DESIGN-CHECK] → {base / 'design_check_result.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
