# base-델타 골렘 planning 모드 — 현 base 계약을 FROZEN으로 주고 가산 카드 델타를 직접 뱉게(그래프트 무인의 마지막 조각)
"""골렘이 scratch 풀게임 대신, 동결된 base(REQ 전부 + 참조 game_logic)에 얹는 '가산 델타'를 base 관례로 출력한다.
델타 = {new_req(자기완결), new_state, new_worlds(입력+골렘 expected), game_logic(가산 슈퍼셋 전문)}.
graft.py가 조립+키0 검증(회귀 바이트동일·gate·golden·결정성) + 골렘 expected vs 참조 실행 교차검산.
교차검산이 핵심: 골렘의 '코드(game_logic)'와 골렘의 '이해(expected)'가 어긋나면 잡는다(그럴듯하게 틀림 차단).

사용: python card_delta.py --level l8 --prev l7 --idea "흡혈: 근접으로 입힌 피해 일부를 영웅 hp로 회복" [--cap 1]
★키 사용(사용자 go 뒤에만).
"""

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

INVARIANTS = (
    "HERO-ONLY INVARIANTS (MUST NOT CHANGE): there is NO enemy turn, NO enemy AI, NO enemy movement, "
    "NO enemy mana. The ONLY actor is the hero; the only actions are hero move/attack/ranged_attack from a "
    "fixed list; turn increments by 1 per hero action. The CLI output is FIXED: exactly status/turn/hero_hp/"
    "hero_pos/enemies, each enemy EXACTLY {id,hp,pos}. Do NOT change engine.js / main.js / scenarios.js — only "
    "src/game_logic.js. The new card MUST be purely ADDITIVE: when no new field/data is present, every prior "
    "world is byte-for-byte unchanged."
)

PROMPT = """You extend a deterministic, hero-only tactical-grid combat game by ONE additive card.

=== FROZEN CONTRACT (rules REQ-001..{lastreq}, carried verbatim — DO NOT restate or edit them) ===
{rules}

=== OUTPUT CONTRACT (FIXED) ===
{output}

=== CURRENT REFERENCE src/game_logic.js (this is the exact current behavior; your new game_logic MUST be a superset) ===
{game_logic}

=== {invariants} ===

=== NEW CARD IDEA ===
{idea}

Design this card yourself, deterministically, in the SAME conventions as the contract above (status READY/VICTORY/
DEFEAT/FINISHED, string enemy ids, integer hp that may be negative, opt-in optional fields on hero/enemy that
default to the no-op value so absence = unchanged). Output ONLY a single JSON object (no prose, no markdown fence)
with EXACTLY these keys:
{{
  "new_req": "REQ-{nextreq}: <one self-contained rule describing the card, base conventions, additive>",
  "new_state": {{ "<optional new state_shape field(s)>": "<description>" }},
  "new_worlds": [
    {{ "id": "SCN-{firstworld}", "initialState": {{...}}, "actions": [...], "expected": {{"status":..,"turn":..,"hero_hp":..,"hero_pos":[..],"enemies":[{{"id":..,"hp":..,"pos":[..]}}]}} }}
  ],
  "game_logic": "<the COMPLETE updated src/game_logic.js as one string — current reference PLUS your additive change>"
}}
Provide 3 new worlds that exercise the card (each with the EXACT 5-field expected you compute by hand). Each new world MUST actually TRIGGER the card — its 5-field result must differ from what the SAME world would
produce without the card (e.g. for an execute/threshold card, the target must be one that SURVIVES the plain
attack but dies to the card; do not pick a target that already dies from the normal hit). Keep enemy ids like 'E1'.
The PRINTED status is one of VICTORY | DEFEAT | FINISHED — NEVER 'READY' (READY is internal pre-run only). A world
whose actions run out without reaching VICTORY/DEFEAT prints status 'FINISHED'. Compute each expected.turn as the
number of actions actually executed. Double-check your expected against your own game_logic before answering.
Do not include 'expected' anywhere except inside new_worlds. Return only the JSON object."""


def _extract_json(text):
    """응답에서 JSON 오브젝트 추출(펜스/잡음 제거, 첫 균형 중괄호 블록)."""
    t = text.strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t, flags=re.MULTILINE).strip()
    start = t.find("{")
    if start < 0:
        raise ValueError("JSON 없음")
    depth, instr, esc = 0, False, False
    for i in range(start, len(t)):
        c = t[i]
        if instr:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                instr = False
        else:
            if c == '"':
                instr = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(t[start:i + 1])
    raise ValueError("균형 중괄호 못 찾음")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--level", required=True, help="새 레벨 이름(예: l8)")
    ap.add_argument("--prev", required=True, help="이전 레벨(예: l7)")
    ap.add_argument("--idea", required=True, help="카드 한 줄 아이디어")
    ap.add_argument("--cap", type=int, default=1, help="델타 생성 시도 수(첫 검증 통과본 채택)")
    ap.add_argument("--replay", default=None, help="응답 텍스트 파일로 키 없이 재생(디버그)")
    args = ap.parse_args(argv)

    sys.path.insert(0, str(HERE))
    sys.path.insert(0, str(HERE.parent))
    sys.path.insert(0, str(HERE.parent.parent))  # config·llm은 바깥 루트(golem/ 상위)에 있음
    import os
    os.environ["GENERATOR_MODEL"] = "gemma-4-31b-it"
    os.environ["CRITIC_MODEL"] = "gemma-4-31b-it"
    from config import force_utf8_stdout, get_api_keys
    force_utf8_stdout()
    import graft as G
    from importlib import import_module

    prev_pkt = json.loads((HERE / f"planning_packet_tactics_{args.prev}" / "contract.json").read_text(encoding="utf-8"))
    dc = prev_pkt["data_contract"]
    prev_ref = import_module(f"gen_tactics_{args.prev}_golden").REF_GAME_LOGIC
    prev_n = len(dc["scenario_data"])
    nextreq = f"{len(dc['rules']) + 1:03d}"
    prompt = PROMPT.format(
        lastreq=f"{len(dc['rules']):03d}", rules="\n".join(dc["rules"]),
        output=json.dumps(dc["output_contract"], ensure_ascii=False),
        game_logic=prev_ref, invariants=INVARIANTS, idea=args.idea,
        nextreq=nextreq, firstworld=f"{prev_n + 1:03d}")

    def gen():
        if args.replay:
            return Path(args.replay).read_text(encoding="utf-8")
        from llm import KeyPool, LLMClient
        pool = KeyPool(get_api_keys(), models=["gemma-4-31b-it"])
        with pool.checkout() as key:
            return LLMClient(api_key=key).generate("critic", prompt)

    for attempt in range(1, args.cap + 1):
        print(f"[CARD-DELTA {args.level}] 시도 {attempt}/{args.cap} — 골렘 base-델타 생성{' (replay)' if args.replay else ' (★키)'}")
        raw = gen()
        (HERE / f"_carddelta_{args.level}_raw.txt").write_text(raw, encoding="utf-8")
        try:
            d = _extract_json(raw)
        except Exception as e:  # noqa: BLE001
            print(f"  파싱 실패: {e} (raw=_carddelta_{args.level}_raw.txt)")
            continue

        new_req = d["new_req"]
        new_state = d.get("new_state") or {}
        claimed = {w["id"]: w.get("expected") for w in d["new_worlds"]}
        new_worlds = [{k: w[k] for k in ("id", "initialState", "actions")} for w in d["new_worlds"]]
        game_logic = d["game_logic"]

        contract, specqa, ok = G.graft(args.level, args.prev, new_req, new_state, new_worlds,
                                       game_logic, prev_ref, write=False)
        # 교차검산: 골렘 expected(이해) vs 참조 실행(코드)
        ref_exp = {s["id"]: s["expected"] for s in specqa}
        import build_graded as bg
        cross = [wid for wid, ce in claimed.items()
                 if ce is None or any(bg._canon(ce.get(k)) != bg._canon(ref_exp[wid].get(k))
                                      for k in G.OUTPUT_KEYS if k in ref_exp[wid])]
        if cross:
            print(f"  교차검산 불일치(골렘 코드↔이해 어긋남): {cross} — 채택 안 함")
            continue
        if not ok:
            print("  graft 키0 검증 실패 — 채택 안 함")
            continue

        # 통과 — 패킷·specqa·참조 gen 작성
        G.graft(args.level, args.prev, new_req, new_state, new_worlds, game_logic, prev_ref, write=True)
        (HERE / f"gen_tactics_{args.level}_golden.py").write_text(
            f'# {args.level} 참조 game_logic(골렘 base-델타 산출, card_delta.py) — graft 체인용\nREF_GAME_LOGIC = '
            + 'r"""' + "\n" + game_logic + '\n"""\n', encoding="utf-8")
        (HERE / f"planning_packet_tactics_{args.level}" / "concept.md").write_text(
            f"전술 커널 {args.prev} 위 가산 카드({args.level}) — 골렘 base-델타 자율 설계: {args.idea}\n", encoding="utf-8")
        print(f"  채택 — 패킷/specqa/참조 작성. 교차검산·키0 검증 통과. 다음=★키 빌드.")
        print(f"  build: python golem/studio/build_graded.py --base golem/studio/tactics_kernel_base "
              f"--packet golem/studio/planning_packet_tactics_{args.level} "
              f"--specqa golem/studio/specqa_packet_tactics_{args.level} --inject-modules src/game_logic.js --reconcile")
        return 0

    print(f"[CARD-DELTA {args.level}] 모든 시도 실패 — 프롬프트/아이디어 조이거나 재시도.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
