# Atelier specQA 단계 — FROZEN 아웃라인 → lead 씬 계약 초안 → 다축 리뷰 → synthesis(FROZEN 씬 계약)
"""design.py의 거울. design이 바이블→비트시트를 낳듯, specQA는 FROZEN 아웃라인(premise+setups+beats)을
받아 씬별 계약(scene contract)을 낳는다. 각 씬의 기준을 **원자화**(한 기준 = 한 축)하고 kind를 단다 —
canon(객관 검증가능: 연속성·세계규칙·인물사실·복선회수·타임라인) vs aesthetic(검증불가: 문장·긴장·페이싱·
목소리). 산출물 contract.json(kind 제거)은 specqa_check이 그대로 먹는 모양이라, specQA가 계약을 낳고
specqa_check이 캐논/미학 격리를 채점한다 — design → specQA → specqa_check 루프가 닫힌다.

이 단계의 핵심(실콜이 짚은 soft spot): 기준을 원자화해 사실 축과 톤 축을 *한 기준에 섞지 않는다*. 혼합
기준(예: "발타자르는 적대자다 — 우호적으로 묘사돼선 안 된다")은 사실(canon)/톤(aesthetic) 둘로 쪼갠다.

31B(critic)만 쓴다. 리뷰어는 atelier 키 11개에 병렬(워커=키).

사용:
  python specqa.py --replay fixtures_specqa/specqa_replay.json                          # 키 안 씀(패킷까지)
  python specqa.py --outline runs/outline_ko --out runs/contract_ko                     # ★키 (FROZEN 계약)
"""

import argparse
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "lib"))   # vendored 인프라 — golem 폴더 비의존

from jsonutil import extract_json        # noqa: E402

MODEL_31 = "gemma-4-31b-it"
ROLE = "critic"   # 씬 계약 설계·비평 = '머리' 일 → 31B

# 리뷰어 10축. 각 리뷰어는 단 하나의 축에서만 계약 구멍을 사냥한다(다양성 강제).
# 1축(혼합 기준)이 이 단계의 핵심 — 실콜이 짚은 유일 soft spot을 생산 단계에서 차단한다.
AXES = [
    "mixed criterion: a single criterion fuses an objective fact (canon) with a matter of taste (aesthetic) and must be split into two atomized criteria",
    "miscategorized kind: a criterion tagged 'canon' that has no objective yes/no oracle, or tagged 'aesthetic' that is actually objectively checkable",
    "uncovered canon: a hard fact from the premise/setups that is relevant to a scene but no criterion asserts it",
    "setup payoff unassigned: a setup that should pay off in a scene but no criterion of that scene requires it",
    "vague criterion: a criterion too vague for a drafter to satisfy or for anyone to check",
    "timeline criterion: a scene's order/timing constraint is missing or contradicts another scene",
    "redundant criterion: two criteria (within or across scenes) doing the same work (should merge)",
    "missing aesthetic guidance: a scene with only canon criteria and no aesthetic direction (under-specified for prose)",
    "scope error: a criterion filed under a scene it does not belong to",
    "handoff risk to draft: things the next stage (chapter drafting) would misread from this scene contract",
]

ISSUE_KEYS = ["mixed_criteria", "miscategorized", "coverage_gaps",
              "vague_or_redundant", "risky_assumptions"]

_LEAD_PROMPT = """You are the SPEC EDITOR turning a FROZEN STORY OUTLINE into SCENE CONTRACTS. A drafter
must be able to write each scene from your contract, and a QA must be able to separate the
machine-checkable (canon) criteria from the matters of taste (aesthetic).

FROZEN OUTLINE PREMISE:
{premise}

TRACKED SETUPS (must be paid off across scenes):
{setups}

BEAT SHEET (the ordered scenes to cover):
{beats}

LANGUAGE: Write every criterion text in the SAME LANGUAGE as the PREMISE above.
Keep only the === SECTION === markers and JSON keys/ids/kind values in English.

ATOMIZATION RULE (the whole point): each criterion tests EXACTLY ONE thing. NEVER fuse an objective
fact with a matter of taste in one criterion — split them. Example: NOT "Balthazar is the antagonist
and must not be depicted warmly" (fact + tone fused); instead TWO criteria: a canon one "Balthazar
appears as the regent-antagonist in this scene" and an aesthetic one "the scene keeps Balthazar's
menace palpable". Tag each criterion's kind:
- "canon"     = objective yes/no oracle (continuity, world rule, character fact, setup payoff, timeline).
- "aesthetic" = matter of craft/taste with no objective oracle (prose, tension, pacing, voice, tone, mood).

Write the scene contracts using EXACT section markers:

=== SCENES ===
A JSON array of scenes covering the beats. At least 3 scenes, at least 8 criteria total. Each scene:
{{"scene_id":"sc1","summary":"<one line>","criteria":[{{"id":"C1","text":"...","kind":"canon"}}, ...]}}
Each scene needs at least one canon criterion AND at least one aesthetic criterion. criterion ids are
scene-local (C1, C2, ... restart per scene).
"""

_REVIEW_INSTRUCTIONS = """Do NOT rewrite the contract. ONLY hunt for problems on your assigned axis.
Output ONE JSON object EXACTLY in this shape (each a list of short strings, [] if none):
{{
  "mixed_criteria": [],
  "miscategorized": [],
  "coverage_gaps": [],
  "vague_or_redundant": [],
  "risky_assumptions": [],
  "questions_for_lead": [{{"q": "...", "class": "BLOCKING|ASSUMED|DEFERRED"}}]
}}
Put each problem under the most fitting key. questions_for_lead: only real questions, classified.
Output the JSON object only, no prose."""

_REVIEWER_PROMPT = """You are a SCENE CONTRACT REVIEWER. Your single review axis is:
AXIS: {axis}

Here is the scene contract to review:
{draft}

{instructions}
"""

_SYNTHESIS_PROMPT = """You are the SPEC EDITOR doing SYNTHESIS. You wrote this scene contract:
{draft}

Independent reviewers found these issues (JSON):
{issues}

Resolve them and FREEZE the scene contract. Output ONE JSON object EXACTLY in this shape:
{{
  "decisions": ["concrete fix of a hole", "..."],
  "premise": "the frozen 2-4 sentence premise (carry from the outline)",
  "scenes": [{{"scene_id":"sc1","summary":"...","criteria":[{{"id":"C1","text":"...","kind":"canon|aesthetic"}}]}}],
  "assumed": ["assumption you fix to proceed"],
  "deferred": ["question pushed to a later draft/book"]
}}
HARD RULE: every BLOCKING reviewer question MUST be either answered in decisions OR moved to
assumed/deferred. Leave NO blocking question open. ATOMIZE every criterion (one fact OR one taste, never
both fused) and tag kind correctly. scenes>=3, criteria total>=8, each scene >=1 canon and >=1 aesthetic.
JSON only, no prose.
LANGUAGE: write premise, every criterion text, decisions, assumed and deferred in the SAME LANGUAGE as
the contract above (keep JSON keys/ids/kind values in English)."""

_SECTION_RE = re.compile(r"^===\s*(.+?)\s*===\s*$", re.MULTILINE)


def _split_sections(draft):
    """초안의 '=== NAME ===' 마커로 섹션 분리. {name_upper: body}."""
    parts = _SECTION_RE.split(draft)
    out = {}
    for i in range(1, len(parts) - 1, 2):
        out[parts[i].strip().upper()] = parts[i + 1].strip()
    return out


def _aggregate_issues(reviews):
    """리뷰들을 카테고리별로 합치고 BLOCKING 질문도 모은다(synthesis 입력)."""
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


def run_synthesis(outline, caller):
    """전체 specQA: 씬 계약 초안 → 리뷰어 10 → synthesis(BLOCKING→0 + FROZEN 씬 계약)."""
    draft = caller.draft(outline)
    reviews = caller.reviews(outline, draft, AXES)
    issues = _aggregate_issues(reviews)
    packet = caller.synth(outline, draft, issues)
    return draft, reviews, issues, packet


def _scenes_from_packet(packet, draft):
    """synthesis의 scenes를 쓰되, 비면 lead 초안의 === SCENES === JSON 배열로 폴백."""
    scenes = packet.get("scenes", []) or []
    if scenes:
        return scenes
    body = _split_sections(draft).get("SCENES", "")
    lo, hi = body.find("["), body.rfind("]")
    if lo < 0 or hi <= lo:
        return []
    try:
        return json.loads(body[lo:hi + 1])
    except json.JSONDecodeError:
        return []


def _write_packet(outline, draft, reviews, issues, packet, outdir):
    """씬 계약 패킷을 파일로 굳힌다. scenes가 차고 criteria가 차고 BLOCKING이 흡수되면 FROZEN.
    contract.json은 specqa_check이 그대로 먹는 모양(premise + scenes{scene_id:[{id,text}]}, kind 제거)이고,
    cases.json은 kind=='canon'에서 뽑은 golden_canon이라 닫힘 검증(채점기가 의도와 일치하나)에 쓴다."""
    outdir.mkdir(parents=True, exist_ok=True)
    scenes = _scenes_from_packet(packet, draft)
    premise = packet.get("premise", "") or outline.get("premise", "")

    # contract.json: 채점기 입력 모양 — kind 제거(채점기가 블라인드 분류)
    scenes_map, cases, dup_ids, total_crit = {}, [], [], 0
    for sc in scenes:
        sid = sc.get("scene_id") or f"sc{len(scenes_map) + 1}"
        crits = sc.get("criteria", []) or []
        scenes_map[sid] = [{"id": c.get("id"), "text": c.get("text", "")} for c in crits]
        golden = [c.get("id") for c in crits if str(c.get("kind", "")).lower() == "canon"]
        cases.append({"id": sid, "golden_canon": golden})
        total_crit += len(crits)
        ids = [c.get("id") for c in crits]
        dup_ids += [f"{sid}:{i}" for i in ids if i and ids.count(i) > 1]
    dup_ids = sorted(set(dup_ids))

    (outdir / "contract.json").write_text(
        json.dumps({"premise": premise, "scenes": scenes_map}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    (outdir / "cases.json").write_text(
        json.dumps(cases, ensure_ascii=False, indent=2), encoding="utf-8")

    # 사람이 읽는 씬 계약(kind 포함)
    lines = ["# 씬 계약 (FROZEN — kind 포함, 채점기엔 kind 빼고 넣음)", ""]
    for sc in scenes:
        lines.append(f"## {sc.get('scene_id', '?')} — {sc.get('summary', '')}")
        for c in sc.get("criteria", []) or []:
            lines.append(f"- [{c.get('id')}] ({c.get('kind')}) {c.get('text', '')}")
        lines.append("")
    (outdir / "contract.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    (outdir / "review.json").write_text(
        json.dumps({"reviews": reviews, "aggregated": issues}, ensure_ascii=False, indent=2),
        encoding="utf-8")

    n_block = len(issues.get("BLOCKING_questions", []))
    decisions = packet.get("decisions", [])
    assumed = packet.get("assumed", [])
    deferred = packet.get("deferred", [])
    q = ["# questions — 질문 처리", "",
         f"## 해소된 결정(decisions) {len(decisions)}", *[f"- {d}" for d in decisions], "",
         f"## ASSUMED(가정 고정) {len(assumed)}", *[f"- {a}" for a in assumed], "",
         f"## DEFERRED(후속 미룸) {len(deferred)}", *[f"- {d}" for d in deferred]]
    (outdir / "questions.md").write_text("\n".join(q) + "\n", encoding="utf-8")

    # FROZEN 조건: ⑴ BLOCKING 흡수(개수 게이트, design과 동일), ⑵ scenes>=3 + criteria>=8,
    #   ⑶ 씬 안 criterion ID 중복 없음, ⑷ 각 씬에 canon·aesthetic 둘 다 있음(격리 가능한 계약).
    absorbed = len(decisions) + len(assumed) + len(deferred)
    unresolved_block = max(0, n_block - absorbed)
    resolved = bool(decisions or assumed or deferred) and unresolved_block == 0
    both_kinds = all(
        any(str(c.get("kind", "")).lower() == "canon" for c in (sc.get("criteria") or []))
        and any(str(c.get("kind", "")).lower() == "aesthetic" for c in (sc.get("criteria") or []))
        for sc in scenes) if scenes else False
    frozen = (resolved and len(scenes) >= 3 and total_crit >= 8 and not dup_ids and both_kinds)
    status = ["# STATUS", "",
              f"- 리뷰어 BLOCKING 원본: {n_block}",
              f"- 흡수: decisions {len(decisions)} / assumed {len(assumed)} / deferred {len(deferred)}",
              f"- 미해소 BLOCKING: {unresolved_block} (흡수 {absorbed} vs 원본 {n_block})",
              f"- scenes 수: {len(scenes)} / criteria 총수: {total_crit}",
              f"- criterion ID 중복: {', '.join(dup_ids) if dup_ids else '없음'}",
              f"- 각 씬 canon+aesthetic 공존: {'예' if both_kinds else '아니오'}",
              "",
              f"CONTRACT_STATUS: {'FROZEN' if frozen else 'OPEN (BLOCKING 미해소 / scenes<3 / criteria<8 / ID중복 / kind불균형)'}"]
    (outdir / "STATUS.md").write_text("\n".join(status) + "\n", encoding="utf-8")
    return {"frozen": frozen, "blocking_original": n_block, "unresolved_block": unresolved_block,
            "decisions": len(decisions), "assumed": len(assumed), "deferred": len(deferred),
            "scenes": len(scenes), "criteria": total_crit, "dup_ids": dup_ids, "both_kinds": both_kinds}


# ---- caller: fake(녹음 재생, 키X) / real(LLMClient, 키O) ----

class FakeCaller:
    """fixture JSON에서 lead 초안과 리뷰를 재생한다(콜0)."""

    def __init__(self, fixture):
        self.fx = fixture

    def draft(self, outline):
        return self.fx["lead_draft"]

    def reviews(self, outline, draft, axes):
        return [self.fx["reviews"][i] for i in range(len(axes))]

    def synth(self, outline, draft, issues):
        return self.fx["synthesis"]


class RealCaller:
    """31B(critic)로 실제 호출. 리뷰어는 키풀에 병렬(워커=키). ★키 씀."""

    def __init__(self):
        # 31B 핀 가드: atelier는 critic(31B)만 쓴다. .env 오염·역할 오용으로 26B가 새지 않게 강제.
        if ROLE != "critic":
            raise SystemExit(f"[SPECQA] ROLE은 critic(31B)이어야 한다 — 받은 값 {ROLE!r}")
        os.environ["GENERATOR_MODEL"] = MODEL_31
        os.environ["CRITIC_MODEL"] = MODEL_31
        from config import get_api_keys, load_env
        from llm import KeyPool
        env_path = HERE / ".env"
        if not env_path.exists():
            raise SystemExit(f"[SPECQA] atelier 전용 키가 없다 — {env_path} 에 "
                             "GOOGLE_API_KEY_1..N 을 넣어라 (golem 키와 섞이지 않게).")
        load_env(env_path)
        self.pool = KeyPool(get_api_keys(), models=[MODEL_31])

    def _one(self, prompt):
        from llm import LLMClient
        with self.pool.checkout() as key:
            return LLMClient(api_key=key).generate(ROLE, prompt)

    def _fmt_outline(self, outline):
        premise = outline.get("premise", "")
        setups = "\n".join(f'- [{s["id"]}] {s["text"]}' for s in outline.get("setups", []))
        beats = "\n".join(outline.get("beats", []))
        return premise, setups, beats

    def draft(self, outline):
        premise, setups, beats = self._fmt_outline(outline)
        return self._one(_LEAD_PROMPT.format(premise=premise, setups=setups, beats=beats))

    def reviews(self, outline, draft, axes):
        out = [None] * len(axes)
        with ThreadPoolExecutor(max_workers=min(len(axes), self.pool.size)) as ex:
            futs = {ex.submit(self._one, _REVIEWER_PROMPT.format(
                axis=ax, draft=draft, instructions=_REVIEW_INSTRUCTIONS)): i
                for i, ax in enumerate(axes)}
            for fut in futs:
                i = futs[fut]
                out[i] = extract_json(fut.result())
        return out

    def synth(self, outline, draft, issues):
        text = self._one(_SYNTHESIS_PROMPT.format(
            draft=draft, issues=json.dumps(issues, ensure_ascii=False)))
        parsed = extract_json(text)
        if not parsed:   # 파싱 실패(잘림/형식) 진단용 raw 덤프 — runs는 gitignore
            (HERE / "runs").mkdir(exist_ok=True)
            (HERE / "runs" / "_specqa_synth_raw.txt").write_text(
                f"len={len(text)}\ntail<<<\n{text[-600:]}\n>>>\nhead<<<\n{text[:600]}",
                encoding="utf-8")
        return parsed


def _load_outline(path):
    """FROZEN 아웃라인 폴더(outline.json + beatsheet.md) 또는 outline.json 파일을 읽어 premise+setups+beats."""
    p = Path(path)
    odir = p if p.is_dir() else p.parent
    oj = json.loads((odir / "outline.json").read_text(encoding="utf-8")) if p.is_dir() \
        else json.loads(p.read_text(encoding="utf-8"))
    beats = []
    bs = odir / "beatsheet.md"
    if bs.exists():
        beats = [ln.strip() for ln in bs.read_text(encoding="utf-8").splitlines()
                 if ln.strip().startswith("[B")]
    return {"premise": oj.get("premise", ""), "setups": oj.get("setups", []), "beats": beats}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--replay", default=None, help="fixture JSON으로 키 없이 재생")
    ap.add_argument("--outline", default=None,
                    help="FROZEN 아웃라인 폴더(outline.json + beatsheet.md) 또는 outline.json — ★키 씀")
    ap.add_argument("--out", default=None, help="패킷 출력 폴더(기본 contract_packet)")
    args = ap.parse_args(argv)

    try:
        from config import force_utf8_stdout
        force_utf8_stdout()
    except Exception:  # noqa: BLE001
        pass

    if args.replay:
        fx = json.loads(Path(args.replay).read_text(encoding="utf-8"))
        outline = fx.get("outline", {})
        caller = FakeCaller(fx)
    elif args.outline:
        outline = _load_outline(args.outline)
        caller = RealCaller()
    else:
        ap.error("--replay 또는 --outline 중 하나 필요")

    outdir = Path(args.out) if args.out else (HERE / "contract_packet")
    draft, reviews, issues, packet = run_synthesis(outline, caller)
    st = _write_packet(outline, draft, reviews, issues, packet, outdir)
    print(f"[SPECQA] outline premise={outline.get('premise', '')[:40]!r}...")
    print(f"  BLOCKING 원본 {st['blocking_original']} → 흡수 "
          f"decisions {st['decisions']}/assumed {st['assumed']}/deferred {st['deferred']}")
    print(f"  scenes {st['scenes']}개 / criteria {st['criteria']}개 / 각 씬 canon+aesthetic {st['both_kinds']}")
    print(f"  CONTRACT_STATUS: {'FROZEN' if st['frozen'] else 'OPEN'}  → {outdir}")
    return 0 if st["frozen"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
