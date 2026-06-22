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


def latest_level(family):
    """동결된 {family}_base_lN 중 최신(가장 큰 N)을 자동 탐지 — 기계 노브 --start 제거용."""
    import re
    prefix = FAMILY[family]["base"].format("")  # "squad_base_" / "tactics_base_"
    levels = [int(m.group(1)) for d in BASES.iterdir() if d.is_dir()
              for m in [re.fullmatch(re.escape(prefix) + r"l(\d+)", d.name)] if m]
    return f"l{max(levels)}" if levels else None


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
    ap.add_argument("--start", default=None, help="시작 base 레벨(기본=최신 동결 base 자동탐지 — 기계 노브라 비워두면 자동)")
    ap.add_argument("--family", default="tactics", help="base 패밀리: tactics(영웅)|squad(부대)")
    ap.add_argument("--setting", default="백 년 전 봉인된 '변칙' 검술을 되살린 마지막 검사가 무너진 제국 성채를 거슬러 봉인의 핵으로 향한다.",
                    help="캠페인 서사 세계관 한 줄")
    ap.add_argument("--ideas-file", default=None,
                    help="propose_cards.py 산출(tactics_ideas.json) 경로. 주면 그 아이디어들로 PLAN 자동 구성(선별 퍼널).")
    ap.add_argument("--max-cards", type=int, default=0, help="ideas-file에서 누적할 카드 수 상한(0=전부)")
    ap.add_argument("--no-select", action="store_true", help="선별기(★키 의미 비평가) 끄기 — 제안 카드 전부 빌드")
    args = ap.parse_args(argv)

    sys.path.insert(0, str(HERE)); sys.path.insert(0, str(ROOT))
    try:
        from config import force_utf8_stdout
        force_utf8_stdout()
    except Exception:  # noqa: BLE001
        pass

    # 기계 노브 제거: --start 비면 최신 동결 base 자동탐지(사람이 base 번호 외울 필요 없음).
    if not args.start:
        args.start = latest_level(args.family)
        if not args.start:
            ap.error(f"{args.family} 동결 base 없음 — 먼저 커널/카드를 빌드하라")

    # 선별 퍼널: 아이디어 없으면 골렘이 자동 제안(propose_cards ★키) → 진짜 한 명령 무인.
    ideas_path = Path(args.ideas_file) if args.ideas_file else None
    if ideas_path is None:
        n_ideas = args.max_cards if args.max_cards > 0 else 4
        log(f"아이디어 미지정 → 골렘 카드 제안 자동(propose_cards --family {args.family} --n {n_ideas})")
        run([sys.executable, str(TOOLS / "propose_cards.py"), "--family", args.family,
             "--prev", args.start, "--n", str(n_ideas)], MAX_SECONDS)
        ideas_path = BUILD_RUNS / "proposals" / f"{args.family}_ideas.json"
    ideas = json.loads(ideas_path.read_text(encoding="utf-8"))

    # 선별기(★키 의미 비평가): 기존 카드 대비 역할겹침·얕음을 골렘이 평가해 약한 후보 자동 탈락.
    # 빌드 전 단계라 ★키 낭비 전에 거른다. 실패(키/파싱)면 fail-open으로 전부 통과(파이프라인 안 막음).
    if not args.no_select:
        try:
            from propose_cards import critique_ideas
            before = len(ideas)
            ideas, reviews = critique_ideas(ideas, prev=args.start, family=args.family)
            for r in reviews:
                if r.get("verdict") == "drop":
                    log(f"  선별 DROP[{r.get('role','?')}]: {r.get('name')} — {r.get('reason','')}")
            log(f"선별기: {before}개 중 {len(ideas)}개 채택, {before - len(ideas)}개 탈락")
        except Exception as e:  # noqa: BLE001
            log(f"선별기 건너뜀(fail-open): {e}")
    if not ideas:
        log("빌드할 카드 없음(선별기가 전부 탈락 or 빈 아이디어)")
        return 1

    if args.max_cards > 0:
        ideas = ideas[:args.max_cards]
    plan, prev = [], args.start
    for x in ideas:
        nxt = f"l{int(prev[1:]) + 1}"
        idea_text = f"{x.get('name','')}: {x.get('mechanic','')} (관측: {x.get('observable','')})".strip()
        plan.append((nxt, prev, idea_text))
        prev = nxt

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

    # 완결 후보: 레벨(★키)·서사(★키)·렌더 — 패밀리별 마감. 완전 무인 루프의 끝.
    story_ok = render_ok = levels_ok = False
    if last_good != args.start or not stopped:
        log(f"=== 완결 후보 마감 ({fam}, level {last_good}) ===")
        if fam == "squad":
            # 부대: 골렘 레벨 생성(그리디게이트) → 서사 → 뷰어
            rc = run([sys.executable, str(TOOLS / "propose_levels.py"), "--family", "squad", "--prev", last_good,
                      "--n", "5", "--min-turns", "3", "--max-turns", "8"], MAX_SECONDS)
            levels_ok = rc == 0
            rc = run([sys.executable, str(TACTICS / "gen_tactics_levelstory.py"), "--family", "squad",
                      "--idea", args.setting, "--cap", "2"], MAX_SECONDS)
            story_ok = rc == 0
            rc = run([sys.executable, str(TACTICS / "gen_squad_play.py"), "--level", last_good,
                      "--source", "levels"], MAX_SECONDS)
            render_ok = rc == 0
        else:
            rc = run([sys.executable, str(TACTICS / "gen_tactics_story.py"), "--idea", args.setting, "--cap", "3"], MAX_SECONDS)
            story_ok = rc == 0
            rc = run([sys.executable, str(TACTICS / "gen_tactics_play.py"), "--level", last_good], MAX_SECONDS)
            render_ok = rc == 0

    report = {"family": fam, "start": args.start, "last_good": last_good, "stopped": stopped,
              "cards": results, "levels_ok": levels_ok, "story_ok": story_ok, "render_ok": render_ok,
              "elapsed_s": round(time.time() - started)}
    (showcase / "REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"=== 완료 — 누적 {last_good}, 중단={stopped}, 레벨={levels_ok}, 스토리={story_ok}, 렌더={render_ok} → {showcase/'REPORT.json'}")
    return 0 if (stopped is None) else 1


if __name__ == "__main__":
    raise SystemExit(main())
