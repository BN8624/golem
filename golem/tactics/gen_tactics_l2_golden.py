# 전술 카드 l2(사거리 ranged_attack) 골든 생성기 — base+확장 참조 game_logic을 node로 역산, 회귀 무결 검증(키0)
"""쇼케이스 전술 SRPG 둘째 카드(누적). l1(마나방패+ANOMALY) 위에 사거리(REQ-014)를 더한다.
ranged_attack은 맨해튼 거리 2..3의 적에 일방 피해(영웅 무피해→마나/파열 무관). 인접/사거리밖은 no-op.
세계는 planning_packet_tactics_l2/contract.json의 scenario_data가 단일 출처(빌드 주입과 동일).
골든은 base + 확장 참조 game_logic.js를 실Node로 역산(모델 독립).

회귀(SCN-001~009: 멜레 6 + 마나방패 3)는 base==ref 바이트동일이 아니라, l1 참조와 동일해야 한다 →
여기선 base(원커널)와 비교하면 마나 세계가 갈리므로, 회귀 무결은 "ranged 미사용 세계에서 l1 확장참조 == l2 확장참조"로 본다.
구현상 l2 참조는 l1 참조의 순수 슈퍼셋(ranged 분기만 추가)이라 ranged 미사용 세계는 자동 동일 — node로 확인.
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
PACKET = PACKETS / "planning_packet_tactics_l2"
SPECQA = PACKETS / "specqa_packet_tactics_l2"
L1_PACKET = PACKETS / "planning_packet_tactics_l1"

# 확장 참조 game_logic = l1(마나방패+ANOMALY) + REQ-014 사거리. applyAction에 ranged_attack 분기만 추가.
REF_GAME_LOGIC = """// 전술 커널 규칙 코어 — 액션 적용·상태전이·승패판정. 카드 l2: l1(마나방패+ANOMALY) 위에 사거리(REQ-014) 추가
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
  } else if (action.type === 'ranged_attack') {
    const target = newState.enemies.find(e => e.id === action.target);
    if (target && target.hp > 0) {
      const [hx, hy] = newState.hero.pos;
      const [ex, ey] = target.pos;
      const dist = Math.abs(hx - ex) + Math.abs(hy - ey);

      // REQ-014: one-way damage if 2 <= dist <= 3; hero takes nothing, mana untouched (no rupture)
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

# 회귀 = l1의 9세계(멜레 6 + 마나방패 3). 신규 = 사거리 3세계.
REGRESSION = {f"SCN-{i:03d}" for i in range(1, 10)}
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
    from gen_tactics_l1_golden import REF_GAME_LOGIC as L1_REF

    contract = json.loads((PACKET / "contract.json").read_text(encoding="utf-8"))
    scenario_data = contract["data_contract"]["scenario_data"]
    scenarios_js = bg._gen_scenarios_module(scenario_data)

    # l2 확장 참조 + l1 참조(회귀 동일성 대조: ranged 미사용 세계는 l1==l2여야 함)
    ref2 = build_ref("_tactics_ref_l2_tmp", REF_GAME_LOGIC, scenarios_js)
    ref1 = build_ref("_tactics_ref_l1_for_l2_tmp", L1_REF, scenarios_js)

    out = []
    regression_ok = True
    new_fired = 0
    new_total = 0
    for i, s in enumerate(scenario_data, 1):
        sid = s["id"]
        out2 = run(ref2, i)
        out1 = run(ref1, i)
        expected = parse_expected(out2)
        out.append({"id": sid, "input": {"args": ["--scenario", str(i)]},
                    "covers_reqs": s.get("covers_reqs", []),
                    "expected": expected, "oracle_risk": {"risk": False, "reason": ""}})
        same = out1 == out2
        if sid in REGRESSION:
            regression_ok = regression_ok and same  # l1 미사용 분기 = l2 동일(순수 슈퍼셋)
            tag = f"회귀 l1==l2:{same}"
        else:
            new_total += 1
            if out1 != out2:  # 신규는 ranged 분기라 l1(분기없음)과 달라야
                new_fired += 1
            tag = "신규발동" if out1 != out2 else "신규미발동(?)"
        print(f"  {sid} {tag}  status={expected['status']} hero_hp={expected['hero_hp']} enemies={expected['enemies']}")

    SPECQA.mkdir(parents=True, exist_ok=True)
    (SPECQA / "acceptance_tests_draft.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    (SPECQA / "oracle_risk_review.json").write_text(json.dumps(
        {"risky_scenarios": [],
         "notes": [{"risk": False,
                    "reason": "전 시나리오 oracle_risk.risk=false. 전술 카드 l2(사거리) — 골든은 tactics_kernel_base+확장 참조 game_logic(l1+ranged) 실Node 역산(모델 독립)."}]},
        ensure_ascii=False, indent=2), encoding="utf-8")

    shutil.rmtree(ref2)
    shutil.rmtree(ref1)
    ok = regression_ok and new_fired == new_total
    print(f"\n회귀 무결(l1==l2): {regression_ok}  신규 발동 {new_fired}/{new_total}  시나리오 {len(out)}개 → {SPECQA}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
