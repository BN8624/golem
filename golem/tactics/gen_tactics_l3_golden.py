# 전술 카드 l3(지형 terrain) 골든 생성기 — base+확장 참조 game_logic을 node로 역산, 회귀 무결 검증(키0)
"""쇼케이스 전술 SRPG 셋째 카드(누적). l2(마나방패+ANOMALY+사거리) 위에 지형(REQ-015/016)을 더한다.
Wall=이동 차단(사거리는 무시), Conductive=영웅이 그 위에서 파열시 anomaly_dmg ×2. terrain은 initialState에 static.
세계는 planning_packet_tactics_l3/contract.json의 scenario_data가 단일 출처(빌드 주입과 동일).
골든은 base + 확장 참조 game_logic.js(l2+terrain)를 실Node로 역산(모델 독립).
회귀(SCN-001~012, terrain 없음)는 l2 참조의 순수 슈퍼셋이라 자동 동일 — node로 확인.
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
PACKET = PACKETS / "planning_packet_tactics_l3"
SPECQA = PACKETS / "specqa_packet_tactics_l3"

# 확장 참조 game_logic = l2(마나방패+ANOMALY+사거리) + REQ-015 Wall(이동 차단) + REQ-016 Conductive(anomaly ×2).
REF_GAME_LOGIC = """// 전술 커널 규칙 코어 — 액션 적용·상태전이·승패판정. 카드 l3: l2 위에 지형(Wall 이동차단·Conductive anomaly×2) 추가
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
        // REQ-003: hero deals hero.atk to target; hero receives target.atk (mediated by shield)
        const heroAtk = newState.hero.atk;
        const incoming = target.atk;
        target.hp -= heroAtk;

        // REQ-012: Mana Shield absorbs incoming damage first; overflow hits hp
        const manaBefore = newState.hero.mana || 0;
        const absorbed = Math.min(incoming, manaBefore);
        newState.hero.mana = manaBefore - absorbed;
        newState.hero.hp -= (incoming - absorbed);

        // REQ-013/016: ANOMALY rupture; Conductive tile under hero doubles anomaly damage
        if (manaBefore > 0 && newState.hero.mana <= 0) {
          const [ahx, ahy] = newState.hero.pos;
          let anomaly = newState.hero.anomaly_dmg || 0;
          if (newState.terrain && newState.terrain[ahx + ',' + ahy] === 'Conductive') {
            anomaly *= 2;
          }
          for (const e of newState.enemies) {
            if (e.hp > 0 && Math.abs(ahx - e.pos[0]) + Math.abs(ahy - e.pos[1]) === 1) {
              e.hp -= anomaly;
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

      // REQ-014: one-way damage if 2 <= dist <= 3; terrain does NOT block ranged (no line-of-sight)
      if (dist >= 2 && dist <= 3) {
        target.hp -= newState.hero.atk;
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

# 회귀 = l2의 12세계(terrain 없음, l2==l3여야). 지형 세계 분류:
#  TERRAIN_DIFF = 지형이 결과를 바꿔 l2와 달라야(Wall 이동차단·Conductive ×2).
#  TERRAIN_SAME = 지형이 있어도 l2와 같아야(Wall은 사거리 무시 — 음성 테스트, 모델이 ranged에 벽 적용하면 잡힘).
REGRESSION = {f"SCN-{i:03d}" for i in range(1, 13)}
TERRAIN_DIFF = {"SCN-013", "SCN-014"}
TERRAIN_SAME = {"SCN-015"}
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
    from gen_tactics_l2_golden import REF_GAME_LOGIC as L2_REF

    contract = json.loads((PACKET / "contract.json").read_text(encoding="utf-8"))
    scenario_data = contract["data_contract"]["scenario_data"]
    scenarios_js = bg._gen_scenarios_module(scenario_data)

    ref3 = build_ref("_tactics_ref_l3_tmp", REF_GAME_LOGIC, scenarios_js)
    ref2 = build_ref("_tactics_ref_l2_for_l3_tmp", L2_REF, scenarios_js)

    out = []
    regression_ok = True
    diff_ok = True
    same_ok = True
    for i, s in enumerate(scenario_data, 1):
        sid = s["id"]
        out3 = run(ref3, i)
        out2 = run(ref2, i)
        expected = parse_expected(out3)
        out.append({"id": sid, "input": {"args": ["--scenario", str(i)]},
                    "covers_reqs": s.get("covers_reqs", []),
                    "expected": expected, "oracle_risk": {"risk": False, "reason": ""}})
        same = out2 == out3
        if sid in REGRESSION:
            regression_ok = regression_ok and same  # terrain 미사용 = l2 동일(순수 슈퍼셋)
            tag = f"회귀 l2==l3:{same}"
        elif sid in TERRAIN_DIFF:
            diff_ok = diff_ok and (not same)  # 지형이 결과를 바꿔야
            tag = "지형발동(l2와 다름)" if not same else "지형미발동(?)"
        else:  # TERRAIN_SAME
            same_ok = same_ok and same  # 지형 있어도 l2와 같아야(Wall은 ranged 무시)
            tag = "지형중립(ranged 벽무시, l2와 같음)" if same else "지형오작동(?)"
        print(f"  {sid} {tag}  status={expected['status']} hero_hp={expected['hero_hp']} hero_pos={expected['hero_pos']} enemies={expected['enemies']}")

    SPECQA.mkdir(parents=True, exist_ok=True)
    (SPECQA / "acceptance_tests_draft.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    (SPECQA / "oracle_risk_review.json").write_text(json.dumps(
        {"risky_scenarios": [],
         "notes": [{"risk": False,
                    "reason": "전 시나리오 oracle_risk.risk=false. 전술 카드 l3(지형) — 골든은 tactics_kernel_base+확장 참조 game_logic(l2+terrain) 실Node 역산(모델 독립)."}]},
        ensure_ascii=False, indent=2), encoding="utf-8")

    shutil.rmtree(ref3)
    shutil.rmtree(ref2)
    ok = regression_ok and diff_ok and same_ok
    print(f"\n회귀 무결(l2==l3): {regression_ok}  지형발동: {diff_ok}  지형중립(벽 ranged무시): {same_ok}  시나리오 {len(out)}개 → {SPECQA}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
