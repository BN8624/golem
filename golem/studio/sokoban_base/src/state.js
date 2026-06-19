// 소코반 초기 상태 생성 — 레벨 격자를 파싱해 벽·목표·플레이어·상자와 일반 타일맵을 결정적으로 만든다
// 표준 기호 외의 문자(예: 카드가 더하는 K/D/I/O)는 tiles 맵에 그대로 담아 move_logic이 해석하게 둔다
exports.createInitialState = (lines) => {
  const grid = lines || [];
  const walls = {};
  const targets = {};
  const tiles = {};
  let player = [0, 0];
  const boxes = [];
  for (let r = 0; r < grid.length; r++) {
    const row = grid[r];
    for (let c = 0; c < row.length; c++) {
      const ch = row[c];
      const pos = r + ',' + c;
      if (ch === '#') walls[pos] = true;
      else if (ch === '.') targets[pos] = true;
      else if (ch === '@') player = [r, c];
      else if (ch === '+') { player = [r, c]; targets[pos] = true; }
      else if (ch === '$') boxes.push([r, c]);
      else if (ch === '*') { boxes.push([r, c]); targets[pos] = true; }
      else if (ch === ' ') { /* 바닥 */ }
      else tiles[pos] = ch; // 비표준 타일은 일반 맵에 보관(바닥처럼 통행 가능)
    }
  }
  return {
    moves: 0,
    player: player,
    boxes: boxes,
    walls: walls,
    targets: targets,
    tiles: tiles,
    logs: [],
    isWon: false,
    isGameOver: false,
  };
};
