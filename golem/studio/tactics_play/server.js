// 전술 7카드 쇼케이스(index.html)를 아이폰(테일스케일)에서 보게 하는 정적 웹 서버 — 0.0.0.0 바인딩, 읽기전용
const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = process.env.PORT ? parseInt(process.env.PORT, 10) : 8770;
const HTML = path.join(__dirname, 'index.html');

const server = http.createServer((req, res) => {
  // 단일 페이지 — 모든 경로에 검증된 렌더러 한 장을 돌려준다.
  fs.readFile(HTML, (err, buf) => {
    if (err) {
      res.writeHead(500, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end('index.html 없음 — gen_tactics_play.py를 먼저 실행하세요.');
      return;
    }
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' });
    res.end(buf);
  });
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`전술 쇼케이스 서버 → http://0.0.0.0:${PORT}  (테일스케일 IP로 아이폰 접속)`);
});
