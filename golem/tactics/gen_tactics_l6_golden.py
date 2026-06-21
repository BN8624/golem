# 전술 카드 l6(상태이상 Corrosion) 골든 생성기 — base+확장 참조 game_logic을 node로 역산, 회귀 무결 검증(키0)
"""쇼케이스 전술 SRPG 여섯째 카드(누적). l5 위에 Corrosion DoT(REQ-019)를 더한다.
hero.corrosion={dmg,duration} 있으면 ranged_attack가 적에 Corrosion 부여, 매 행동 끝(루트 전환 전)에 1틱·duration 감소(Glass ×2).
hero.corrosion 없으면 ranged 그대로 → l5 회귀 바이트동일. 세계는 contract scenario_data 단일 출처.
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
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = BASES / "tactics_kernel_base"
PACKET = PACKETS / "planning_packet_tactics_l6"
SPECQA = PACKETS / "specqa_packet_tactics_l6"

# 확장 참조 = l5 + REQ-019 Corrosion. applyAction의 ranged 분기에 부여, updateState에 틱(루트 전환 전).
REF_GAME_LOGIC = """// 전술 커널 규칙 코어 — 카드 l6: l5 위에 Corrosion DoT 추가(ranged 부여·매 행동 끝 틱, 루트 전환 전). 적은 여전히 수동
function dmgToEnemy(enemy, base, source) {
  let d = base;
  if (source === 'melee' && enemy.unit_type === 'Hardened') d = Math.max(0, d - 1);
  if (enemy.unit_type === 'Glass') d *= 2;
  return d;
}

exports.applyAction = (state, action) => {
  const newState = {
    ...state,
    hero: { ...state.hero, pos: [...state.hero.pos] },
    enemies: state.enemies.map(e => ({ ...e, pos: [...e.pos] })),
    turn: state.turn
  };

  if (action.type === 'move') {
    const [dx, dy] = action.dir;
    const [cx, cy] = newState.hero.pos;
    const nx = cx + dx;
    const ny = cy + dy;
    const isOffGrid = nx < 0 || ny < 0;
    const isOccupied = newState.enemies.some(e => e.hp > 0 && e.pos[0] === nx && e.pos[1] === ny);
    const isWall = !!(newState.terrain && newState.terrain[nx + ',' + ny] === 'Wall');
    if (!isOffGrid && !isOccupied && !isWall) {
      newState.hero.pos = [nx, ny];
    }
  } else if (action.type === 'attack') {
    const target = newState.enemies.find(e => e.id === action.target);
    if (target && target.hp > 0) {
      const dist = Math.abs(newState.hero.pos[0] - target.pos[0]) + Math.abs(newState.hero.pos[1] - target.pos[1]);
      if (dist === 1) {
        const incoming = target.atk;
        target.hp -= dmgToEnemy(target, newState.hero.atk, 'melee');
        const manaBefore = newState.hero.mana || 0;
        const absorbed = Math.min(incoming, manaBefore);
        newState.hero.mana = manaBefore - absorbed;
        newState.hero.hp -= (incoming - absorbed);
        if (manaBefore > 0 && newState.hero.mana <= 0) {
          const [ahx, ahy] = newState.hero.pos;
          let base = newState.hero.anomaly_dmg || 0;
          if (newState.terrain && newState.terrain[ahx + ',' + ahy] === 'Conductive') base *= 2;
          for (const e of newState.enemies) {
            if (e.hp > 0 && Math.abs(ahx - e.pos[0]) + Math.abs(ahy - e.pos[1]) === 1) {
              e.hp -= dmgToEnemy(e, base, 'anomaly');
              if (e.unit_type === 'Resonant') newState.hero.hp -= 1;
            }
          }
        }
      }
    }
  } else if (action.type === 'ranged_attack') {
    const target = newState.enemies.find(e => e.id === action.target);
    if (target && target.hp > 0) {
      const dist = Math.abs(newState.hero.pos[0] - target.pos[0]) + Math.abs(newState.hero.pos[1] - target.pos[1]);
      if (dist >= 2 && dist <= 3) {
        target.hp -= dmgToEnemy(target, newState.hero.atk, 'ranged');
        // REQ-019: ranged inflicts Corrosion if the hero has the capability
        if (newState.hero.corrosion) {
          target.status = { type: 'Corrosion', duration: newState.hero.corrosion.duration, dmg: newState.hero.corrosion.dmg };
        }
      }
    }
  }

  return newState;
};

exports.updateState = (state, action) => {
  const nextState = exports.applyAction(state, action);
  // REQ-002: turn = turn + 1 after every action attempt
  nextState.turn += 1;

  // REQ-019: Corrosion ticks at end of every action (before route advance / win-loss check)
  for (const e of nextState.enemies) {
    if (e.hp > 0 && e.status && e.status.type === 'Corrosion' && e.status.duration > 0) {
      e.hp -= e.status.dmg * (e.unit_type === 'Glass' ? 2 : 1);
      e.status = { ...e.status, duration: e.status.duration - 1 };
      if (e.status.duration <= 0) delete e.status;
    }
  }

  // REQ-018: route advance — current battle cleared, hero alive, more battles remain
  if (nextState.hero.hp > 0 && Array.isArray(nextState.route)) {
    const idx = nextState.route_index || 0;
    const allDead = nextState.enemies.every(e => e.hp <= 0);
    if (allDead && idx < nextState.route.length) {
      const battle = nextState.route[idx];
      nextState.enemies = battle.enemies.map(e => ({ ...e, pos: [...e.pos] }));
      nextState.terrain = battle.terrain || undefined;
      nextState.hero = { ...nextState.hero, pos: [0, 0] };
      nextState.route_index = idx + 1;
    }
  }
  return nextState;
};

exports.checkGameState = (state, initialEnemyCount) => {
  const heroDead = state.hero.hp <= 0;
  const allEnemiesDead = state.enemies.every(e => e.hp <= 0);
  const routeRemaining = Array.isArray(state.route) && (state.route_index || 0) < state.route.length;
  if (heroDead && allEnemiesDead) return 'DEFEAT';
  if (allEnemiesDead && !routeRemaining && initialEnemyCount > 0) return 'VICTORY';
  if (heroDead) return 'DEFEAT';
  return null;
};
"""

REGRESSION = {f"SCN-{i:03d}" for i in range(1, 23)}
STATUS_DIFF = {"SCN-023", "SCN-024", "SCN-025"}
OUTPUT_KEYS = ["status", "turn", "hero_hp", "hero_pos", "enemies"]


def run(workdir, idx):
    r = subprocess.run(["node", "main.js", "--scenario", str(idx)], cwd=str(workdir),
                       capture_output=True, text=True, encoding="utf-8", timeout=30, stdin=subprocess.DEVNULL)
    if r.returncode != 0:
        raise RuntimeError(f"node 실패 scn{idx}: {r.stderr[:200]}")
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
        elif k in ("hero_pos", "enemies"):
            exp[k] = json.loads(v)
        elif k == "hero_hp":
            exp[k] = int(v)
        else:
            exp[k] = v
    return exp


def build_ref(name, game_logic_src, scenarios_js):
    ref = HERE / name
    if ref.exists():
        shutil.rmtree(ref)
    shutil.copytree(BASE, ref)
    (ref / "module_manifest.json").unlink(missing_ok=True)
    (ref / "src" / "game_logic.js").write_text(game_logic_src, encoding="utf-8")
    (ref / "src" / "scenarios.js").write_text(scenarios_js, encoding="utf-8")
    return ref


def main():
    sys.path.insert(0, str(HERE.parent))
    sys.path.insert(0, str(HERE))
    try:
        from config import force_utf8_stdout
        force_utf8_stdout()
    except Exception:  # noqa: BLE001
        pass

    import build_graded as bg
    from gen_tactics_l5_golden import REF_GAME_LOGIC as L5_REF

    contract = json.loads((PACKET / "contract.json").read_text(encoding="utf-8"))
    scenario_data = contract["data_contract"]["scenario_data"]
    scenarios_js = bg._gen_scenarios_module(scenario_data)

    ref6 = build_ref("_tactics_ref_l6_tmp", REF_GAME_LOGIC, scenarios_js)
    ref5 = build_ref("_tactics_ref_l5_for_l6_tmp", L5_REF, scenarios_js)

    out = []
    regression_ok = True
    diff_ok = True
    for i, s in enumerate(scenario_data, 1):
        sid = s["id"]
        out6 = run(ref6, i)
        out5 = run(ref5, i)
        expected = parse_expected(out6)
        out.append({"id": sid, "input": {"args": ["--scenario", str(i)]},
                    "covers_reqs": s.get("covers_reqs", []),
                    "expected": expected, "oracle_risk": {"risk": False, "reason": ""}})
        same = out5 == out6
        if sid in REGRESSION:
            regression_ok = regression_ok and same
            tag = f"회귀 l5==l6:{same}"
        else:
            diff_ok = diff_ok and (not same)
            tag = "상태이상발동(l5와 다름)" if not same else "상태이상미발동(?)"
        print(f"  {sid} {tag}  status={expected['status']} turn={expected['turn']} hero_hp={expected['hero_hp']} enemies={expected['enemies']}")

    SPECQA.mkdir(parents=True, exist_ok=True)
    (SPECQA / "acceptance_tests_draft.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    (SPECQA / "oracle_risk_review.json").write_text(json.dumps(
        {"risky_scenarios": [],
         "notes": [{"risk": False,
                    "reason": "전 시나리오 oracle_risk.risk=false. 전술 카드 l6(상태이상 Corrosion) — 골든은 tactics_kernel_base+확장 참조 game_logic(l5+corrosion) 실Node 역산(모델 독립)."}]},
        ensure_ascii=False, indent=2), encoding="utf-8")

    shutil.rmtree(ref6)
    shutil.rmtree(ref5)
    ok = regression_ok and diff_ok
    print(f"\n회귀 무결(l5==l6): {regression_ok}  상태이상발동: {diff_ok}  시나리오 {len(out)}개 → {SPECQA}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
