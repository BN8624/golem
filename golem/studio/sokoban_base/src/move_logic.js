// 한 번의 이동 해석(규칙 코어) — 벽·상자 밀기를 처리하고 결과 로그를 반환한다. 카드는 이 모듈에 새 타일 규칙을 더한다
const { DIRS } = require('./constants');

const key = (r, c) => r + ',' + c;

// 해당 칸에 있는 상자의 인덱스(없으면 -1)
function boxIndexAt(state, r, c) {
  for (let i = 0; i < state.boxes.length; i++) {
    if (state.boxes[i][0] === r && state.boxes[i][1] === c) return i;
  }
  return -1;
}

// dir 방향으로 플레이어를 한 칸 움직인다(상자는 밀 수 있으면 민다). state를 갱신하고 로그 문자열을 반환.
exports.resolveMove = (state, dir) => {
  const d = DIRS[dir];
  if (!d) return dir + ':none';
  const [pr, pc] = state.player;
  const nr = pr + d[0];
  const nc = pc + d[1];
  if (state.walls[key(nr, nc)]) return dir + ':block';

  const bi = boxIndexAt(state, nr, nc);
  if (bi >= 0) { // 상자 밀기
    const br = nr + d[0];
    const bc = nc + d[1];
    if (state.walls[key(br, bc)] || boxIndexAt(state, br, bc) >= 0) return dir + ':block';
    state.boxes[bi] = [br, bc];
    state.player = [nr, nc];
    return dir + ':push';
  }

  state.player = [nr, nc];
  return dir + ':move';
};

exports.boxIndexAt = boxIndexAt;
