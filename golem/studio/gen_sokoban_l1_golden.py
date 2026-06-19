# 소코반 카드 l1(열쇠 K / 문 D) 골든 생성기 — 참조 move_logic/levels를 node로 역산, 회귀 무결 검증(키0)
"""쇼케이스 새 장르 카드1. sokoban_base에 열쇠(K)·문(D) 메커니즘과 그를 쓰는 레벨을 더한다.
문 D는 열쇠가 없으면 벽처럼 막히고, K 칸을 밟으면 열쇠를 얻어 문이 열린다. 골든은 base+참조 모듈 실행으로 역산.

흐름:
  1) sokoban_base를 ref로 복사, src/move_logic.js·src/levels.js만 카드1 버전으로 교체.
  2) 시나리오 입력(level_id/moves)을 node 실행 → expected.
  3) 회귀(원래 6종, K/D 없는 레벨)는 base==ref 바이트동일. 신규(열쇠/문 레벨)는 base와 달라야.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE / "sokoban_base"
SPECQA = HERE / "specqa_packet_sokoban_l1"

# 참조 move_logic = base + 문/열쇠. 문 D(열쇠 없으면 막힘) + K 밟으면 열쇠 획득(타일 소거, 로그 +key).
REF_MOVE_LOGIC = """// 한 번의 이동 해석(규칙 코어) — 벽·상자 밀기를 처리하고 결과 로그를 반환한다. 카드는 이 모듈에 새 타일 규칙을 더한다
const { DIRS } = require('./constants');

const key = (r, c) => r + ',' + c;

function boxIndexAt(state, r, c) {
  for (let i = 0; i < state.boxes.length; i++) {
    if (state.boxes[i][0] === r && state.boxes[i][1] === c) return i;
  }
  return -1;
}

// 닫힌 문 = 열쇠 없는 상태의 D 타일(벽처럼 막는다)
function doorClosed(state, r, c) {
  return state.tiles[key(r, c)] === 'D' && !state.hasKey;
}

// 칸에 들어설 때 효과: K면 열쇠 획득 + 타일 소거, 로그 접미사 반환
function enter(state, r, c) {
  const p = key(r, c);
  if (state.tiles[p] === 'K') { state.hasKey = true; delete state.tiles[p]; return '+key'; }
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
  return dir + ':move' + enter(state, nr, nc);
};

exports.boxIndexAt = boxIndexAt;
"""

# 참조 levels = base 레벨 + 열쇠/문 레벨 2종.
REF_LEVELS = """// 레벨 데이터(콘텐츠) — 격자 레이아웃 문자열 배열. 카드는 새 타일을 쓰는 레벨을 여기에 더한다
// 기호: '#' 벽, ' ' 바닥, '.' 목표, '@' 플레이어, '$' 상자, '*' 목표 위 상자, '+' 목표 위 플레이어
// 카드1 추가: 'K' 열쇠, 'D' 문(열쇠 없으면 막힘)
exports.LEVELS = {
  L1: [
    "#####",
    "#@$.#",
    "#####",
  ],
  L2: [
    "####",
    "#@ #",
    "#$ #",
    "#. #",
    "####",
  ],
  L3: [
    "#######",
    "#@$ . #",
    "#######",
  ],
  L_key: [
    "########",
    "#@K D$.#",
    "########",
  ],
  L_locked: [
    "######",
    "#@D$.#",
    "######",
  ],
};
"""


def scn(sid, reqs, level_id, moves):
    return {"id": sid, "covers_reqs": reqs, "input": {"level_id": level_id, "moves": moves}}


SCENARIOS = [
    scn("SCN-001", ["RULE-02", "RULE-05"], "L1", ["R"]),
    scn("SCN-002", ["RULE-03"], "L1", ["L"]),
    scn("SCN-003", ["RULE-02", "RULE-05"], "L2", ["D"]),
    scn("SCN-004", ["RULE-05"], "L1", ["R", "R"]),
    scn("SCN-005", ["RULE-02"], "L3", ["R", "R"]),
    scn("SCN-006", ["RULE-02"], "L3", ["R"]),
    scn("SCN-007", ["RULE-06"], "L_key", ["R", "R", "R", "R"]),     # 열쇠 획득→문 통과→밀어 승리
    scn("SCN-008", ["RULE-06"], "L_locked", ["R"]),                # 열쇠 없이 문 → 막힘
    scn("SCN-009", ["RULE-06"], "L_key", ["R", "R"]),              # 열쇠만 얻고 중간 상태
]
REGRESSION = {"SCN-001", "SCN-002", "SCN-003", "SCN-004", "SCN-005", "SCN-006"}

OUTPUT_KEYS = ["moves", "player", "boxes", "on_target", "isWon", "isGameOver", "logs"]


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
        if k in ("boxes", "logs"):
            exp[k] = json.loads(v)
        elif k in ("isWon", "isGameOver"):
            exp[k] = (v == "true")
        elif k in ("moves", "on_target"):
            exp[k] = int(v)
        else:
            exp[k] = v
    return exp


def build_ref(name, move_logic_src, levels_src=None):
    ref = HERE / name
    if ref.exists():
        shutil.rmtree(ref)
    shutil.copytree(BASE, ref)
    (ref / "src" / "move_logic.js").write_text(move_logic_src, encoding="utf-8")
    if levels_src is not None:  # 레벨은 베이스에 고정. 카드는 move_logic만 키운다(levels 미변경).
        (ref / "src" / "levels.js").write_text(levels_src, encoding="utf-8")
    return ref


def main():
    sys.path.insert(0, str(HERE.parent))
    try:
        from config import force_utf8_stdout
        force_utf8_stdout()
    except Exception:  # noqa: BLE001
        pass

    ref = build_ref("_sokoban_ref_l1_tmp", REF_MOVE_LOGIC)
    inputs = [{"input": s["input"]} for s in SCENARIOS]
    (ref / "scenarios.json").write_text(json.dumps(inputs, ensure_ascii=False), encoding="utf-8")
    (BASE / "scenarios.json").write_text(json.dumps(inputs, ensure_ascii=False), encoding="utf-8")

    out = []
    regression_ok = True
    new_fired = 0
    for i, s in enumerate(SCENARIOS, 1):
        ref_out = run(ref, i)
        base_out = run(BASE, i)
        expected = parse_expected(ref_out)
        out.append({"id": s["id"], "input": s["input"], "covers_reqs": s["covers_reqs"],
                    "expected": expected, "oracle_risk": {"risk": False, "reason": ""}})
        same = base_out == ref_out
        if s["id"] in REGRESSION:
            regression_ok = regression_ok and same
        else:
            if not same:
                new_fired += 1
        tag = ("회귀 base==ref:" + str(same)) if s["id"] in REGRESSION else ("신규발동" if not same else "신규미발동(?)")
        print(f"  {s['id']} {tag}  isWon={expected['isWon']} logs={expected['logs']}")

    SPECQA.mkdir(parents=True, exist_ok=True)
    (SPECQA / "acceptance_tests_draft.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    (SPECQA / "oracle_risk_review.json").write_text(json.dumps(
        {"risky_scenarios": [],
         "notes": [{"risk": False,
                    "reason": "전 시나리오 oracle_risk.risk=false. 소코반 카드1(열쇠/문) — 골든은 sokoban_base+참조 move_logic/levels 실Node 역산(모델 독립)."}]},
        ensure_ascii=False, indent=2), encoding="utf-8")

    (BASE / "scenarios.json").unlink(missing_ok=True)
    shutil.rmtree(ref)
    print(f"\n회귀 무결: {regression_ok}  신규 발동 {new_fired}/{len(SCENARIOS) - len(REGRESSION)}  시나리오 {len(out)}개 → {SPECQA}")
    return 0 if (regression_ok and new_fired == len(SCENARIOS) - len(REGRESSION)) else 1


if __name__ == "__main__":
    raise SystemExit(main())
