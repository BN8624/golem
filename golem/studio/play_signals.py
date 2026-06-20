# 실노출 신호(결정적) — 검증 엔진 위에서 레벨의 풀이가능성·최소턴·지배전략·카드영향을 계산해 사람 판단(재미/밸런스)에 보탬
"""북극성 퍼널의 마지막 칸 '[실노출]→신호'. 엔진이 결정적이라 랜덤 플레이테스트 대신 검증 l9 엔진 위에서
측정 가능한 신호를 뽑는다(잴 수 있는 페이싱·지배전략=코드, 재미·취향=사람):
  - solvable / min_turns: 승리가 가능한가, 최소 몇 수(BFS, 상태 dedup·경계/깊이 cap).
  - 지배전략: greedy 멜레·greedy 사거리가 거저 이기나(둘 다 이기면 깊이 얕음=FLAG 후보).
  - 카드영향: hero의 opt-in 필드(mana/anomaly_dmg/corrosion/execute) 제거 시 풀이가능성/최소턴 변화(카드가 실제로 결정적인가).
판정은 사람이. 이 신호는 '재미있나'를 사람이 데이터로 보게 하는 보조다. (키0)

사용: python play_signals.py [--level l9]
"""

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

const out=[];
for(const lvl of LV){
  const init=lvl.initialState;
  const minw=bfsMinWin(init);
  const gm=greedy(init,'melee'), gr=greedy(init,'ranged');
  const [stripped, removed]=stripCard(init);
  const minwNoCard = removed.length? bfsMinWin(stripped): null;
  out.push({name:lvl.name, solvable: minw!==null, min_turns: minw,
            greedy_melee: gm, greedy_ranged: gr,
            card_fields: removed, min_turns_no_card: minwNoCard});
}
process.stdout.write(JSON.stringify(out));
"""


def verdict(s):
    if not s["solvable"]:
        return "FLAG 풀이불가(레벨 결함)"
    flags = []
    if s["greedy_melee"] == "VICTORY" and s["greedy_ranged"] == "VICTORY":
        flags.append("지배전략 둘 다 거저 승리(깊이 얕음)")
    if s["card_fields"]:
        if s["min_turns_no_card"] is None:
            flags.append(f"카드 결정적({'·'.join(s['card_fields'])} 없으면 풀이불가)")
        elif s["min_turns"] is not None and s["min_turns_no_card"] > s["min_turns"]:
            flags.append(f"카드 유효(없으면 {s['min_turns']}→{s['min_turns_no_card']}수)")
        else:
            flags.append(f"카드 영향 약함({'·'.join(s['card_fields'])} 빼도 동급)")
    return "OK · " + "; ".join(flags) if flags else "OK"


def compute_signals(levels, gl_src):
    """레벨 리스트 + 엔진 소스 → 신호 dict 리스트(재사용 가능·키0). propose_levels가 검증 게이트로 씀."""
    js = SEARCH_JS.replace("__GAME_LOGIC__", gl_src).replace("__LEVEL_JSON__", json.dumps(levels, ensure_ascii=False))
    tmp = HERE / "_play_signals_tmp.js"
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
    args = ap.parse_args(argv)
    sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE.parent.parent))
    try:
        from config import force_utf8_stdout
        force_utf8_stdout()
    except Exception:  # noqa: BLE001
        pass
    gl = import_module(f"gen_tactics_{args.level}_golden").REF_GAME_LOGIC
    levels = import_module("gen_tactics_interactive").LEVELS
    sig = compute_signals(levels, gl)
    print(f"== 실노출 신호(결정적, {args.level} 엔진) — 판정은 사람 ==")
    for s in sig:
        mt = s["min_turns"] if s["solvable"] else "-"
        print(f"  {s['name']}")
        print(f"    풀이={'O' if s['solvable'] else 'X'} 최소턴={mt} | greedy 멜레={s['greedy_melee']} 사거리={s['greedy_ranged']}"
              + (f" | 카드{s['card_fields']} 없을때 최소턴={s['min_turns_no_card']}" if s['card_fields'] else ""))
        print(f"    → {verdict(s)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
