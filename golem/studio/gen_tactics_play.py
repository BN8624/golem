# 전술 7카드 게임을 정사각 탑다운으로 보여주는 독립 HTML 렌더러 생성기 — 검증된 l7 엔진 그대로 재사용(키0·읽기전용)
"""쇼케이스 외형. tactics_kernel_base + 검증된 l7 참조 game_logic(마나방패·사거리·지형·유닛·루트맵·상태이상·밸런스)을
node로 require해 28세계+캠페인 1편 전부 턴별 상태를 추출 → 단일 index.html에 트레이스 임베드.
엔진은 골렘이 게이트·golden_diff 0으로 검증한 바로 그 로직. 렌더러는 표시 전용(로직 안 건드림).
브라우저로 index.html 열면 시나리오 고르고 턴 재생.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE / "tactics_kernel_base"
PACKET = HERE / "planning_packet_tactics_l7"
OUT = HERE / "tactics_play"

# 캠페인 한 편 — 7카드 엔진을 루트맵으로 엮은 4전투 데모(검증된 l7 엔진으로 결정적 실행). 콘텐츠는 엔진과 분리.
CAMPAIGN = {
    "id": "CAMPAIGN",
    "initialState": {
        "hero": {"hp": 150, "atk": 40, "pos": [0, 0], "mana": 0, "anomaly_dmg": 0,
                 "corrosion": {"dmg": 10, "duration": 3}},
        "enemies": [{"id": "G1", "hp": 40, "atk": 10, "pos": [1, 0]}],
        "route": [
            {"enemies": [{"id": "A1", "hp": 30, "atk": 0, "pos": [2, 0]}], "terrain": {"1,0": "Wall"}},
            {"enemies": [{"id": "T1", "hp": 50, "atk": 5, "pos": [1, 0], "unit_type": "Hardened"}]},
            {"enemies": [{"id": "B1", "hp": 100, "atk": 0, "pos": [2, 0], "unit_type": "Glass"}]}
        ]
    },
    "actions": [
        {"type": "attack", "target": "G1"},
        {"type": "ranged_attack", "target": "A1"},
        {"type": "attack", "target": "T1"},
        {"type": "attack", "target": "T1"},
        {"type": "ranged_attack", "target": "B1"}
    ]
}

# 시나리오 라벨(어떤 메커니즘을 보여주나).
LABELS = {
    "SCN-001": "기본 멜레 — 3연타 처치", "SCN-002": "패배 — 강적", "SCN-003": "이동만",
    "SCN-004": "적 0 → FINISHED", "SCN-005": "동시 사망 → DEFEAT", "SCN-006": "동시 0 → DEFEAT",
    "SCN-007": "마나방패 흡수(무파열)", "SCN-008": "마나방패 파열(생존)", "SCN-009": "ANOMALY 파열 처치(스플래시)",
    "SCN-010": "사거리 일방공격", "SCN-011": "사거리밖→이동→적중", "SCN-012": "사거리 무위험 처치",
    "SCN-013": "지형 Wall 이동차단", "SCN-014": "Conductive ANOMALY ×2→VICTORY", "SCN-015": "Wall은 사거리 안 막음",
    "SCN-016": "유닛 Hardened(멜레 -1)", "SCN-017": "유닛 Glass 사거리 ×2", "SCN-018": "유닛 Glass ANOMALY ×2→VICTORY",
    "SCN-019": "유닛 Resonant 반사피해", "SCN-020": "루트맵 2전투 승리(hp 이월)",
    "SCN-021": "루트 전환 후 FINISHED", "SCN-022": "루트 2전투에서 DEFEAT",
    "SCN-023": "상태이상 Corrosion DoT 처치", "SCN-024": "Corrosion ×2(Glass)",
    "SCN-025": "Corrosion 처치→루트 전환",
    "SCN-026": "밸런스 recMult→DEFEAT", "SCN-027": "밸런스 atkMult→원샷", "SCN-028": "밸런스 anomMult→일소",
    "CAMPAIGN": "★ 캠페인 — 7카드 4전투 한 편",
}

# 검증된 l7 참조 game_logic을 가져온다(gen_tactics_l7_golden 단일 출처 — 6카드 전부 포함).
def l7_game_logic():
    sys.path.insert(0, str(HERE))
    from gen_tactics_l7_golden import REF_GAME_LOGIC
    return REF_GAME_LOGIC

# 턴별 상태를 뽑는 node 트레이서(engine 초기화 재현 + updateState/checkGameState 스텝마다 스냅샷).
TRACER_JS = """
const gl = require('./src/game_logic');
const scenarios = require('./src/scenarios');
const n = parseInt(process.argv[2], 10);
const scn = scenarios.getScenario(n);
let state = {
  ...scn.initialState,
  hero: { ...scn.initialState.hero, pos: [...scn.initialState.hero.pos] },
  enemies: scn.initialState.enemies.map(e => ({ ...e, pos: [...e.pos] })),
  turn: 0
};
const initialEnemyCount = state.enemies.length;
const routeTotal = 1 + (Array.isArray(scn.initialState.route) ? scn.initialState.route.length : 0);
function snap(s, status, lastAction) {
  return {
    turn: s.turn,
    hero: { hp: s.hero.hp, mana: s.hero.mana || 0, anomaly_dmg: s.hero.anomaly_dmg || 0, atk: s.hero.atk, pos: [...s.hero.pos] },
    enemies: s.enemies.map(e => ({ id: e.id, hp: e.hp, pos: [...e.pos], unit_type: e.unit_type || null })),
    terrain: s.terrain || null,
    status, lastAction,
    battle: (s.route_index || 0) + 1, battles: routeTotal
  };
}
const frames = [snap(state, 'READY', null)];
let status = 'READY';
for (const action of scn.actions) {
  state = gl.updateState(state, action);
  const result = gl.checkGameState(state, initialEnemyCount);
  frames.push(snap(state, result || 'ACTIVE', action));
  if (result) { status = result; break; }
}
if (status === 'READY') status = 'FINISHED';
frames[frames.length - 1].status = status;
process.stdout.write(JSON.stringify({ n, frames }));
"""


def main():
    sys.path.insert(0, str(HERE.parent))
    sys.path.insert(0, str(HERE))
    try:
        from config import force_utf8_stdout
        force_utf8_stdout()
    except Exception:  # noqa: BLE001
        pass
    import build_graded as bg

    contract = json.loads((PACKET / "contract.json").read_text(encoding="utf-8"))
    scenario_data = list(contract["data_contract"]["scenario_data"]) + [CAMPAIGN]  # 25세계 + 캠페인 1편
    scenarios_js = bg._gen_scenarios_module(scenario_data)

    # 검증된 l7 엔진 워크스페이스(읽기전용 재사용).
    ws = HERE / "_tactics_play_engine_tmp"
    if ws.exists():
        shutil.rmtree(ws)
    shutil.copytree(BASE, ws)
    (ws / "module_manifest.json").unlink(missing_ok=True)
    (ws / "src" / "game_logic.js").write_text(l7_game_logic(), encoding="utf-8")
    (ws / "src" / "scenarios.js").write_text(scenarios_js, encoding="utf-8")
    (ws / "trace.js").write_text(TRACER_JS, encoding="utf-8")

    traces = []
    for i, s in enumerate(scenario_data, 1):
        r = subprocess.run(["node", "trace.js", str(i)], cwd=str(ws),
                           capture_output=True, text=True, encoding="utf-8", timeout=30, stdin=subprocess.DEVNULL)
        if r.returncode != 0:
            raise RuntimeError(f"trace 실패 scn{i}: {r.stderr[:300]}")
        t = json.loads(r.stdout)
        t["id"] = s["id"]
        t["label"] = LABELS.get(s["id"], s["id"])
        traces.append(t)

    shutil.rmtree(ws)

    # 캠페인 한 편이 결정적으로 VICTORY로 닫히는지 sanity(엔진은 검증됨, 캠페인은 콘텐츠 입력).
    camp = next(t for t in traces if t["id"] == "CAMPAIGN")
    camp_final = camp["frames"][-1]
    if camp_final["status"] != "VICTORY":
        print(f"  CAMPAIGN sanity FAIL: 최종 status={camp_final['status']} (VICTORY 기대)")
        return 1

    OUT.mkdir(parents=True, exist_ok=True)
    html = HTML_TEMPLATE.replace("__TRACES__", json.dumps(traces, ensure_ascii=False))
    (OUT / "index.html").write_text(html, encoding="utf-8")
    print(f"  트레이스 {len(traces)}세계(+캠페인) → {OUT / 'index.html'}")
    print(f"  캠페인 4전투 {len(camp['frames'])-1}액션 → VICTORY(turn {camp_final['turn']}).")
    print("  브라우저로 열어 시나리오 선택·턴 재생(읽기전용, 검증된 l7 엔진).")
    return 0


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>전술 SRPG — 7카드 쇼케이스</title>
<style>
  :root { --bg:#0f1220; --panel:#1a1f33; --grid:#2a3150; --cell:#161b2e; --hero:#4ea1ff; --enemy:#ff5d6c; --wall:#3a3f52; --cond:#21d3c8; --txt:#e6e9f5; --dim:#8b93b5; --ok:#43d17a; --bad:#ff6b7a; }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--txt); font:14px/1.4 system-ui,'Segoe UI',sans-serif; }
  .wrap { max-width:860px; margin:0 auto; padding:16px; }
  h1 { font-size:18px; margin:0 0 4px; }
  .sub { color:var(--dim); font-size:12px; margin-bottom:12px; }
  select, button { background:var(--panel); color:var(--txt); border:1px solid var(--grid); border-radius:8px; padding:7px 12px; font:inherit; cursor:pointer; }
  button:hover { border-color:var(--hero); }
  .bar { display:flex; gap:8px; align-items:center; flex-wrap:wrap; margin-bottom:12px; }
  .stage { display:flex; gap:16px; flex-wrap:wrap; }
  canvas { background:var(--panel); border-radius:12px; touch-action:none; }
  .side { flex:1; min-width:220px; }
  .stat { background:var(--panel); border-radius:10px; padding:10px 12px; margin-bottom:8px; }
  .stat b { color:var(--hero); }
  .status { font-size:16px; font-weight:700; }
  .status.VICTORY { color:var(--ok); } .status.DEFEAT { color:var(--bad); } .status.FINISHED,.status.ACTIVE,.status.READY { color:var(--dim); }
  .bars { height:7px; background:var(--cell); border-radius:4px; overflow:hidden; margin-top:3px; }
  .bars > i { display:block; height:100%; }
  .legend { font-size:11px; color:var(--dim); margin-top:8px; }
  .legend span { display:inline-block; margin-right:10px; }
  .dot { display:inline-block; width:10px; height:10px; border-radius:3px; vertical-align:middle; margin-right:3px; }
  .log { font-size:12px; color:var(--dim); margin-top:6px; min-height:18px; }
</style>
</head>
<body>
<div class="wrap">
  <h1>전술 SRPG — 7카드 쇼케이스</h1>
  <div class="sub">마나방패·ANOMALY · 사거리 · 지형 · 유닛 · 루트맵 · 상태이상 · 밸런스 — 골렘이 설계·검증한 l7 엔진(읽기전용 렌더)</div>
  <div class="bar">
    <select id="pick"></select>
    <button id="prev">◀ 이전</button>
    <button id="play">▶ 재생</button>
    <button id="next">다음 ▶</button>
    <span id="frameinfo" class="sub" style="margin:0"></span>
  </div>
  <div class="stage">
    <canvas id="cv" width="440" height="440"></canvas>
    <div class="side">
      <div class="stat"><span id="status" class="status"></span> <span id="battle" class="sub"></span></div>
      <div class="stat">턴 <b id="turn"></b> · 영웅 HP <b id="hp"></b> · 마나 <b id="mana"></b> · ATK <b id="atk"></b>
        <div class="bars"><i id="hpbar" style="background:var(--hero)"></i></div>
      </div>
      <div class="stat" id="enemybox"></div>
      <div class="log" id="log"></div>
      <div class="legend">
        <span><i class="dot" style="background:var(--hero)"></i>영웅</span>
        <span><i class="dot" style="background:var(--enemy)"></i>적</span>
        <span><i class="dot" style="background:var(--wall)"></i>Wall</span>
        <span><i class="dot" style="background:var(--cond)"></i>Conductive</span>
        <span>적 글자 H=Hardened G=Glass R=Resonant</span>
      </div>
    </div>
  </div>
</div>
<script>
const TRACES = __TRACES__;
const cv = document.getElementById('cv'), ctx = cv.getContext('2d');
let cur = 0, fi = 0, timer = null;

function bounds(tr) {
  let mx = 2, my = 2;
  for (const f of tr.frames) {
    mx = Math.max(mx, f.hero.pos[0]); my = Math.max(my, f.hero.pos[1]);
    for (const e of f.enemies) { mx = Math.max(mx, e.pos[0]); my = Math.max(my, e.pos[1]); }
    if (f.terrain) for (const k of Object.keys(f.terrain)) { const [x,y]=k.split(',').map(Number); mx=Math.max(mx,x); my=Math.max(my,y); }
  }
  return { w: mx + 1, h: my + 1 };
}

function draw() {
  const tr = TRACES[cur], f = tr.frames[fi], b = bounds(tr);
  const pad = 8, size = cv.width - pad*2, cs = Math.floor(size / Math.max(b.w, b.h));
  ctx.clearRect(0,0,cv.width,cv.height);
  const ox = pad, oy = pad;
  // y축은 위가 0(탑다운).
  for (let y=0;y<b.h;y++) for (let x=0;x<b.w;x++){
    const px=ox+x*cs, py=oy+y*cs;
    let fill = getCss('--cell');
    if (f.terrain){ const t=f.terrain[x+','+y]; if(t==='Wall')fill=getCss('--wall'); else if(t==='Conductive')fill=getCss('--cond'); }
    ctx.fillStyle=fill; ctx.fillRect(px+1,py+1,cs-2,cs-2);
    ctx.strokeStyle=getCss('--grid'); ctx.lineWidth=1; ctx.strokeRect(px+1,py+1,cs-2,cs-2);
  }
  // 적
  for (const e of f.enemies){
    const alive = e.hp>0; const px=ox+e.pos[0]*cs, py=oy+e.pos[1]*cs;
    ctx.fillStyle = alive ? getCss('--enemy') : 'rgba(255,93,108,0.25)';
    circle(px+cs/2, py+cs/2, cs*0.32);
    ctx.fillStyle = alive ? '#fff' : getCss('--dim');
    ctx.font = 'bold '+Math.floor(cs*0.22)+'px system-ui'; ctx.textAlign='center'; ctx.textBaseline='middle';
    ctx.fillText(e.hp, px+cs/2, py+cs/2);
    if (e.unit_type){ ctx.fillStyle='#ffd866'; ctx.font='bold '+Math.floor(cs*0.2)+'px system-ui';
      ctx.fillText(e.unit_type[0], px+cs*0.78, py+cs*0.22); }
  }
  // 영웅
  const hx=ox+f.hero.pos[0]*cs, hy=oy+f.hero.pos[1]*cs;
  ctx.fillStyle=getCss('--hero'); circle(hx+cs/2, hy+cs/2, cs*0.34);
  ctx.fillStyle='#fff'; ctx.font='bold '+Math.floor(cs*0.24)+'px system-ui';
  ctx.fillText('英', hx+cs/2, hy+cs/2);
  renderSide(tr, f);
}
function circle(x,y,r){ ctx.beginPath(); ctx.arc(x,y,r,0,7); ctx.fill(); }
function getCss(v){ return getComputedStyle(document.documentElement).getPropertyValue(v).trim(); }

function renderSide(tr, f){
  const st = document.getElementById('status'); st.textContent = f.status; st.className='status '+f.status;
  document.getElementById('battle').textContent = tr.frames.some(x=>x.battles>1) ? ('전투 '+f.battle+'/'+f.battles) : '';
  document.getElementById('turn').textContent = f.turn;
  document.getElementById('hp').textContent = f.hero.hp;
  document.getElementById('mana').textContent = f.hero.mana;
  document.getElementById('atk').textContent = f.hero.atk;
  const hp0 = tr.frames[0].hero.hp; document.getElementById('hpbar').style.width = Math.max(0, Math.min(100, 100*f.hero.hp/Math.max(1,hp0)))+'%';
  const eb = document.getElementById('enemybox');
  eb.innerHTML = f.enemies.map(e=>{
    const tag = e.unit_type ? ' <span style="color:#ffd866">['+e.unit_type+']</span>' : '';
    const dead = e.hp<=0 ? ' style="opacity:.4;text-decoration:line-through"' : '';
    return '<div'+dead+'>'+e.id+tag+' — HP '+e.hp+' @['+e.pos+']</div>';
  }).join('') || '<div class="sub">적 없음</div>';
  const a = f.lastAction;
  document.getElementById('log').textContent = a ? ('액션: '+a.type+(a.target?(' → '+a.target):(a.dir?(' '+JSON.stringify(a.dir)):''))) : '초기 상태';
  document.getElementById('frameinfo').textContent = '프레임 '+(fi+1)+'/'+tr.frames.length;
}

function setScn(i){ cur=i; fi=0; stop(); draw(); }
function go(d){ const tr=TRACES[cur]; fi=Math.max(0, Math.min(tr.frames.length-1, fi+d)); draw(); }
function stop(){ if(timer){clearInterval(timer); timer=null; document.getElementById('play').textContent='▶ 재생';} }
function play(){
  if(timer){ stop(); return; }
  document.getElementById('play').textContent='⏸ 정지';
  timer=setInterval(()=>{ const tr=TRACES[cur]; if(fi>=tr.frames.length-1){stop();return;} fi++; draw(); }, 750);
}

const pick=document.getElementById('pick');
TRACES.forEach((t,i)=>{ const o=document.createElement('option'); o.value=i; o.textContent=t.id+' — '+t.label; pick.appendChild(o); });
pick.onchange=e=>setScn(+e.target.value);
document.getElementById('prev').onclick=()=>{stop();go(-1);};
document.getElementById('next').onclick=()=>{stop();go(1);};
document.getElementById('play').onclick=play;
window.addEventListener('keydown',e=>{ if(e.key==='ArrowLeft'){stop();go(-1);} if(e.key==='ArrowRight'){stop();go(1);} if(e.key===' '){e.preventDefault();play();} });
setScn(0);
</script>
</body>
</html>
"""


if __name__ == "__main__":
    raise SystemExit(main())
