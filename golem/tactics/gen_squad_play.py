# 부대(squad) 전술을 정사각 탑다운으로 턴별 재생하는 독립 HTML 뷰어 생성기 — 검증된 squad 엔진 그대로 embed(키0·읽기전용)
"""squad_base_{level}의 검증된 game_logic(mutable: updateState가 state 변경+status 반환)을 브라우저에 그대로 심고,
계약 세계(planning_packet_squad_{level})를 시나리오로 임베드한다. 뷰어는 각 시나리오를 턴별로 updateState 호출해
아군(파랑) 다수·적(빨강) 다수의 이동·공격·적 AI 추격을 격자에 재생한다. 룰 복제 0, 표시 전용.

사용: python gen_squad_play.py [--level l4]   (키0). 산출=tactics/play/squad.html.
"""
import sys as _sys
from pathlib import Path as _Path
_PKG = _Path(__file__).resolve().parents[1]
for _p in (str(_PKG), str(_PKG / "core"), str(_PKG / "tools"), str(_PKG / "tactics"),
           str(_PKG / "validators"), str(_PKG.parent)):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)
from paths import (PKG, REPO_ROOT, CORE, TOOLS, TACTICS, VALIDATORS,  # noqa: E402,F401
                   BASES, PACKETS, PLAY, FIXTURES, SCHEMAS, BUILD_RUNS, SCRATCH)

import argparse
import json
from pathlib import Path


def _game_logic(level):
    base = BASES / ("squad_base" if level == "kernel" else f"squad_base_{level}")
    return (base / "src" / "game_logic.js").read_text(encoding="utf-8")


def _rules(level):
    try:
        pkt = PACKETS / f"planning_packet_squad_{level}"
        return json.loads((pkt / "contract.json").read_text(encoding="utf-8"))["data_contract"]["rules"]
    except Exception:  # noqa: BLE001
        return []


def load(level):
    """계약 데모월드(scenario_data) 모드 — 검증 세계를 그대로 재생."""
    pkt = PACKETS / f"planning_packet_squad_{level}"
    contract = json.loads((pkt / "contract.json").read_text(encoding="utf-8"))
    worlds = contract["data_contract"]["scenario_data"]
    return _game_logic(level), worlds, contract["data_contract"]["rules"]


def load_levels(level, levels_path):
    """실미션 레벨 모드 — squad_levels.json을 로드, 레벨별 최단 솔루션을 BFS로 풀어 actions로 붙여 재생 가능하게.
    풀이불가 레벨은 건너뛰고 경고. 룰 패널은 계약 누적 규칙을 보여줌."""
    from play_signals import solve_levels
    game_logic = _game_logic(level)
    levels = json.loads(Path(levels_path).read_text(encoding="utf-8"))
    if not levels:
        raise RuntimeError(f"{levels_path} 비어있음 — 먼저 propose_levels로 레벨 생성")
    sols = solve_levels(levels, game_logic, "squad")
    worlds, skipped = [], []
    for lv, sol in zip(levels, sols):
        name = lv.get("name") or lv.get("id", "?")
        if not sol:
            skipped.append(name); continue
        worlds.append({"id": name, "initialState": lv["initialState"], "actions": sol,
                       "covers_reqs": [lv.get("teaches", ""), f"{len(sol)}수 해법"]})
    return game_logic, worlds, _rules(level), skipped


HTML = """<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>부대 전술 뷰어 — squad %LEVEL%</title>
<style>
  :root { color-scheme: dark; }
  body { margin:0; background:#11131a; color:#e7e9f0; font:14px/1.5 system-ui,sans-serif; }
  .wrap { max-width:760px; margin:0 auto; padding:16px; }
  h1 { font-size:18px; margin:4px 0 2px; }
  .sub { color:#9aa0b4; font-size:12px; margin-bottom:12px; }
  .bar { display:flex; gap:8px; flex-wrap:wrap; align-items:center; margin:10px 0; }
  select,button { background:#1b1e29; color:#e7e9f0; border:1px solid #333a52; border-radius:7px;
    padding:7px 11px; font-size:14px; cursor:pointer; }
  button:active { transform:translateY(1px); }
  button:disabled { opacity:.4; cursor:default; }
  canvas { background:#0c0e14; border:1px solid #262b3d; border-radius:10px; display:block; margin:6px 0; width:100%; max-width:520px; }
  .status { font-weight:700; }
  .v { color:#7ee0a0; } .d { color:#ff8d8d; } .f { color:#c9b56a; } .p { color:#9aa0b4; }
  .legend { font-size:12px; color:#9aa0b4; }
  .dot { display:inline-block; width:10px; height:10px; border-radius:50%; vertical-align:middle; margin:0 3px 0 8px; }
  .desc { font-size:12px; color:#aeb4c8; min-height:18px; }
  .cards { font-size:12px; color:#8b91a6; margin-top:14px; border-top:1px solid #262b3d; padding-top:8px; }
</style></head><body><div class="wrap">
<h1>부대 전술 뷰어 <span class="p">— squad %LEVEL%</span></h1>
<div class="sub">검증된 엔진을 그대로 재생(읽기전용). 아군 여럿이 행동하고, 적이 가장 가까운 아군을 추격·공격한다.</div>
<div class="bar">
  <select id="scn"></select>
  <button id="reset">⏮ 리셋</button><button id="prev">◀ 이전</button>
  <button id="next">다음 ▶</button><button id="play">▶▶ 재생</button>
</div>
<div class="desc" id="desc"></div>
<canvas id="cv" width="520" height="520"></canvas>
<div class="bar">
  <span>턴 <b id="turn">0</b></span>
  <span class="status" id="st"></span>
  <span class="legend"><span class="dot" style="background:#5b8cff"></span>아군<span class="dot" style="background:#ff5b6e"></span>적</span>
</div>
<div class="cards" id="cards"></div>
</div>
<script>
const GAME_LOGIC = (function(){ const exports={}; const module={exports};
%GAME_LOGIC%
 return module.exports; })();
const WORLDS = %WORLDS%;
const RULES = %RULES%;

function clone(s){ return JSON.parse(JSON.stringify(s)); }
function freshState(w){ const s = clone(w.initialState); s.turn = 0;
  s.allies = s.allies.map(u=>({...u})); s.enemies = s.enemies.map(u=>({...u})); return s; }
// k 액션 적용 후 상태 + status (검증 엔진 그대로: updateState가 state 변경 + status 반환)
function stateAt(w, k){
  const s = freshState(w); let status='PLAYING';
  for(let i=0;i<k;i++){
    const r = GAME_LOGIC.updateState(s, w.actions[i]);
    if(r==='VICTORY'||r==='DEFEAT'){ status=r; return {s, status, ended:i+1}; }
  }
  if(k>=w.actions.length) status='FINISHED';
  return {s, status, ended:null};
}

const cv=document.getElementById('cv'), ctx=cv.getContext('2d');
let wi=0, step=0, timer=null;

function gridSize(w){ return w.initialState.gridSize; }
function draw(w){
  const N=gridSize(w), S=cv.width, c=S/N;
  ctx.clearRect(0,0,S,S);
  ctx.strokeStyle='#222838';
  for(let i=0;i<=N;i++){ ctx.beginPath(); ctx.moveTo(i*c,0); ctx.lineTo(i*c,S); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(0,i*c); ctx.lineTo(S,i*c); ctx.stroke(); }
  const {s,status}=stateAt(w, step);
  const unit=(u,color,dead)=>{ const [x,y]=u.pos; const cx=x*c+c/2, cy=y*c+c/2;
    ctx.globalAlpha = dead?0.28:1; ctx.fillStyle=color;
    ctx.beginPath(); ctx.arc(cx,cy,c*0.33,0,7); ctx.fill();
    ctx.globalAlpha=1; ctx.fillStyle='#fff'; ctx.font=`bold ${Math.floor(c*0.26)}px system-ui`;
    ctx.textAlign='center'; ctx.textBaseline='middle';
    ctx.fillText((dead?'✕':u.id), cx, cy-c*0.04);
    ctx.font=`${Math.floor(c*0.2)}px system-ui`; ctx.fillStyle = dead?'#888':'#dfe';
    ctx.fillText('hp'+u.hp, cx, cy+c*0.26); };
  for(const e of s.enemies) unit(e,'#ff5b6e', e.hp<=0);
  for(const a of s.allies) unit(a,'#5b8cff', a.hp<=0);
  document.getElementById('turn').textContent=s.turn;
  const st=document.getElementById('st');
  const cls={VICTORY:'v',DEFEAT:'d',FINISHED:'f',PLAYING:'p'}[status];
  st.className='status '+cls; st.textContent=status;
  document.getElementById('prev').disabled = step<=0;
  document.getElementById('next').disabled = (status==='VICTORY'||status==='DEFEAT'||step>=w.actions.length);
}
function render(){ draw(WORLDS[wi]); }
function setScn(i){ wi=i; step=0; stopPlay();
  const w=WORLDS[i];
  document.getElementById('desc').textContent =
    `${w.id} · 아군 ${w.initialState.allies.length} · 적 ${w.initialState.enemies.length} · ${(w.covers_reqs||[]).join(', ')}`;
  render(); }
function next(){ const w=WORLDS[wi]; const {status}=stateAt(w,step);
  if(status==='VICTORY'||status==='DEFEAT'||step>=w.actions.length){ stopPlay(); return; }
  step++; render(); }
function prev(){ if(step>0){ step--; render(); } }
function stopPlay(){ if(timer){ clearInterval(timer); timer=null; document.getElementById('play').textContent='▶▶ 재생'; } }
function play(){ if(timer){ stopPlay(); return; }
  document.getElementById('play').textContent='⏸ 정지';
  timer=setInterval(()=>{ const w=WORLDS[wi]; const {status}=stateAt(w,step);
    if(status==='VICTORY'||status==='DEFEAT'||step>=w.actions.length){ stopPlay(); } else { step++; render(); } }, 650); }

const sel=document.getElementById('scn');
WORLDS.forEach((w,i)=>{ const o=document.createElement('option'); o.value=i;
  o.textContent=`${w.id} (아군${w.initialState.allies.length}·적${w.initialState.enemies.length})`; sel.appendChild(o); });
sel.onchange=e=>setScn(+e.target.value);
document.getElementById('reset').onclick=()=>{ step=0; stopPlay(); render(); };
document.getElementById('next').onclick=next;
document.getElementById('prev').onclick=prev;
document.getElementById('play').onclick=play;
document.getElementById('cards').innerHTML='<b>누적 규칙</b><br>'+RULES.map(r=>'· '+r).join('<br>');
setScn(0);
</script></body></html>
"""


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--level", default="l4", help="squad 레벨(kernel|l1|l2|...). 검증된 누적 base를 embed")
    ap.add_argument("--source", default="contract", choices=["contract", "levels"],
                    help="contract=계약 데모월드 재생(기본) | levels=실미션 레벨(squad_levels.json) 솔루션 재생")
    ap.add_argument("--levels", default=None, help="levels 모드의 레벨팩 경로(기본=tactics/play/squad_levels.json)")
    args = ap.parse_args(argv)

    skipped = []
    if args.source == "levels":
        levels_path = args.levels or (PLAY / "squad_levels.json")
        game_logic, worlds, rules, skipped = load_levels(args.level, levels_path)
        if not worlds:
            print(f"  [squad {args.level}] 재생 가능한 레벨 0개(전부 풀이불가?) — 렌더 생략"); return 1
    else:
        game_logic, worlds, rules = load(args.level)

    html = (HTML.replace("%LEVEL%", f"{args.level} · {args.source}")
            .replace("%GAME_LOGIC%", game_logic)
            .replace("%WORLDS%", json.dumps(worlds, ensure_ascii=False))
            .replace("%RULES%", json.dumps(rules, ensure_ascii=False)))
    OUT = PLAY / "squad.html"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    kind = "실미션 레벨(솔루션 재생)" if args.source == "levels" else "계약 데모월드"
    print(f"  [squad {args.level}] {kind} {len(worlds)}세계 뷰어 → {OUT}")
    if skipped:
        print(f"  ⚠ 풀이불가로 건너뜀 {len(skipped)}개: {', '.join(skipped[:4])}")
    print(f"  아군 다수·적 AI 추격을 턴별 재생(읽기전용·검증 엔진 그대로). 브라우저로 열기.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
