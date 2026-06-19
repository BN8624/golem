# 소코반 카드 l3(구덩이 O) 골든 생성기 — 카드2 위에 누적, 회귀 무결 검증(키0)
"""쇼케이스 새 장르 카드3(누적). 카드2(텔레포트) 위에 구덩이(O) 메커니즘과 그 레벨을 더한다.
상자를 구덩이로 밀어넣으면 구덩이가 메워지고(상자 소멸·O→바닥) 길이 열린다. 골든은 base+카드1~3 참조 실Node 역산.
"""

import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE / "sokoban_base"
SPECQA = HERE / "specqa_packet_sokoban_l3"

import gen_sokoban_l1_golden as L1  # noqa: E402  (헬퍼)
import gen_sokoban_l2_golden as L2  # noqa: E402  (prev 참조 + 시나리오 누적)

# cur move_logic = 카드2(문/열쇠/텔레포트) + 구덩이(상자를 O로 밀면 메워짐).
REF_MOVE_LOGIC = """// 한 번의 이동 해석(규칙 코어) — 벽·상자 밀기를 처리하고 결과 로그를 반환한다. 카드는 이 모듈에 새 타일 규칙을 더한다
const { DIRS } = require('./constants');

const key = (r, c) => r + ',' + c;

function boxIndexAt(state, r, c) {
  for (let i = 0; i < state.boxes.length; i++) {
    if (state.boxes[i][0] === r && state.boxes[i][1] === c) return i;
  }
  return -1;
}

function doorClosed(state, r, c) {
  return state.tiles[key(r, c)] === 'D' && !state.hasKey;
}

function enter(state, r, c) {
  const p = key(r, c);
  if (state.tiles[p] === 'K') { state.hasKey = true; delete state.tiles[p]; return '+key'; }
  return '';
}

function teleport(state, r, c) {
  if (state.tiles[key(r, c)] !== 'T') return '';
  for (const p in state.tiles) {
    if (state.tiles[p] === 'T' && p !== key(r, c)) {
      const parts = p.split(',');
      state.player = [parseInt(parts[0], 10), parseInt(parts[1], 10)];
      return '+tp';
    }
  }
  return '';
}

exports.resolveMove = (state, dir) => {
  const d = DIRS[dir];
  if (!d) return dir + ':none';
  const [pr, pc] = state.player;
  const nr = pr + d[0];
  const nc = pc + d[1];
  if (state.walls[key(nr, nc)] || doorClosed(state, nr, nc)) return dir + ':block';

  const bi = boxIndexAt(state, nr, nc);
  if (bi >= 0) {
    const br = nr + d[0];
    const bc = nc + d[1];
    if (state.walls[key(br, bc)] || doorClosed(state, br, bc) || boxIndexAt(state, br, bc) >= 0) return dir + ':block';
    if (state.tiles[key(br, bc)] === 'O') { // 구덩이에 밀어넣으면 메워진다(상자 소멸, O→바닥)
      state.boxes.splice(bi, 1);
      delete state.tiles[key(br, bc)];
      state.player = [nr, nc];
      return dir + ':fill';
    }
    state.boxes[bi] = [br, bc];
    state.player = [nr, nc];
    return dir + ':push' + enter(state, nr, nc);
  }

  state.player = [nr, nc];
  let suf = enter(state, nr, nc);
  suf += teleport(state, nr, nc);
  return dir + ':move' + suf;
};

exports.boxIndexAt = boxIndexAt;
"""

# 레벨(L_hole 포함)은 sokoban_base에 고정. 카드3은 move_logic(구덩이)만 키운다.

SCENARIOS = L2.SCENARIOS + [
    L1.scn("SCN-012", ["RULE-08"], "L_hole", ["R", "R", "R", "R"]),  # 구덩이 메우고 다리 삼아 밀어 승리
    L1.scn("SCN-013", ["RULE-08"], "L_hole", ["R"]),                # 구덩이 메우기(중간 상태)
]
NEW = {"SCN-012", "SCN-013"}


def main():
    sys.path.insert(0, str(HERE.parent))
    try:
        from config import force_utf8_stdout
        force_utf8_stdout()
    except Exception:  # noqa: BLE001
        pass

    prev = L1.build_ref("_sokoban_ref_l2_prev_tmp", L2.REF_MOVE_LOGIC)
    cur = L1.build_ref("_sokoban_ref_l3_tmp", REF_MOVE_LOGIC)

    inputs = [{"input": s["input"]} for s in SCENARIOS]
    for d in (prev, cur):
        (d / "scenarios.json").write_text(json.dumps(inputs, ensure_ascii=False), encoding="utf-8")

    out = []
    regression_ok = True
    new_fired = 0
    for i, s in enumerate(SCENARIOS, 1):
        prev_out = L1.run(prev, i)
        cur_out = L1.run(cur, i)
        expected = L1.parse_expected(cur_out)
        out.append({"id": s["id"], "input": s["input"], "covers_reqs": s["covers_reqs"],
                    "expected": expected, "oracle_risk": {"risk": False, "reason": ""}})
        same = prev_out == cur_out
        if s["id"] in NEW:
            if not same:
                new_fired += 1
        else:
            regression_ok = regression_ok and same
        tag = ("신규발동" if not same else "신규미발동(?)") if s["id"] in NEW else ("회귀 prev==cur:" + str(same))
        print(f"  {s['id']} {tag}  isWon={expected['isWon']} logs={expected['logs']}")

    SPECQA.mkdir(parents=True, exist_ok=True)
    (SPECQA / "acceptance_tests_draft.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    (SPECQA / "oracle_risk_review.json").write_text(json.dumps(
        {"risky_scenarios": [],
         "notes": [{"risk": False,
                    "reason": "전 시나리오 oracle_risk.risk=false. 소코반 카드3(구덩이, 누적) — 골든은 base+카드1~3 참조 실Node 역산(모델 독립)."}]},
        ensure_ascii=False, indent=2), encoding="utf-8")

    shutil.rmtree(prev)
    shutil.rmtree(cur)
    print(f"\n회귀 무결(prev==cur): {regression_ok}  신규 발동 {new_fired}/{len(NEW)}  시나리오 {len(out)}개 → {SPECQA}")
    return 0 if (regression_ok and new_fired == len(NEW)) else 1


if __name__ == "__main__":
    raise SystemExit(main())
