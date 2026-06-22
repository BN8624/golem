# 플레이 레벨팩(levels.json)의 서사(B겹)를 골렘이 생성 — 레벨별 적·메커니즘 반영, 구조만 검증·엔진 불변
"""StoryForge 레벨팩판. gen_tactics_story가 캠페인 뷰어(index.html)를 덮는다면, 이건 사용자가 실제로
플레이하는 레벨팩(play.html)을 덮는다. 검증된 엔진/룰·레벨 데이터는 안 건드리고, 난이도 순서로 늘어선
레벨 시퀀스(각 레벨의 적·지형·가르치는 메커니즘)에 맞춰 골렘이 서사 텍스트를 저작한다.
검증은 구조만(장면 수=레벨 수·키 채움) — 문장 질은 사람 몫(출력전용 B겹).
산출=tactics_play/levelstory.json. gen_tactics_interactive가 있으면 play.html에 입힌다.

사용: python gen_tactics_levelstory.py --idea "세계관 한 줄" [--cap 2]   (★키)
"""
import sys as _sys
from pathlib import Path as _Path
_PKG = _Path(__file__).resolve().parents[1]
for _p in (str(_PKG), str(_PKG / "core"), str(_PKG / "tools"), str(_PKG / "tactics"),
           str(_PKG / "validators"), str(_PKG.parent)):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)
from paths import (PKG, REPO_ROOT, CORE, TOOLS, TACTICS, VALIDATORS,  # noqa: E402,F401
                   BASES, PACKETS, PLAY, FIXTURES, SCHEMAS, BUILD_RUNS, SCRATCH)

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODEL_31 = "gemma-4-31b-it"

PROMPT = """You are the story lead (StoryForge) for a deterministic tactical-grid SRPG. The engine and rules are
FIXED and you MUST NOT change them — you only author narrative TEXT (a display-only layer).

The game is a sequence of {n} playable LEVELS in ascending difficulty (a campaign the player works through). Each
level below lists what it TEACHES (a mechanic the {actor} wields), its foes (id, hp, any trait), and terrain — write
a scene for EACH level, in order, that fits those foes and that mechanic.

CRAFT (continuity over flavor): give the {actor} a NAME/identity and use it; carry one through-line (a goal/stake set
in the prologue) and let tension ESCALATE level by level toward the finale; let later scenes call back to earlier so
it reads as one journey, not {n} separate blurbs. Reflect each level's taught mechanic and actual foe trait in its
scene (an armored foe feels impenetrable, a glass one brittle, a newly-learned technique feels earned, etc.).
Evocative but concise (intro 1-2 sentences). Write all prose in Korean; end Korean sentences with a period, not a
colon.

SETTING IDEA: {idea}

LEVELS (in order — one scene per level, no more, no less):
{levels}

Output ONE JSON object EXACTLY, no prose, no markdown fences:
{{
  "title": "<campaign title>",
  "prologue": "<2-3 sentence opening>",
  "scenes": [ {{ "name": "<scene name like 'I. ...'>", "intro": "<1-2 sentence lead-in reflecting this level's mechanic and foes>", "clear": "<1 sentence on clearing it>" }} ],
  "epilogue": "<2-3 sentence ending after the final level>"
}}
"scenes" MUST have EXACTLY {n} entries, one per level in order. Every field non-empty. Return only the JSON."""

# 패밀리별 actor·opt-in 카드 필드→메커니즘 이름·라이브 레벨팩 파일(서사 힌트용)
FAMILY = {
    "tactics": {"actor": "hero", "levels_file": "levels.json",
                "cards": {"mana": "마나방패/파열", "anomaly_dmg": "파열(ANOMALY)", "corrosion": "부식", "execute": "처형"}},
    "squad": {"actor": "squad of allies", "levels_file": "squad_levels.json",
              "cards": {"range": "사거리", "knockback": "충격파", "flank_bonus": "협공", "reflect_dmg": "가시갑옷", "armor": "강철피부"}},
}


def level_descriptors(levels, family="tactics"):
    """레벨팩(난이도순) → 레벨별 적·지형·가르침·아군 카드 서술자(패밀리별 상태형)."""
    cfg = FAMILY[family]
    lines = []
    for i, lv in enumerate(levels, 1):
        init = lv["initialState"]
        foes = ", ".join(
            f"{e['id']}(hp {e['hp']}{', ' + e['unit_type'] if e.get('unit_type') else ''})"
            for e in init["enemies"])
        terr = ""
        if init.get("terrain"):
            terr = f" | terrain: {', '.join(sorted(set(init['terrain'].values())))}"
        if family == "squad":   # 카드는 아군 유닛들에 분산된 opt-in 필드
            present = {f for u in init.get("allies", []) for f in cfg["cards"] if f in u}
            cards = [cfg["cards"][f] for f in cfg["cards"] if f in present]
            actor_note = f" | allies: {len(init.get('allies', []))}"
        else:
            cards = [lbl for f, lbl in cfg["cards"].items() if f in init.get("hero", {})]
            actor_note = ""
        cardtxt = f" | wields: {', '.join(cards)}" if cards else ""
        teaches = lv.get("teaches", "") or "기본"
        lines.append(f"  Level {i}: [{teaches}] {foes}{terr}{cardtxt}{actor_note}")
    return len(levels), "\n".join(lines)


def validate(story, n):
    errs = []
    for k in ("title", "prologue", "epilogue"):
        if not str(story.get(k, "")).strip():
            errs.append(f"{k} 비었음")
    scenes = story.get("scenes") or []
    if len(scenes) != n:
        errs.append(f"scenes 수 {len(scenes)} != 레벨 {n}")
    for i, s in enumerate(scenes, 1):
        for k in ("name", "intro", "clear"):
            if not str(s.get(k, "")).strip():
                errs.append(f"scene {i}.{k} 비었음")
    return errs


def _load_levels(family="tactics"):
    """라이브 레벨팩(패밀리별 파일) 로드. tactics는 없으면 빌트인, squad는 없으면 빈 리스트."""
    pack = PLAY / FAMILY[family]["levels_file"]
    if pack.exists():
        lv = json.loads(pack.read_text(encoding="utf-8"))
        if lv:
            return lv
    if family == "tactics":
        from gen_tactics_interactive import _BUILTIN_LEVELS
        return _BUILTIN_LEVELS
    return []


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--idea", required=True, help="세계관/설정 한 줄")
    ap.add_argument("--family", default="tactics", help="tactics(영웅)|squad(부대)")
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

    levels = _load_levels(args.family)
    if not levels:
        print(f"  레벨팩 없음({FAMILY[args.family]['levels_file']}) — 먼저 propose_levels --family {args.family}로 생성하라.")
        return 1
    n, level_lines = level_descriptors(levels, args.family)
    prompt = PROMPT.format(n=n, idea=args.idea, levels=level_lines, actor=FAMILY[args.family]["actor"])

    def gen():
        if args.replay:
            return _extract_json(Path(args.replay).read_text(encoding="utf-8"))
        from config import get_api_keys
        from llm import KeyPool, LLMClient
        pool = KeyPool(get_api_keys(), models=[MODEL_31])
        with pool.checkout() as key:
            return _extract_json(LLMClient(api_key=key).generate("generator", prompt))

    for attempt in range(1, args.cap + 1):
        print(f"[LVLSTORY] 시도 {attempt}/{args.cap} — 골렘 서사 생성{' (replay)' if args.replay else ' (★키)'} (레벨 {n})")
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
        dst = PLAY / ("levelstory.json" if args.family == "tactics" else f"{args.family}_levelstory.json")
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  채택 — 구조 검증 통과(장면 {n}/{n}·키 채움). → {dst}")
        print(f"  제목: {out['title']}")
        print("  렌더 반영: python golem/tactics/gen_tactics_interactive.py --level l9")
        return 0

    print("[LVLSTORY] 모든 시도 실패 — 아이디어/프롬프트 조이거나 재시도.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
