# 전술 카드 l4(유닛 unit_type) 골든 생성기 — base+확장 참조 game_logic을 node로 역산, 회귀 무결 검증(키0)
"""쇼케이스 전술 SRPG 넷째 카드(누적). l3(마나방패+ANOMALY+사거리+지형) 위에 적 unit_type(REQ-017)을 더한다.
Hardened=멜레 -1, Glass=받는 모든 피해 ×2, Resonant=anomaly 맞으면 영웅 1 반사. unit_type은 적 엔티티에 static.
세계는 planning_packet_tactics_l4/contract.json의 scenario_data가 단일 출처(빌드 주입과 동일).
골든은 base + 확장 참조 game_logic.js(l3+units)를 실Node로 역산(모델 독립).
회귀(SCN-001~015, unit_type 없음)는 l3 참조의 순수 슈퍼셋이라 자동 동일 — node로 확인.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE / "tactics_kernel_base"
PACKET = HERE / "planning_packet_tactics_l4"
SPECQA = HERE / "specqa_packet_tactics_l4"

# 확장 참조 game_logic = l3 + REQ-017 적 unit_type(Hardened/Glass/Resonant). applyAction에 피해계산 헬퍼 추가.
REF_GAME_LOGIC = """// 전술 커널 규칙 코어 — 액션 적용·상태전이·승패판정. 카드 l4: l3 위에 적 unit_type(Hardened/Glass/Resonant) 추가
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

    // REQ-010/015: Blocked if negative, occupied by living enemy, or a Wall tile
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

      // REQ-011: Valid melee only if orthogonally adjacent
      if (dist === 1) {
        // REQ-003/017: hero deals melee damage to target (Hardened/Glass), hero receives target.atk
        const incoming = target.atk;
        target.hp -= dmgToEnemy(target, newState.hero.atk, 'melee');

        // REQ-012: Mana Shield absorbs incoming damage first; overflow hits hp
        const manaBefore = newState.hero.mana || 0;
        const absorbed = Math.min(incoming, manaBefore);
        newState.hero.mana = manaBefore - absorbed;
        newState.hero.hp -= (incoming - absorbed);

        // REQ-013/016/017: ANOMALY rupture; Conductive doubles base; Glass doubles per-enemy; Resonant retaliates
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

      // REQ-014/017: one-way damage if 2 <= dist <= 3 (Glass doubles); terrain does not block ranged
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
  return nextState;
};

exports.checkGameState = (state, initialEnemyCount) => {
  const heroDead = state.hero.hp <= 0;
  const allEnemiesDead = state.enemies.every(e => e.hp <= 0);

  // REQ-006: Both dead -> DEFEAT
  if (heroDead && allEnemiesDead) return 'DEFEAT';
  // REQ-007: Initial enemies 0 -> FINISHED, not VICTORY
  if (allEnemiesDead && initialEnemyCount > 0) return 'VICTORY';
  // Only hero dead -> DEFEAT
  if (heroDead) return 'DEFEAT';

  return null;
};
"""

# 회귀 = l3의 15세계(unit_type 없음, l3==l4여야). 신규 = 유닛 4세계(모두 l3와 달라야).
REGRESSION = {f"SCN-{i:03d}" for i in range(1, 16)}
UNIT_DIFF = {"SCN-016", "SCN-017", "SCN-018", "SCN-019"}
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
    from gen_tactics_l3_golden import REF_GAME_LOGIC as L3_REF

    contract = json.loads((PACKET / "contract.json").read_text(encoding="utf-8"))
    scenario_data = contract["data_contract"]["scenario_data"]
    scenarios_js = bg._gen_scenarios_module(scenario_data)

    ref4 = build_ref("_tactics_ref_l4_tmp", REF_GAME_LOGIC, scenarios_js)
    ref3 = build_ref("_tactics_ref_l3_for_l4_tmp", L3_REF, scenarios_js)

    out = []
    regression_ok = True
    diff_ok = True
    for i, s in enumerate(scenario_data, 1):
        sid = s["id"]
        out4 = run(ref4, i)
        out3 = run(ref3, i)
        expected = parse_expected(out4)
        out.append({"id": sid, "input": {"args": ["--scenario", str(i)]},
                    "covers_reqs": s.get("covers_reqs", []),
                    "expected": expected, "oracle_risk": {"risk": False, "reason": ""}})
        same = out3 == out4
        if sid in REGRESSION:
            regression_ok = regression_ok and same  # unit_type 미사용 = l3 동일(순수 슈퍼셋)
            tag = f"회귀 l3==l4:{same}"
        else:  # UNIT_DIFF
            diff_ok = diff_ok and (not same)  # 유닛 특성이 결과를 바꿔야
            tag = "유닛발동(l3와 다름)" if not same else "유닛미발동(?)"
        print(f"  {sid} {tag}  status={expected['status']} hero_hp={expected['hero_hp']} enemies={expected['enemies']}")

    SPECQA.mkdir(parents=True, exist_ok=True)
    (SPECQA / "acceptance_tests_draft.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    (SPECQA / "oracle_risk_review.json").write_text(json.dumps(
        {"risky_scenarios": [],
         "notes": [{"risk": False,
                    "reason": "전 시나리오 oracle_risk.risk=false. 전술 카드 l4(유닛) — 골든은 tactics_kernel_base+확장 참조 game_logic(l3+units) 실Node 역산(모델 독립)."}]},
        ensure_ascii=False, indent=2), encoding="utf-8")

    shutil.rmtree(ref4)
    shutil.rmtree(ref3)
    ok = regression_ok and diff_ok
    print(f"\n회귀 무결(l3==l4): {regression_ok}  유닛발동: {diff_ok}  시나리오 {len(out)}개 → {SPECQA}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
