# Atelier Planning 단계 — 로그라인 한 줄 → lead 바이블 초안 → 다축 리뷰 → synthesis(FROZEN 바이블)
"""골렘 studio/planning.py의 소설판. 핵심 질문은 동일하다 — 독립 리뷰어가 self-review보다
스토리 구멍(연속성·타임라인·동기·복선)을 더 잡나(A/B/C arm). 출력은 canon_check이 먹는
bible.json 모양(premise + canon[{id,text}])이라, planning이 바이블을 낳고 canon_check이 지킨다.

세 arm:
  A = lead 초안 + 자기검토(self-review, 출제=채점 같은 모델 → 편향).
  B = lead 초안 + 독립 리뷰어 3 (서로 다른 축).
  C = lead 초안 + 독립 리뷰어 10.

사용:
  python planning.py --replay fixtures/planning_replay.json                 # 키 안 씀
  python planning.py --replay fixtures/planning_replay.json --synthesize    # 키 안 씀(패킷까지)
  python planning.py --idea "..." [--arms A,B,C]                            # ★키 (사용자 go 뒤)
  python planning.py --idea "..." --synthesize --out bible_packet           # ★키 (FROZEN 바이블)

31B(critic)만 쓴다. 리뷰어는 atelier 키 11개에 병렬(워커=키).
"""

import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "lib"))   # vendored 인프라 — golem 폴더 비의존

from jsonutil import extract_json        # noqa: E402

MODEL_31 = "gemma-4-31b-it"
ROLE = "critic"   # 스토리 기획·비평 = '머리' 일 → 31B

# 리뷰어 10축. 각 리뷰어는 단 하나의 축에서만 구멍을 사냥한다(다양성 강제).
# 앞쪽 축(타임라인·지식·세계규칙)은 캐논-기계채점 가능, 뒤쪽(톤·테마·긴장)은 미학 영역.
AXES = [
    "unmotivated action: a character does something the bible gives no reason for",
    "unresolved setup: a promise/object/mystery introduced but the bible never pays off",
    "timeline contradiction: events whose order cannot all be true",
    "character knowledge violation: someone knows or uses info they could not have yet",
    "world-rule contradiction: a world rule that conflicts with another rule or with the plot",
    "redundant character: two characters serving the same dramatic function (should merge)",
    "theme without payoff: a theme stated but nothing in the story can dramatize it",
    "tone/voice inconsistency: the stated tone clashes with the premise or characters",
    "stakes ambiguity: unclear what is at risk or why the reader should care",
    "handoff risk to outline: things the next stage (beat sheet) would misread from this bible",
]

ISSUE_KEYS = ["ambiguous_facts", "missing_canon", "contradictions",
              "underspecified_arcs", "risky_assumptions"]

_LEAD_PROMPT = """You are the STORY LEAD building the bible for a novel from ONE logline. Keep it tight and
internally consistent — another writer must be able to draft chapters from it without asking you anything.

LOGLINE: {idea}

LANGUAGE: Write EVERY section body AND every canon text in the SAME LANGUAGE as the LOGLINE above.
Keep only the === SECTION === markers and JSON keys/ids in English.

Write the bible using EXACT section markers:

=== PREMISE ===
2-4 sentences: who wants what, the central conflict, the engine that keeps the story moving.

=== CHARACTERS ===
- Each: name, role, ONE defining hard fact (body/past/relation), their want, their secret.

=== WORLD ===
- Setting + the HARD rules of this world (e.g. "magic works only at night"). Rules must be unambiguous.

=== TIMELINE ===
- Ordered key events (before and during the story). Make the order checkable.

=== THEMES ===
- 1-3 themes the story will dramatize.

=== CANON ===
A JSON array of the HARD FACTS that must NEVER be contradicted later (drawn from characters/world/timeline).
Each fact one line, checkable: [{{"id":"C1","text":"..."}}, {{"id":"C2","text":"..."}}, ...]
"""

_REVIEW_INSTRUCTIONS = """Do NOT add plot or rewrite the bible. ONLY hunt for problems on your assigned axis.
Output ONE JSON object EXACTLY in this shape (each a list of short strings, [] if none):
{{
  "ambiguous_facts": [],
  "missing_canon": [],
  "contradictions": [],
  "underspecified_arcs": [],
  "risky_assumptions": [],
  "questions_for_lead": [{{"q": "...", "class": "BLOCKING|ASSUMED|DEFERRED"}}]
}}
Put each problem under the most fitting key. questions_for_lead: only real questions, classified.
Output the JSON object only, no prose."""

_REVIEWER_PROMPT = """You are a STORY REVIEWER. Your single review axis is:
AXIS: {axis}

Here is the bible to review:
{draft}

{instructions}
"""

_SELF_REVIEW_PROMPT = """You are the STORY LEAD reviewing YOUR OWN bible for holes before handoff.
Here is your bible:
{draft}

{instructions}
"""

_SYNTHESIS_PROMPT = """You are the STORY LEAD doing SYNTHESIS. You wrote this bible:
{draft}

Independent reviewers found these issues (JSON):
{issues}

Resolve them and FREEZE the story bible. Output ONE JSON object EXACTLY in this shape:
{{
  "decisions": ["concrete resolution of a hole", "..."],
  "terms": {{"term": "definition"}},
  "scope": {{"goals": ["what this story IS about"], "non_goals": ["what it will NOT cover"]}},
  "premise": "the frozen 2-4 sentence premise",
  "canon": [{{"id": "C1", "text": "a hard fact that must never be contradicted"}}],
  "assumed": ["assumption you fix to proceed"],
  "deferred": ["question pushed to a later draft/book"]
}}
HARD RULE: every BLOCKING reviewer question MUST be either answered in decisions OR moved to assumed/deferred.
Leave NO blocking question open. canon must have >=3 checkable facts. JSON only, no prose.
LANGUAGE: write premise text, every canon text, decisions, assumed and deferred in the SAME LANGUAGE as the bible above (keep JSON keys/ids in English)."""

_SECTION_RE = re.compile(r"^===\s*(.+?)\s*===\s*$", re.MULTILINE)

_STOP = {"the", "and", "for", "are", "not", "что", "when", "with", "this", "that",
         "will", "may", "via", "per", "into", "from", "does", "between"}


def _norm(s):
    """이슈 문자열 정규화(중복 판정용): 소문자·영숫자만·공백 단일화."""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", str(s).lower())).strip()


def _tokens(s):
    """의미어 토큰 집합(3글자 이상, 불용어 제거) — 어순 무관 중복 판정용."""
    return {w for w in _norm(s).split() if len(w) > 2 and w not in _STOP}


def _similar(a, b, th):
    """두 이슈가 같은 문제를 가리키나(토큰 Jaccard ≥ th). 토큰 없으면 정규화 동일성."""
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return _norm(a) == _norm(b)
    return len(ta & tb) / len(ta | tb) >= th


def _dedup(items, th=0.5):
    """어휘 유사도 클러스터링으로 의미중복을 접는다(stdlib only, 키X)."""
    reps = []
    for it in items:
        if not any(_similar(it, r, th) for r in reps):
            reps.append(it)
    return reps


def _issues_of(review):
    """리뷰 dict에서 카테고리 이슈를 (category, text) 리스트로 평탄화."""
    out = []
    for k in ISSUE_KEYS:
        for item in (review.get(k) or []):
            out.append((k, str(item)))
    return out


def _blocking_count(review):
    return sum(1 for q in (review.get("questions_for_lead") or [])
               if str(q.get("class", "")).upper() == "BLOCKING")


def _metrics(reviews):
    """여러 리뷰의 이슈를 합쳐 total/unique/duplicate_rate/blocking 계산."""
    flat = [t for r in reviews for (_c, t) in _issues_of(r) if str(t).strip()]
    unique = _dedup(flat)
    total = len(flat)
    dup_rate = 0.0 if total == 0 else round(1 - len(unique) / total, 3)
    return {
        "reviewer_count": len(reviews),
        "total_issues": total,
        "unique_issue_count": len(unique),
        "duplicate_issue_rate": dup_rate,
        "blocking_count": sum(_blocking_count(r) for r in reviews),
        "unique_issues": unique,
    }


def _split_sections(draft):
    """초안의 '=== NAME ===' 마커로 섹션 분리. {name_upper: body}."""
    parts = _SECTION_RE.split(draft)
    out = {}
    for i in range(1, len(parts) - 1, 2):
        out[parts[i].strip().upper()] = parts[i + 1].strip()
    return out


def _aggregate_issues(reviews):
    """C arm 리뷰들을 카테고리별로 합치고 BLOCKING 질문도 모은다(synthesis 입력)."""
    agg = {k: [] for k in ISSUE_KEYS}
    blocking = []
    for r in reviews:
        for k in ISSUE_KEYS:
            agg[k].extend(r.get(k) or [])
        for q in (r.get("questions_for_lead") or []):
            if str(q.get("class", "")).upper() == "BLOCKING":
                blocking.append(q.get("q", ""))
    agg["BLOCKING_questions"] = blocking
    return agg


def run_synthesis(idea, caller):
    """전체 Planning: 초안 → 리뷰어 10 → synthesis(BLOCKING→0 + FROZEN 바이블)."""
    draft = caller.draft(idea)
    reviews = caller.reviews(idea, draft, AXES)
    issues = _aggregate_issues(reviews)
    packet = caller.synth(idea, draft, issues)
    return draft, reviews, issues, packet


def _write_packet(idea, draft, reviews, issues, packet, outdir):
    """바이블 패킷을 파일로 굳힌다. canon이 차고 BLOCKING이 흡수되면 FROZEN.
    bible.json은 canon_check이 그대로 먹는 모양(premise + canon[{id,text}])이다."""
    outdir.mkdir(parents=True, exist_ok=True)
    sec = _split_sections(draft)
    for name, fname in (("PREMISE", "premise.md"), ("CHARACTERS", "characters.md"),
                        ("WORLD", "world.md"), ("TIMELINE", "timeline.md"),
                        ("THEMES", "themes.md")):
        (outdir / fname).write_text(sec.get(name, "(없음)") + "\n", encoding="utf-8")
    (outdir / "ambiguity_review.json").write_text(
        json.dumps({"reviews": reviews, "aggregated": issues}, ensure_ascii=False, indent=2),
        encoding="utf-8")

    canon = packet.get("canon", []) or []
    (outdir / "bible.json").write_text(
        json.dumps({"premise": packet.get("premise", sec.get("PREMISE", "")), "canon": canon},
                   ensure_ascii=False, indent=2), encoding="utf-8")

    n_block = len(issues.get("BLOCKING_questions", []))
    decisions = packet.get("decisions", [])
    assumed = packet.get("assumed", [])
    deferred = packet.get("deferred", [])
    q = ["# questions — 질문 처리", "",
         f"## 해소된 결정(decisions) {len(decisions)}", *[f"- {d}" for d in decisions], "",
         f"## ASSUMED(가정 고정) {len(assumed)}", *[f"- {a}" for a in assumed], "",
         f"## DEFERRED(후속 미룸) {len(deferred)}", *[f"- {d}" for d in deferred]]
    (outdir / "questions.md").write_text("\n".join(q) + "\n", encoding="utf-8")
    (outdir / "backlog.json").write_text(json.dumps(
        {"consumer": "다음 패스/책 planning이 입력으로 읽는다", "deferred": deferred},
        ensure_ascii=False, indent=2), encoding="utf-8")

    # FROZEN 조건: BLOCKING이 decisions/assumed/deferred로 흡수됐고, canon이 ≥3 차 있어야 한다
    # (canon이 비면 canon_check이 지킬 게 없다 — 빈 바이블은 동결 의미 없음).
    resolved = bool(decisions or assumed or deferred)
    frozen = resolved and len(canon) >= 3
    status = ["# STATUS", "",
              f"- 로그라인: {idea}",
              f"- 리뷰어 BLOCKING 원본: {n_block}",
              f"- 흡수: decisions {len(decisions)} / assumed {len(assumed)} / deferred {len(deferred)}",
              f"- 미해소 BLOCKING: {0 if resolved else n_block}",
              f"- canon 사실 수: {len(canon)}",
              "",
              f"BIBLE_STATUS: {'FROZEN' if frozen else 'OPEN (BLOCKING 미해소 또는 canon<3)'}"]
    (outdir / "STATUS.md").write_text("\n".join(status) + "\n", encoding="utf-8")
    return {"frozen": frozen, "blocking_original": n_block,
            "decisions": len(decisions), "assumed": len(assumed), "deferred": len(deferred),
            "canon": len(canon)}


# ---- caller: fake(녹음 재생, 키X) / real(LLMClient, 키O) ----

class FakeCaller:
    """fixture JSON에서 lead 초안과 리뷰를 재생한다(콜0)."""

    def __init__(self, fixture):
        self.fx = fixture

    def draft(self, idea):
        return self.fx["lead_draft"]

    def self_review(self, idea, draft):
        return [self.fx["self_review"]]

    def reviews(self, idea, draft, axes):
        return [self.fx["reviews"][i] for i in range(len(axes))]

    def synth(self, idea, draft, issues):
        return self.fx["synthesis"]


class RealCaller:
    """31B(critic)로 실제 호출. 리뷰어는 키풀에 병렬(워커=키). ★키 씀."""

    def __init__(self):
        import os
        os.environ["GENERATOR_MODEL"] = MODEL_31
        os.environ["CRITIC_MODEL"] = MODEL_31
        from config import get_api_keys, load_env
        from llm import KeyPool
        env_path = HERE / ".env"
        if not env_path.exists():
            raise SystemExit(f"[PLANNING] atelier 전용 키가 없다 — {env_path} 에 "
                             "GOOGLE_API_KEY_1..N 을 넣어라 (golem 키와 섞이지 않게).")
        load_env(env_path)
        self.pool = KeyPool(get_api_keys(), models=[MODEL_31])

    def _one(self, prompt):
        from llm import LLMClient
        with self.pool.checkout() as key:
            return LLMClient(api_key=key).generate(ROLE, prompt)

    def draft(self, idea):
        return self._one(_LEAD_PROMPT.format(idea=idea))

    def self_review(self, idea, draft):
        text = self._one(_SELF_REVIEW_PROMPT.format(draft=draft, instructions=_REVIEW_INSTRUCTIONS))
        return [extract_json(text)]

    def reviews(self, idea, draft, axes):
        out = [None] * len(axes)
        with ThreadPoolExecutor(max_workers=min(len(axes), self.pool.size)) as ex:
            futs = {ex.submit(self._one, _REVIEWER_PROMPT.format(
                axis=ax, draft=draft, instructions=_REVIEW_INSTRUCTIONS)): i
                for i, ax in enumerate(axes)}
            for fut in futs:
                i = futs[fut]
                out[i] = extract_json(fut.result())
        return out

    def synth(self, idea, draft, issues):
        text = self._one(_SYNTHESIS_PROMPT.format(
            draft=draft, issues=json.dumps(issues, ensure_ascii=False)))
        parsed = extract_json(text)
        if not parsed:   # 파싱 실패(잘림/형식) 진단용 raw 덤프 — runs는 gitignore
            (HERE / "runs").mkdir(exist_ok=True)
            (HERE / "runs" / "_synth_raw.txt").write_text(
                f"len={len(text)}\ntail<<<\n{text[-600:]}\n>>>\nhead<<<\n{text[:600]}",
                encoding="utf-8")
        return parsed


ARM_REVIEWERS = {"A": 0, "B": 3, "C": 10}


def run(idea, arms, caller):
    draft = caller.draft(idea)
    results = {}
    for arm in arms:
        if arm == "A":
            reviews = caller.self_review(idea, draft)
            mode = "self-review"
        else:
            n = ARM_REVIEWERS[arm]
            reviews = caller.reviews(idea, draft, AXES[:n])
            mode = f"{n} independent reviewers"
        m = _metrics(reviews)
        m["mode"] = mode
        results[arm] = m
    return draft, results


def _verdict(results):
    """B가 A보다 unique +30%, C가 B보다 +20% 못 늘리면 독립리뷰 채택 근거 약함."""
    out = []
    a = results.get("A", {}).get("unique_issue_count")
    b = results.get("B", {}).get("unique_issue_count")
    c = results.get("C", {}).get("unique_issue_count")
    if a is not None and b is not None:
        gain = None if a == 0 else round((b - a) / a, 3)
        ok = (a == 0 and b > 0) or (gain is not None and gain >= 0.30)
        out.append(f"B vs A: unique {a}->{b} (gain={gain}) → {'독립리뷰 채택 근거 있음' if ok else '기준 미달'}")
    if b is not None and c is not None:
        gain = None if b == 0 else round((c - b) / b, 3)
        ok = (b == 0 and c > 0) or (gain is not None and gain >= 0.20)
        out.append(f"C vs B: unique {b}->{c} (gain={gain}) → {'10리뷰어 채택 근거 있음' if ok else '기준 미달'}")
    return out


def _write_outputs(idea, draft, results, api_calls):
    summary = {"idea": idea, "api_calls": api_calls, "arms": results, "verdict": _verdict(results)}
    (HERE / "runs").mkdir(exist_ok=True)
    (HERE / "runs" / "planning_result.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--replay", default=None, help="fixture JSON으로 키 없이 재생")
    ap.add_argument("--idea", default=None, help="기획할 로그라인 한 줄(★키 씀)")
    ap.add_argument("--arms", default="A,B,C")
    ap.add_argument("--synthesize", action="store_true",
                    help="A/B/C 측정 대신 전체 Planning(초안→리뷰10→synthesis→FROZEN 바이블)")
    ap.add_argument("--out", default=None, help="패킷 출력 폴더(기본 bible_packet)")
    args = ap.parse_args(argv)
    arms = [a.strip().upper() for a in args.arms.split(",") if a.strip()]

    try:
        from config import force_utf8_stdout
        force_utf8_stdout()
    except Exception:  # noqa: BLE001
        pass

    if args.replay:
        fx = json.loads(Path(args.replay).read_text(encoding="utf-8"))
        idea = fx.get("idea", "(fixture)")
        caller = FakeCaller(fx)
        api_calls = 0
    elif args.idea:
        caller = RealCaller()
        idea = args.idea
        api_calls = None
    else:
        ap.error("--replay 또는 --idea 중 하나 필요")

    if args.synthesize:
        outdir = Path(args.out) if args.out else (HERE / "bible_packet")
        draft, reviews, issues, packet = run_synthesis(idea, caller)
        st = _write_packet(idea, draft, reviews, issues, packet, outdir)
        print(f"[SYNTHESIS] idea={idea!r}")
        print(f"  BLOCKING 원본 {st['blocking_original']} → 흡수 "
              f"decisions {st['decisions']}/assumed {st['assumed']}/deferred {st['deferred']}")
        print(f"  canon 사실 {st['canon']}개")
        print(f"  BIBLE_STATUS: {'FROZEN' if st['frozen'] else 'OPEN'}  → {outdir}")
        return 0 if st["frozen"] else 1

    draft, results = run(idea, arms, caller)
    summary = _write_outputs(idea, draft, results, 0 if args.replay else api_calls)
    print(f"[PLANNING] idea={idea!r} arms={arms}")
    for arm in ("A", "B", "C"):
        if arm in results:
            r = results[arm]
            print(f"  [{arm}] {r['mode']}: total={r['total_issues']} "
                  f"unique={r['unique_issue_count']} dup={r['duplicate_issue_rate']} "
                  f"blocking={r['blocking_count']}")
    for v in summary["verdict"]:
        print(f"  {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
