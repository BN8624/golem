# 전술 카드 자율 누적 드라이버(종착점) — idea→골렘설계(card_delta)→patch빌드→base누적→스토리→렌더 한 바퀴 무인
"""4조각을 한 파이프라인으로 묶는다. 각 카드에 대해:
  1) card_delta.py(★키): 골렘이 base-델타 자율 설계 → graft 키0 검증 + 교차검산 → 패킷/specqa/참조 작성.
  2) 검증된 참조를 tactics_base_lN으로 동결(다음 patch base).
  3) build_graded --patch(★키): 직전 base에 카드 델타만 패치 → consensus 그린 판정(gate≥1·합의1.0·golden_diff []).
  4) 그린이면 누적, 실패면 마지막 그린 base 보존하고 중단(키 낭비 방지).
끝나면 (b)gen_tactics_story(★키 서사)·(c)gen_tactics_play(렌더)로 완결 후보(엔진+카드+스토리+렌더) 생성 + REPORT.
"엔진+카드+스토리+렌더"가 클로드 손번역 없이 무인으로 — "어디까지=완결 후보까지" 실연.

사용: python driver_autocard.py [--start l8] [--setting "세계관"]   (★키, 사용자 go 뒤에만)
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
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
MAX_SECONDS = int(3.5 * 3600)

# 패밀리별 base 네이밍·렌더 가용(영웅/부대). render=렌더러가 그 출력형식을 지원하나(squad 렌더는 미적응).
FAMILY = {
    "tactics": {"kernel": "tactics_kernel_base", "base": "tactics_base_{}", "render": True},
    "squad": {"kernel": "squad_base", "base": "squad_base_{}", "render": False},
}

# 누적할 카드 계획 — (새 레벨, 이전 레벨, 아이디어). 기본 시연=l9 처형 한 장. 더 누적하려면 줄 추가.
PLAN = [
    ("l9", "l8", "처형(execute): opt-in 정수 hero.execute. 근접(attack)으로 적을 때린 직후, 그 적의 hp가 0보다 크고 hero.execute 이하이면 즉사시켜 hp를 0으로 만든다. 사거리/anomaly/corrosion엔 적용 안 됨, 근접만. 없으면 기존과 동일."),
]


def log(m):
    print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)


def freeze_base(level, family="tactics"):
    """gen_{family}_{level}_golden.REF_GAME_LOGIC를 {family}_base_{level}로 동결(다음 patch base)."""
    from importlib import import_module, reload
    mod = reload(import_module(f"gen_{family}_{level}_golden"))
    out = BASES / FAMILY[family]["base"].format(level)
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(BASES / FAMILY[family]["kernel"], out)
    (out / "src" / "game_logic.js").write_text(mod.REF_GAME_LOGIC, encoding="utf-8")
    return out


def green(cons):
    return bool(cons) and cons.get("gate_passed", 0) >= 1 and \
        cons.get("overall_agreement") == 1.0 and cons.get("golden_diffs") == []


def run(cmd, timeout):
    import os
    env = {**os.environ, "PYTHONUTF8": "1"}
    return subprocess.run(cmd, cwd=str(ROOT), env=env, timeout=timeout).returncode


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="l8", help="시작 base 레벨(이미 graft 검증된 최신)")
    ap.add_argument("--family", default="tactics", help="base 패밀리: tactics(영웅)|squad(부대)")
    ap.add_argument("--setting", default="백 년 전 봉인된 '변칙' 검술을 되살린 마지막 검사가 무너진 제국 성채를 거슬러 봉인의 핵으로 향한다.",
                    help="캠페인 서사 세계관 한 줄")
    ap.add_argument("--ideas-file", default=None,
                    help="propose_cards.py 산출(tactics_ideas.json) 경로. 주면 그 아이디어들로 PLAN 자동 구성(선별 퍼널).")
    ap.add_argument("--max-cards", type=int, default=0, help="ideas-file에서 누적할 카드 수 상한(0=전부)")
    args = ap.parse_args(argv)

    # 선별 퍼널: 제안 아이디어가 있으면 그걸로 PLAN 구성(start 위로 lN+1, lN+2 …). 없으면 기본 PLAN.
    plan = PLAN
    if args.ideas_file:
        ideas = json.loads(Path(args.ideas_file).read_text(encoding="utf-8"))
        if args.max_cards > 0:
            ideas = ideas[:args.max_cards]
        plan = []
        prev = args.start
        for x in ideas:
            nxt = f"l{int(prev[1:]) + 1}"
            idea_text = f"{x.get('name','')}: {x.get('mechanic','')} (관측: {x.get('observable','')})".strip()
            plan.append((nxt, prev, idea_text))
            prev = nxt

    sys.path.insert(0, str(HERE))
    sys.path.insert(0, str(ROOT))
    try:
        from config import force_utf8_stdout
        force_utf8_stdout()
    except Exception:  # noqa: BLE001
        pass

    showcase = BUILD_RUNS / "autocard"
    showcase.mkdir(parents=True, exist_ok=True)
    started = time.time()

    fam = args.family
    # 시작 base 동결(없으면).
    if not (BASES / FAMILY[fam]["base"].format(args.start)).exists():
        freeze_base(args.start, fam)
        log(f"시작 base 동결: {FAMILY[fam]['base'].format(args.start)}")

    results = []
    last_good = args.start
    stopped = None
    for level, prev, idea in plan:
        if time.time() - started > MAX_SECONDS:
            stopped = "시간 상한"
            break
        log(f"=== 카드 {level} (prev {prev}) ===")

        # 1) 설계: card_delta(골렘 base-델타 → graft 키0 검증 + 교차검산)
        rc = run([sys.executable, str(TOOLS / "card_delta.py"), "--family", fam, "--level", level, "--prev", prev,
                  "--idea", idea, "--cap", "3"], MAX_SECONDS)
        if rc != 0 or not (PACKETS / f"planning_packet_{fam}_{level}" / "contract.json").exists():
            stopped = f"{level} card_delta 실패"
            results.append({"level": level, "stage": "design", "ok": False})
            break
        log(f"  설계 OK — 패킷/specqa/참조 작성됨")

        # 2) 새 참조 동결(다음 base)
        freeze_base(level, fam)

        # 3) patch 빌드(직전 base에 델타만)
        out_dir = showcase / level
        if out_dir.exists():
            shutil.rmtree(out_dir)
        rc = run([sys.executable, str(CORE / "build_graded.py"),
                  "--base", str(BASES / FAMILY[fam]["base"].format(prev)),
                  "--packet", str(PACKETS / f"planning_packet_{fam}_{level}"),
                  "--specqa", str(PACKETS / f"specqa_packet_{fam}_{level}"),
                  "--inject-modules", "src/game_logic.js", "--patch", "--cap", "11",
                  "--out", str(out_dir)], MAX_SECONDS)
        cons = None
        cp = out_dir / "consensus.json"
        if cp.exists():
            cons = json.loads(cp.read_text(encoding="utf-8"))
        g = green(cons)
        results.append({"level": level, "stage": "build", "ok": g,
                        "gate": cons.get("gate_passed") if cons else None,
                        "agreement": cons.get("overall_agreement") if cons else None,
                        "golden_clean": (cons.get("golden_diffs") == []) if cons else None})
        log(f"  patch 빌드 {'그린' if g else '실패'} — "
            f"gate={cons.get('gate_passed') if cons else None} "
            f"agree={cons.get('overall_agreement') if cons else None} "
            f"golden_clean={(cons.get('golden_diffs')==[]) if cons else None}")
        if not g:
            stopped = f"{level} patch 빌드 비그린"
            break
        last_good = level

    # 완결 후보: 스토리(★키) + 렌더 — 렌더러가 그 패밀리 출력형식을 지원할 때만(squad 렌더 미적응).
    story_ok = render_ok = False
    if FAMILY[fam]["render"] and (last_good != args.start or not stopped):
        log(f"=== 완결 후보: 스토리 + 렌더 (level {last_good}) ===")
        rc = run([sys.executable, str(TACTICS / "gen_tactics_story.py"), "--idea", args.setting, "--cap", "3"], MAX_SECONDS)
        story_ok = rc == 0
        rc = run([sys.executable, str(TACTICS / "gen_tactics_play.py"), "--level", last_good], MAX_SECONDS)
        render_ok = rc == 0
    elif not FAMILY[fam]["render"]:
        log(f"  (렌더 스킵 — {fam} 렌더러 미적응; 카드 누적만)")

    report = {"start": args.start, "last_good": last_good, "stopped": stopped,
              "cards": results, "story_ok": story_ok, "render_ok": render_ok,
              "elapsed_s": round(time.time() - started)}
    (showcase / "REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"=== 완료 — 누적 {last_good}, 중단={stopped}, 스토리={story_ok}, 렌더={render_ok} → {showcase/'REPORT.json'}")
    return 0 if (stopped is None) else 1


if __name__ == "__main__":
    raise SystemExit(main())
