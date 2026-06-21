# 레벨 시스템 자동화 — 골렘이 (카드+난이도 노브)로 레벨 생성, play_signals로 검증·재시도, 통과본만 난이도순 팩으로
"""북극성 운영원칙(다 자동화·사용자는 노브 몇 개)대로 레벨 디자인을 자동화한다.
레벨=데이터(initialState)라 엔진(l9, 검증됨)이 그대로 굴리므로 룰 위험 0 — 잘못된 레벨은 play_signals가 거른다.
루프: 골렘이 레벨 제안(메커니즘·목표턴 의도) → play_signals 게이트(풀이가능·min_turns 범위·비원샷) → 미스면
측정 피드백으로 재시도 → 통과본만 채택, 최소턴 오름차순으로 정렬(난이도 커브).
사용자 노브: --n(개수) --min-turns/--max-turns(난이도) --ref(장르 시드). 손편집 없음.
산출=build_runs/proposals/tactics_levels.json. (★키=생성 / 키0=검증)

사용: python propose_levels.py [--prev l9] [--n 5] [--min-turns 3] [--max-turns 8]
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
import re
import sys
from importlib import import_module
from pathlib import Path

# 채택 레벨 이름의 batch-로컬 번호(1~6 중복)를 최종 순서 1..N으로 재넘버링.
def _renumber(levels):
    for i, lv in enumerate(levels, 1):
        base = re.sub(r"^\s*\d+\s*[.．]\s*", "", lv.get("name", "")).strip()
        lv["name"] = f"{i}. {base}"
    return levels

HERE = Path(__file__).resolve().parent
MODEL_31 = "gemma-4-31b-it"

PROMPT = """You are a LEVEL DESIGNER for a deterministic, hero-only tactical-grid SRPG. The engine and rules are
FIXED (below). Design playable single-battle levels as DATA only (initialState) — never change rules.

CARDS/RULES IN THE ENGINE (mechanics you can build encounters around):
{cards}

INVARIANTS: {invariants}

STATE SCHEMA for each level's initialState (small grid, min coord 0; keep coords 0..4, enemies 1~3 for tractable
checking):
  hero: {{hp, atk, pos:[x,y], mana?, anomaly_dmg?, corrosion?:{{dmg,duration}}, execute?}}  (optional fields = that card on)
  enemies: [{{id, hp, atk, pos:[x,y], unit_type?: 'Hardened'|'Glass'|'Resonant'}}]
  terrain?: {{"x,y": "Wall"|"Conductive"}}

GENRE REFERENCES — adapt PATTERNS (do NOT clone): {refs}

Design {batch} levels forming an ESCALATING curve: early ones teach ONE mechanic, later ones COMBINE mechanics
(introduce-then-combine). Each level must be SOLVABLE and take roughly {tmin}..{tmax} hero actions to win (not a
1-action auto-win, not unwinnable). Make the taught mechanic MATTER (the level should be much harder/unsolvable
without it). Give the hero enough stats to win with the right play. Vary mechanics AND difficulty across the batch.
{feedback}
Output ONE JSON object EXACTLY, no prose, no markdown fences:
{{ "levels": [ {{ "name": "<번호. 이름>", "desc": "<한 줄 한국어 안내>", "teaches": "<이 레벨이 가르치는 메커니즘>",
  "initialState": {{ "hero": {{...}}, "enemies": [...], "terrain": {{...}} }} }} ] }}
"levels" must have EXACTLY {batch} entries. Return only the JSON."""


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--prev", default="l9", help="엔진/카드 레벨(이 계약·참조 사용)")
    ap.add_argument("--n", type=int, default=5, help="목표 레벨 총수(볼륨 노브 — 1시간 분량이면 ~18)")
    ap.add_argument("--batch", type=int, default=6, help="한 ★키 생성당 요청 레벨 수(모델 친화적 작게)")
    ap.add_argument("--min-turns", type=int, default=3, help="목표 최소턴 하한(노브)")
    ap.add_argument("--max-turns", type=int, default=9, help="목표 최소턴 상한(노브)")
    ap.add_argument("--ref", default=None, help="장르 레퍼런스 시드(기본=propose_cards 표본)")
    ap.add_argument("--cap", type=int, default=4, help="생성 재시도 수(목표 못 채우면 늘리기)")
    ap.add_argument("--replay", default=None, help="응답 파일 재생(키0 디버그)")
    args = ap.parse_args(argv)

    sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE.parent.parent))
    import os
    os.environ["GENERATOR_MODEL"] = MODEL_31; os.environ["CRITIC_MODEL"] = MODEL_31
    from config import force_utf8_stdout
    force_utf8_stdout()
    from planning import _extract_json
    from play_signals import compute_signals
    pc = import_module("propose_cards")
    gl = import_module(f"gen_tactics_{args.prev}_golden").REF_GAME_LOGIC
    cards = pc.card_summary(args.prev)
    refs = args.ref or pc.DEFAULT_REFS

    def gen(p):
        if args.replay:
            return Path(args.replay).read_text(encoding="utf-8")
        from config import get_api_keys
        from llm import KeyPool, LLMClient
        pool = KeyPool(get_api_keys(), models=[MODEL_31])
        with pool.checkout() as key:
            return LLMClient(api_key=key).generate("generator", p)

    def gate(lv, s):
        if not s["solvable"]:
            return False, "풀이불가"
        mt = s["min_turns"]
        if mt <= 1:
            return False, f"원샷(min_turns={mt})"
        if mt < args.min_turns or mt > args.max_turns:
            return False, f"min_turns {mt} 범위밖[{args.min_turns},{args.max_turns}]"
        return True, f"OK min_turns={mt}"

    # 변별 누적: attempt마다 batch개 생성 → 게이트 통과분을 (메커니즘×최소턴) 중복제거 + 난이도 구간 cap로 누적.
    # 단순 누적이 쉬운 레벨만 남기던 과거 문제는 구간별 cap + 커버리지 피드백(보완 생성 유도)으로 차단한다.
    span = max(1, args.max_turns - args.min_turns + 1)
    per_turn_cap = max(2, -(-args.n // span))  # ceil(n/span): 한 난이도에 쏠림 방지

    def _sig(lv):
        return ((lv.get("teaches", "") or "").strip().lower(), lv["_signals"]["min_turns"])

    accepted, feedback = [], ""
    for attempt in range(1, args.cap + 1):
        if len(accepted) >= args.n:
            break
        print(f"[LEVELS] 시도 {attempt}/{args.cap} — 골렘 {args.batch}개 생성"
              f"{' (replay)' if args.replay else ' (★키)'} | 누적 {len(accepted)}/{args.n}"
              + (" [피드백]" if feedback else ""))
        prompt = PROMPT.format(cards=cards, invariants=pc.INVARIANTS, refs=refs, batch=args.batch,
                               tmin=args.min_turns, tmax=args.max_turns,
                               feedback=("\n" + feedback + "\n") if feedback else "")
        try:
            d = _extract_json(gen(prompt))
            levels = d["levels"]
        except Exception as e:  # noqa: BLE001
            feedback = f"직전 시도 JSON 파싱 실패({e}). JSON 오브젝트만 출력."
            print(f"  파싱 실패: {e}"); continue
        sigs = compute_signals(levels, gl)
        misses = []
        for lv, s in zip(levels, sigs):
            ok, why = gate(lv, s)
            if not ok:
                misses.append(f"{lv.get('name','?')[:18]}={why}")
                print(f"  ✗ {lv.get('name','?')[:30]} — {why}"); continue
            lv["_signals"] = {"min_turns": s["min_turns"], "greedy_melee": s["greedy_melee"],
                              "greedy_ranged": s["greedy_ranged"], "card_fields": s["card_fields"],
                              "min_turns_no_card": s["min_turns_no_card"]}
            if _sig(lv) in {_sig(a) for a in accepted}:
                print(f"  ~ {lv.get('name','?')[:30]} — 중복(메커니즘×난이도 {_sig(lv)})"); continue
            if sum(1 for a in accepted if a["_signals"]["min_turns"] == s["min_turns"]) >= per_turn_cap:
                print(f"  ~ {lv.get('name','?')[:30]} — {s['min_turns']}수 정원초과(cap {per_turn_cap})"); continue
            accepted.append(lv)
            print(f"  ✓ {lv.get('name','?')[:30]} [{lv.get('teaches','')[:16]}] min_turns={s['min_turns']} "
                  f"greedy(멜레{s['greedy_melee'][:3]}/사거리{s['greedy_ranged'][:3]}) | 누적 {len(accepted)}/{args.n}")
            if len(accepted) >= args.n:
                break
        # 커버리지 피드백: 이미 채운 (메커니즘,최소턴)과 아직 빈 난이도 구간을 알려 보완 생성을 유도(중복 줄임).
        covered = sorted({_sig(a) for a in accepted})
        thin = [mt for mt in range(args.min_turns, args.max_turns + 1)
                if sum(1 for a in accepted if a["_signals"]["min_turns"] == mt) < per_turn_cap]
        feedback = (f"이미 채운 (메커니즘,최소턴)={covered}. 다른 메커니즘 조합이나 최소턴 {thin}수 레벨로 보완하라(중복 금지)."
                    + (" 직전 탈락: " + "; ".join(misses[:3]) if misses else ""))

    # 난이도 커브: 최소턴 오름차순 정렬. n 초과시 구간 고르게 솎아 커브 유지(쉬운 쪽 쏠림 방지).
    accepted.sort(key=lambda l: l["_signals"]["min_turns"])
    if len(accepted) > args.n:
        idx = sorted({round(i * (len(accepted) - 1) / (args.n - 1)) for i in range(args.n)}) if args.n > 1 else [0]
        accepted = [accepted[i] for i in idx]
    _renumber(accepted)  # 난이도순 1..N 순번(batch-로컬 중복번호 제거)
    out = BUILD_RUNS / "proposals" / "tactics_levels.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(accepted, ensure_ascii=False, indent=2), encoding="utf-8")
    # 충분히 채웠으면 라이브 레벨팩으로 승격(인터랙티브가 이걸 우선 로드). 손편집 없이 노브 재실행으로 교체.
    if len(accepted) >= args.n:
        live = PLAY / "levels.json"
        live.parent.mkdir(parents=True, exist_ok=True)
        live.write_text(json.dumps(accepted, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  라이브 승격 → {live} (gen_tactics_interactive가 이걸 로드)")
    print(f"\n채택 {len(accepted)}/{args.n} (난이도 커브=최소턴 오름차순) → {out}")
    for lv in accepted:
        print(f"  · {lv['name']} (min_turns={lv['_signals']['min_turns']}, teaches={lv.get('teaches','')})")
    if len(accepted) < args.n:
        print(f"  ⚠ {args.n - len(accepted)}개 부족 — --cap↑ 또는 --min/max-turns 범위 넓혀 재시도.")
        return 1
    print("  다음: gen_tactics_interactive가 이 팩을 로드하게 배선하면 손튜닝 LEVELS 대체.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
