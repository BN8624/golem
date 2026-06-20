// 전술 쇼케이스/플레이를 아이폰(테일스케일)에서 보게 하는 정적 웹 서버 — 0.0.0.0, 읽기전용. / = 뷰어, /play = 직접 플레이
const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = process.env.PORT ? parseInt(process.env.PORT, 10) : 8770;
const PAGES = {
  '/': path.join(__dirname, 'index.html'),       // 턴 재생 뷰어(gen_tactics_play.py)
  '/play': path.join(__dirname, 'play.html'),    // 직접 플레이(gen_tactics_interactive.py)
};

const server = http.createServer((req, res) => {
  const route = (req.url || '/').split('?')[0].replace(/\/$/, '') || '/';
  const file = PAGES[route] || PAGES['/'];
  fs.readFile(file, (err, buf) => {
    if (err) {
      res.writeHead(500, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end(path.basename(file) + ' 없음 — gen_tactics_play.py / gen_tactics_interactive.py를 먼저 실행하세요.');
      return;
    }
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' });
    res.end(buf);
  });
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`전술 서버 → http://0.0.0.0:${PORT}/ (뷰어) · /play (직접 플레이)  [테일스케일 IP로 아이폰 접속]`);
});
