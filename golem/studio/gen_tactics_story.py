# 전술 캠페인 서사(B겹)를 골렘이 생성 — 전투 구조→스토리(제목·프롤로그·장면·에필로그), 구조만 검증·엔진 불변
"""StoryForge(트랙 b) 전술판. 검증된 엔진/룰은 안 건드리고, 캠페인 전투 시퀀스(고정 비트)에 맞춰
골렘이 서사 텍스트를 저작한다. 검증은 구조만(장면 수=전투 수·키 채움) — 문장 질은 사람 몫(출력전용 B겹).
산출=tactics_play/campaign_story.json. 렌더러(gen_tactics_play.py)가 있으면 그걸 읽어 캠페인에 입힌다.

사용: python gen_tactics_story.py --idea "세계관 한 줄" [--cap 2]   (★키)
"""

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODEL_31 = "gemma-4-31b-it"

PROMPT = """You are the story lead (StoryForge) for a deterministic tactical-grid SRPG campaign. The engine and
rules are FIXED and you MUST NOT change them — you only author narrative TEXT (a display-only layer).

The campaign is a fixed sequence of {n} battles (a "route"). Each battle below lists its foes (id, hp, and any
unit trait) and terrain — write a scene for EACH battle, in order, that fits those foes. Stay consistent across
scenes (one world, one hero's journey). Write all prose in Korean; end Korean sentences with a period, not a colon.

SETTING IDEA: {idea}

FIXED BATTLES (in order — one scene per battle, no more, no less):
{battles}

Output ONE JSON object EXACTLY, no prose, no markdown fences:
{{
  "title": "<campaign title>",
  "prologue": "<2-3 sentence opening>",
  "scenes": [ {{ "name": "<scene name like 'I. ...'>", "intro": "<1-2 sentence lead-in reflecting this battle's foes>", "clear": "<1 sentence on clearing it>" }} ],
  "epilogue": "<2-3 sentence ending after the final battle>"
}}
"scenes" MUST have EXACTLY {n} entries, one per battle in order. Every field non-empty. Return only the JSON."""


def battle_descriptors(campaign):
    """CAMPAIGN(초기 전투 + route)에서 전투별 적/지형 서술자 추출."""
    init = campaign["initialState"]
    battles = [{"enemies": init["enemies"], "terrain": init.get("terrain")}]
    for b in init.get("route", []):
        battles.append({"enemies": b["enemies"], "terrain": b.get("terrain")})
    lines = []
    for i, b in enumerate(battles, 1):
        foes = ", ".join(
            f"{e['id']}(hp {e['hp']}{', ' + e['unit_type'] if e.get('unit_type') else ''})"
            for e in b["enemies"])
        terr = ""
        if b["terrain"]:
            kinds = sorted(set(b["terrain"].values()))
            terr = f" | terrain: {', '.join(kinds)}"
        lines.append(f"  Battle {i}: {foes}{terr}")
    return len(battles), "\n".join(lines)


def validate(story, n):
    errs = []
    for k in ("title", "prologue", "epilogue"):
        if not str(story.get(k, "")).strip():
            errs.append(f"{k} 비었음")
    scenes = story.get("scenes") or []
    if len(scenes) != n:
        errs.append(f"scenes 수 {len(scenes)} != 전투 {n}")
    for i, s in enumerate(scenes, 1):
        for k in ("name", "intro", "clear"):
            if not str(s.get(k, "")).strip():
                errs.append(f"scene {i}.{k} 비었음")
    return errs


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--idea", required=True, help="세계관/설정 한 줄")
    ap.add_argument("--cap", type=int, default=2, help="생성 시도 수(첫 구조통과본 채택)")
    ap.add_argument("--replay", default=None, help="응답 텍스트 파일로 키 없이 재생(디버그)")
    args = ap.parse_args(argv)

    sys.path.insert(0, str(HERE))
    sys.path.insert(0, str(HERE.parent))
    sys.path.insert(0, str(HERE.parent.parent))
    import os
    os.environ["GENERATOR_MODEL"] = MODEL_31
    os.environ["CRITIC_MODEL"] = MODEL_31
    from config import force_utf8_stdout
    force_utf8_stdout()
    from planning import _extract_json
    from gen_tactics_play import CAMPAIGN

    n, battles = battle_descriptors(CAMPAIGN)
    prompt = PROMPT.format(n=n, idea=args.idea, battles=battles)

    def gen():
        if args.replay:
            return _extract_json(Path(args.replay).read_text(encoding="utf-8"))
        from config import get_api_keys
        from llm import KeyPool, LLMClient
        pool = KeyPool(get_api_keys(), models=[MODEL_31])
        with pool.checkout() as key:
            return _extract_json(LLMClient(api_key=key).generate("generator", prompt))

    for attempt in range(1, args.cap + 1):
        print(f"[STORY] 시도 {attempt}/{args.cap} — 골렘 서사 생성{' (replay)' if args.replay else ' (★키)'} (전투 {n})")
        try:
            story = gen()
        except Exception as e:  # noqa: BLE001
            print(f"  생성/파싱 실패: {e}")
            continue
        errs = validate(story, n)
        if errs:
            print(f"  구조 검증 실패: {errs[:5]} — 채택 안 함")
            continue
        out = {"title": story["title"], "prologue": story["prologue"],
               "epilogue": story["epilogue"],
               "scenes": [{"name": s["name"], "intro": s["intro"], "clear": s["clear"]} for s in story["scenes"]]}
        dst = HERE / "tactics_play" / "campaign_story.json"
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  채택 — 구조 검증 통과(장면 {n}/{n}·키 채움). → {dst}")
        print(f"  제목: {out['title']}")
        print("  렌더 반영: python golem/studio/gen_tactics_play.py")
        return 0

    print("[STORY] 모든 시도 실패 — 아이디어/프롬프트 조이거나 재시도.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
