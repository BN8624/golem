# 다중유닛(능동적 적 AI) 커널 골든 생성기 — 골렘 설계 룰을 인코딩한 완결 REF base를 node로 역산(키0)
"""적 AI 커널 첫 빌드의 골든 앵커. 골렘이 planning에서 고정한 룰(매 영웅 액션 뒤 적 턴·인접시 공격·
아니면 거리최소화 이동·id오름차순·타이브레이크 X축→작은x→작은y·막히면 정지)을 그대로 JS REF base로 쓴다.
계약(output_contract·scenario_data)을 핀하고, REF를 실Node로 돌려 9세계 골든을 역산한다(모델 독립).

이 파일이 증명하는 것 = '적이 실제로 움직이고 공격한다'(정적-적 커널과의 핵심 차이)를 키0으로.
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
import sys

PACKET = PACKETS / "planning_packet_multiunit_kernel"
SPECQA = PACKETS / "specqa_packet_multiunit_kernel"

# ---- 출력계약(평면 5필드, 기존 전술 도구와 호환되게 [x,y] 배열) ----
OUTPUT_CONTRACT = {
    "fields": ["status", "turn", "hero_hp", "hero_pos", "enemies"],
    "lines": [
        "status: <one of PLAYING|VICTORY|DEFEAT|FINISHED>",
        "turn: <integer>",
        "hero_hp: <integer, may be negative>",
        "hero_pos: <a JSON array [x, y] of integers>",
        'enemies: <a JSON array; each living-or-dead enemy EXACTLY {"id":..., "hp":..., "pos":[x,y]} '
        '— include all enemies in ascending id, DO NOT include atk>',
    ],
}

# ---- 고정 세계(골든 단일 출처). hero/enemies pos=[x,y], gridSize 포함 ----
SCENARIO_DATA = [
    # 적이 영웅을 향해 가로질러 추격(전투 없음) — 적 pos가 바뀌어야 함
    {"id": "SCN-001", "covers_reqs": ["AI-MOVE"], "initialState": {
        "hero": {"hp": 10, "atk": 3, "pos": [0, 0]}, "gridSize": 5,
        "enemies": [{"id": 1, "hp": 5, "atk": 2, "pos": [4, 0]}]},
     "actions": [{"type": "move", "dir": [0, 1]}, {"type": "move", "dir": [0, 1]}]},
    # 적이 인접까지 와서 영웅 공격(hero_hp 감소)
    {"id": "SCN-002", "covers_reqs": ["AI-ATTACK"], "initialState": {
        "hero": {"hp": 10, "atk": 3, "pos": [0, 0]}, "gridSize": 5,
        "enemies": [{"id": 1, "hp": 5, "atk": 2, "pos": [2, 0]}]},
     "actions": [{"type": "move", "dir": [0, 1]}, {"type": "move", "dir": [0, 1]},
                 {"type": "move", "dir": [0, 1]}]},
    # 영웅이 인접 적 처치 → VICTORY(적 턴 전)
    {"id": "SCN-003", "covers_reqs": ["WIN"], "initialState": {
        "hero": {"hp": 10, "atk": 5, "pos": [0, 0]}, "gridSize": 5,
        "enemies": [{"id": 1, "hp": 5, "atk": 2, "pos": [1, 0]}]},
     "actions": [{"type": "attack"}]},
    # 두 적에게 둘러싸여 영웅 사망 → DEFEAT
    {"id": "SCN-004", "covers_reqs": ["LOSE"], "initialState": {
        "hero": {"hp": 3, "atk": 1, "pos": [1, 1]}, "gridSize": 5,
        "enemies": [{"id": 1, "hp": 9, "atk": 2, "pos": [0, 1]},
                    {"id": 2, "hp": 9, "atk": 2, "pos": [1, 0]}]},
     "actions": [{"type": "attack"}]},
    # 두 적이 양쪽에서 수렴(둘 다 이동, id 순서)
    {"id": "SCN-005", "covers_reqs": ["AI-MOVE", "MULTI"], "initialState": {
        "hero": {"hp": 20, "atk": 3, "pos": [2, 2]}, "gridSize": 5,
        "enemies": [{"id": 1, "hp": 5, "atk": 1, "pos": [0, 2]},
                    {"id": 2, "hp": 5, "atk": 1, "pos": [4, 2]}]},
     "actions": [{"type": "move", "dir": [0, 1]}]},
    # 타이브레이크: 대각 위치 적은 X축 이동 우선
    {"id": "SCN-006", "covers_reqs": ["AI-TIEBREAK"], "initialState": {
        "hero": {"hp": 10, "atk": 3, "pos": [0, 0]}, "gridSize": 5,
        "enemies": [{"id": 1, "hp": 5, "atk": 1, "pos": [2, 2]}]},
     "actions": [{"type": "move", "dir": [1, 0]}]},
    # 적이 영웅 칸/다른 적으로 못 들어감(점유 차단)
    {"id": "SCN-007", "covers_reqs": ["AI-BLOCK"], "initialState": {
        "hero": {"hp": 10, "atk": 3, "pos": [2, 0]}, "gridSize": 3,
        "enemies": [{"id": 1, "hp": 5, "atk": 2, "pos": [0, 0]},
                    {"id": 2, "hp": 5, "atk": 2, "pos": [1, 0]}]},
     "actions": [{"type": "move", "dir": [0, 1]}]},
    # 영웅이 한 적 처치 후 남은 적 추격 — 부분 처치 + 계속
    {"id": "SCN-008", "covers_reqs": ["WIN", "MULTI"], "initialState": {
        "hero": {"hp": 15, "atk": 5, "pos": [0, 0]}, "gridSize": 5,
        "enemies": [{"id": 1, "hp": 5, "atk": 2, "pos": [1, 0]},
                    {"id": 2, "hp": 5, "atk": 2, "pos": [4, 4]}]},
     "actions": [{"type": "attack"}, {"type": "move", "dir": [0, 1]}]},
    # 액션 소진되고 미결 → FINISHED
    {"id": "SCN-009", "covers_reqs": ["FINISHED"], "initialState": {
        "hero": {"hp": 10, "atk": 3, "pos": [0, 0]}, "gridSize": 6,
        "enemies": [{"id": 1, "hp": 9, "atk": 1, "pos": [5, 5]}]},
     "actions": [{"type": "move", "dir": [1, 0]}]},
]

# ---- 골렘 룰을 인코딩한 완결 REF base (4모듈) ----
REF_GAME_LOGIC = """// 다중유닛 커널 규칙 코어 — 영웅 액션 적용 + 결정적 적 AI 페이즈 + 상태전이/승패판정
const DIRS = [[1, 0], [-1, 0], [0, 1], [0, -1]];
function manhattan(a, b) { return Math.abs(a[0] - b[0]) + Math.abs(a[1] - b[1]); }
function clone(state) {
  return {
    ...state,
    hero: { ...state.hero, pos: [...state.hero.pos] },
    enemies: state.enemies.map(e => ({ ...e, pos: [...e.pos] })),
    turn: state.turn, gridSize: state.gridSize
  };
}

exports.applyHeroAction = (state, action) => {
  const hero = state.hero;
  if (action.type === 'move') {
    const nx = hero.pos[0] + action.dir[0], ny = hero.pos[1] + action.dir[1];
    const off = nx < 0 || ny < 0 || nx >= state.gridSize || ny >= state.gridSize;
    const occ = state.enemies.some(e => e.hp > 0 && e.pos[0] === nx && e.pos[1] === ny);
    if (!off && !occ) { hero.pos = [nx, ny]; }
  } else if (action.type === 'attack') {
    const adj = state.enemies.filter(e => e.hp > 0 && manhattan(e.pos, hero.pos) === 1)
                             .sort((a, b) => a.id - b.id);
    if (adj.length) { adj[0].hp -= hero.atk; }
  }
};

function betterMove(c, b) {
  if (c.axisIsX !== b.axisIsX) return c.axisIsX;   // X축 이동 우선
  if (c.nx !== b.nx) return c.nx < b.nx;            // 작은 X
  return c.ny < b.ny;                               // 작은 Y
}

exports.enemyPhase = (state) => {
  const hero = state.hero;
  const order = state.enemies.filter(e => e.hp > 0).sort((a, b) => a.id - b.id);
  for (const e of order) {
    if (e.hp <= 0) continue;
    const cur = manhattan(e.pos, hero.pos);
    if (cur === 1) { hero.hp -= e.atk; continue; }   // 인접 → 공격
    let best = null;
    for (const [dx, dy] of DIRS) {
      const nx = e.pos[0] + dx, ny = e.pos[1] + dy;
      if (nx < 0 || ny < 0 || nx >= state.gridSize || ny >= state.gridSize) continue;
      if (hero.pos[0] === nx && hero.pos[1] === ny) continue;
      if (state.enemies.some(o => o !== e && o.hp > 0 && o.pos[0] === nx && o.pos[1] === ny)) continue;
      if (manhattan([nx, ny], hero.pos) < cur) {     // 거리 최소화 이동만 후보
        const cand = { nx, ny, axisIsX: dx !== 0 };
        if (best === null || betterMove(cand, best)) best = cand;
      }
    }
    if (best) { e.pos = [best.nx, best.ny]; }         // 후보 없으면 정지
  }
};

exports.updateState = (state, action) => {
  const ns = clone(state);
  exports.applyHeroAction(ns, action);
  const allDead = ns.enemies.every(e => e.hp <= 0);
  if (!allDead) { exports.enemyPhase(ns); }           // 영웅이 마지막 적 처치시 적 턴 생략
  ns.turn = state.turn + 1;
  return ns;
};

exports.checkGameState = (state, initialEnemyCount) => {
  const heroDead = state.hero.hp <= 0;
  const allDead = state.enemies.every(e => e.hp <= 0);
  if (allDead && initialEnemyCount > 0) return 'VICTORY';
  if (heroDead) return 'DEFEAT';
  return null;
};
"""

REF_ENGINE = """const gameLogic = require('./game_logic');
exports.runScenario = (initialState, actionSequence) => {
  let state = {
    ...initialState,
    hero: { ...initialState.hero, pos: [...initialState.hero.pos] },
    enemies: initialState.enemies.map(e => ({ ...e, pos: [...e.pos] })),
    turn: 0, gridSize: initialState.gridSize
  };
  const initialEnemyCount = state.enemies.length;
  let status = 'PLAYING';
  for (const action of actionSequence) {
    state = gameLogic.updateState(state, action);
    const r = gameLogic.checkGameState(state, initialEnemyCount);
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
console.log('hero_hp: ' + state.hero.hp);
console.log('hero_pos: ' + JSON.stringify(state.hero.pos));
console.log('enemies: ' + JSON.stringify(state.enemies.map(e => ({ id: e.id, hp: e.hp, pos: e.pos }))));
"""

OUTPUT_KEYS = ["status", "turn", "hero_hp", "hero_pos", "enemies"]


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
        if k == "turn" or k == "hero_hp":
            exp[k] = int(v)
        elif k in ("hero_pos", "enemies"):
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

    # 1) 계약에 output_contract + scenario_data 핀(빌드 단일 출처)
    contract = json.loads((PACKET / "contract.json").read_text(encoding="utf-8"))
    contract["data_contract"]["output_contract"] = OUTPUT_CONTRACT
    contract["data_contract"]["scenario_data"] = SCENARIO_DATA
    (PACKET / "contract.json").write_text(json.dumps(contract, ensure_ascii=False, indent=2), encoding="utf-8")

    # 2) REF base 조립 + 계약 세계 주입
    ref = BUILD_RUNS / "_multiunit_ref_tmp"
    if ref.exists():
        shutil.rmtree(ref)
    (ref / "src").mkdir(parents=True)
    (ref / "main.js").write_text(REF_MAIN, encoding="utf-8")
    (ref / "src" / "engine.js").write_text(REF_ENGINE, encoding="utf-8")
    (ref / "src" / "game_logic.js").write_text(REF_GAME_LOGIC, encoding="utf-8")
    (ref / "src" / "scenarios.js").write_text(bg._gen_scenarios_module(SCENARIO_DATA), encoding="utf-8")

    # 3) 9세계 실Node 역산 + 적 이동 증명
    out = []
    for i, s in enumerate(SCENARIO_DATA, 1):
        sid = s["id"]
        expected = parse_expected(run(ref, i))
        out.append({"id": sid, "input": {"args": ["--scenario", str(i)]},
                    "covers_reqs": s.get("covers_reqs", []),
                    "expected": expected, "oracle_risk": {"risk": False, "reason": ""}})
        e0 = s["initialState"]["enemies"]
        moved = any(e0[j]["pos"] != expected["enemies"][j]["pos"] for j in range(len(e0)))
        print(f"  {sid} status={expected['status']} hero_hp={expected['hero_hp']} "
              f"적이동={moved}  enemies {[e['pos'] for e in e0]}→{[e['pos'] for e in expected['enemies']]}")

    SPECQA.mkdir(parents=True, exist_ok=True)
    (SPECQA / "acceptance_tests_draft.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    (SPECQA / "oracle_risk_review.json").write_text(json.dumps(
        {"risky_scenarios": [],
         "notes": [{"risk": False, "reason": "다중유닛 적 AI 커널 — 골든은 골렘 룰 인코딩 REF base 실Node 역산(모델 독립)."}]},
        ensure_ascii=False, indent=2), encoding="utf-8")
    shutil.rmtree(ref)
    print(f"\n골든 {len(out)}세계 역산 → {SPECQA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
