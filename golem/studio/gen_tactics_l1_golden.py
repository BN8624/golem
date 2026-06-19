# 전술 카드 l1(변칙검술 마나방패+ANOMALY) 골든 생성기 — base+확장 참조 game_logic을 node로 역산, 회귀 무결 검증(키0)
"""쇼케이스 전술 SRPG 첫 카드. tactics_kernel_base에 마나방패(REQ-012)+ANOMALY 파열(REQ-013)을 더한다.
세계는 planning_packet_tactics_l1/contract.json의 scenario_data가 단일 출처(빌드가 주입할 것과 동일).
골든은 base + 확장 참조 game_logic.js를 실Node로 역산(모델 독립).

흐름:
  1) contract scenario_data로 src/scenarios.js 생성(build_graded._gen_scenarios_module과 동일 함수).
  2) base를 ref로 복사, src/game_logic.js만 확장 참조 버전으로 교체(엔진/메인/시나리오 그대로).
  3) 9세계 node 실행 → expected(5필드). 회귀(001~006, mana 없음)는 base==ref 바이트동일.
     신규(007~009, 마나방패)는 base와 달라야(흡수=hp보존 / 파열=적 추가피해 / 파열킬=인접 전멸).
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE / "tactics_kernel_base"
PACKET = HERE / "planning_packet_tactics_l1"
SPECQA = HERE / "specqa_packet_tactics_l1"

# 확장 참조 game_logic = base + REQ-012 마나방패 + REQ-013 ANOMALY 파열. applyAction의 attack 분기에만 추가.
REF_GAME_LOGIC = """// 전술 커널 규칙 코어 — 액션 적용·상태전이·승패판정. 카드 l1: 마나방패(REQ-012)+ANOMALY 파열(REQ-013) 추가
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

    // REQ-010: Blocked if negative coordinates OR occupied by living enemy
    const isOffGrid = nx < 0 || ny < 0;
    const isOccupied = newState.enemies.some(e => e.hp > 0 && e.pos[0] === nx && e.pos[1] === ny);

    if (!isOffGrid && !isOccupied) {
      newState.hero.pos = [nx, ny];
    }
  } else if (action.type === 'attack') {
    const target = newState.enemies.find(e => e.id === action.target);
    if (target && target.hp > 0) {
      const [hx, hy] = newState.hero.pos;
      const [ex, ey] = target.pos;
      const dist = Math.abs(hx - ex) + Math.abs(hy - ey);

      // REQ-011: Valid attack only if orthogonally adjacent
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

        // REQ-013: ANOMALY rupture when mana crosses >0 -> <=0 in this action
        if (manaBefore > 0 && newState.hero.mana <= 0) {
          const anomaly = newState.hero.anomaly_dmg || 0;
          const [ahx, ahy] = newState.hero.pos;
          for (const e of newState.enemies) {
            if (e.hp > 0 && Math.abs(ahx - e.pos[0]) + Math.abs(ahy - e.pos[1]) === 1) {
              e.hp -= anomaly;
            }
          }
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

REGRESSION = {"SCN-001", "SCN-002", "SCN-003", "SCN-004", "SCN-005", "SCN-006"}
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


def main():
    sys.path.insert(0, str(HERE.parent))
    sys.path.insert(0, str(HERE))
    try:
        from config import force_utf8_stdout
        force_utf8_stdout()
    except Exception:  # noqa: BLE001
        pass

    import build_graded as bg

    contract = json.loads((PACKET / "contract.json").read_text(encoding="utf-8"))
    scenario_data = contract["data_contract"]["scenario_data"]
    scenarios_js = bg._gen_scenarios_module(scenario_data)

    # ref = base + 확장 game_logic + 계약 세계 주입
    ref = HERE / "_tactics_ref_l1_tmp"
    if ref.exists():
        shutil.rmtree(ref)
    shutil.copytree(BASE, ref)
    (ref / "module_manifest.json").unlink(missing_ok=True)
    (ref / "src" / "game_logic.js").write_text(REF_GAME_LOGIC, encoding="utf-8")
    (ref / "src" / "scenarios.js").write_text(scenarios_js, encoding="utf-8")

    # base도 동일 세계로(회귀 바이트동일 대조용). base는 원래 game_logic 유지.
    base_tmp = HERE / "_tactics_base_l1_tmp"
    if base_tmp.exists():
        shutil.rmtree(base_tmp)
    shutil.copytree(BASE, base_tmp)
    (base_tmp / "module_manifest.json").unlink(missing_ok=True)
    (base_tmp / "src" / "scenarios.js").write_text(scenarios_js, encoding="utf-8")

    out = []
    regression_ok = True
    new_fired = 0
    new_total = 0
    for i, s in enumerate(scenario_data, 1):
        sid = s["id"]
        ref_out = run(ref, i)
        base_out = run(base_tmp, i)
        expected = parse_expected(ref_out)
        out.append({"id": sid, "input": {"args": ["--scenario", str(i)]},
                    "covers_reqs": s.get("covers_reqs", []),
                    "expected": expected, "oracle_risk": {"risk": False, "reason": ""}})
        same = base_out == ref_out
        if sid in REGRESSION:
            regression_ok = regression_ok and same
            tag = f"회귀 base==ref:{same}"
        else:
            new_total += 1
            if not same:
                new_fired += 1
            tag = "신규발동" if not same else "신규미발동(?)"
        print(f"  {sid} {tag}  status={expected['status']} hero_hp={expected['hero_hp']} enemies={expected['enemies']}")

    SPECQA.mkdir(parents=True, exist_ok=True)
    (SPECQA / "acceptance_tests_draft.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    (SPECQA / "oracle_risk_review.json").write_text(json.dumps(
        {"risky_scenarios": [],
         "notes": [{"risk": False,
                    "reason": "전 시나리오 oracle_risk.risk=false. 전술 카드 l1(마나방패/ANOMALY) — 골든은 tactics_kernel_base+확장 참조 game_logic 실Node 역산(모델 독립)."}]},
        ensure_ascii=False, indent=2), encoding="utf-8")

    shutil.rmtree(ref)
    shutil.rmtree(base_tmp)
    ok = regression_ok and new_fired == new_total
    print(f"\n회귀 무결: {regression_ok}  신규 발동 {new_fired}/{new_total}  시나리오 {len(out)}개 → {SPECQA}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
