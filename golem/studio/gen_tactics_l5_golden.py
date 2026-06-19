# 전술 카드 l5(루트 맵 route) 골든 생성기 — base+확장 참조 game_logic을 node로 역산, 회귀 무결 검증(키0)
"""쇼케이스 전술 SRPG 다섯째 카드(누적). l4(마나방패+ANOMALY+사거리+지형+유닛) 위에 루트 맵(REQ-018)을 더한다.
route=뒤따르는 전투 목록. 현재 전투 전멸+다음 있으면 updateState가 다음 전투 로드(hero hp/mana 이월·pos [0,0] 리셋).
최종 전투 클리어만 VICTORY. engine.js는 불변(루프 그대로) — 전투 전환은 updateState/checkGameState에만.
세계는 planning_packet_tactics_l5/contract.json의 scenario_data가 단일 출처(빌드 주입과 동일).
회귀(SCN-001~019, route 없음)는 l4 참조의 순수 슈퍼셋이라 자동 동일 — node로 확인.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE / "tactics_kernel_base"
PACKET = HERE / "planning_packet_tactics_l5"
SPECQA = HERE / "specqa_packet_tactics_l5"

# 확장 참조 game_logic = l4 + REQ-018 루트. applyAction는 l4 그대로, updateState/checkGameState만 루트 인지.
REF_GAME_LOGIC = """// 전술 커널 규칙 코어 — 액션 적용·상태전이·승패판정. 카드 l5: l4 위에 루트 맵(전투 체인) 추가. 전환은 updateState에
// REQ-017: 적에 가하는 피해 계산. source = 'melee' | 'ranged' | 'anomaly'
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
      const [hx, hy] = newState.hero.pos;
      const [ex, ey] = target.pos;
      const dist = Math.abs(hx - ex) + Math.abs(hy - ey);

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
          if (newState.terrain && newState.terrain[ahx + ',' + ahy] === 'Conductive') {
            base *= 2;
          }
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
      const [hx, hy] = newState.hero.pos;
      const [ex, ey] = target.pos;
      const dist = Math.abs(hx - ex) + Math.abs(hy - ey);
      if (dist >= 2 && dist <= 3) {
        target.hp -= dmgToEnemy(target, newState.hero.atk, 'ranged');
      }
    }
  }

  return newState;
};

exports.updateState = (state, action) => {
  const nextState = exports.applyAction(state, action);
  // REQ-002: turn = turn + 1 after every action attempt
  nextState.turn += 1;

  // REQ-018: route advance — current battle cleared, hero alive, more battles remain -> load next (no extra turn)
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

  // REQ-006: Both dead -> DEFEAT
  if (heroDead && allEnemiesDead) return 'DEFEAT';
  // REQ-018: VICTORY only when current battle cleared AND no further battles remain
  if (allEnemiesDead && !routeRemaining && initialEnemyCount > 0) return 'VICTORY';
  if (heroDead) return 'DEFEAT';

  return null;
};
"""

# 회귀 = l4의 19세계(route 없음, l4==l5여야). 신규 = 루트 3세계(모두 l4와 달라야).
REGRESSION = {f"SCN-{i:03d}" for i in range(1, 20)}
ROUTE_DIFF = {"SCN-020", "SCN-021", "SCN-022"}
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
    from gen_tactics_l4_golden import REF_GAME_LOGIC as L4_REF

    contract = json.loads((PACKET / "contract.json").read_text(encoding="utf-8"))
    scenario_data = contract["data_contract"]["scenario_data"]
    scenarios_js = bg._gen_scenarios_module(scenario_data)

    ref5 = build_ref("_tactics_ref_l5_tmp", REF_GAME_LOGIC, scenarios_js)
    ref4 = build_ref("_tactics_ref_l4_for_l5_tmp", L4_REF, scenarios_js)

    out = []
    regression_ok = True
    diff_ok = True
    for i, s in enumerate(scenario_data, 1):
        sid = s["id"]
        out5 = run(ref5, i)
        out4 = run(ref4, i)
        expected = parse_expected(out5)
        out.append({"id": sid, "input": {"args": ["--scenario", str(i)]},
                    "covers_reqs": s.get("covers_reqs", []),
                    "expected": expected, "oracle_risk": {"risk": False, "reason": ""}})
        same = out4 == out5
        if sid in REGRESSION:
            regression_ok = regression_ok and same  # route 미사용 = l4 동일(순수 슈퍼셋)
            tag = f"회귀 l4==l5:{same}"
        else:  # ROUTE_DIFF
            diff_ok = diff_ok and (not same)  # 루트가 결과를 바꿔야(l4는 battle0만)
            tag = "루트발동(l4와 다름)" if not same else "루트미발동(?)"
        print(f"  {sid} {tag}  status={expected['status']} turn={expected['turn']} hero_hp={expected['hero_hp']} enemies={expected['enemies']}")

    SPECQA.mkdir(parents=True, exist_ok=True)
    (SPECQA / "acceptance_tests_draft.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    (SPECQA / "oracle_risk_review.json").write_text(json.dumps(
        {"risky_scenarios": [],
         "notes": [{"risk": False,
                    "reason": "전 시나리오 oracle_risk.risk=false. 전술 카드 l5(루트 맵) — 골든은 tactics_kernel_base+확장 참조 game_logic(l4+route) 실Node 역산(모델 독립)."}]},
        ensure_ascii=False, indent=2), encoding="utf-8")

    shutil.rmtree(ref5)
    shutil.rmtree(ref4)
    ok = regression_ok and diff_ok
    print(f"\n회귀 무결(l4==l5): {regression_ok}  루트발동: {diff_ok}  시나리오 {len(out)}개 → {SPECQA}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
