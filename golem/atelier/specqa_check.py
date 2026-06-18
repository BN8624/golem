# Golem Atelier — 씬 계약 캐논/미학 격리 채점기: 31B가 검증가능(캐논) 기준과 검증불가(미학)을 옳게 가르나 측정
"""핵심 질문(specQA frontier): 싼 모델(31B)이 씬 계약(scene contract)의 기준 목록을 보고
*기계로 검증 가능한 캐논 기준*(연속성·세계규칙·인물사실·복선회수·타임라인)과 *검증 불가한 미학 기준*
(문장·긴장·페이싱·목소리)을 정확히 가를 수 있나. canon_check·design_check의 형제다 — 둘이 "검출"을
잰다면 specQA는 "격리(분류)"를 잰다. NovelStudioMode의 oracle 2층 분리("검증 불가한 기준은 미학으로
격리")를 31B가 기계화할 수 있나가 frontier 질문이다.

위험한 방향(false alarm): 미학 기준을 캐논(검증가능)이라 잘못 라벨하는 것 = "검증 못 할 걸 exact로
재려는" 합의채점 흉내. NovelStudioMode가 금지한 바로 그 실패다. 그래서 보수적 기본값은 "검증가능한지
의심되면 미학으로 둔다"(캐논 목록에 안 올린다)로, fp를 핵심 측정축으로 둔다.

방법(키 ★): 골든 *라벨을 심은* 픽스처(캐논/미학 정답이 박힌 씬 계약)로
  입력 = premise + 씬의 기준 목록(라벨 없이)
  출력 = 31B가 '검증 가능(캐논)'이라 라벨한 기준 [{criterion_id, reason(인용/근거)}]
채점 = 검증가능이라 라벨한 집합 vs 골든(심은 캐논) 집합. exact = 오분류(누락·오탐) 0.
N시드 재실행 → 정확률 + 기준별 검출률(recall) + 오탐(미학→캐논 오라벨) + 시드 안정성.

사용:
  python specqa_check.py --replay fixtures_specqa/replay_demo.json   # 키 안 씀(배선·채점 검증)
  python specqa_check.py --n 3                                       # ★키 (사용자 go 뒤에만)
  python specqa_check.py --n 3 --verify --fixtures fixtures_specqa
"""

import argparse
import json
import os
import re
import statistics
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "lib"))   # vendored 인프라(config·llm·key_usage·jsonutil) — golem 폴더 비의존

from jsonutil import extract_json        # noqa: E402

# 캐논/미학 격리 판단은 '머리' 일이다 → critic 역할(=gemma 31B). 실제 모델 ID는 get_model이 준다.
ROLE = "critic"
MODEL_31 = "gemma-4-31b-it"   # atelier는 31B(머리)만 쓴다 — 핀 가드용 상수

_CLASSIFY_PROMPT = """You are the SPEC EDITOR triaging a SCENE CONTRACT for a novel.
A scene contract is a list of CRITERIA the scene must satisfy. Your one job: split them into
VERIFIABLE (canon) vs UNVERIFIABLE (aesthetic).

VERIFIABLE (canon) = can be checked by exact match against established story facts — continuity,
world rules, character facts, foreshadowing payoff (a setup is resolved), timeline order. A reader
or a machine can answer YES/NO objectively: did it happen / is it consistent.

UNVERIFIABLE (aesthetic) = a matter of craft or taste with NO objective oracle — prose quality,
tension, pacing, voice, tone, atmosphere, emotional impact, whether something "feels" believable or
moving. Two careful readers can disagree. These MUST NOT be treated as machine-checkable.

Report ONLY the criteria you judge VERIFIABLE (canon). Anything you do not list is treated as
aesthetic and isolated from machine scoring. When in doubt whether a criterion is objectively
checkable, treat it as AESTHETIC and do NOT list it — over-claiming verifiability (calling a matter
of taste "canon") is the worst error. A contract that is entirely aesthetic should yield an EMPTY list.

EXAMPLES (how to judge direction):
- CRITERION "Kael lost his left arm, so he must open the seal with his right hand or prosthetic."
  -> VERIFIABLE (character fact / continuity). List it.
- CRITERION "The infiltration must build suffocating, escalating tension toward near-discovery."
  -> AESTHETIC (tension/pacing). Do NOT list.
- CRITERION "Lia's pendant (S2) is opened in this scene, paying off the setup."
  -> VERIFIABLE (setup->payoff). List it.
- CRITERION "The library should feel cold and embalmed, mirroring Kael's frozen past."
  -> AESTHETIC (atmosphere/metaphor). Do NOT list.

PREMISE:
{premise}

SCENE CRITERIA:
{criteria}

Output ONE JSON object EXACTLY, no prose, no explanation:
{{ "verifiable": [ {{ "criterion_id": "<id from criteria>", "reason": "<short why it is objectively checkable>" }} ] }}"""


_VERIFY_PROMPT = """You are a STRICT SPEC EDITOR auditing criteria flagged as VERIFIABLE (canon) for
OVER-CLAIMS. For each candidate, decide whether it is REALLY checkable by an objective YES/NO against
established story facts (continuity, world rules, character facts, setup payoff, timeline) — or whether
it is actually a matter of craft/taste (prose, tension, pacing, voice, tone, mood, emotional impact,
believability) dressed in concrete-sounding words.

Confirm (confirmed=true) ONLY criteria that have a real objective oracle. If two careful readers could
disagree about whether it is satisfied, it is aesthetic (confirmed=false).

PREMISE:
{premise}

SCENE CRITERIA:
{criteria}

CANDIDATE VERIFIABLE CRITERIA (JSON): {candidates}

Output ONE JSON object EXACTLY, no prose:
{{ "verdicts": [ {{ "criterion_id": "<id>", "confirmed": true }} ] }}"""


def _ask_classify(pool, premise, criteria, crit_text):
    """31B에 씬 기준을 캐논(검증가능)/미학으로 가르게 시킨다. 반환 = 파싱된 {verifiable:[...]} 또는 None."""
    from llm import LLMClient
    prompt = _CLASSIFY_PROMPT.format(premise=premise, criteria=crit_text)
    with pool.checkout() as key:
        return extract_json(LLMClient(api_key=key).generate(ROLE, prompt))


def _verify(pool, premise, criteria, crit_text, pred):
    """2패스: 1패스가 캐논이라 라벨한 후보를 '정말 객관 검증가능하냐' 재확인해 confirmed=true만 남긴다.
    미학→캐논 오라벨(fp) 억제. 후보 0이면 콜 없이 그대로. 검증 콜 실패 시 1패스 보존(보수적)."""
    cands = [{"criterion_id": _norm_id(v["criterion_id"]), "reason": v.get("reason", "")}
             for v in pred.get("verifiable", []) if v.get("criterion_id")]
    if not cands:
        return pred
    from llm import LLMClient
    prompt = _VERIFY_PROMPT.format(premise=premise, criteria=crit_text,
                                   candidates=json.dumps(cands, ensure_ascii=False))
    with pool.checkout() as key:
        res = extract_json(LLMClient(api_key=key).generate(ROLE, prompt))
    if not res:
        return pred
    confirmed = {_norm_id(v["criterion_id"]) for v in res.get("verdicts", [])
                 if v.get("confirmed") and v.get("criterion_id")}
    return {"verifiable": [v for v in pred.get("verifiable", [])
                           if _norm_id(v.get("criterion_id", "")) in confirmed]}


def _norm_id(rid):
    """모델이 '[C2]'·'C2 '처럼 형식을 흔들어도 같은 기준으로 정규화한다(대괄호·공백 제거)."""
    m = re.search(r"[A-Za-z]+\d+", str(rid))
    return m.group(0).upper() if m else str(rid).strip()


def _found_ids(pred):
    """예측에서 검증가능(캐논)이라 라벨한 criterion_id 집합만 뽑는다(정규화; 근거는 채점 안 씀, 보고용)."""
    if not pred:
        return set()
    return {_norm_id(v["criterion_id"]) for v in pred.get("verifiable", []) if v.get("criterion_id")}


def _score(pred, golden_ids):
    """검증가능이라 라벨한 집합 vs 골든(심은 캐논) 집합. exact = 누락·오탐 0."""
    found = _found_ids(pred)
    golden = set(golden_ids)
    return {
        "found": sorted(found),
        "tp": sorted(found & golden),
        "fp": sorted(found - golden),   # 오탐(미학 기준을 캐논=검증가능이라 오라벨 — 금지된 합의채점 흉내)
        "fn": sorted(golden - found),   # 누락(검증가능한 캐논 기준을 미학으로 흘림 → 기계검증 안 됨)
        "exact": (found == golden),
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=3, help="시드(재실행) 수 — 안정성/분산용")
    ap.add_argument("--fixtures", default="fixtures_specqa")
    ap.add_argument("--replay", default=None, help="키 없이 채점 배선 검증 (canned 응답 JSON)")
    ap.add_argument("--verify", action="store_true",
                    help="2패스 검증 — 1패스 캐논 후보를 재확인 콜로 걸러 미학→캐논 오라벨 억제(★키 더 씀)")
    args = ap.parse_args(argv)

    try:
        from config import force_utf8_stdout
        force_utf8_stdout()
    except Exception:  # noqa: BLE001
        pass

    fx = (HERE / args.fixtures)
    contract = json.loads((fx / "contract.json").read_text(encoding="utf-8"))
    premise = contract.get("premise", "")
    scenes = contract["scenes"]   # {scene_id: [ {id, text}, ... ]}
    cases = json.loads((fx / "cases.json").read_text(encoding="utf-8"))

    replay = None
    pool = None
    model_id = None
    if args.replay:
        replay = json.loads((HERE / args.replay).read_text(encoding="utf-8"))
        print(f"[SPECQA-CHECK · REPLAY] 키 안 씀 | 케이스 {len(cases)} × {args.n}시드\n")
    else:
        from config import get_api_keys, get_model, load_env
        from llm import KeyPool
        env_path = HERE / ".env"
        if not env_path.exists():
            raise SystemExit(f"[SPECQA-CHECK] atelier 전용 키가 없다 — {env_path} 에 "
                             "GOOGLE_API_KEY_1..N 을 넣어라 (golem 키와 섞이지 않게).")
        load_env(env_path)
        # 31B 핀 가드: atelier는 critic(31B)만 쓴다. .env 오염·역할 오용으로 26B가 새지 않게 강제.
        if ROLE != "critic":
            raise SystemExit(f"[SPECQA-CHECK] ROLE은 critic(31B)이어야 한다 — 받은 값 {ROLE!r}")
        os.environ["GENERATOR_MODEL"] = MODEL_31
        os.environ["CRITIC_MODEL"] = MODEL_31
        keys = get_api_keys()
        model_id = get_model(ROLE)
        pool = KeyPool(keys, models=[model_id])
        print(f"[SPECQA-CHECK] atelier 전용 키 {len(keys)}개 ({env_path}) | "
              f"케이스 {len(cases)} × {args.n}시드 | 모델 {model_id}\n")

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    base = HERE / "runs" / f"specqa-{stamp}"
    base.mkdir(parents=True, exist_ok=True)

    per_case = []
    for c in cases:
        golden = c["golden_canon"]
        criteria = scenes[c["id"]]
        crit_text = "\n".join(f'- [{x["id"]}] {x["text"]}' for x in criteria)
        seed_exact, seed_found, fp_counts, fn_total = [], [], [], Counter()
        fp_total, fp_ev = Counter(), {}   # 오탐 진단: 어떤 미학 기준을 무슨 근거로 캐논이라 헛라벨하나
        for i in range(args.n):
            if replay is not None:
                seq = replay.get(c["id"], [])
                pred = seq[i % len(seq)] if seq else None
            else:
                pred = _ask_classify(pool, premise, criteria, crit_text)
                if args.verify and pred:
                    pred = _verify(pool, premise, criteria, crit_text, pred)
            sc = _score(pred, golden)
            seed_exact.append(sc["exact"])
            seed_found.append(tuple(sc["found"]))
            fp_counts.append(len(sc["fp"]))
            for rid in sc["fn"]:
                fn_total[rid] += 1
            for rid in sc["fp"]:
                fp_total[rid] += 1
            for v in (pred or {}).get("verifiable", []):
                rid = _norm_id(v.get("criterion_id", ""))
                if rid in sc["fp"]:
                    fp_ev.setdefault(rid, []).append(str(v.get("reason", "")))
        exact_rate = sum(seed_exact) / args.n
        votes = Counter(seed_found)
        stability = votes.most_common(1)[0][1] / args.n if votes else 0.0
        recall_by_rule = {rid: round((args.n - fn_total[rid]) / args.n, 3) for rid in golden}
        per_case.append({
            "id": c["id"], "golden_canon": golden, "exact_rate": round(exact_rate, 3),
            "stability": round(stability, 3), "mean_false_alarm": round(statistics.mean(fp_counts), 3),
            "recall_by_rule": recall_by_rule,
            "false_alarm_by_rule": dict(fp_total),
            "false_alarm_evidence": {rid: list(dict.fromkeys(e))[:3] for rid, e in fp_ev.items()},
        })
        print(f"  {c['id']:18s} exact {exact_rate:.2f} 안정 {stability:.2f} "
              f"오탐 {statistics.mean(fp_counts):.2f}  검출 {recall_by_rule or '(전부 미학 계약)'}")

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
    (base / "specqa_check_result.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n" + "=" * 60)
    print(f"[SPECQA-CHECK 결과] exact 정확률 {summary['exact_rate_mean']} "
          f"(완전정확 케이스 {summary['fully_exact_cases']}/{len(per_case)}), "
          f"평균 안정성 {summary['mean_stability']}, 평균 오탐 {summary['mean_false_alarm']}")
    print(f"  기준별 검출률(recall): {recall_by_name}")
    print(f"[SPECQA-CHECK] → {base / 'specqa_check_result.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
