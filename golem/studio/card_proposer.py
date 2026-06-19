# 카드 자동 제안(B+검토) — 31B가 다음 카드(메커니즘+규칙+REF 골든+시나리오)를 뽑고, 사람이 검토 후 빌드한다
"""B 경로지만 무인 아님: 31B가 골든 REF(결정적 Node)까지 제안하되, 빌드(키) 전에 사람이 그 REF를 검토해
정답 앵커로 승격한다. 이 스크립트는 제안 1건을 생성하고 자동 속성검사를 돌려 검토용 산출물을 남긴다(★키 1콜).

자동 속성검사(검토 보조):
  - REF가 static_gate + node 스모크를 통과하나.
  - 신규 타일을 쓰는 시나리오는 prev(현재 누적 게임)와 출력이 달라야(메커니즘이 실제로 동작).
  - 신규 타일을 안 쓰는 시나리오는 prev==cur(회귀 무결).
통과해도 '그럴듯하게 틀린' REF는 못 거르니 — 사람이 move_logic_proposed.js를 읽고 규칙과 대조해야 한다.
"""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
GAME = "sokoban"
PREV_BASE = HERE / "build_runs" / "showcase_sokoban" / "l3_built"   # 현재 누적 게임(카드3까지)
PREV_CONTRACT = HERE / "planning_packet_sokoban_l3" / "contract.json"
OUT = HERE / "build_runs" / "proposals" / "sokoban_card4"

PROMPT = """You are a GAME DESIGNER extending a deterministic Sokoban puzzle engine (Node.js, CommonJS, no
Math.random). The engine never changes; new tile mechanics are added ONLY by editing src/move_logic.js.
State has: player [r,c], boxes [[r,c]], walls{{}}, targets{{}}, tiles{{}} (any non-standard grid char is stored
here, e.g. 'K' key, 'D' door, 'T' teleport, 'O' hole — already implemented). hasKey is a dynamic flag.
A move returns a log string like '<dir>:move' / ':push' / ':block' / ':move+key' / ':fill' / ':move+tp'.

CURRENT move_logic.js (cumulative through card 3 — keep ALL of this behavior intact):
=== CURRENT ===
{current}
=== END CURRENT ===

Existing rules (RULE-01..RULE-08):
{rules}

Propose ONE NEW tile mechanic as card 4 (a NEW single-char tile not already used: K/D/T/O taken). It must be
deterministic, keep resolveMove(state, dir) signature, and leave every existing behavior byte-for-byte intact
(a play with no new tile must be identical). Output EXACTLY this format, nothing else:

MECHANIC: <short name>
TILE: <single char>
RULE: RULE-09 (THIS CARD): <one precise sentence describing the behavior and the log suffix/marker>
CONCEPT: <one Korean sentence>
=== MOVE_LOGIC ===
<the FULL new src/move_logic.js source, cumulative (all old mechanics + the new one)>
=== SCENARIOS ===
<a JSON array of 4 scenarios. Each: {{"id":"SCN-0NN","covers_reqs":["RULE-09"],"input":{{"level":["#...","..."],"moves":["R","U",...]}}}}.
Use INLINE level grids (array of row strings) that include your new tile. Include at least one scenario that
uses the new tile (mechanic fires) and at least one plain scenario with NO new tile (regression). Keep grids small.>
"""


def call_31b(prompt):
    os.environ["GENERATOR_MODEL"] = "gemma-4-31b-it"
    os.environ["CRITIC_MODEL"] = "gemma-4-31b-it"
    sys.path.insert(0, str(ROOT))
    from config import get_api_keys
    from llm import KeyPool, LLMClient
    pool = KeyPool(get_api_keys(), models=["gemma-4-31b-it"])
    with pool.checkout() as key:
        return LLMClient(api_key=key).generate("critic", prompt)


def parse_response(resp):
    def field(name):
        m = re.search(rf"^{name}:\s*(.*)$", resp, re.MULTILINE)
        return m.group(1).strip() if m else ""
    ml = resp.split("=== MOVE_LOGIC ===", 1)[1].split("=== SCENARIOS ===", 1)[0].strip()
    ml = re.sub(r"^```[a-z]*\n|```$", "", ml.strip()).strip()
    scen_raw = resp.split("=== SCENARIOS ===", 1)[1].strip()
    scen_raw = re.sub(r"^```[a-z]*\n|```$", "", scen_raw.strip()).strip()
    scenarios = json.loads(scen_raw)
    return {"mechanic": field("MECHANIC"), "tile": field("TILE"),
            "rule": field("RULE"), "concept": field("CONCEPT"),
            "move_logic": ml, "scenarios": scenarios}


def run_node(workdir, idx):
    r = subprocess.run(["node", "main.js", "--scenario", str(idx)], cwd=str(workdir),
                       capture_output=True, text=True, encoding="utf-8", timeout=30, stdin=subprocess.DEVNULL)
    return r.stdout if r.returncode == 0 else None


def main():
    sys.path.insert(0, str(ROOT))
    try:
        from config import force_utf8_stdout
        force_utf8_stdout()
    except Exception:  # noqa: BLE001
        pass
    import importlib
    sys.path.insert(0, str(HERE))          # studio 모듈
    sys.path.insert(0, str(HERE.parent))   # golem 패키지(static_gate 등)
    sg = importlib.import_module("static_gate")

    current = (PREV_BASE / "src" / "move_logic.js").read_text(encoding="utf-8")
    rules = "\n".join(f"- {r}" for r in
                      json.loads(PREV_CONTRACT.read_text(encoding="utf-8"))["data_contract"]["rules"])
    prompt = PROMPT.format(current=current, rules=rules)

    print("[제안기] 31B 호출(★키 1콜)…")
    resp = call_31b(prompt)
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    (OUT / "_raw_response.txt").write_text(resp, encoding="utf-8")
    try:
        p = parse_response(resp)
    except Exception as e:  # noqa: BLE001
        print(f"[제안기] 파싱 실패: {e}. raw={OUT / '_raw_response.txt'}")
        return 1

    (OUT / "move_logic_proposed.js").write_text(p["move_logic"], encoding="utf-8")

    # cur(제안 REF) / prev(현재 누적) 두 워크스페이스에 시나리오 적용
    cur = OUT / "ref_cur"
    prev = OUT / "ref_prev"
    for d, ml in ((cur, p["move_logic"]), (prev, current)):
        shutil.copytree(PREV_BASE, d)
        (d / "src" / "move_logic.js").write_text(ml, encoding="utf-8")
        (d / "scenarios.json").write_text(
            json.dumps([{"input": s["input"]} for s in p["scenarios"]], ensure_ascii=False), encoding="utf-8")

    gate = sg.check(str(cur))
    rows = []
    differ = 0
    regression_ok = True
    tile = p["tile"]
    for i, s in enumerate(p["scenarios"], 1):
        cur_out = run_node(cur, i)
        prev_out = run_node(prev, i)
        uses_new = any(tile in row for row in s["input"].get("level", []))
        same = (cur_out == prev_out)
        if uses_new and not same:
            differ += 1
        if not uses_new and not same:
            regression_ok = False
        rows.append({"id": s["id"], "uses_new_tile": uses_new, "prev==cur": same,
                     "output": (cur_out or "").strip()})

    review = {"game": GAME, "mechanic": p["mechanic"], "tile": tile, "rule": p["rule"],
              "concept": p["concept"],
              "auto_checks": {"static_gate_ok": gate["ok"], "gate_reason": gate.get("reason", ""),
                              "new_tile_fired": differ, "regression_ok": regression_ok,
                              "scenarios": len(p["scenarios"])},
              "scenario_results": rows}
    (OUT / "review.json").write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")

    shutil.rmtree(cur)
    shutil.rmtree(prev)
    print(f"\n=== 제안: {p['mechanic']} (타일 '{tile}') ===")
    print(f"규칙: {p['rule']}")
    print(f"자동검사 — static_gate={gate['ok']} 신규발동={differ} 회귀무결={regression_ok} 시나리오={len(p['scenarios'])}")
    print(f"검토 산출물 → {OUT}\\review.json, move_logic_proposed.js")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
