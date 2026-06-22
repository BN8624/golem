# 실노출 신호(결정적) + 재미 평가 — 검증 엔진 위에서 레벨의 풀이가능성·최소턴·지배전략·카드영향·선택지·치사율을 계산하고 휴리스틱 재미 점수(A/B/C/D)로 합쳐 자동 선별·정렬에 보탬
"""북극성 퍼널의 마지막 칸 '[실노출]→신호'. 엔진이 결정적이라 랜덤 플레이테스트 대신 검증 l9 엔진 위에서
측정 가능한 신호를 뽑는다(잴 수 있는 페이싱·지배전략=코드, 재미·취향=사람):
  - solvable / min_turns: 승리가 가능한가, 최소 몇 수(BFS, 상태 dedup·경계/깊이 cap).
  - 지배전략: greedy 멜레·greedy 사거리가 거저 이기나(둘 다 이기면 깊이 얕음=FLAG 후보).
  - 선택지 수(branch_first): 최단해의 서로 다른 첫 수 가짓수(1=단선 퍼즐, 클수록 진짜 선택).
  - 전략 다양성(shortest_solutions): 최단 길이 해의 개수(1=한 전략 몰빵).
  - 치사율(lethality): 탐색 영역에서 즉사(DEFEAT)로 끝나는 간선 비율(높을수록 한 수 실수=즉사, 재시도 빡셈).
  - 카드영향: hero의 opt-in 필드(mana/anomaly_dmg/corrosion/execute) 제거 시 풀이가능성/최소턴 변화(카드가 실제로 결정적인가).
판정은 사람이. 이 신호는 '재미있나'를 사람이 데이터로 보게 하는 보조다. (키0)

사용: python play_signals.py [--level l9]
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
import subprocess
import sys
from importlib import import_module
from pathlib import Path

HERE = Path(__file__).resolve().parent

# 검증 엔진 위 BFS + 그리디 프로브(노드). updateState/checkGameState는 골렘 검증 코드 그대로.
SEARCH_JS = r"""
__GAME_LOGIC__
const LV = __LEVEL_JSON__;
const DEPTH = 14, STATE_CAP = 400000;

function mkState(init){
  return {...init, hero:{...init.hero, pos:[...init.hero.pos]},
          enemies:init.enemies.map(e=>({...e,pos:[...e.pos]})), turn:0};
}
function bbox(init){
  let mx=2,my=2; const all=[init.hero.pos,...init.enemies.map(e=>e.pos)];
  (init.route||[]).forEach(b=>b.enemies.forEach(e=>all.push(e.pos)));
  for(const p of all){mx=Math.max(mx,p[0]);my=Math.max(my,p[1]);}
  return [mx+1,my+1];
}
function actionsFor(s){
  const acts=[{type:'move',dir:[1,0]},{type:'move',dir:[-1,0]},{type:'move',dir:[0,1]},{type:'move',dir:[0,-1]}];
  for(const e of s.enemies) if(e.hp>0){acts.push({type:'attack',target:e.id});acts.push({type:'ranged_attack',target:e.id});}
  return acts;
}
function key(s){return JSON.stringify([s.hero.hp,s.hero.pos,s.hero.mana||0,s.route_index||0,
  s.enemies.map(e=>[e.id,e.hp,e.pos])]);}

function bfsMinWin(init){
  const ic=init.enemies.length, [bx,by]=bbox(init);
  let frontier=[mkState(init)]; const seen=new Set([key(frontier[0])]); let depth=0, cap=STATE_CAP;
  while(frontier.length && depth<DEPTH){
    const next=[];
    for(const s of frontier){
      for(const a of actionsFor(s)){
        if(a.type==='move'){const nx=s.hero.pos[0]+a.dir[0],ny=s.hero.pos[1]+a.dir[1];
          if(nx<0||ny<0||nx>bx||ny>by) continue;}            // 경계 cap(무한 이동 방지)
        const ns=GLupdate(s,a); const r=GLcheck(ns,ic);
        if(r==='VICTORY') return depth+1;
        if(r) continue;                                      // DEFEAT/FINISHED 가지 닫음
        const k=key(ns); if(seen.has(k)) continue; seen.add(k); next.push(ns);
        if(seen.size>cap) return null;                       // 폭주 cap
      }
    }
    frontier=next; depth++;
  }
  return null;
}
function GLupdate(s,a){return exports.updateState(s,a);}
function GLcheck(s,ic){return exports.checkGameState(s,ic);}

function nearest(s){let best=null,bd=1e9;for(const e of s.enemies)if(e.hp>0){const d=Math.abs(s.hero.pos[0]-e.pos[0])+Math.abs(s.hero.pos[1]-e.pos[1]);if(d<bd){bd=d;best=e;}}return best;}
function stepToward(s,e){const dx=e.pos[0]-s.hero.pos[0],dy=e.pos[1]-s.hero.pos[1];
  if(Math.abs(dx)>=Math.abs(dy)&&dx!==0)return{type:'move',dir:[dx>0?1:-1,0]};
  if(dy!==0)return{type:'move',dir:[0,dy>0?1:-1]};return{type:'move',dir:[dx>0?1:-1,0]};}
function greedy(init, mode){  // mode: 'melee' | 'ranged'
  let s=mkState(init); const ic=init.enemies.length;
  for(let t=0;t<DEPTH+6;t++){
    const e=nearest(s); if(!e){return 'FINISHED';}
    const d=Math.abs(s.hero.pos[0]-e.pos[0])+Math.abs(s.hero.pos[1]-e.pos[1]);
    let a;
    if(mode==='ranged'){ a = (d>=2&&d<=3)?{type:'ranged_attack',target:e.id} : d===1?{type:'attack',target:e.id} : stepToward(s,e); }
    else { a = d===1?{type:'attack',target:e.id} : stepToward(s,e); }
    s=GLupdate(s,a); const r=GLcheck(s,ic); if(r) return r;
  }
  return 'FINISHED';
}

function stripCard(init){  // hero opt-in 카드 필드 제거본
  const h={...init.hero}; let removed=[];
  for(const f of ['mana','anomaly_dmg','corrosion','execute']) if(f in h){delete h[f];removed.push(f);}
  return [{...init, hero:h}, removed];
}

// 재미 신호: 최단해 레이어까지 BFS — 선택지 수(서로다른 첫 수)·최단해 개수·치사율(즉사 간선 비율)
function analyze(init){
  const ic=init.enemies.length, [bx,by]=bbox(init);
  let frontier=[{s:mkState(init), fm:null}];
  const seen=new Set([key(frontier[0].s)]); let depth=0, cap=STATE_CAP;
  let minWin=null, solCount=0; const winFirst=new Set();
  let defeatEdges=0, totalEdges=0;
  while(frontier.length && depth<DEPTH){
    const next=[];
    for(const node of frontier){
      for(const a of actionsFor(node.s)){
        if(a.type==='move'){const nx=node.s.hero.pos[0]+a.dir[0],ny=node.s.hero.pos[1]+a.dir[1];
          if(nx<0||ny<0||nx>bx||ny>by) continue;}
        const ns=GLupdate(node.s,a); const r=GLcheck(ns,ic);
        totalEdges++; const fm=node.fm||a;
        if(r==='VICTORY'){ if(minWin===null) minWin=depth+1;
          if(depth+1===minWin){ solCount++; winFirst.add(JSON.stringify(fm)); } continue; }
        if(r==='DEFEAT'){ defeatEdges++; continue; }
        if(r) continue;
        const k=key(ns); if(seen.has(k)) continue; seen.add(k); next.push({s:ns, fm});
        if(seen.size>cap) return {minWin, solCount, branchFirst:winFirst.size, lethality:null};
      }
    }
    if(minWin!==null) break;   // 최단 깊이 레이어를 다 봤으니 종료(더 깊은 해는 무의미)
    frontier=next; depth++;
  }
  return {minWin, solCount, branchFirst:winFirst.size,
          lethality: totalEdges? +(defeatEdges/totalEdges).toFixed(2):0};
}

const out=[];
for(const lvl of LV){
  const init=lvl.initialState;
  const A=analyze(init);
  const gm=greedy(init,'melee'), gr=greedy(init,'ranged');
  const [stripped, removed]=stripCard(init);
  const minwNoCard = removed.length? bfsMinWin(stripped): null;
  out.push({name:lvl.name, solvable: A.minWin!==null, min_turns: A.minWin,
            branch_first: A.branchFirst, shortest_solutions: A.solCount, lethality: A.lethality,
            greedy_melee: gm, greedy_ranged: gr,
            card_fields: removed, min_turns_no_card: minwNoCard});
}
process.stdout.write(JSON.stringify(out));
"""


# 부대(squad) 신호 — 아군 여럿×행동 BFS + 그리디(전진·공격). updateState는 mutable(state변경+status 반환)이라 BFS서 clone.
SQUAD_SEARCH_JS = r"""
__GAME_LOGIC__
const GL = module.exports;
const LV = __LEVEL_JSON__;
const DEPTH = 11, STATE_CAP = 300000;

function clone(s){ return JSON.parse(JSON.stringify(s)); }
function mkState(init){ const s=clone(init); s.turn=0; return s; }
function actionsFor(s){ const acts=[];
  for(const a of s.allies) if(a.hp>0){
    acts.push({unit:a.id,type:'attack'});
    acts.push({unit:a.id,type:'move',dir:[1,0]}); acts.push({unit:a.id,type:'move',dir:[-1,0]});
    acts.push({unit:a.id,type:'move',dir:[0,1]}); acts.push({unit:a.id,type:'move',dir:[0,-1]});
  } return acts; }
function key(s){ return JSON.stringify([s.allies.map(a=>[a.id,a.hp,a.pos]), s.enemies.map(e=>[e.id,e.hp,e.pos])]); }

function bfsMinWin(init){
  let frontier=[mkState(init)]; const seen=new Set([key(frontier[0])]); let depth=0;
  while(frontier.length && depth<DEPTH){
    const next=[];
    for(const s of frontier){
      for(const a of actionsFor(s)){
        const ns=clone(s); const r=GL.updateState(ns,a);   // mutable: ns 변경 + status 반환
        if(r==='VICTORY') return depth+1;
        if(r==='DEFEAT') continue;
        const k=key(ns); if(seen.has(k)) continue; seen.add(k); next.push(ns);
        if(seen.size>STATE_CAP) return null;
      }
    }
    frontier=next; depth++;
  }
  return null;
}
function nearestEnemy(pos,s){ let best=null,bd=1e9; for(const e of s.enemies) if(e.hp>0){
  const d=Math.abs(pos[0]-e.pos[0])+Math.abs(pos[1]-e.pos[1]); if(d<bd){bd=d;best=e;} } return [best,bd]; }
function greedy(init){  // 각 단계: 인접 적 있으면 그 아군이 공격, 없으면 적과 제일 가까운 아군이 전진
  let s=mkState(init);
  for(let t=0;t<DEPTH+12;t++){
    const living=s.allies.filter(a=>a.hp>0); if(!living.length) return 'DEFEAT';
    let act=null;
    for(const a of living){ const [e,d]=nearestEnemy(a.pos,s); if(e&&d<=1){ act={unit:a.id,type:'attack'}; break; } }
    if(!act){ let bestA=null,bd=1e9,be=null;
      for(const a of living){ const [e,d]=nearestEnemy(a.pos,s); if(e&&d<bd){bd=d;bestA=a;be=e;} }
      if(!bestA) return 'FINISHED';
      const dx=be.pos[0]-bestA.pos[0], dy=be.pos[1]-bestA.pos[1];
      const dir=(Math.abs(dx)>=Math.abs(dy)&&dx!==0)?[dx>0?1:-1,0]:(dy!==0?[0,dy>0?1:-1]:[dx>0?1:-1,0]);
      act={unit:bestA.id,type:'move',dir}; }
    const r=GL.updateState(s,act); if(r) return r;
  }
  return 'FINISHED';
}
function stripCard(init){ const opt=['range','knockback','flank_bonus','reflect_dmg','armor']; let removed=[];
  const strip=arr=>arr.map(u=>{const c={...u}; for(const f of opt) if(f in c){delete c[f]; if(!removed.includes(f))removed.push(f);} return c;});
  return [{...init, allies:strip(init.allies), enemies:strip(init.enemies)}, removed]; }

// 재미 신호(부대): 최단해 레이어까지 BFS — 선택지 수·최단해 개수·치사율
function analyze(init){
  let frontier=[{s:mkState(init), fm:null}];
  const seen=new Set([key(frontier[0].s)]); let depth=0;
  let minWin=null, solCount=0; const winFirst=new Set();
  let defeatEdges=0, totalEdges=0;
  while(frontier.length && depth<DEPTH){
    const next=[];
    for(const node of frontier){
      for(const a of actionsFor(node.s)){
        const ns=clone(node.s); const r=GL.updateState(ns,a);
        totalEdges++; const fm=node.fm||a;
        if(r==='VICTORY'){ if(minWin===null) minWin=depth+1;
          if(depth+1===minWin){ solCount++; winFirst.add(JSON.stringify(fm)); } continue; }
        if(r==='DEFEAT'){ defeatEdges++; continue; }
        const k=key(ns); if(seen.has(k)) continue; seen.add(k); next.push({s:ns, fm});
        if(seen.size>STATE_CAP) return {minWin, solCount, branchFirst:winFirst.size, lethality:null};
      }
    }
    if(minWin!==null) break;
    frontier=next; depth++;
  }
  return {minWin, solCount, branchFirst:winFirst.size,
          lethality: totalEdges? +(defeatEdges/totalEdges).toFixed(2):0};
}

const out=[];
for(const lvl of LV){ const init=lvl.initialState;
  const A=analyze(init); const g=greedy(init);
  const [stripped,removed]=stripCard(init);
  const minwNo = removed.length? bfsMinWin(stripped): null;
  out.push({name:lvl.name||lvl.id, solvable:A.minWin!==null, min_turns:A.minWin,
            branch_first:A.branchFirst, shortest_solutions:A.solCount, lethality:A.lethality,
            greedy:g, card_fields:removed, min_turns_no_card:minwNo});
}
process.stdout.write(JSON.stringify(out));
"""


# 부대 솔버 — 레벨별 최단 승리 액션 수열을 BFS로 반환(경로 추적). 뷰어가 솔루션 턴재생에 씀.
SQUAD_SOLVE_JS = r"""
__GAME_LOGIC__
const GL = module.exports;
const LV = __LEVEL_JSON__;
const DEPTH = 14, STATE_CAP = 400000;
function clone(s){ return JSON.parse(JSON.stringify(s)); }
function mkState(init){ const s=clone(init); s.turn=0; return s; }
function actionsFor(s){ const acts=[];
  for(const a of s.allies) if(a.hp>0){
    acts.push({unit:a.id,type:'attack'});
    acts.push({unit:a.id,type:'move',dir:[1,0]}); acts.push({unit:a.id,type:'move',dir:[-1,0]});
    acts.push({unit:a.id,type:'move',dir:[0,1]}); acts.push({unit:a.id,type:'move',dir:[0,-1]});
  } return acts; }
function key(s){ return JSON.stringify([s.allies.map(a=>[a.id,a.hp,a.pos]), s.enemies.map(e=>[e.id,e.hp,e.pos])]); }
function solve(init){
  let frontier=[{s:mkState(init), path:[]}];
  const seen=new Set([key(frontier[0].s)]); let depth=0;
  while(frontier.length && depth<DEPTH){
    const next=[];
    for(const node of frontier){
      for(const a of actionsFor(node.s)){
        const ns=clone(node.s); const r=GL.updateState(ns,a); const np=node.path.concat([a]);
        if(r==='VICTORY') return np;
        if(r==='DEFEAT') continue;
        const k=key(ns); if(seen.has(k)) continue; seen.add(k); next.push({s:ns, path:np});
        if(seen.size>STATE_CAP) return null;
      }
    }
    frontier=next; depth++;
  }
  return null;
}
const out=[];
for(const lvl of LV){ out.push(solve(lvl.initialState)); }
process.stdout.write(JSON.stringify(out));
"""


def solve_levels(levels, gl_src, family="squad"):
    """레벨별 최단 승리 액션 수열을 반환(BFS·키0). 풀이불가면 그 자리 None. 뷰어가 솔루션 재생에 씀.
    현재 squad 전용(아군 다중유닛·mutable 엔진)."""
    if family != "squad":
        raise NotImplementedError("solve_levels는 현재 squad 전용")
    js = SQUAD_SOLVE_JS.replace("__GAME_LOGIC__", gl_src).replace("__LEVEL_JSON__", json.dumps(levels, ensure_ascii=False))
    BUILD_RUNS.mkdir(parents=True, exist_ok=True)
    tmp = BUILD_RUNS / "_solve_tmp.js"
    tmp.write_text(js, encoding="utf-8")
    try:
        r = subprocess.run(["node", str(tmp)], capture_output=True, text=True, encoding="utf-8", timeout=300)
    finally:
        tmp.unlink(missing_ok=True)
    if r.returncode != 0:
        raise RuntimeError(f"node 실패: {r.stderr[:400]}")
    return json.loads(r.stdout)


def verdict(s):
    if not s["solvable"]:
        return "FLAG 풀이불가(레벨 결함)"
    flags = []
    # 부대(squad)=단일 greedy 키, 영웅(tactics)=멜레·사거리 두 키
    if "greedy" in s:
        if s["greedy"] == "VICTORY":
            flags.append("그리디(전진·공격)로 거저 승리(깊이 얕음)")
    elif s.get("greedy_melee") == "VICTORY" and s.get("greedy_ranged") == "VICTORY":
        flags.append("지배전략 둘 다 거저 승리(깊이 얕음)")
    # 재미 신호(선택지·전략 다양성·재시도 가치) — 판정은 사람, 여기선 플래그만
    bf = s.get("branch_first")
    if bf is not None and bf <= 1:
        flags.append("선택지 좁음(최단해 첫 수 1가지=단선)")
    ss = s.get("shortest_solutions")
    if ss is not None and ss == 1:
        flags.append("전략 단일(최단해 1개=몰빵)")
    leth = s.get("lethality")
    if leth is not None and leth >= 0.5:
        flags.append(f"고치사율({leth}=한 수 실수 즉사 잦음, 재시도 빡셈)")
    if s["card_fields"]:
        if s["min_turns_no_card"] is None:
            flags.append(f"카드 결정적({'·'.join(s['card_fields'])} 없으면 풀이불가)")
        elif s["min_turns"] is not None and s["min_turns_no_card"] > s["min_turns"]:
            flags.append(f"카드 유효(없으면 {s['min_turns']}→{s['min_turns_no_card']}수)")
        else:
            flags.append(f"카드 영향 약함({'·'.join(s['card_fields'])} 빼도 동급)")
    return "OK · " + "; ".join(flags) if flags else "OK"


def fun_score(s):
    """결정적 재미 평가(휴리스틱·키0): 신호들을 0~100 점수+등급(A/B/C/D)으로 합친다.
    가중치·임계값은 미보정(뷰어 플레이로 보정 예정) — '정답'이 아니라 정렬·자동탈락용 보조다.
    A(재밌음 후보)>=70, B(보통)>=50, C(약함)>=30, D(버릴 후보)<30. 풀이불가=REJECT."""
    if not s.get("solvable"):
        return 0, "REJECT", ["풀이불가(레벨 결함)"]
    score, r = 50, []
    # 1) 지배전략(깊이): 그리디로 거저 이기면 감점, 없으면 가점
    if "greedy" in s:  # squad
        if s["greedy"] == "VICTORY":
            score -= 25; r.append("그리디 거저승리 -25")
        else:
            score += 15; r.append("지배전략 없음 +15")
    else:  # tactics(멜레·사거리)
        gv = (s.get("greedy_melee") == "VICTORY") + (s.get("greedy_ranged") == "VICTORY")
        if gv == 2:
            score -= 25; r.append("두 그리디 거저승리 -25")
        elif gv == 1:
            score -= 5; r.append("한 그리디 통함 -5")
        else:
            score += 15; r.append("지배전략 없음 +15")
    # 2) 선택지(최단해 첫 수 가짓수)
    bf = s.get("branch_first") or 0
    if bf >= 3:
        score += 15; r.append(f"선택지 풍부({bf}) +15")
    elif bf == 2:
        score += 8; r.append("선택지 있음(2) +8")
    else:
        score -= 15; r.append(f"선택지 좁음({bf}) -15")
    # 3) 전략 다양성(최단해 개수)
    ss = s.get("shortest_solutions") or 0
    if ss >= 4:
        score += 8; r.append(f"최단해 다양({ss}) +8")
    elif ss >= 2:
        score += 4; r.append(f"최단해 복수({ss}) +4")
    else:
        score -= 8; r.append("최단해 단일 -8")
    # 4) 카드 관련성(카드 테스트 레벨만)
    if s.get("card_fields"):
        nc, mt = s.get("min_turns_no_card"), s.get("min_turns")
        if nc is None or (mt is not None and nc > mt):
            score += 12; r.append("카드 결정적 +12")
        else:
            score -= 12; r.append("카드 영향 약함 -12")
    # 5) 페이싱(최소턴)
    mt = s.get("min_turns") or 0
    if 3 <= mt <= 9:
        score += 8; r.append(f"페이싱 적정({mt}) +8")
    elif mt <= 1:
        score -= 10; r.append(f"즉결({mt}) -10")
    elif mt > 9:
        score += 2
    # 6) 재시도/치사율
    leth = s.get("lethality")
    if leth is None:
        pass
    elif leth == 0:
        score -= 3; r.append("위험 전무 -3")
    elif leth < 0.4:
        score += 8; r.append(f"긴장 적정({leth}) +8")
    elif leth < 0.6:
        score += 2
    else:
        score -= 10; r.append(f"즉사 과함({leth}) -10")
    score = max(0, min(100, score))
    grade = "A" if score >= 70 else "B" if score >= 50 else "C" if score >= 30 else "D"
    return score, grade, r


def compute_signals(levels, gl_src, family="tactics"):
    """레벨 리스트 + 엔진 소스 → 신호 dict 리스트(재사용 가능·키0). propose_levels가 검증 게이트로 씀.
    family=tactics(영웅 BFS·멜레/사거리 그리디) | squad(부대 다중유닛 BFS·전진/공격 그리디)."""
    search = SQUAD_SEARCH_JS if family == "squad" else SEARCH_JS
    js = search.replace("__GAME_LOGIC__", gl_src).replace("__LEVEL_JSON__", json.dumps(levels, ensure_ascii=False))
    tmp = BUILD_RUNS / "_play_signals_tmp.js"
    tmp.write_text(js, encoding="utf-8")
    try:
        r = subprocess.run(["node", str(tmp)], capture_output=True, text=True, encoding="utf-8", timeout=300)
    finally:
        tmp.unlink(missing_ok=True)
    if r.returncode != 0:
        raise RuntimeError(f"node 실패: {r.stderr[:400]}")
    return json.loads(r.stdout)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--level", default="l9", help="embed할 검증 엔진(기본 l9)")
    ap.add_argument("--family", default="tactics", help="tactics(영웅)|squad(부대)")
    args = ap.parse_args(argv)
    sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE.parent.parent))
    try:
        from config import force_utf8_stdout
        force_utf8_stdout()
    except Exception:  # noqa: BLE001
        pass
    gl = import_module(f"gen_{args.family}_{args.level}_golden").REF_GAME_LOGIC
    if args.family == "squad":
        # squad 레벨원: 계약 세계(아직 전용 levels.json 전이라 검증 월드로 신호 표시)
        c = json.loads((PACKETS / f"planning_packet_squad_{args.level}" / "contract.json").read_text(encoding="utf-8"))
        levels = [{"name": w["id"], "initialState": w["initialState"]} for w in c["data_contract"]["scenario_data"]]
    else:
        levels = import_module("gen_tactics_interactive").LEVELS
    sig = compute_signals(levels, gl, args.family)
    print(f"== 재미 평가 + 실노출 신호(결정적, {args.family} {args.level} 엔진) — 점수는 휴리스틱 보조, 최종 취향은 사람 ==")
    scored = []
    for s in sig:
        sc, gr, reasons = fun_score(s)
        s["fun_score"], s["fun_grade"] = sc, gr
        scored.append((sc, gr, s, reasons))
        mt = s["min_turns"] if s["solvable"] else "-"
        gtxt = f"greedy={s['greedy']}" if "greedy" in s else f"greedy 멜레={s.get('greedy_melee')} 사거리={s.get('greedy_ranged')}"
        fun = f" | 선택지={s.get('branch_first')} 최단해={s.get('shortest_solutions')} 치사율={s.get('lethality')}"
        print(f"  [{gr} {sc:>3}] {s['name']}: 풀이={'O' if s['solvable'] else 'X'} 최소턴={mt} | {gtxt}{fun}"
              + (f" | 카드{s['card_fields']} 없을때={s['min_turns_no_card']}" if s['card_fields'] else "")
              + f"  → {verdict(s)}")
    # 재미 등급 분포 + 버릴 후보 요약
    from collections import Counter
    dist = Counter(gr for _, gr, _, _ in scored)
    weak = [(sc, s["name"]) for sc, gr, s, _ in scored if gr in ("C", "D", "REJECT")]
    print(f"\n== 재미 등급 분포: " + " ".join(f"{g}={dist.get(g,0)}" for g in ("A", "B", "C", "D", "REJECT")) + " ==")
    if weak:
        print("버릴 후보(C이하):")
        for sc, nm in sorted(weak):
            print(f"  - [{sc}] {nm}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
