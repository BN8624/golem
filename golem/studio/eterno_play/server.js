// 에테르노 IF를 아이폰(테일스케일)에서 클릭 플레이하게 하는 모바일 웹 서버 — 검증된 l1_built 엔진을 그대로 재사용한다
const http = require('http');
const path = require('path');

// 골렘이 게이트·합의 1.0으로 검증한 바로 그 빌드의 장면/비트/상수를 재사용한다(드리프트 0)
const BUILT = path.join(__dirname, '..', 'build_runs', 'showcase_eterno', 'l1_built', 'src');
const { SCENES } = require(path.join(BUILT, 'scenes'));
const { createInitialState } = require(path.join(BUILT, 'state'));
const { fireBeats } = require(path.join(BUILT, 'beats'));
const C = require(path.join(BUILT, 'constants'));

const PORT = 8765;

// 이모지 매핑(표시 전용 — 게임 로직은 건드리지 않는다)
const SCENE_EMOJI = { start: '🚪', hub: '🏚️', checkpoint: '🛡️', end_dawn: '🌅', end_ritual: '🩸', end_fled: '🌑', end_caught: '⛓️' };
const CHOICE_EMOJI = {
  enter: '🕳️', turn_back: '↩️', infiltrate: '🤫',
  altar_1: '🕯️', altar_2: '🏛️', altar_3: '⚔️', altar_4: '🏔️', altar_5: '❄️',
  march: '🗡️', flee: '🏃', attune: '🌀', bluff: '😏',
};
const FRAG_EMOJI = { F1: '🕯️', F2: '🏛️', F3: '⚔️', F4: '🏔️', F5: '❄️' };
const BEAT_EMOJI = { AWAKENING: '✨', RESONANCE: '💫' };
const ENDING_LABEL = {
  NEW_DAWN: '🌅 새로운 여명 — 다섯 조각이 융합되고 거짓 권능이 무너진다.',
  RITUAL_COMPLETE: '🩸 피의 제사 완성 — 개기일식이 차오르고 제국이 연료가 된다.',
  FLED: '🌑 후퇴 — 아직 길이 열리지 않았다.',
  CAUGHT: '⛓️ 붙잡힘 — 위조 통행증의 허점이 드러났다.',
};

// 검증된 engine.js의 스텝 로직을 한 선택 단위로 재현한다(원본과 동일한 전이 규칙)
function step(state, choiceId) {
  const scene = SCENES[state.scene];
  if (!scene || scene.ending != null) return state;
  const option = scene.choices && scene.choices[choiceId];
  if (!option) { state.logs.push('무시:' + choiceId); return state; }

  state.turn += 1;
  state.logs.push('선택:' + choiceId);

  if (option.fragment && !state.fragments.includes(option.fragment)) {
    state.fragments.push(option.fragment);
    state.logs.push('조각:' + option.fragment);
    const newly = fireBeats(state.fragments, state.beats);
    for (const b of newly) { state.beats.push(b); state.logs.push('BEAT:' + b); }
  }

  if (option.verdict) {
    state.scene = C.ALL_FRAGMENTS.every((f) => state.fragments.includes(f)) ? 'end_dawn' : 'end_ritual';
  } else {
    state.scene = option.to;
  }

  const next = SCENES[state.scene];
  if (next && next.ending == null) {
    state.eclipse -= 1;
    if (state.eclipse <= 0) state.scene = 'end_ritual';
  }

  const finalScene = SCENES[state.scene];
  if (finalScene && finalScene.ending != null) {
    state.ending = finalScene.ending;
    state.isGameOver = true;
  }
  return state;
}

// 선택 배열을 처음부터 재생해 현재 상태를 만든다(서버 무상태 — 클라이언트가 선택 이력을 보관)
function compute(choices) {
  const state = createInitialState();
  for (let i = 0; i < choices.length && i < C.MAX_STEPS; i++) step(state, choices[i]);
  return state;
}

// 현재 상태를 클라이언트가 그릴 수 있는 형태(텍스트·선택지·트래커)로 직렬화한다
function view(choices) {
  const state = compute(choices);
  const scene = SCENES[state.scene];
  const out = {
    turn: state.turn,
    scene: state.scene,
    sceneEmoji: SCENE_EMOJI[state.scene] || '•',
    text: scene ? scene.text : '',
    eclipse: state.eclipse,
    fragments: C.ALL_FRAGMENTS.map((f) => ({ id: f, emoji: FRAG_EMOJI[f], have: state.fragments.includes(f) })),
    beats: state.beats.map((b) => ({ id: b, emoji: BEAT_EMOJI[b] || '◆' })),
    isGameOver: state.isGameOver,
    ending: state.ending ? ENDING_LABEL[state.ending] || state.ending : null,
    choices: [],
  };
  if (scene && scene.choices && !state.isGameOver) {
    out.choices = Object.entries(scene.choices).map(([id, o]) => ({ id, emoji: CHOICE_EMOJI[id] || '▶️', label: o.label }));
  }
  return out;
}

const PAGE = `<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<title>🌒 에테르노의 그림자</title>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
  body { margin: 0; font-family: -apple-system, system-ui, sans-serif;
    background: linear-gradient(160deg, #14101f, #241a33 60%, #0d0a14);
    color: #ece6f5; min-height: 100vh; padding: 16px; }
  .wrap { max-width: 560px; margin: 0 auto; }
  h1 { font-size: 22px; text-align: center; margin: 8px 0 4px; letter-spacing: 1px; }
  .bar { display: flex; justify-content: space-between; align-items: center;
    font-size: 14px; opacity: .85; margin-bottom: 10px; }
  .frags { font-size: 20px; letter-spacing: 3px; }
  .frags .off { opacity: .22; filter: grayscale(1); }
  .eclipse { background: rgba(0,0,0,.35); padding: 4px 10px; border-radius: 20px; }
  .card { background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.1);
    border-radius: 18px; padding: 20px 18px; margin-bottom: 16px; }
  .scene-emoji { font-size: 40px; text-align: center; display: block; margin-bottom: 8px; }
  .text { font-size: 17px; line-height: 1.7; }
  .beats { text-align: center; font-size: 13px; opacity: .8; margin: 8px 0; min-height: 18px; }
  button.choice { width: 100%; text-align: left; font-size: 16px; color: #ece6f5;
    background: rgba(126,90,200,.18); border: 1px solid rgba(150,110,220,.35);
    border-radius: 14px; padding: 15px 16px; margin-bottom: 11px; cursor: pointer;
    transition: transform .06s, background .15s; }
  button.choice:active { transform: scale(.97); background: rgba(150,110,220,.4); }
  .ce { font-size: 20px; margin-right: 10px; }
  .ending { text-align: center; font-size: 19px; line-height: 1.6; padding: 12px 0; }
  .restart { width: 100%; font-size: 16px; color: #14101f; background: #d9c8ff;
    border: none; border-radius: 14px; padding: 15px; margin-top: 6px; font-weight: 600; cursor: pointer; }
  .foot { text-align: center; font-size: 11px; opacity: .4; margin-top: 14px; }
</style>
</head>
<body>
<div class="wrap">
  <h1>🌒 에테르노의 그림자</h1>
  <div class="bar">
    <span class="frags" id="frags"></span>
    <span class="eclipse" id="eclipse"></span>
  </div>
  <div class="card">
    <span class="scene-emoji" id="sceneEmoji"></span>
    <div class="beats" id="beats"></div>
    <div class="text" id="text"></div>
  </div>
  <div id="choices"></div>
  <div class="foot">golem studio · 결정적 IF 엔진(검증 1.0)</div>
</div>
<script>
let history = [];
async function refresh() {
  const r = await fetch('/api/state', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ choices: history }) });
  const s = await r.json();
  render(s);
}
function render(s) {
  document.getElementById('sceneEmoji').textContent = s.sceneEmoji;
  document.getElementById('text').textContent = s.text;
  document.getElementById('frags').innerHTML = s.fragments.map(f => '<span class="' + (f.have ? 'on' : 'off') + '">' + f.emoji + '</span>').join('');
  document.getElementById('eclipse').textContent = '🌑 일식까지 ' + s.eclipse;
  document.getElementById('beats').textContent = s.beats.map(b => b.emoji + ' ' + b.id).join('   ');
  const cc = document.getElementById('choices');
  cc.innerHTML = '';
  if (s.isGameOver) {
    const e = document.createElement('div'); e.className = 'card ending'; e.textContent = s.ending; cc.appendChild(e);
    const b = document.createElement('button'); b.className = 'restart'; b.textContent = '🔄 다시 시작';
    b.onclick = () => { history = []; refresh(); }; cc.appendChild(b);
  } else {
    for (const c of s.choices) {
      const b = document.createElement('button'); b.className = 'choice';
      b.innerHTML = '<span class="ce">' + c.emoji + '</span>' + c.label;
      b.onclick = () => { history.push(c.id); refresh(); }; cc.appendChild(b);
    }
  }
}
refresh();
</script>
</body>
</html>`;

const server = http.createServer((req, res) => {
  if (req.method === 'POST' && req.url === '/api/state') {
    let body = '';
    req.on('data', (c) => { body += c; if (body.length > 1e5) req.destroy(); });
    req.on('end', () => {
      let choices = [];
      try { choices = (JSON.parse(body).choices || []).filter((x) => typeof x === 'string'); } catch (e) {}
      res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
      res.end(JSON.stringify(view(choices)));
    });
    return;
  }
  res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
  res.end(PAGE);
});

server.listen(PORT, '0.0.0.0', () => {
  console.log('에테르노 플레이 서버 가동: http://0.0.0.0:' + PORT);
  console.log('아이폰(테일스케일)에서 접속: http://100.89.73.83:' + PORT + '  또는  http://node.tail3e9e21.ts.net:' + PORT);
});
