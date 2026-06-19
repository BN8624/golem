# 카드 자동 제안(B+검토) — 31B가 다음 카드를 제안하고, 레저(RAG) 주입 + 사전필터 신호로 검토 부담을 줄인다
"""B 경로지만 무인 아님: 31B가 골든 REF(결정적 Node)까지 제안하되, 빌드(키) 전에 사전필터로 거르고 사람이 검토해
정답 앵커로 승격한다. (★키 1콜)

레저(RAG): 과거 검토 교훈(부정 예시)·검증 패턴(긍정 예시)을 프롬프트에 주입해 같은 드리프트를 예방한다.
사전필터(키0, 검토 보조):
  - static_gate 통과.
  - 직전 카드 전체 시나리오 회귀: 제안 REF를 직전 검증 골든(specqa)으로 돌려 전부 일치해야(스펙밖 변경 적발).
  - 발동 커버리지: 신규 타일을 실제로 발동(출력이 직전과 다름)시키는 시나리오 ≥2.
  - 결정성: 두 번 돌려 동일.
  - 구조 스코프(자문): 직전 move_logic 대비 제거/변경 줄 수(기존 분기 재구성 의심 신호).
판정 PASS_PREFILTER면 사람 검토 권장 후보로 올린다. FLAGGED면 사유와 함께 보류. 통과해도 '그럴듯하게 틀린' REF는
못 거르니 사람이 move_logic_proposed.js를 규칙과 대조해야 한다.
"""

import difflib
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
PRIOR_SPECQA = HERE / "specqa_packet_sokoban_l3" / "acceptance_tests_draft.json"  # 직전 검증 골든
OUT = HERE / "build_runs" / "proposals" / "sokoban_card4"

PROMPT = """You are a GAME DESIGNER extending a deterministic Sokoban puzzle engine (Node.js, CommonJS, no
Math.random). The engine never changes; new tile mechanics are added ONLY by editing src/move_logic.js.
State: player [r,c], boxes [[r,c]], walls{{}}, targets{{}}, tiles{{}} (any non-standard grid char, e.g.
'K' key, 'D' door, 'T' teleport, 'O' hole — already implemented). hasKey is a dynamic flag.
A move returns a log string like '<dir>:move' / ':push' / ':block' / ':move+key' / ':fill' / ':move+tp'.

{ledger}

CURRENT move_logic.js (cumulative through card 3 — keep ALL of this behavior intact):
=== CURRENT ===
{current}
=== END CURRENT ===

Existing rules (RULE-01..RULE-08):
{rules}

Propose ONE NEW tile mechanic as card 4 (a NEW single-char tile; K/D/T/O are taken). Deterministic, keep
resolveMove(state, dir) signature, leave EVERY existing behavior byte-for-byte intact. Add your new behavior
as a NEW localized case ONLY — do NOT restructure or alter the existing wall/push/move/fill/door/key/teleport
branches. Output EXACTLY this format, nothing else:

MECHANIC: <short name>
TILE: <single char>
RULE: RULE-09 (THIS CARD): <one precise sentence: behavior + the log suffix/marker>
CONCEPT: <one Korean sentence>
=== MOVE_LOGIC ===
<FULL new src/move_logic.js source, cumulative (all old mechanics + the new one)>
=== SCENARIOS ===
<JSON array of 4 scenarios: {{"id":"SCN-0NN","covers_reqs":["RULE-09"],"input":{{"level":["#...","..."],"moves":["R","U",...]}}}}.
Use INLINE level grids that include your new tile. At least 2 scenarios MUST fire the new mechanic in ISOLATION
(not mixed with K/D/T/O). Include at least 1 plain scenario with NO new tile (regression). Keep grids small.>
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
    return {"mechanic": field("MECHANIC"), "tile": field("TILE"), "rule": field("RULE"),
            "concept": field("CONCEPT"), "move_logic": ml, "scenarios": json.loads(scen_raw)}


def canon(v):
    if isinstance(v, str):
        try:
            v = json.loads(v)
        except (ValueError, TypeError):
            return v
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def parse_out(stdout):
    d = {}
    for ln in (stdout or "").splitlines():
        if ":" in ln:
            k, _, v = ln.partition(":")
            d[k.strip()] = v.strip()
    return d


def run_node(workdir, idx):
    r = subprocess.run(["node", "main.js", "--scenario", str(idx)], cwd=str(workdir),
                       capture_output=True, text=True, encoding="utf-8", timeout=30, stdin=subprocess.DEVNULL)
    return r.stdout if r.returncode == 0 else None


def write_scenarios(workdir, scen_inputs):
    (workdir / "scenarios.json").write_text(json.dumps(scen_inputs, ensure_ascii=False), encoding="utf-8")


def main():
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(HERE))
    sys.path.insert(0, str(HERE.parent))
    try:
        from config import force_utf8_stdout
        force_utf8_stdout()
    except Exception:  # noqa: BLE001
        pass
    import importlib
    sg = importlib.import_module("static_gate")
    ledger = importlib.import_module("cardgen_ledger")

    current = (PREV_BASE / "src" / "move_logic.js").read_text(encoding="utf-8")
    contract = json.loads(PREV_CONTRACT.read_text(encoding="utf-8"))
    rules = "\n".join(f"- {r}" for r in contract["data_contract"]["rules"])
    output_keys = [k for k, v in contract["data_contract"]["state_shape"].items() if not isinstance(v, dict)]
    lessons, exemplars = ledger.retrieve(GAME)
    ledger_block = ledger.format_for_prompt(lessons, exemplars)
    prompt = PROMPT.format(ledger=ledger_block, current=current, rules=rules)

    reuse = "--reuse" in sys.argv
    raw_path = OUT / "_raw_response.txt"
    if reuse and raw_path.exists():
        resp = raw_path.read_text(encoding="utf-8")
        print("[제안기] 기존 응답 재사용(키 0) — 분석만 재실행")
    else:
        print(f"[제안기] 레저 주입(교훈 {len(lessons)}·예시 {len(exemplars)}) → 31B 호출(★키 1콜)…")
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

    # cur(제안 REF) / prev(현재 누적) 워크스페이스
    cur, prev = OUT / "ref_cur", OUT / "ref_prev"
    for d, ml in ((cur, p["move_logic"]), (prev, current)):
        shutil.copytree(PREV_BASE, d)
        (d / "src" / "move_logic.js").write_text(ml, encoding="utf-8")

    # 신호 1: static_gate
    gate = sg.check(str(cur))

    # 신호 2: 제안 시나리오 — 발동 커버리지 + 결정성
    own_inputs = [{"input": s["input"]} for s in p["scenarios"]]
    write_scenarios(cur, own_inputs)
    write_scenarios(prev, own_inputs)
    rows, fired = [], 0
    determinism_ok = True
    for i, s in enumerate(p["scenarios"], 1):
        cur_out, prev_out = run_node(cur, i), run_node(prev, i)
        if run_node(cur, i) != cur_out:
            determinism_ok = False
        uses_new = any(p["tile"] in row for row in s["input"].get("level", []))
        diff = (cur_out != prev_out)
        if uses_new and diff:
            fired += 1
        rows.append({"id": s["id"], "uses_new_tile": uses_new, "differs_from_prev": diff,
                     "output": (cur_out or "").strip()})

    # 신호 3: 직전 카드 전체 시나리오 회귀(스펙밖 변경 적발) — 제안 REF를 직전 골든으로 채점
    prior = json.loads(PRIOR_SPECQA.read_text(encoding="utf-8"))
    write_scenarios(cur, [{"input": s["input"]} for s in prior])
    prior_breaks = []
    for i, s in enumerate(prior, 1):
        got = parse_out(run_node(cur, i))
        for k in output_keys:
            if k in s["expected"] and canon(got.get(k)) != canon(s["expected"][k]):
                prior_breaks.append(f"{s['id']}.{k}")

    # 신호 4: 구조 스코프(자문) — 직전 move_logic 대비 제거/추가 줄
    diff_lines = list(difflib.unified_diff(current.splitlines(), p["move_logic"].splitlines(), lineterm=""))
    removed = sum(1 for l in diff_lines if l.startswith("-") and not l.startswith("---"))
    added = sum(1 for l in diff_lines if l.startswith("+") and not l.startswith("+++"))

    reasons = []
    if not gate["ok"]:
        reasons.append(f"static_gate 실패: {gate.get('reason')}")
    if prior_breaks:
        reasons.append(f"직전 골든 회귀 깨짐 {len(prior_breaks)}: {prior_breaks[:5]}")
    if fired < 2:
        reasons.append(f"신규 발동 커버리지 {fired}<2")
    if not determinism_ok:
        reasons.append("결정성 실패(두 번 출력 불일치)")
    verdict = "PASS_PREFILTER" if not reasons else "FLAGGED"

    review = {"game": GAME, "verdict": verdict, "reasons": reasons,
              "mechanic": p["mechanic"], "tile": p["tile"], "rule": p["rule"], "concept": p["concept"],
              "signals": {"static_gate_ok": gate["ok"], "prior_regression_breaks": prior_breaks,
                          "new_tile_fired": fired, "determinism_ok": determinism_ok,
                          "structural_diff": {"removed_lines": removed, "added_lines": added,
                                              "advisory": "removed가 크면 기존 분기 재구성 의심 — 사람이 diff 확인"}},
              "scenario_results": rows}
    (OUT / "review.json").write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")
    shutil.rmtree(cur)
    shutil.rmtree(prev)

    print(f"\n=== 제안: {p['mechanic']} (타일 '{p['tile']}') — 판정 {verdict} ===")
    print(f"규칙: {p['rule']}")
    print(f"신호 — gate={gate['ok']} 직전회귀깨짐={len(prior_breaks)} 신규발동={fired} 결정성={determinism_ok} "
          f"구조diff(-{removed}/+{added})")
    if reasons:
        print("FLAGGED 사유: " + " / ".join(reasons))
    print(f"검토 산출물 → {OUT}\\review.json, move_logic_proposed.js")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
