# 카드 아이디어 제안(선별 퍼널 입구) — 골렘이 현 누적 게임을 보고 다음 카드 후보 N개를 뽑는다(다작→graft 사전필터→사람 선별)
"""북극성(§1.5) 다작·선별의 '생성' 쪽. 골렘이 현 base 계약(REQ·카드)을 읽고 가산 가능한 다음 카드 아이디어를
여러 개 제안한다(한 줄 메커니즘+왜+발동 관측). 각 아이디어를 driver_autocard에 넣으면 card_delta→graft가
무인 사전필터(회귀·gate·골든·결정성·교차검산)하고, 통과한 완결 후보를 사람이 '재미있나'로 선별한다.
제안 자체는 키 안 씀(빌드 전 단계)이지만 골렘 1콜=★키. 산출=build_runs/proposals/tactics_ideas.json.

사용: python propose_cards.py [--prev l9] [--n 5]   (★키)
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

INVARIANTS = (
    "HERO-ONLY·결정적 불변: 적은 수동(턴/AI/이동 없음), 영웅만 행동, 액션은 move/attack/ranged_attack, "
    "출력은 status/turn/hero_hp/hero_pos/enemies(각 {id,hp,pos}) 고정, RNG 없음. 새 카드는 순수 가산"
    "(새 opt-in 필드 없으면 기존 바이트동일)이고 game_logic.js 한 모듈 안에서 결정적으로 구현 가능해야 한다.")

# 장르 레퍼런스 — 검증된 디자인의 '패턴'을 우리 제약에 맞게 차용(특정 게임 클론 금지). 시드 품질 레버.
DEFAULT_REFS = (
    "Into the Breach (위치·존 제어, 밀치기), Fire Emblem/영걸전 (사거리·지형·유닛 상성), "
    "Final Fantasy Tactics (높이·직업 특성), Slay the Spire (카드 시너지·콤보), "
    "로그라이트 유물 (빌드를 규정하는 패시브 변형)")

PROMPT = """You are a GAME DESIGNER proposing the NEXT cards for a deterministic, hero-only tactical-grid SRPG.
The engine is FIXED; cards are additive opt-in mechanics. Below are the cards already in the game (do NOT repeat
them) and the hard invariants any new card must respect.

EXISTING CARDS (rules already in the contract):
{cards}

INVARIANTS: {invariants}

GENRE REFERENCES — adapt the PATTERNS from these proven tactics/roguelite designs to our hero-only deterministic
grid (borrow the IDEA, do NOT clone any specific game): {refs}

Propose {n} DISTINCT, fresh next-card ideas that are deterministic, purely additive (gated by a new optional
field so absence = unchanged), implementable within game_logic.js, and observable in the fixed 5-field output.
Ground each idea in a recognizable genre pattern (positioning/zone-control, synergy/combo with EXISTING cards,
risk-reward, resource/tempo) adapted to our constraints. Favor variety (offense / defense / positioning / tempo /
risk) and synergy with the existing cards above. Avoid anything needing enemy turns, RNG, or output-format
changes. Write the prose in Korean.

Output ONE JSON object EXACTLY, no prose, no markdown fences:
{{ "ideas": [ {{ "name": "<카드 이름>", "mechanic": "<한 줄: 무엇을 어떻게(가산·opt-in 필드 명시)>", "why": "<왜 변별력 있나, 한 줄>", "observable": "<5필드 출력에서 어떻게 관측되나>" }} ] }}
"ideas" must have EXACTLY {n} entries. Return only the JSON."""


def card_summary(prev):
    """직전 패킷 계약에서 REQ 목록(앞 줄)을 카드 요약으로."""
    c = json.loads((PACKETS / f"planning_packet_tactics_{prev}" / "contract.json").read_text(encoding="utf-8"))
    lines = []
    for r in c["data_contract"]["rules"]:
        head = r.split(".")[0].split(":")[0].strip()
        first = r.split(":", 1)[1].strip() if ":" in r else r
        lines.append(f"  {head}: {first[:90]}")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--prev", default="l9", help="현 누적 레벨(이 계약을 읽어 제안)")
    ap.add_argument("--n", type=int, default=5, help="제안 개수")
    ap.add_argument("--ref", default=DEFAULT_REFS, help="장르 레퍼런스(패턴 차용 시드). 기본=SRPG/로그라이트 표본")
    ap.add_argument("--replay", default=None, help="응답 파일로 키 없이 재생(디버그)")
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

    prompt = PROMPT.format(cards=card_summary(args.prev), invariants=INVARIANTS, n=args.n, refs=args.ref)

    if args.replay:
        d = _extract_json(Path(args.replay).read_text(encoding="utf-8"))
    else:
        from config import get_api_keys
        from llm import KeyPool, LLMClient
        pool = KeyPool(get_api_keys(), models=[MODEL_31])
        with pool.checkout() as key:
            d = _extract_json(LLMClient(api_key=key).generate("generator", prompt))

    ideas = d.get("ideas") or []
    if not ideas:
        print("제안 없음(파싱 실패?)")
        return 1
    out = BUILD_RUNS / "proposals" / "tactics_ideas.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(ideas, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"제안 {len(ideas)}개 → {out}")
    for i, x in enumerate(ideas, 1):
        print(f"  {i}. {x.get('name','?')} — {x.get('mechanic','')[:80]}")
    print("다음: driver_autocard.py가 이 아이디어로 card_delta→graft 사전필터→완결 후보 생성(사람이 선별).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
