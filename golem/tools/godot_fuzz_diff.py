# JS↔GDScript 차등 퍼징 — 시드 결정적으로 무작위 유효·엣지 케이스를 생성, JS 엔진(정답)과 rules.gd trace를 0-diff 대조(키0)
"""검증된 JS 룰(squad_base_l8/game_logic.js)과 Godot 포팅(rules.gd)이 '알려진 36스텝' 밖의
무작위 상태·행동열에서도 동치인지 본다. 36스텝 골든은 고정 시나리오라 카드 상호작용 조합·경계·
승패 타이밍·존재하지 않는 유닛 등의 미검증 조합을 못 훑는다. fast-check식 차등 퍼징을 시드 PRNG로
구현(Math.random 금지·결정적 재현). JS 엔진이 정답, rules.gd가 피검.

사용: python golem/tools/godot_fuzz_diff.py [--n 300] [--seed 20260623] [--godot <exe>]   (키0, node+godot 필요)
"""
import sys as _sys
from pathlib import Path as _Path
_PKG = _Path(__file__).resolve().parents[1]
for _p in (str(_PKG), str(_PKG / "core"), str(_PKG / "tools"), str(_PKG / "tactics"),
           str(_PKG / "validators"), str(_PKG.parent)):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)
from paths import REPO_ROOT, BUILD_RUNS  # noqa: E402

import argparse
import json
import os
import random
import subprocess
from pathlib import Path

from godot_export_golden import TRACE_JS, ENGINE  # JS 엔진·trace 템플릿 재사용(DRY)

GODOT_DIR = REPO_ROOT / "godot"
CASES_OUT = GODOT_DIR / "test" / "_fuzz_cases.json"
FAIL_OUT = GODOT_DIR / "test" / "_fuzz_fail.json"
DEFAULT_GODOT = r"C:\Users\USER\godot-engine\Godot_v4.7-stable_win64_console.exe"
DIRS = [[1, 0], [-1, 0], [0, 1], [0, -1]]


def gen_case(rng, idx):
    """무작위 유효 케이스 + 엣지(존재하지 않는 unit·경계 이동·무사거리 공격)를 섞어 생성."""
    grid = rng.randint(3, 6)
    cells = [(x, y) for x in range(grid) for y in range(grid)]
    rng.shuffle(cells)
    na = rng.randint(1, 3)
    ne = rng.randint(1, 3)
    pi = 0
    allies = []
    for i in range(na):
        x, y = cells[pi]; pi += 1
        a = {"id": i + 1, "hp": rng.randint(3, 20), "atk": rng.randint(1, 8), "pos": [x, y]}
        if rng.random() < 0.3:
            a["range"] = rng.randint(2, 3)
        if rng.random() < 0.25:
            a["knockback"] = True
        if rng.random() < 0.2:
            a["flank_bonus"] = rng.randint(1, 2)
        if rng.random() < 0.15:
            a["aura_shield"] = rng.randint(1, 2)
        if rng.random() < 0.15:
            a["asymmetric_strike"] = rng.randint(1, 2)
        allies.append(a)
    enemies = []
    for i in range(ne):
        x, y = cells[pi]; pi += 1
        e = {"id": i + 1, "hp": rng.randint(3, 20), "atk": rng.randint(1, 8), "pos": [x, y]}
        if rng.random() < 0.2:
            e["reflect_dmg"] = rng.randint(1, 3)
        if rng.random() < 0.15:
            e["aura_shield"] = rng.randint(1, 2)
        if rng.random() < 0.15:
            e["phalanx_defense"] = rng.randint(1, 2)
        if rng.random() < 0.15:
            e["asymmetric_strike"] = rng.randint(1, 2)
        enemies.append(e)
    n_actions = rng.randint(3, 8)
    actions = []
    for _ in range(n_actions):
        uid = rng.randint(1, na + 1)  # na+1 = 존재하지 않는 유닛(엣지)
        if rng.random() < 0.5:
            actions.append({"unit": uid, "type": "move", "dir": rng.choice(DIRS)})
        else:
            actions.append({"unit": uid, "type": "attack"})
    return {"name": f"fuzz_{idx}", "category": "fuzz",
            "initialState": {"gridSize": grid, "allies": allies, "enemies": enemies},
            "actions": actions}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--seed", type=int, default=20260623)
    ap.add_argument("--godot", default=os.environ.get("GODOT", DEFAULT_GODOT))
    args = ap.parse_args(argv)

    try:
        from config import force_utf8_stdout
        force_utf8_stdout()
    except Exception:  # noqa: BLE001
        pass

    rng = random.Random(args.seed)
    cases = [gen_case(rng, i) for i in range(args.n)]

    # JS 엔진(정답)으로 trace를 굽는다 — godot_export_golden 의 TRACE_JS 재사용.
    gl = ENGINE.read_text(encoding="utf-8")
    js = TRACE_JS.replace("__GAME_LOGIC__", gl).replace("__CASES__", json.dumps(cases, ensure_ascii=False))
    BUILD_RUNS.mkdir(parents=True, exist_ok=True)
    tmp = BUILD_RUNS / "_fuzz_trace_tmp.js"
    tmp.write_text(js, encoding="utf-8")
    try:
        r = subprocess.run(["node", str(tmp)], capture_output=True, text=True, encoding="utf-8", timeout=300)
    finally:
        tmp.unlink(missing_ok=True)
    if r.returncode != 0:
        raise SystemExit(f"node(JS 엔진) 실패: {r.stderr[:400]}")
    golden = json.loads(r.stdout)
    n_steps = sum(len(c["steps"]) for c in golden)
    CASES_OUT.write_text(json.dumps(golden, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"퍼즈 케이스 {len(golden)}개 · {n_steps}스텝 생성(seed={args.seed}) → JS 정답 trace")

    # rules.gd 로 재생해 0-diff 대조.
    if FAIL_OUT.exists():
        FAIL_OUT.unlink()
    rr = subprocess.run([args.godot, "--headless", "--path", str(GODOT_DIR),
                         "--script", "res://test/run_fuzz_diff.gd"],
                        capture_output=True, text=True, encoding="utf-8", timeout=300)
    out = (rr.stdout or "") + (rr.stderr or "")
    for line in out.splitlines():
        if "FUZZ" in line or "SCRIPT ERROR" in line or "Parse Error" in line:
            print(line)
    if rr.returncode != 0 and FAIL_OUT.exists():
        print("\n최초 불일치 케이스(시드 재현 가능) →", FAIL_OUT)
        fail = json.loads(FAIL_OUT.read_text(encoding="utf-8"))
        print(json.dumps({"case": fail.get("case"), "step": fail.get("step"),
                          "action": fail.get("action"),
                          "got_status": fail.get("got_status"), "want_status": fail.get("want_status")},
                         ensure_ascii=False, indent=2))
    print("RESULT:", "ALL MATCH" if rr.returncode == 0 else "DIFF FOUND")
    return rr.returncode


if __name__ == "__main__":
    raise SystemExit(main())
