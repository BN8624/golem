# 전술 카드 l7(밸런스 config) 골든 생성기 — base+확장 참조 game_logic을 node로 역산, 회귀 무결 검증(키0)
"""쇼케이스 전술 SRPG 일곱째 카드(누적). l6 위에 밸런스 config(REQ-020)를 더한다.
config={atkMult,recMult,anomMult}(기본 1)가 영웅 행동 해석 안에서 floor 배율로 적용. 없으면 ×1 → l6 바이트동일.
세계는 contract scenario_data 단일 출처. 골든은 base+확장 참조(l6+config) 실Node 역산(모델 독립).
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE / "tactics_kernel_base"
PACKET = HERE / "planning_packet_tactics_l7"
SPECQA = HERE / "specqa_packet_tactics_l7"

# 확장 참조 = l6 + REQ-020 config 배율(floor). 적용 지점: 가하는 피해(atkMult)·anomaly(anomMult)·받는 피해(recMult).
REF_GAME_LOGIC = """// 전술 커널 규칙 코어 — 카드 l7: l6 위에 밸런스 config(atkMult/recMult/anomMult, floor) 추가. 적은 여전히 수동
function dmgToEnemy(enemy, base, source) {
  let d = base;
  if (source === 'melee' && enemy.unit_type === 'Hardened') d = Math.max(0, d - 1);
  if (enemy.unit_type === 'Glass') d *= 2;
  return d;
}
function mults(state) {
  const c = state.config || {};
  return {
    atk: c.atkMult != null ? c.atkMult : 1,
    rec: c.recMult != null ? c.recMult : 1,
    anom: c.anomMult != null ? c.anomMult : 1
  };
}

exports.applyAction = (state, action) => {
  const newState = {
    ...state,
    hero: { ...state.hero, pos: [...state.hero.pos] },
    enemies: state.enemies.map(e => ({ ...e, pos: [...e.pos] })),
    turn: state.turn
  };
  const m = mults(newState);

  if (action.type === 'move') {
    const [dx, dy] = action.dir;
    const [cx, cy] = newState.hero.pos;
    const nx = cx + dx, ny = cy + dy;
    const isOffGrid = nx < 0 || ny < 0;
    const isOccupied = newState.enemies.some(e => e.hp > 0 && e.pos[0] === nx && e.pos[1] === ny);
    const isWall = !!(newState.terrain && newState.terrain[nx + ',' + ny] === 'Wall');
    if (!isOffGrid && !isOccupied && !isWall) newState.hero.pos = [nx, ny];
  } else if (action.type === 'attack') {
    const target = newState.enemies.find(e => e.id === action.target);
    if (target && target.hp > 0) {
      const dist = Math.abs(newState.hero.pos[0] - target.pos[0]) + Math.abs(newState.hero.pos[1] - target.pos[1]);
      if (dist === 1) {
        // REQ-017/020: melee base = floor(atk*atkMult), then unit_type
        target.hp -= dmgToEnemy(target, Math.floor(newState.hero.atk * m.atk), 'melee');
        // REQ-020: incoming = floor(enemy.atk*recMult)
        const incoming = Math.floor(target.atk * m.rec);
        const manaBefore = newState.hero.mana || 0;
        const absorbed = Math.min(incoming, manaBefore);
        newState.hero.mana = manaBefore - absorbed;
        newState.hero.hp -= (incoming - absorbed);
        if (manaBefore > 0 && newState.hero.mana <= 0) {
          const [ahx, ahy] = newState.hero.pos;
          // REQ-016/020: base anomaly = floor(anomaly_dmg*anomMult), then Conductive
          let base = Math.floor((newState.hero.anomaly_dmg || 0) * m.anom);
          if (newState.terrain && newState.terrain[ahx + ',' + ahy] === 'Conductive') base *= 2;
          for (const e of newState.enemies) {
            if (e.hp > 0 && Math.abs(ahx - e.pos[0]) + Math.abs(ahy - e.pos[1]) === 1) {
              e.hp -= dmgToEnemy(e, base, 'anomaly');
              if (e.unit_type === 'Resonant') newState.hero.hp -= Math.floor(1 * m.rec);
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
        target.hp -= dmgToEnemy(target, Math.floor(newState.hero.atk * m.atk), 'ranged');
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
  nextState.turn += 1;
  const m = mults(nextState);

  // REQ-019/020: Corrosion tick = floor(status.dmg*atkMult)*(Glass?2:1), before route advance
  for (const e of nextState.enemies) {
    if (e.hp > 0 && e.status && e.status.type === 'Corrosion' && e.status.duration > 0) {
      e.hp -= Math.floor(e.status.dmg * m.atk) * (e.unit_type === 'Glass' ? 2 : 1);
      e.status = { ...e.status, duration: e.status.duration - 1 };
      if (e.status.duration <= 0) delete e.status;
    }
  }

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

REGRESSION = {f"SCN-{i:03d}" for i in range(1, 26)}
CONFIG_DIFF = {"SCN-026", "SCN-027", "SCN-028"}
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
    from gen_tactics_l6_golden import REF_GAME_LOGIC as L6_REF

    contract = json.loads((PACKET / "contract.json").read_text(encoding="utf-8"))
    scenario_data = contract["data_contract"]["scenario_data"]
    scenarios_js = bg._gen_scenarios_module(scenario_data)

    ref7 = build_ref("_tactics_ref_l7_tmp", REF_GAME_LOGIC, scenarios_js)
    ref6 = build_ref("_tactics_ref_l6_for_l7_tmp", L6_REF, scenarios_js)

    out = []
    regression_ok = True
    diff_ok = True
    for i, s in enumerate(scenario_data, 1):
        sid = s["id"]
        out7 = run(ref7, i)
        out6 = run(ref6, i)
        expected = parse_expected(out7)
        out.append({"id": sid, "input": {"args": ["--scenario", str(i)]},
                    "covers_reqs": s.get("covers_reqs", []),
                    "expected": expected, "oracle_risk": {"risk": False, "reason": ""}})
        same = out6 == out7
        if sid in REGRESSION:
            regression_ok = regression_ok and same
            tag = f"회귀 l6==l7:{same}"
        else:
            diff_ok = diff_ok and (not same)
            tag = "config발동(l6와 다름)" if not same else "config미발동(?)"
        print(f"  {sid} {tag}  status={expected['status']} hero_hp={expected['hero_hp']} enemies={expected['enemies']}")

    SPECQA.mkdir(parents=True, exist_ok=True)
    (SPECQA / "acceptance_tests_draft.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    (SPECQA / "oracle_risk_review.json").write_text(json.dumps(
        {"risky_scenarios": [],
         "notes": [{"risk": False,
                    "reason": "전 시나리오 oracle_risk.risk=false. 전술 카드 l7(밸런스 config) — 골든은 tactics_kernel_base+확장 참조 game_logic(l6+config) 실Node 역산(모델 독립)."}]},
        ensure_ascii=False, indent=2), encoding="utf-8")

    shutil.rmtree(ref7)
    shutil.rmtree(ref6)
    ok = regression_ok and diff_ok
    print(f"\n회귀 무결(l6==l7): {regression_ok}  config발동: {diff_ok}  시나리오 {len(out)}개 → {SPECQA}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
