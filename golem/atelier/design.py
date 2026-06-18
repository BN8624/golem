# Atelier Design 단계 — FROZEN 바이블 → lead 비트시트 초안 → 다축 리뷰 → synthesis(FROZEN 아웃라인)
"""planning.py의 거울. planning이 로그라인→바이블을 낳듯, design은 FROZEN 바이블(계약 패킷)을
받아 비트시트(ordered beats + tracked setups)를 낳는다. 출력은 design_check이 그대로 먹는 모양
(outline.json: premise + setups[{id,text}], beatsheet.md)이라, design이 아웃라인을 낳고 design_check이
setup→payoff를 지킨다 — planning → design → (canon_check / design_check) 루프가 닫힌다.

31B(critic)만 쓴다. 리뷰어는 atelier 키 11개에 병렬(워커=키).

사용:
  python design.py --replay fixtures_design/design_replay.json                       # 키 안 씀(패킷까지)
  python design.py --bible runs/bible_packet_ko/bible.json --out runs/outline_ko     # ★키 (FROZEN 아웃라인)
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
ROLE = "critic"   # 비트시트 설계·비평 = '머리' 일 → 31B

# 리뷰어 10축. 각 리뷰어는 단 하나의 축에서만 비트시트 구멍을 사냥한다(다양성 강제).
# 앞쪽 축(미회수·반전·캐논·타임라인)은 구조-기계채점 가능, 뒤쪽(페이싱·스테이크)은 미학 영역.
AXES = [
    "unresolved setup: a setup the bible plants is introduced in a beat but never paid off in a later beat",
    "unsetup payoff: a beat resolves something that was never set up in an earlier beat",
    "reversal on hidden info: a twist/reveal depends on information the reader was never shown on the page",
    "canon contradiction: a beat asserts something that contradicts a frozen canon fact",
    "motivation gap: a character acts in a beat with no motivation established by an earlier beat",
    "timeline contradiction: the beat order contains events that cannot all be true",
    "pacing imbalance: the beats are wildly uneven (one stretch crammed, another empty of event)",
    "stakes flatline: a run of beats with no escalation or change in what is at risk",
    "redundant beat: two beats doing the same dramatic work (should merge)",
    "handoff risk to draft: things the next stage (chapter drafting) would misread from this beat sheet",
]

ISSUE_KEYS = ["unresolved_setups", "missing_beats", "contradictions",
              "weak_pacing", "risky_assumptions"]

_LEAD_PROMPT = """You are the STORY ARCHITECT turning a FROZEN STORY BIBLE into a BEAT SHEET (chapter
outline). Another writer must be able to draft chapters from your beat sheet without asking you anything.

FROZEN BIBLE PREMISE:
{premise}

FROZEN CANON (hard facts you must NEVER contradict):
{canon}

LANGUAGE: Write every beat and every setup text in the SAME LANGUAGE as the PREMISE above.
Keep only the === SECTION === markers and JSON keys/ids in English.

Write the beat sheet using EXACT section markers:

=== SETUPS ===
A JSON array of the SETUPS this story plants — promises/objects/mysteries/threats introduced that MUST
be paid off before the end. At least 4: [{{"id":"S1","text":"..."}}, {{"id":"S2","text":"..."}}, ...]

=== BEATS ===
An ordered list of beats, one per line, each labeled [B1], [B2], ... Each beat one or two sentences.
HARD RULE: every setup in === SETUPS === MUST be both introduced in some beat AND paid off (resolved,
not merely re-mentioned) in a LATER beat. Do not contradict any FROZEN CANON fact. At least 8 beats.
"""

_REVIEW_INSTRUCTIONS = """Do NOT rewrite the beat sheet. ONLY hunt for problems on your assigned axis.
Output ONE JSON object EXACTLY in this shape (each a list of short strings, [] if none):
{{
  "unresolved_setups": [],
  "missing_beats": [],
  "contradictions": [],
  "weak_pacing": [],
  "risky_assumptions": [],
  "questions_for_lead": [{{"q": "...", "class": "BLOCKING|ASSUMED|DEFERRED"}}]
}}
Put each problem under the most fitting key. questions_for_lead: only real questions, classified.
Output the JSON object only, no prose."""

_REVIEWER_PROMPT = """You are a BEAT SHEET REVIEWER. Your single review axis is:
AXIS: {axis}

Here is the beat sheet to review:
{draft}

{instructions}
"""

_SYNTHESIS_PROMPT = """You are the STORY ARCHITECT doing SYNTHESIS. You wrote this beat sheet:
{draft}

Independent reviewers found these issues (JSON):
{issues}

Resolve them and FREEZE the beat sheet. Output ONE JSON object EXACTLY in this shape:
{{
  "decisions": ["concrete fix of a hole", "..."],
  "premise": "the frozen 2-4 sentence premise (carry from the bible)",
  "setups": [{{"id": "S1", "text": "a promise/object/mystery that must be paid off"}}],
  "beats": ["[B1] ...", "[B2] ...", "..."],
  "assumed": ["assumption you fix to proceed"],
  "deferred": ["question pushed to a later draft/book"]
}}
HARD RULE: every BLOCKING reviewer question MUST be either answered in decisions OR moved to assumed/deferred.
Leave NO blocking question open. EVERY setup MUST be paid off by some later beat. setups>=4, beats>=8.
JSON only, no prose.
LANGUAGE: write premise, every setup text, every beat, decisions, assumed and deferred in the SAME LANGUAGE as the beat sheet above (keep JSON keys/ids in English)."""

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


def run_synthesis(bible, caller):
    """전체 Design: 비트시트 초안 → 리뷰어 10 → synthesis(BLOCKING→0 + FROZEN 아웃라인)."""
    draft = caller.draft(bible)
    reviews = caller.reviews(bible, draft, AXES)
    issues = _aggregate_issues(reviews)
    packet = caller.synth(bible, draft, issues)
    return draft, reviews, issues, packet


def _write_packet(bible, draft, reviews, issues, packet, outdir):
    """아웃라인 패킷을 파일로 굳힌다. setups가 차고 beats가 차고 BLOCKING이 흡수되면 FROZEN.
    outline.json은 design_check이 그대로 먹는 모양(premise + setups[{id,text}])이다."""
    outdir.mkdir(parents=True, exist_ok=True)
    setups = packet.get("setups", []) or []
    beats = packet.get("beats", []) or []
    if not beats:   # synthesis가 beats를 빠뜨리면 lead 초안의 BEATS 섹션으로 폴백
        sec = _split_sections(draft)
        beats = [ln for ln in sec.get("BEATS", "").splitlines() if ln.strip()]

    premise = packet.get("premise", "") or bible.get("premise", "")
    (outdir / "outline.json").write_text(
        json.dumps({"premise": premise, "setups": setups}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    (outdir / "beatsheet.md").write_text(
        "# 비트시트 (FROZEN 아웃라인)\n\n" + "\n".join(beats) + "\n", encoding="utf-8")
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

    # FROZEN 조건: ⑴ BLOCKING 흡수, ⑵ setups>=4 + beats>=8, ⑶ setup ID 중복 없음.
    # ⑴ 거짓 0 방지: 흡수 항목 총수가 BLOCKING 수 이상이어야 한다(질문보다 답이 적으면 OPEN). 완전한 1:1
    #    해소 추적은 자유서술 답이라 LLM 판정이 필요(별도) — 여기선 개수 게이트로 "일부만 답하면 통과"를 막는다.
    absorbed = len(decisions) + len(assumed) + len(deferred)
    unresolved_block = max(0, n_block - absorbed)
    resolved = bool(decisions or assumed or deferred) and unresolved_block == 0
    setup_ids = [s.get("id") for s in setups]
    dup_ids = sorted({i for i in setup_ids if i and setup_ids.count(i) > 1})
    frozen = resolved and len(setups) >= 4 and len(beats) >= 8 and not dup_ids
    status = ["# STATUS", "",
              f"- 리뷰어 BLOCKING 원본: {n_block}",
              f"- 흡수: decisions {len(decisions)} / assumed {len(assumed)} / deferred {len(deferred)}",
              f"- 미해소 BLOCKING: {unresolved_block} (흡수 {absorbed} vs 원본 {n_block})",
              f"- setups 수: {len(setups)} / beats 수: {len(beats)}",
              f"- setup ID 중복: {', '.join(dup_ids) if dup_ids else '없음'}",
              "",
              f"OUTLINE_STATUS: {'FROZEN' if frozen else 'OPEN (BLOCKING 미해소 또는 setups<4/beats<8 또는 ID중복)'}"]
    (outdir / "STATUS.md").write_text("\n".join(status) + "\n", encoding="utf-8")
    return {"frozen": frozen, "blocking_original": n_block, "unresolved_block": unresolved_block,
            "decisions": len(decisions), "assumed": len(assumed), "deferred": len(deferred),
            "setups": len(setups), "beats": len(beats), "dup_ids": dup_ids}


# ---- caller: fake(녹음 재생, 키X) / real(LLMClient, 키O) ----

class FakeCaller:
    """fixture JSON에서 lead 초안과 리뷰를 재생한다(콜0)."""

    def __init__(self, fixture):
        self.fx = fixture

    def draft(self, bible):
        return self.fx["lead_draft"]

    def reviews(self, bible, draft, axes):
        return [self.fx["reviews"][i] for i in range(len(axes))]

    def synth(self, bible, draft, issues):
        return self.fx["synthesis"]


class RealCaller:
    """31B(critic)로 실제 호출. 리뷰어는 키풀에 병렬(워커=키). ★키 씀."""

    def __init__(self):
        # 31B 핀 가드: atelier는 critic(31B)만 쓴다. .env 오염·역할 오용으로 26B가 새지 않게 강제.
        if ROLE != "critic":
            raise SystemExit(f"[DESIGN] ROLE은 critic(31B)이어야 한다 — 받은 값 {ROLE!r}")
        os.environ["GENERATOR_MODEL"] = MODEL_31
        os.environ["CRITIC_MODEL"] = MODEL_31
        from config import get_api_keys, load_env
        from llm import KeyPool
        env_path = HERE / ".env"
        if not env_path.exists():
            raise SystemExit(f"[DESIGN] atelier 전용 키가 없다 — {env_path} 에 "
                             "GOOGLE_API_KEY_1..N 을 넣어라 (golem 키와 섞이지 않게).")
        load_env(env_path)
        self.pool = KeyPool(get_api_keys(), models=[MODEL_31])

    def _one(self, prompt):
        from llm import LLMClient
        with self.pool.checkout() as key:
            return LLMClient(api_key=key).generate(ROLE, prompt)

    def _fmt_bible(self, bible):
        premise = bible.get("premise", "")
        canon = "\n".join(f'- [{c["id"]}] {c["text"]}' for c in bible.get("canon", []))
        return premise, canon

    def draft(self, bible):
        premise, canon = self._fmt_bible(bible)
        return self._one(_LEAD_PROMPT.format(premise=premise, canon=canon))

    def reviews(self, bible, draft, axes):
        out = [None] * len(axes)
        with ThreadPoolExecutor(max_workers=min(len(axes), self.pool.size)) as ex:
            futs = {ex.submit(self._one, _REVIEWER_PROMPT.format(
                axis=ax, draft=draft, instructions=_REVIEW_INSTRUCTIONS)): i
                for i, ax in enumerate(axes)}
            for fut in futs:
                i = futs[fut]
                out[i] = extract_json(fut.result())
        return out

    def synth(self, bible, draft, issues):
        text = self._one(_SYNTHESIS_PROMPT.format(
            draft=draft, issues=json.dumps(issues, ensure_ascii=False)))
        parsed = extract_json(text)
        if not parsed:   # 파싱 실패(잘림/형식) 진단용 raw 덤프 — runs는 gitignore
            (HERE / "runs").mkdir(exist_ok=True)
            (HERE / "runs" / "_design_synth_raw.txt").write_text(
                f"len={len(text)}\ntail<<<\n{text[-600:]}\n>>>\nhead<<<\n{text[:600]}",
                encoding="utf-8")
        return parsed


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--replay", default=None, help="fixture JSON으로 키 없이 재생")
    ap.add_argument("--bible", default=None, help="FROZEN 바이블 경로(bible.json: premise+canon) — ★키 씀")
    ap.add_argument("--out", default=None, help="패킷 출력 폴더(기본 outline_packet)")
    args = ap.parse_args(argv)

    try:
        from config import force_utf8_stdout
        force_utf8_stdout()
    except Exception:  # noqa: BLE001
        pass

    if args.replay:
        fx = json.loads(Path(args.replay).read_text(encoding="utf-8"))
        bible = fx.get("bible", {})
        caller = FakeCaller(fx)
    elif args.bible:
        bible = json.loads(Path(args.bible).read_text(encoding="utf-8"))
        caller = RealCaller()
    else:
        ap.error("--replay 또는 --bible 중 하나 필요")

    outdir = Path(args.out) if args.out else (HERE / "outline_packet")
    draft, reviews, issues, packet = run_synthesis(bible, caller)
    st = _write_packet(bible, draft, reviews, issues, packet, outdir)
    print(f"[DESIGN] bible premise={bible.get('premise', '')[:40]!r}...")
    print(f"  BLOCKING 원본 {st['blocking_original']} → 흡수 "
          f"decisions {st['decisions']}/assumed {st['assumed']}/deferred {st['deferred']}")
    print(f"  setups {st['setups']}개 / beats {st['beats']}개")
    print(f"  OUTLINE_STATUS: {'FROZEN' if st['frozen'] else 'OPEN'}  → {outdir}")
    return 0 if st["frozen"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
