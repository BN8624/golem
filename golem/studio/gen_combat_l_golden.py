# 전투 카드 l(FATIGUE) 골든 생성기 — 참조 engine(베이스+RULE-11)을 node로 역산, 회귀 무결 검증(키0)
"""고결합 도메인 검증. 골든은 손계산 않고 combat_base + 참조 engine(FATIGUE) 실행으로 역산(모델 독립).

흐름:
  1) combat_base를 ref로 복사, engine.js만 FATIGUE 버전으로 교체.
  2) 시나리오 입력(setup/commands)을 scenarios.json으로 쓰고 node 실행 → expected.
  3) 회귀 시나리오(피로 미발동)는 base==ref 바이트동일 검증. 피로 발동 시나리오는 base와 달라야(죽은코드 아님).
"""

import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE / "combat_base"
SPECQA = HERE / "specqa_packet_combat_l"

# 참조 engine = combat_base 틱 루프 + RULE-11 FATIGUE(틱 끝 energy==0 → hp-3, 그 후 종료판정).
REF_ENGINE = """// 전투 틱 루프 — 독→게이지→행동(player 우선 enemy)→stun감소를 maxTicks까지. 카드는 이 모듈을 편집한다
const C = require('./constants');
const { createInitialState } = require('./state');
const L = require('./unit_logic');

function endCheck(state) {
  const pd = state.player.hp <= 0;
  const ed = state.enemy.hp <= 0;
  if (!pd && !ed) return false;
  state.isGameOver = true;
  state.winner = pd && ed ? 'draw' : pd ? 'enemy' : 'player';
  return true;
}

exports.runScenario = (scenario) => {
  const input = (scenario && scenario.input) || {};
  const commands = input.commands || {};
  const state = createInitialState(input.setup);

  while (!state.isGameOver && state.tick < C.maxTicks) {
    state.tick += 1;

    state.player = L.applyPoison(state.player); // RULE-01
    state.enemy = L.applyPoison(state.enemy);
    if (endCheck(state)) break;

    state.player = L.gainGauge(state.player); // RULE-02
    state.enemy = L.gainGauge(state.enemy);

    if (state.player.gauge >= C.gaugeThreshold) { // RULE-03 player 우선
      const r = L.calculateAction(state.player, state.enemy, commands.player, 'PLAYER');
      state.player = r.actor;
      state.enemy = r.target;
      state.gameLog.push(r.log);
      if (endCheck(state)) break;
    }
    if (state.enemy.gauge >= C.gaugeThreshold) {
      const r = L.calculateAction(state.enemy, state.player, commands.enemy, 'ENEMY');
      state.enemy = r.actor;
      state.player = r.target;
      state.gameLog.push(r.log);
      if (endCheck(state)) break;
    }

    state.player = L.decStun(state.player); // RULE-08
    state.enemy = L.decStun(state.enemy);

    // [RULE-11] FATIGUE — 틱 끝 energy==0 유닛은 hp 3 감소, 그 후 종료판정.
    if (state.player.energy === 0) state.player = { ...state.player, hp: state.player.hp - 3 };
    if (state.enemy.energy === 0) state.enemy = { ...state.enemy, hp: state.enemy.hp - 3 };
    if (endCheck(state)) break;
  }

  if (!state.isGameOver && state.tick >= C.maxTicks) { // RULE-10
    state.isGameOver = true;
    state.winner = 'draw';
  }
  return state;
};
"""

A, M, Wt = "ATTACK", "MOVE", "WAIT"


def scn(sid, reqs, setup, cmds):
    return {"id": sid, "covers_reqs": reqs, "input": {"setup": setup, "commands": cmds}}


SCENARIOS = [
    scn("SCN-001", ["RULE-03", "RULE-04", "RULE-09"],
        {"player": {"pos": 0, "speed": 100}, "enemy": {"pos": 1, "speed": 100}}, {"player": A, "enemy": A}),
    scn("SCN-002", ["RULE-02", "RULE-04"],
        {"player": {"pos": 0, "speed": 30}, "enemy": {"pos": 1, "speed": 30}}, {"player": A, "enemy": A}),
    scn("SCN-003", ["RULE-01", "RULE-09"],
        {"player": {"pos": 0, "speed": 40, "poison": 2}, "enemy": {"pos": 1, "speed": 40}}, {"player": A, "enemy": A}),
    scn("SCN-004", ["RULE-08", "RULE-04"],
        {"player": {"pos": 0, "speed": 50, "stun": 3}, "enemy": {"pos": 1, "speed": 50}}, {"player": A, "enemy": A}),
    scn("SCN-005", ["RULE-05", "RULE-06"],
        {"player": {"pos": 0, "speed": 50}, "enemy": {"pos": 9, "speed": 50}}, {"player": M, "enemy": Wt}),
    scn("SCN-006", ["RULE-06", "RULE-10"],
        {"player": {"pos": 0, "speed": 20}, "enemy": {"pos": 9, "speed": 20}}, {"player": Wt, "enemy": Wt}),
    scn("SCN-007", ["RULE-11", "RULE-05"],
        {"player": {"pos": 0, "speed": 100, "energy": 10, "hp": 10}, "enemy": {"pos": 9, "speed": 5}}, {"player": M, "enemy": Wt}),
    scn("SCN-008", ["RULE-11", "RULE-04"],
        {"player": {"pos": 0, "speed": 60, "energy": 40, "hp": 30}, "enemy": {"pos": 1, "speed": 5, "hp": 200}}, {"player": A, "enemy": Wt}),
]
# 회귀(피로 미발동 기대) = 종료가 빠르거나 에너지 0에 안 닿는 시나리오. 나머지(SCN-007/008)는 피로 발동 기대.
REGRESSION = {"SCN-001", "SCN-002", "SCN-003", "SCN-004", "SCN-006"}

OUTPUT_KEYS = ["tick", "player_hp", "player_energy", "player_gauge", "player_pos",
               "enemy_hp", "enemy_energy", "enemy_gauge", "enemy_pos", "isGameOver", "winner", "logs"]


def run(workdir, idx):
    import subprocess
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
        if k == "logs":
            exp[k] = json.loads(v)
        elif k == "isGameOver":
            exp[k] = (v == "true")
        elif k == "winner":
            exp[k] = None if v == "null" else v
        else:
            exp[k] = int(v)
    return exp


def main():
    sys.path.insert(0, str(HERE.parent))
    try:
        from config import force_utf8_stdout
        force_utf8_stdout()
    except Exception:  # noqa: BLE001
        pass

    ref = HERE / "_combat_ref_tmp"
    if ref.exists():
        shutil.rmtree(ref)
    shutil.copytree(BASE, ref)
    (ref / "src" / "engine.js").write_text(REF_ENGINE, encoding="utf-8")

    inputs = [{"input": s["input"]} for s in SCENARIOS]
    (ref / "scenarios.json").write_text(json.dumps(inputs, ensure_ascii=False), encoding="utf-8")
    (BASE / "scenarios.json").write_text(json.dumps(inputs, ensure_ascii=False), encoding="utf-8")

    out = []
    regression_ok = True
    fatigue_fired = 0
    for i, s in enumerate(SCENARIOS, 1):
        ref_out = run(ref, i)
        base_out = run(BASE, i)
        expected = parse_expected(ref_out)
        out.append({"id": s["id"], "input": s["input"], "covers_reqs": s["covers_reqs"],
                    "expected": expected, "oracle_risk": {"risk": False, "reason": ""}})
        same = base_out == ref_out
        if not same:
            fatigue_fired += 1
        if s["id"] in REGRESSION:
            regression_ok = regression_ok and same
        print(f"  {s['id']} {'회귀 base==ref:'+str(same) if s['id'] in REGRESSION else ('FATIGUE발동' if not same else 'FATIGUE미발동(?)')}"
              f"  winner={expected['winner']} tick={expected['tick']}")

    SPECQA.mkdir(parents=True, exist_ok=True)
    (SPECQA / "acceptance_tests_draft.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    (SPECQA / "oracle_risk_review.json").write_text(json.dumps(
        {"risky_scenarios": [],
         "notes": [{"risk": False,
                    "reason": "전 시나리오 oracle_risk.risk=false. 고결합 전투 카드 — 골든은 combat_base+참조 engine(FATIGUE) 실Node 역산(모델 독립)."}]},
        ensure_ascii=False, indent=2), encoding="utf-8")

    (BASE / "scenarios.json").unlink(missing_ok=True)
    shutil.rmtree(ref)
    print(f"\n회귀 무결: {regression_ok}  FATIGUE 발동 {fatigue_fired}개  시나리오 {len(out)}개 → {SPECQA}")
    return 0 if (regression_ok and fatigue_fired > 0) else 1


if __name__ == "__main__":
    raise SystemExit(main())
