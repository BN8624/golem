# 다중 아군(squad) 커널 골든 생성기 — 적 AI 커널을 allies 리스트로 일반화한 완결 REF base를 node로 역산(키0)
"""다중 아군 커널의 골든 앵커. multiunit_base(영웅1+능동적 적)를 아군 여럿으로 일반화한다.
액션은 {unit: 아군id, type}로 어느 아군이 행동하는지 지정하고, 적은 가장 가까운 아군을 목표로 추격·공격한다.
골렘 룰을 그대로 JS REF base로 인코딩하고 실Node로 9세계 골든을 역산한다(모델 독립).

증명 = '아군이 여럿이고 각각 행동하며, 적이 가장 가까운 아군을 골라 추격·공격한다'를 키0으로.
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

import json
import shutil
import subprocess

PACKET = PACKETS / "planning_packet_squad_kernel"
SPECQA = PACKETS / "specqa_packet_squad_kernel"

OUTPUT_CONTRACT = {
    "fields": ["status", "turn", "allies", "enemies"],
    "lines": [
        "status: <one of PLAYING|VICTORY|DEFEAT|FINISHED>",
        "turn: <integer>",
        'allies: <a JSON array in ascending id; each EXACTLY {"id":..., "hp":..., "pos":[x,y]} — no atk>',
        'enemies: <a JSON array in ascending id; each EXACTLY {"id":..., "hp":..., "pos":[x,y]} — no atk>',
    ],
}

# 고정 세계. allies/enemies = [{id,hp,atk,pos:[x,y]}], gridSize. actions = [{unit: 아군id, type, dir?}]
SCENARIO_DATA = [
    # 두 아군 + 한 적: 적이 가장 가까운 아군(id2, 더 가까움)을 추격
    {"id": "SCN-001", "covers_reqs": ["AI-TARGET"], "initialState": {
        "gridSize": 6,
        "allies": [{"id": 1, "hp": 10, "atk": 3, "pos": [0, 0]},
                   {"id": 2, "hp": 10, "atk": 3, "pos": [4, 4]}],
        "enemies": [{"id": 1, "hp": 8, "atk": 2, "pos": [5, 5]}]},
     "actions": [{"unit": 1, "type": "move", "dir": [1, 0]}]},
    # 두 아군이 한 적을 협공 처치 → VICTORY
    {"id": "SCN-002", "covers_reqs": ["WIN", "FOCUS"], "initialState": {
        "gridSize": 5,
        "allies": [{"id": 1, "hp": 10, "atk": 3, "pos": [0, 1]},
                   {"id": 2, "hp": 10, "atk": 3, "pos": [2, 1]}],
        "enemies": [{"id": 1, "hp": 6, "atk": 1, "pos": [1, 1]}]},
     "actions": [{"unit": 1, "type": "attack"}, {"unit": 2, "type": "attack"}]},
    # 적 다수가 아군 하나를 처치 → DEFEAT
    {"id": "SCN-003", "covers_reqs": ["LOSE"], "initialState": {
        "gridSize": 5,
        "allies": [{"id": 1, "hp": 3, "atk": 1, "pos": [2, 2]}],
        "enemies": [{"id": 1, "hp": 9, "atk": 2, "pos": [1, 2]},
                    {"id": 2, "hp": 9, "atk": 2, "pos": [3, 2]}]},
     "actions": [{"unit": 1, "type": "attack"}]},
    # 적 두 마리가 서로 다른 가장 가까운 아군을 추격(목표 분기)
    {"id": "SCN-004", "covers_reqs": ["AI-TARGET", "MULTI"], "initialState": {
        "gridSize": 7,
        "allies": [{"id": 1, "hp": 12, "atk": 3, "pos": [0, 0]},
                   {"id": 2, "hp": 12, "atk": 3, "pos": [6, 6]}],
        "enemies": [{"id": 1, "hp": 8, "atk": 1, "pos": [2, 0]},
                    {"id": 2, "hp": 8, "atk": 1, "pos": [6, 4]}]},
     "actions": [{"unit": 1, "type": "move", "dir": [0, 1]}]},
    # 목표 거리 동률 → 아군 id 작은 쪽을 목표
    {"id": "SCN-005", "covers_reqs": ["AI-TARGET-TIE"], "initialState": {
        "gridSize": 5,
        "allies": [{"id": 1, "hp": 10, "atk": 3, "pos": [0, 2]},
                   {"id": 2, "hp": 10, "atk": 3, "pos": [4, 2]}],
        "enemies": [{"id": 1, "hp": 8, "atk": 1, "pos": [2, 2]}]},
     "actions": [{"unit": 2, "type": "move", "dir": [0, 1]}]},
    # 아군 MOVE가 다른 아군 점유칸이면 실패(턴 소비)
    {"id": "SCN-006", "covers_reqs": ["ALLY-BLOCK"], "initialState": {
        "gridSize": 5,
        "allies": [{"id": 1, "hp": 10, "atk": 3, "pos": [1, 1]},
                   {"id": 2, "hp": 10, "atk": 3, "pos": [2, 1]}],
        "enemies": [{"id": 1, "hp": 9, "atk": 1, "pos": [4, 4]}]},
     "actions": [{"unit": 1, "type": "move", "dir": [1, 0]}]},
    # 세 아군 + 두 적, 여러 라운드 전개
    {"id": "SCN-007", "covers_reqs": ["MULTI", "SQUAD"], "initialState": {
        "gridSize": 6,
        "allies": [{"id": 1, "hp": 10, "atk": 4, "pos": [0, 0]},
                   {"id": 2, "hp": 10, "atk": 4, "pos": [0, 1]},
                   {"id": 3, "hp": 10, "atk": 4, "pos": [0, 2]}],
        "enemies": [{"id": 1, "hp": 6, "atk": 2, "pos": [3, 0]},
                    {"id": 2, "hp": 6, "atk": 2, "pos": [3, 2]}]},
     "actions": [{"unit": 1, "type": "move", "dir": [1, 0]},
                 {"unit": 2, "type": "move", "dir": [1, 0]},
                 {"unit": 3, "type": "move", "dir": [1, 0]}]},
    # 한 아군이 인접 적 처치, 남은 적은 다른 아군 추격
    {"id": "SCN-008", "covers_reqs": ["WIN", "MULTI"], "initialState": {
        "gridSize": 6,
        "allies": [{"id": 1, "hp": 12, "atk": 6, "pos": [0, 0]},
                   {"id": 2, "hp": 12, "atk": 6, "pos": [5, 5]}],
        "enemies": [{"id": 1, "hp": 5, "atk": 2, "pos": [1, 0]},
                    {"id": 2, "hp": 5, "atk": 2, "pos": [3, 5]}]},
     "actions": [{"unit": 1, "type": "attack"}, {"unit": 2, "type": "move", "dir": [-1, 0]}]},
    # 액션 소진 미결 → FINISHED
    {"id": "SCN-009", "covers_reqs": ["FINISHED"], "initialState": {
        "gridSize": 8,
        "allies": [{"id": 1, "hp": 10, "atk": 3, "pos": [0, 0]},
                   {"id": 2, "hp": 10, "atk": 3, "pos": [1, 0]}],
        "enemies": [{"id": 1, "hp": 9, "atk": 1, "pos": [7, 7]}]},
     "actions": [{"unit": 1, "type": "move", "dir": [1, 0]}]},
]

REF_GAME_LOGIC = """// 다중 아군(squad) 규칙 코어 — 아군 액션 적용 + 결정적 적 AI(가장 가까운 아군 추격) + 승패판정
const DIRS = [[1, 0], [-1, 0], [0, 1], [0, -1]];
function manhattan(a, b) { return Math.abs(a[0] - b[0]) + Math.abs(a[1] - b[1]); }
function clone(state) {
  return {
    ...state,
    allies: state.allies.map(u => ({ ...u, pos: [...u.pos] })),
    enemies: state.enemies.map(e => ({ ...e, pos: [...e.pos] })),
    turn: state.turn, gridSize: state.gridSize
  };
}
function occupied(state, x, y, self) {
  const units = state.allies.concat(state.enemies);
  return units.some(u => u !== self && u.hp > 0 && u.pos[0] === x && u.pos[1] === y);
}

exports.applyAction = (state, action) => {
  const unit = state.allies.find(u => u.id === action.unit && u.hp > 0);
  if (!unit) return;
  if (action.type === 'move') {
    const nx = unit.pos[0] + action.dir[0], ny = unit.pos[1] + action.dir[1];
    const off = nx < 0 || ny < 0 || nx >= state.gridSize || ny >= state.gridSize;
    if (!off && !occupied(state, nx, ny, unit)) { unit.pos = [nx, ny]; }
  } else if (action.type === 'attack') {
    const adj = state.enemies.filter(e => e.hp > 0 && manhattan(e.pos, unit.pos) === 1)
                             .sort((a, b) => a.id - b.id);
    if (adj.length) { adj[0].hp -= unit.atk; }
  }
};

function betterMove(c, b) {
  if (c.axisIsX !== b.axisIsX) return c.axisIsX;
  if (c.nx !== b.nx) return c.nx < b.nx;
  return c.ny < b.ny;
}

exports.enemyPhase = (state) => {
  const order = state.enemies.filter(e => e.hp > 0).sort((a, b) => a.id - b.id);
  for (const e of order) {
    if (e.hp <= 0) continue;
    const living = state.allies.filter(a => a.hp > 0);
    if (!living.length) break;
    // 목표 = 맨해튼 최소 아군(동률은 아군 id 작은 쪽)
    let target = living[0];
    for (const a of living) {
      const d = manhattan(e.pos, a.pos), td = manhattan(e.pos, target.pos);
      if (d < td || (d === td && a.id < target.id)) target = a;
    }
    const cur = manhattan(e.pos, target.pos);
    if (cur === 1) { target.hp -= e.atk; continue; }
    let best = null;
    for (const [dx, dy] of DIRS) {
      const nx = e.pos[0] + dx, ny = e.pos[1] + dy;
      if (nx < 0 || ny < 0 || nx >= state.gridSize || ny >= state.gridSize) continue;
      if (occupied(state, nx, ny, e)) continue;
      if (manhattan([nx, ny], target.pos) < cur) {
        const cand = { nx, ny, axisIsX: dx !== 0 };
        if (best === null || betterMove(cand, best)) best = cand;
      }
    }
    if (best) { e.pos = [best.nx, best.ny]; }
  }
};

exports.updateState = (state, action) => {
  const ns = clone(state);
  exports.applyAction(ns, action);
  const allEnemiesDead = ns.enemies.every(e => e.hp <= 0);
  if (!allEnemiesDead) { exports.enemyPhase(ns); }
  ns.turn = state.turn + 1;
  return ns;
};

exports.checkGameState = (state) => {
  const alliesDead = state.allies.every(a => a.hp <= 0);
  const enemiesDead = state.enemies.every(e => e.hp <= 0);
  if (enemiesDead) return 'VICTORY';
  if (alliesDead) return 'DEFEAT';
  return null;
};
"""

REF_ENGINE = """const gameLogic = require('./game_logic');
exports.runScenario = (initialState, actionSequence) => {
  let state = {
    ...initialState,
    allies: initialState.allies.map(u => ({ ...u, pos: [...u.pos] })),
    enemies: initialState.enemies.map(e => ({ ...e, pos: [...e.pos] })),
    turn: 0, gridSize: initialState.gridSize
  };
  let status = 'PLAYING';
  for (const action of actionSequence) {
    state = gameLogic.updateState(state, action);
    const r = gameLogic.checkGameState(state);
    if (r) { status = r; break; }
  }
  if (status === 'PLAYING') status = 'FINISHED';
  return { state, status };
};
"""

REF_MAIN = """const { runScenario } = require('./src/engine');
const { getScenario } = require('./src/scenarios');
const i = process.argv.indexOf('--scenario');
const idx = i >= 0 ? parseInt(process.argv[i + 1], 10) : 1;
const world = getScenario(idx);
const { state, status } = runScenario(world.initialState, world.actions);
console.log('status: ' + status);
console.log('turn: ' + state.turn);
console.log('allies: ' + JSON.stringify(state.allies.map(u => ({ id: u.id, hp: u.hp, pos: u.pos }))));
console.log('enemies: ' + JSON.stringify(state.enemies.map(e => ({ id: e.id, hp: e.hp, pos: e.pos }))));
"""

OUTPUT_KEYS = ["status", "turn", "allies", "enemies"]

# ★ 동결 squad_base가 정본 계약(updateState=mutable+status 반환). 위 REF_* 문자열은 골든 역산용 독립
# 참조였으나 base와 game_logic 계약이 달라(immutable) 카드 체인서 어긋난다. card_delta가 확장할
# prev_ref·graft가 쓸 참조는 반드시 동결 base의 실모듈이어야 한다 → base 실모듈로 덮어쓴다.
_SQUAD_BASE = BASES / "squad_base"
REF_GAME_LOGIC = (_SQUAD_BASE / "src" / "game_logic.js").read_text(encoding="utf-8")
REF_ENGINE = (_SQUAD_BASE / "src" / "engine.js").read_text(encoding="utf-8")
REF_MAIN = (_SQUAD_BASE / "main.js").read_text(encoding="utf-8")


def run(workdir, idx):
    r = subprocess.run(["node", "main.js", "--scenario", str(idx)], cwd=str(workdir),
                       capture_output=True, text=True, encoding="utf-8", timeout=30,
                       stdin=subprocess.DEVNULL)
    if r.returncode != 0:
        raise RuntimeError(f"node 실패 scn{idx}: {r.stderr[:300]}")
    return r.stdout


def parse_expected(stdout):
    exp = {}
    for line in stdout.splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        k, v = k.strip(), v.strip()
        if k == "turn":
            exp[k] = int(v)
        elif k in ("allies", "enemies"):
            exp[k] = json.loads(v)
        else:
            exp[k] = v
    return exp


def main():
    try:
        from config import force_utf8_stdout
        force_utf8_stdout()
    except Exception:  # noqa: BLE001
        pass
    import build_graded as bg

    contract = json.loads((PACKET / "contract.json").read_text(encoding="utf-8"))
    contract["data_contract"]["output_contract"] = OUTPUT_CONTRACT
    contract["data_contract"]["scenario_data"] = SCENARIO_DATA
    (PACKET / "contract.json").write_text(json.dumps(contract, ensure_ascii=False, indent=2), encoding="utf-8")

    ref = BUILD_RUNS / "_squad_ref_tmp"
    if ref.exists():
        shutil.rmtree(ref)
    (ref / "src").mkdir(parents=True)
    (ref / "main.js").write_text(REF_MAIN, encoding="utf-8")
    (ref / "src" / "engine.js").write_text(REF_ENGINE, encoding="utf-8")
    (ref / "src" / "game_logic.js").write_text(REF_GAME_LOGIC, encoding="utf-8")
    (ref / "src" / "scenarios.js").write_text(bg._gen_scenarios_module(SCENARIO_DATA), encoding="utf-8")

    out = []
    for i, s in enumerate(SCENARIO_DATA, 1):
        sid = s["id"]
        expected = parse_expected(run(ref, i))
        out.append({"id": sid, "input": {"args": ["--scenario", str(i)]},
                    "covers_reqs": s.get("covers_reqs", []),
                    "expected": expected, "oracle_risk": {"risk": False, "reason": ""}})
        a0 = s["initialState"]["allies"]
        e0 = s["initialState"]["enemies"]
        emoved = any(e0[j]["pos"] != expected["enemies"][j]["pos"] for j in range(len(e0)))
        print(f"  {sid} status={expected['status']} 아군{len(a0)} 적{len(e0)} 적이동={emoved}  "
              f"allies_hp={[u['hp'] for u in expected['allies']]} enemies={[e['pos'] for e in expected['enemies']]}")

    SPECQA.mkdir(parents=True, exist_ok=True)
    (SPECQA / "acceptance_tests_draft.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    (SPECQA / "oracle_risk_review.json").write_text(json.dumps(
        {"risky_scenarios": [],
         "notes": [{"risk": False, "reason": "다중 아군(squad) 커널 — 골든은 골렘 룰 인코딩 REF base 실Node 역산(모델 독립)."}]},
        ensure_ascii=False, indent=2), encoding="utf-8")
    shutil.rmtree(ref)
    print(f"\n골든 {len(out)}세계 역산 → {SPECQA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
