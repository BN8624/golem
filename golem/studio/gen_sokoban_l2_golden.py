# 소코반 카드 l2(텔레포트 T) 골든 생성기 — 카드1 위에 누적, 회귀 무결 검증(키0)
"""쇼케이스 새 장르 카드2(누적). 카드1(열쇠/문) 위에 텔레포트(T) 메커니즘과 그 레벨을 더한다.
T 칸을 밟으면 짝이 되는 다른 T 칸으로 즉시 이동한다(상자는 텔레포트 안 함). 골든은 base+카드1+카드2 참조 실Node 역산.
"""

import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE / "sokoban_base"
SPECQA = HERE / "specqa_packet_sokoban_l2"

import gen_sokoban_l1_golden as L1  # noqa: E402  (prev 참조 + 헬퍼)

# cur move_logic = 카드1(문/열쇠) + 텔레포트(T 밟으면 짝 T로 이동).
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

// 텔레포트: T 칸에 들어서면 짝이 되는 다른 T 칸으로 이동(체인 방지: 도착지에선 재발동 안 함)
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

# 레벨(L_tp 포함)은 sokoban_base에 고정. 카드2는 move_logic(텔레포트)만 키운다.

SCENARIOS = L1.SCENARIOS + [
    L1.scn("SCN-010", ["RULE-07"], "L_tp", ["R", "R"]),   # T로 점프 후 밀어 승리
    L1.scn("SCN-011", ["RULE-07"], "L_tp", ["R"]),        # T로 점프(중간 상태)
]
NEW = {"SCN-010", "SCN-011"}


def main():
    sys.path.insert(0, str(HERE.parent))
    try:
        from config import force_utf8_stdout
        force_utf8_stdout()
    except Exception:  # noqa: BLE001
        pass

    prev = L1.build_ref("_sokoban_ref_l1_prev_tmp", L1.REF_MOVE_LOGIC)
    cur = L1.build_ref("_sokoban_ref_l2_tmp", REF_MOVE_LOGIC)

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
                    "reason": "전 시나리오 oracle_risk.risk=false. 소코반 카드2(텔레포트, 누적) — 골든은 base+카드1+카드2 참조 실Node 역산(모델 독립)."}]},
        ensure_ascii=False, indent=2), encoding="utf-8")

    shutil.rmtree(prev)
    shutil.rmtree(cur)
    print(f"\n회귀 무결(prev==cur): {regression_ok}  신규 발동 {new_fired}/{len(NEW)}  시나리오 {len(out)}개 → {SPECQA}")
    return 0 if (regression_ok and new_fired == len(NEW)) else 1


if __name__ == "__main__":
    raise SystemExit(main())
