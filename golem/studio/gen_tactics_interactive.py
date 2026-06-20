# 전술 9카드를 브라우저에서 직접 플레이하는 독립 HTML 생성기 — 검증된 l9 엔진을 그대로 embed(룰 복제X·읽기전용)
"""인터랙티브 플레이. gen_tactics_l9_golden.REF_GAME_LOGIC(applyAction/updateState/checkGameState)를
exports 심으로 브라우저에 그대로 넣고, 유저 입력(이동/공격)마다 그 검증 엔진을 호출해 상태를 전개한다.
룰은 골렘이 골든0으로 검증한 그 코드 그대로 — UI는 입력만 만들고 결정성·정확성은 엔진이 보장.
산출=tactics_play/play.html. 서버(server.js) /play 로 서빙.
사용: python gen_tactics_interactive.py [--level l9]
"""

import argparse
import json
import sys
from importlib import import_module
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "tactics_play"

# 플레이 레벨 — 초기상태(엔진이 spread). 검증 엔진이 그대로 굴리므로 메커니즘 정합 보장.
LEVELS = [
    {"name": "1. 튜토리얼 (이동·근접)", "desc": "쉬운 연습판. 방향으로 붙어서 적을 클릭해 베라.",
     "initialState": {"hero": {"hp": 100, "atk": 30, "pos": [0, 0]},
                      "enemies": [{"id": "E1", "hp": 40, "atk": 10, "pos": [2, 0]},
                                  {"id": "E2", "hp": 40, "atk": 10, "pos": [0, 2]}]}},
    {"name": "2. 사거리·벽", "desc": "벽은 이동을 막지만 사거리(거리 2~3)는 통과한다. 멀리서 적 클릭.",
     "initialState": {"hero": {"hp": 100, "atk": 30, "pos": [0, 0]},
                      "enemies": [{"id": "궁수", "hp": 60, "atk": 15, "pos": [3, 0]}],
                      "terrain": {"1,0": "Wall", "2,0": "Wall"}}},
    {"name": "3. 변칙검술 (마나방패·파열)", "desc": "마나가 피해를 흡수하고 0으로 터질 때 인접 적에 ANOMALY. 적 사이로 파고들어 베라.",
     "initialState": {"hero": {"hp": 80, "atk": 20, "pos": [1, 1], "mana": 10, "anomaly_dmg": 40},
                      "enemies": [{"id": "E1", "hp": 50, "atk": 10, "pos": [1, 0]},
                                  {"id": "E2", "hp": 50, "atk": 8, "pos": [0, 1]},
                                  {"id": "E3", "hp": 50, "atk": 8, "pos": [2, 1]}]}},
    {"name": "4. 전도체·유리·처형 (위치 퍼즐)", "desc": "적이 흩어져 한 방엔 못 쓸어. [1,1] 전도체로 가 파열(ANOMALY×2)·Glass×2·처형(약한 적 즉사)을 엮어 풀어라.",
     "initialState": {"hero": {"hp": 90, "atk": 20, "pos": [0, 0], "mana": 6, "anomaly_dmg": 25, "execute": 15},
                      "enemies": [{"id": "강철", "hp": 60, "atk": 8, "pos": [1, 0], "unit_type": "Hardened"},
                                  {"id": "유리", "hp": 80, "atk": 6, "pos": [2, 1], "unit_type": "Glass"},
                                  {"id": "잔재", "hp": 25, "atk": 4, "pos": [1, 2], "unit_type": "Resonant"}],
                      "terrain": {"1,1": "Conductive"}}},
    {"name": "5. 캠페인 (루트 3전투)", "desc": "한 전투를 끝내면 다음 전투로. 영웅 체력은 이어진다.",
     "initialState": {"hero": {"hp": 150, "atk": 35, "pos": [0, 0], "mana": 10, "anomaly_dmg": 30,
                               "corrosion": {"dmg": 8, "duration": 3}},
                      "enemies": [{"id": "보초", "hp": 50, "atk": 12, "pos": [1, 0]}],
                      "route": [{"enemies": [{"id": "궁수", "hp": 55, "atk": 0, "pos": [2, 0]}], "terrain": {"1,0": "Wall"}},
                                {"enemies": [{"id": "유리우상", "hp": 90, "atk": 8, "pos": [1, 0], "unit_type": "Glass"},
                                             {"id": "잔재", "hp": 40, "atk": 6, "pos": [0, 1], "unit_type": "Resonant"}]}]}},
]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--level", default="l9", help="embed할 검증 엔진 레벨(기본 l9=9카드 전부)")
    args = ap.parse_args(argv)
    sys.path.insert(0, str(HERE))
    sys.path.insert(0, str(HERE.parent))
    sys.path.insert(0, str(HERE.parent.parent))
    try:
        from config import force_utf8_stdout
        force_utf8_stdout()
    except Exception:  # noqa: BLE001
        pass
    game_logic = import_module(f"gen_tactics_{args.level}_golden").REF_GAME_LOGIC

    OUT.mkdir(parents=True, exist_ok=True)
    html = (HTML.replace("__GAME_LOGIC__", game_logic)
                .replace("__LEVELS__", json.dumps(LEVELS, ensure_ascii=False))
                .replace("__LEVEL__", args.level))
    (OUT / "play.html").write_text(html, encoding="utf-8")
    print(f"  [{args.level}] 플레이 {len(LEVELS)}레벨 → {OUT / 'play.html'}")
    print("  검증 엔진을 그대로 embed(룰 복제X). 서버: node server.js → /play")
    return 0


HTML = r"""<!DOCTYPE html>
<html lang="ko"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>전술 SRPG — 플레이 (__LEVEL__)</title>
<style>
  :root{--bg:#0f1220;--panel:#1a1f33;--grid:#2a3150;--cell:#161b2e;--hero:#4ea1ff;--enemy:#ff5d6c;--wall:#3a3f52;--cond:#21d3c8;--txt:#e6e9f5;--dim:#8b93b5;--ok:#43d17a;--bad:#ff6b7a;--rng:#ffd866}
  *{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--txt);font:14px/1.4 system-ui,'Segoe UI',sans-serif}
  .wrap{max-width:760px;margin:0 auto;padding:14px}h1{font-size:17px;margin:0 0 2px}.sub{color:var(--dim);font-size:12px;margin-bottom:10px}
  select,button{background:var(--panel);color:var(--txt);border:1px solid var(--grid);border-radius:8px;padding:7px 11px;font:inherit;cursor:pointer}
  button:hover{border-color:var(--hero)}button:disabled{opacity:.4;cursor:default}
  .bar{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:10px}
  .stage{display:flex;gap:14px;flex-wrap:wrap}canvas{background:var(--panel);border-radius:12px;touch-action:manipulation}
  .side{flex:1;min-width:230px}.stat{background:var(--panel);border-radius:10px;padding:9px 11px;margin-bottom:7px}.stat b{color:var(--hero)}
  .status{font-size:16px;font-weight:700}.status.VICTORY{color:var(--ok)}.status.DEFEAT{color:var(--bad)}
  .pad{display:grid;grid-template-columns:repeat(3,40px);grid-gap:5px;justify-content:center;margin:6px 0}
  .pad button{height:40px;padding:0;font-size:16px}.pad .sp{visibility:hidden}
  .bars{height:7px;background:var(--cell);border-radius:4px;overflow:hidden;margin-top:3px}.bars>i{display:block;height:100%}
  .log{font-size:12px;color:var(--dim);margin-top:6px;min-height:32px}.hint{font-size:11px;color:var(--dim);margin-top:6px}
  .ebox div{font-size:12px}.dead{opacity:.4;text-decoration:line-through}
  .banner{font-size:15px;font-weight:700;padding:6px 0}
</style></head><body><div class="wrap">
<h1>전술 SRPG — 직접 플레이</h1>
<div class="sub">골렘이 골든0으로 검증한 __LEVEL__ 엔진을 그대로 구동(룰 복제 없음). 이동=방향 버튼, 공격=적 클릭(거리1 근접·거리2~3 사거리 자동).</div>
<div class="bar"><select id="pick"></select><button id="undo">↩ 무르기</button><button id="reset">⟲ 리셋</button><span id="ld" class="sub" style="margin:0"></span></div>
<div class="stage">
  <canvas id="cv" width="420" height="420"></canvas>
  <div class="side">
    <div class="stat"><span id="status" class="status">ACTIVE</span> <span id="battle" class="sub"></span> <span id="banner" class="banner"></span></div>
    <div class="stat">턴 <b id="turn">0</b> · HP <b id="hp"></b> · 마나 <b id="mana"></b> · ATK <b id="atk"></b>
      <div class="bars"><i id="hpbar" style="background:var(--hero)"></i></div></div>
    <div class="pad">
      <button class="sp"></button><button data-dx="0" data-dy="-1">↑</button><button class="sp"></button>
      <button data-dx="-1" data-dy="0">←</button><button class="sp"></button><button data-dx="1" data-dy="0">→</button>
      <button class="sp"></button><button data-dx="0" data-dy="1">↓</button><button class="sp"></button></div>
    <div class="stat ebox" id="ebox"></div>
    <div class="log" id="log"></div>
    <div class="hint">적 위 노란 테두리=클릭하면 공격(거리1 근접/거리2~3 사거리). 벽은 이동만 막음.</div>
  </div></div></div>
<script>
const LEVELS=__LEVELS__;
const GL=(function(){const module={exports:{}};const exports=module.exports;
__GAME_LOGIC__
return module.exports;})();
const cv=document.getElementById('cv'),ctx=cv.getContext('2d');
let lvl=0,state=null,initCount=0,hist=[],over=null;

function clone(s){return JSON.parse(JSON.stringify(s));}
function start(i){
  lvl=i;const init=clone(LEVELS[i].initialState);
  state={...init,hero:{...init.hero,pos:[...init.hero.pos]},enemies:init.enemies.map(e=>({...e,pos:[...e.pos]})),turn:0};
  initCount=state.enemies.length;hist=[];over=null;
  document.getElementById('ld').textContent=LEVELS[i].desc;
  document.getElementById('banner').textContent='';draw();
}
function act(a){
  if(over)return;
  hist.push(clone(state));
  state=GL.updateState(state,a);
  const r=GL.checkGameState(state,initCount);
  if(r){over=r;}
  draw();
}
function dist(p,q){return Math.abs(p[0]-q[0])+Math.abs(p[1]-q[1]);}
function bounds(){let mx=2,my=2;const f=[state,...hist];
  for(const s of f){mx=Math.max(mx,s.hero.pos[0]);my=Math.max(my,s.hero.pos[1]);
    for(const e of s.enemies){mx=Math.max(mx,e.pos[0]);my=Math.max(my,e.pos[1]);}
    if(s.terrain)for(const k of Object.keys(s.terrain)){const[a,b]=k.split(',').map(Number);mx=Math.max(mx,a);my=Math.max(my,b);}}
  return{w:mx+1,h:my+1};}
function css(v){return getComputedStyle(document.documentElement).getPropertyValue(v).trim();}
let cs=40,ox=8,oy=8,gb={w:5,h:5};
function draw(){
  gb=bounds();const pad=8,size=cv.width-pad*2;cs=Math.floor(size/Math.max(gb.w,gb.h));ox=pad;oy=pad;
  ctx.clearRect(0,0,cv.width,cv.height);
  for(let y=0;y<gb.h;y++)for(let x=0;x<gb.w;x++){const px=ox+x*cs,py=oy+y*cs;let fill=css('--cell');
    if(state.terrain){const t=state.terrain[x+','+y];if(t==='Wall')fill=css('--wall');else if(t==='Conductive')fill=css('--cond');}
    ctx.fillStyle=fill;ctx.fillRect(px+1,py+1,cs-2,cs-2);ctx.strokeStyle=css('--grid');ctx.strokeRect(px+1,py+1,cs-2,cs-2);}
  const hp=state.hero.pos;
  for(const e of state.enemies){const al=e.hp>0,px=ox+e.pos[0]*cs,py=oy+e.pos[1]*cs;
    if(al){const d=dist(hp,e.pos);if(d===1||(d>=2&&d<=3)){ctx.strokeStyle=css('--rng');ctx.lineWidth=3;ctx.strokeRect(px+3,py+3,cs-6,cs-6);ctx.lineWidth=1;}}
    ctx.fillStyle=al?css('--enemy'):'rgba(255,93,108,.25)';ctx.beginPath();ctx.arc(px+cs/2,py+cs/2,cs*0.32,0,7);ctx.fill();
    ctx.fillStyle=al?'#fff':css('--dim');ctx.font='bold '+Math.floor(cs*0.22)+'px system-ui';ctx.textAlign='center';ctx.textBaseline='middle';
    ctx.fillText(e.hp,px+cs/2,py+cs/2);if(e.unit_type){ctx.fillStyle='#ffd866';ctx.font='bold '+Math.floor(cs*0.2)+'px system-ui';ctx.fillText(e.unit_type[0],px+cs*0.78,py+cs*0.22);}}
  const px=ox+hp[0]*cs,py=oy+hp[1]*cs;ctx.fillStyle=css('--hero');ctx.beginPath();ctx.arc(px+cs/2,py+cs/2,cs*0.34,0,7);ctx.fill();
  ctx.fillStyle='#fff';ctx.font='bold '+Math.floor(cs*0.24)+'px system-ui';ctx.fillText('英',px+cs/2,py+cs/2);
  side();
}
function side(){
  const st=document.getElementById('status');st.textContent=over||'ACTIVE';st.className='status '+(over||'');
  document.getElementById('banner').textContent=over==='VICTORY'?'승리!':over==='DEFEAT'?'패배…':'';
  const rt=Array.isArray(state.route);document.getElementById('battle').textContent=rt?('전투 '+((state.route_index||0)+1)+'/'+(state.route.length+1)):'';
  document.getElementById('turn').textContent=state.turn;document.getElementById('hp').textContent=state.hero.hp;
  document.getElementById('mana').textContent=state.hero.mana||0;document.getElementById('atk').textContent=state.hero.atk;
  const h0=LEVELS[lvl].initialState.hero.hp;document.getElementById('hpbar').style.width=Math.max(0,Math.min(100,100*state.hero.hp/Math.max(1,h0)))+'%';
  document.getElementById('ebox').innerHTML=state.enemies.map(e=>{const t=e.unit_type?' <span style="color:#ffd866">['+e.unit_type+']</span>':'';
    return '<div class="'+(e.hp<=0?'dead':'')+'">'+e.id+t+' — HP '+e.hp+' @['+e.pos+'] 거리 '+dist(state.hero.pos,e.pos)+'</div>';}).join('')||'<div class="sub">적 없음</div>';
  document.getElementById('undo').disabled=!hist.length||!!over;
}
function tap(x,y){
  if(over)return;
  if(x<0||y<0||x>=gb.w||y>=gb.h)return;
  const e=state.enemies.find(en=>en.hp>0&&en.pos[0]===x&&en.pos[1]===y);
  if(e){const d=dist(state.hero.pos,e.pos);
    if(d===1)act({type:'attack',target:e.id});
    else if(d>=2&&d<=3)act({type:'ranged_attack',target:e.id});
    else flash('사거리 밖 (거리 '+d+')');
    return;}
  // 빈 칸: 인접(거리1)이면 그 방향으로 이동(엔진이 벽/경계는 막음)
  const hp=state.hero.pos, d=dist(hp,[x,y]);
  if(d===1)act({type:'move',dir:[x-hp[0],y-hp[1]]});
  else if(d>1)flash('한 칸씩만 이동 (인접 칸 탭)');
}
function cellFromEvent(ev){const r=cv.getBoundingClientRect();
  const sx=cv.width/r.width, sy=cv.height/r.height;  // CSS 스케일 보정(폰에서 캔버스가 축소됨)
  return [Math.floor(((ev.clientX-r.left)*sx-ox)/cs), Math.floor(((ev.clientY-r.top)*sy-oy)/cs)];}
cv.addEventListener('click',ev=>{const[x,y]=cellFromEvent(ev);tap(x,y);});
function flash(m){document.getElementById('log').textContent=m;}
document.querySelectorAll('.pad button[data-dx]').forEach(b=>b.onclick=()=>act({type:'move',dir:[+b.dataset.dx,+b.dataset.dy]}));
document.getElementById('undo').onclick=()=>{if(hist.length&&!over){state=hist.pop();over=null;draw();}};
document.getElementById('reset').onclick=()=>start(lvl);
const pick=document.getElementById('pick');LEVELS.forEach((l,i)=>{const o=document.createElement('option');o.value=i;o.textContent=l.name;pick.appendChild(o);});
pick.onchange=e=>start(+e.target.value);
window.addEventListener('keydown',e=>{const m={ArrowUp:[0,-1],ArrowDown:[0,1],ArrowLeft:[-1,0],ArrowRight:[1,0]}[e.key];if(m){e.preventDefault();act({type:'move',dir:m});}if(e.key==='z')document.getElementById('undo').click();});
start(0);
</script></body></html>
"""


if __name__ == "__main__":
    raise SystemExit(main())
