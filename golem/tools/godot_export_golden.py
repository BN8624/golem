# Godot 룰 포팅 검증용 골든 추출 — 검증된 JS squad 엔진으로 미션 솔루션 + 엣지케이스를 재생해 per-step 정답 trace를 뽑는다(키0)
"""고도 GDScript 포팅(scripts/rules.gd)이 검증된 JS 룰(squad_base_l8/src/game_logic.js)과 동치인지
0-diff로 대조할 '정답지'를 만든다. 골든 = 케이스마다 액션을 updateState로 재생한 매 스텝 state_after+status.
솔루션 경로만으론 부족(엣지 누락)하므로 invalid move(경계·점유)·무사거리 공격·적 AI 추격·승리/패배·
knockback/reflect/range/flank 엣지케이스를 함께 굽는다. 이 골든은 godot/test/run_rules_golden.gd가 소비.

사용: python golem/tools/godot_export_golden.py   (키0, node 필요)
"""
import sys as _sys
from pathlib import Path as _Path
_PKG = _Path(__file__).resolve().parents[1]
for _p in (str(_PKG), str(_PKG / "core"), str(_PKG / "tools"), str(_PKG / "tactics"),
           str(_PKG / "validators"), str(_PKG.parent)):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)
from paths import (PKG, REPO_ROOT, BASES, PLAY, BUILD_RUNS)  # noqa: E402,F401

import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
GODOT = REPO_ROOT / "godot"          # 고도 프로젝트 루트(저장소 최상위)
ENGINE = BASES / "squad_base_l8" / "src" / "game_logic.js"
MISSIONS = PLAY / "squad_levels.json"

# 케이스를 updateState로 재생해 매 스텝 state_after+status를 캡처(VICTORY/DEFEAT면 중단). JS 엔진이 정답.
TRACE_JS = r"""
__GAME_LOGIC__
const GL = module.exports;
const CASES = __CASES__;
function clone(s){ return JSON.parse(JSON.stringify(s)); }
const out=[];
for(const c of CASES){
  let s=clone(c.initialState); if(s.turn===undefined) s.turn=0;
  const steps=[];
  for(const a of c.actions){
    const status=GL.updateState(s,a);
    steps.push({action:a, state_after:clone(s), status:status});
    if(status==='VICTORY'||status==='DEFEAT') break;
  }
  out.push({name:c.name, category:c.category, initialState:c.initialState, steps:steps});
}
process.stdout.write(JSON.stringify(out));
"""

# 엣지케이스 — 정답은 JS 엔진이 계산하므로 여기선 '분기를 건드리는 입력'만 설계한다.
EDGES = [
    {"name": "oob_move", "category": "invalid",
     "initialState": {"gridSize": 3, "allies": [{"id": 1, "hp": 10, "atk": 3, "pos": [0, 0]}],
                      "enemies": [{"id": 1, "hp": 9, "atk": 2, "pos": [2, 2]}]},
     "actions": [{"unit": 1, "type": "move", "dir": [-1, 0]}, {"unit": 1, "type": "move", "dir": [0, -1]}]},
    {"name": "occupied_move", "category": "invalid",
     "initialState": {"gridSize": 3, "allies": [{"id": 1, "hp": 10, "atk": 3, "pos": [0, 0]},
                                                {"id": 2, "hp": 10, "atk": 3, "pos": [1, 0]}],
                      "enemies": [{"id": 1, "hp": 9, "atk": 2, "pos": [2, 2]}]},
     "actions": [{"unit": 1, "type": "move", "dir": [1, 0]}]},
    {"name": "attack_out_of_range", "category": "invalid",
     "initialState": {"gridSize": 4, "allies": [{"id": 1, "hp": 10, "atk": 3, "pos": [0, 0]}],
                      "enemies": [{"id": 1, "hp": 9, "atk": 2, "pos": [3, 3]}]},
     "actions": [{"unit": 1, "type": "attack"}]},
    {"name": "enemy_chase_attack", "category": "enemy_turn",
     "initialState": {"gridSize": 3, "allies": [{"id": 1, "hp": 10, "atk": 3, "pos": [0, 0]}],
                      "enemies": [{"id": 1, "hp": 20, "atk": 4, "pos": [1, 0]}]},
     "actions": [{"unit": 1, "type": "attack"}]},
    {"name": "enemy_death_victory", "category": "win_loss",
     "initialState": {"gridSize": 3, "allies": [{"id": 1, "hp": 10, "atk": 10, "pos": [0, 0]}],
                      "enemies": [{"id": 1, "hp": 5, "atk": 2, "pos": [1, 0]}]},
     "actions": [{"unit": 1, "type": "attack"}]},
    {"name": "ally_death_defeat", "category": "win_loss",
     "initialState": {"gridSize": 3, "allies": [{"id": 1, "hp": 3, "atk": 1, "pos": [0, 0]}],
                      "enemies": [{"id": 1, "hp": 20, "atk": 5, "pos": [1, 0]}]},
     "actions": [{"unit": 1, "type": "attack"}]},
    {"name": "knockback", "category": "card",
     "initialState": {"gridSize": 4, "allies": [{"id": 1, "hp": 10, "atk": 3, "pos": [0, 0], "knockback": True}],
                      "enemies": [{"id": 1, "hp": 20, "atk": 1, "pos": [1, 0]}]},
     "actions": [{"unit": 1, "type": "attack"}]},
    {"name": "reflect", "category": "card",
     "initialState": {"gridSize": 3, "allies": [{"id": 1, "hp": 10, "atk": 3, "pos": [0, 0]}],
                      "enemies": [{"id": 1, "hp": 20, "atk": 1, "pos": [1, 0], "reflect_dmg": 2}]},
     "actions": [{"unit": 1, "type": "attack"}]},
    {"name": "range_attack", "category": "card",
     "initialState": {"gridSize": 4, "allies": [{"id": 1, "hp": 10, "atk": 3, "pos": [0, 0], "range": 2}],
                      "enemies": [{"id": 1, "hp": 20, "atk": 1, "pos": [2, 0]}]},
     "actions": [{"unit": 1, "type": "attack"}]},
    {"name": "flank_bonus", "category": "card",
     "initialState": {"gridSize": 3, "allies": [{"id": 1, "hp": 10, "atk": 3, "pos": [0, 0], "flank_bonus": 2},
                                                {"id": 2, "hp": 10, "atk": 1, "pos": [1, 1]}],
                      "enemies": [{"id": 1, "hp": 20, "atk": 1, "pos": [1, 0]}]},
     "actions": [{"unit": 1, "type": "attack"}]},
]


def main():
    from play_signals import solve_levels
    gl = ENGINE.read_text(encoding="utf-8")
    missions = json.loads(MISSIONS.read_text(encoding="utf-8"))
    sols = solve_levels(missions, gl, "squad")

    cases = []
    for lv, sol in zip(missions, sols):
        if not sol:
            print(f"  ⚠ 풀이불가 미션 건너뜀: {lv.get('name')}"); continue
        cases.append({"name": lv.get("name") or lv.get("id", "?"), "category": "solution",
                      "initialState": lv["initialState"], "actions": sol})
    cases.extend(EDGES)

    js = TRACE_JS.replace("__GAME_LOGIC__", gl).replace("__CASES__", json.dumps(cases, ensure_ascii=False))
    BUILD_RUNS.mkdir(parents=True, exist_ok=True)
    tmp = BUILD_RUNS / "_godot_golden_tmp.js"
    tmp.write_text(js, encoding="utf-8")
    try:
        r = subprocess.run(["node", str(tmp)], capture_output=True, text=True, encoding="utf-8", timeout=300)
    finally:
        tmp.unlink(missing_ok=True)
    if r.returncode != 0:
        raise SystemExit(f"node 실패: {r.stderr[:400]}")
    golden = json.loads(r.stdout)

    out = GODOT / "test" / "rules_golden.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(golden, ensure_ascii=False, indent=2), encoding="utf-8")
    n_steps = sum(len(c["steps"]) for c in golden)
    print(f"골든 {len(golden)}케이스 · {n_steps}스텝 → {out}")
    for c in golden:
        last = c["steps"][-1]["status"] if c["steps"] else "(빈)"
        print(f"  [{c['category']:9}] {c['name'][:30]:30} 스텝 {len(c['steps'])} · 종료 {last}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
